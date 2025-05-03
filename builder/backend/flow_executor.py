# backend/flow_executor.py
import asyncio
import os
import logging
import time
import re # Import re for stripping tags
from typing import List, Dict, Any, Set, Optional, Tuple
from collections import deque, defaultdict
from dotenv import load_dotenv

# Import agent definitions and model setup
from agent_definitions import get_definition # Import only the getter
from tframex.model import VLLMModel

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("FlowExecutor") # Use a consistent logger name

# --- Model Setup ---
API_URL = os.getenv("API_URL")
API_KEY = os.getenv("API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME")
DEFAULT_MAX_TOKENS = int(os.getenv("MAX_TOKENS", 32000))
DEFAULT_TEMPERATURE = float(os.getenv("TEMPERATURE", 0.7))

vllm_model_instance: Optional[VLLMModel] = None
model_lock = asyncio.Lock()

async def get_model() -> VLLMModel:
    """Gets or creates the VLLMModel instance."""
    global vllm_model_instance
    async with model_lock:
        if vllm_model_instance is None:
            logger.info("Initializing VLLM Model instance...")
            try:
                vllm_model_instance = VLLMModel(
                    model_name=MODEL_NAME,
                    api_url=API_URL,
                    api_key=API_KEY,
                    default_max_tokens=DEFAULT_MAX_TOKENS,
                    default_temperature=DEFAULT_TEMPERATURE
                )
                logger.info("VLLM Model instance created.")
            except Exception as e:
                logger.error(f"Fatal Error: Failed to initialize VLLM Model: {e}", exc_info=True)
                raise RuntimeError(f"Could not initialize VLLM Model: {e}")
        return vllm_model_instance

# --- Helper Functions ---

# NEW: Function to strip <think> tags
def strip_think_tags(text: str) -> str:
    """Removes content up to and including the first </think> tag if present."""
    if not isinstance(text, str): # Ensure input is a string
        return text # Return non-strings as-is

    think_end_tag = "</think>"
    tag_pos = text.find(think_end_tag)
    if tag_pos != -1:
        logger.debug("Found </think> tag, stripping preceding content.")
        # Add basic check for content after tag
        content_after = text[tag_pos + len(think_end_tag):].strip()
        return content_after
    else:
        logger.debug("No </think> tag found, using full response.")
        return text.strip() # Return original text (stripped) if tag not found

# Helper for Handle Mapping
def find_logical_name_for_handle(definition: Dict, handle_id: str, io_type: str) -> Optional[str]:
    """Finds the logical input/output name corresponding to a handle ID."""
    if not definition or io_type not in definition:
        return None
    io_map = definition[io_type] # Either 'inputs' or 'outputs' dict
    for logical_name, details in io_map.items():
        if isinstance(details, dict) and details.get('handle_id') == handle_id:
            return logical_name
    # Fallback: if handle_id itself is a key (less likely with new structure)
    if handle_id in io_map:
        logger.debug(f"Falling back to using handle_id '{handle_id}' as logical name for {io_type}.")
        return handle_id
    return None

# --- Dynamic Flow Execution Logic ---
async def run_flow(nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]) -> str:
    """
    Executes the flow topologically based on nodes and edges.
    Passes data between nodes according to edge connections and handle mapping.
    Strips <think> tags from string outputs before logging or passing downstream.
    """
    run_id = f"run_{int(time.time())}"
    logger.info(f"--- Starting Dynamic Flow Execution ({run_id}) ---")
    output_log = [f"--- Flow Execution Start ({run_id}) ---"]
    start_time = time.time()

    if not nodes:
        output_log.append("No nodes found in the flow.")
        output_log.append(f"--- Flow Execution End ({run_id}) ---")
        return "\n".join(output_log)

    # 1. Build Graph Representation & Dependencies
    adj: Dict[str, List[Tuple[str, str, str]]] = defaultdict(list) # source_id -> list[(target_id, source_handle, target_handle)]
    in_degree: Dict[str, int] = defaultdict(int)
    node_map: Dict[str, Dict] = {node['id']: node for node in nodes}
    all_node_ids: Set[str] = set(node_map.keys())

    # Map target node ID -> { target_logical_input_name: True } if connected by an edge
    connected_logical_inputs: Dict[str, Dict[str, bool]] = defaultdict(dict)

    # Process edges
    for edge in edges:
        source_id = edge.get('source')
        target_id = edge.get('target')
        source_handle = edge.get('sourceHandle') # Visual handle ID on source node
        target_handle = edge.get('targetHandle') # Visual handle ID on target node

        if source_id in all_node_ids and target_id in all_node_ids and source_handle and target_handle:
            adj[source_id].append((target_id, source_handle, target_handle))
            in_degree[target_id] += 1

            # Map the connection to the target's logical input name
            target_definition = get_definition(node_map.get(target_id, {}).get('type'))
            logical_input_name = find_logical_name_for_handle(target_definition, target_handle, 'inputs')
            if logical_input_name:
                connected_logical_inputs[target_id][logical_input_name] = True
                logger.debug(f"[{run_id}] Edge maps: {source_id}[{source_handle}] -> {target_id}[{target_handle}] (logical input: '{logical_input_name}')")
            else:
                logger.warning(f"[{run_id}] Edge target handle '{target_handle}' on node {target_id} does not map to a defined logical input.")
        else:
            logger.warning(f"[{run_id}] Skipping invalid edge: {edge}")

    # 2. Initialize Execution State
    queue = deque([node_id for node_id in all_node_ids if in_degree[node_id] == 0])
    execution_results: Dict[str, Dict[str, Any]] = {} # node_id -> {logical_output_name: stripped_value}
    node_input_data: Dict[str, Dict[str, Any]] = defaultdict(dict) # node_id -> {logical_input_name: stripped_value}
    executed_nodes: Set[str] = set()
    agent_instances: Dict[str, Any] = {} # Store instantiated agents/systems

    # Get model instance once
    try:
        model = await get_model()
    except RuntimeError as e:
        output_log.append(f"\n## FATAL ERROR: Could not initialize model: {e} ##")
        output_log.append(f"--- Flow Execution End ({run_id}) ---")
        return "\n".join(output_log)


    # Instantiate agents/systems
    for node_id, node in node_map.items():
        node_type = node.get('type')
        definition = get_definition(node_type)
        if definition and definition.get('constructor'):
            try:
                agent_instances[node_id] = definition['constructor'](model)
                logger.info(f"[{run_id}] Instantiated agent/system for node {node_id} ({node_type})")
            except Exception as e:
                logger.error(f"[{run_id}] Failed to instantiate node {node_id} ({node_type}): {e}", exc_info=True)
                output_log.append(f"\n## ERROR: Failed to instantiate node {node_id} ({node_type}): {e} ##")
                # Mark as not instantiated by *not* adding to agent_instances

    # 3. Execute Nodes Topologically
    exec_count = 0
    while queue:
        exec_count += 1
        if exec_count > len(all_node_ids) * 2: # Basic cycle detection
             logger.error(f"[{run_id}] Potential cycle detected or excessive execution. Stopping.")
             output_log.append("\n## ERROR: Potential cycle detected or flow stuck. Execution halted. ##")
             break

        node_id = queue.popleft()

        if node_id not in node_map:
            logger.warning(f"[{run_id}] Node {node_id} from queue not found in map. Skipping.")
            continue
        if node_id not in agent_instances:
            # Node failed instantiation, log and skip execution
            node_type_for_log = node_map.get(node_id, {}).get('type', 'Unknown Type')
            logger.warning(f"[{run_id}] Node {node_id} ({node_type_for_log}) was not instantiated successfully. Skipping execution.")
            output_log.append(f"\n--- Node: {node_id} ({node_type_for_log}) ---")
            output_log.append(f"Status: SKIPPED (Instantiation Failed)")
            # We don't decrement downstream in_degrees here; the flow should naturally stop
            # if required inputs are missing due to this node's failure.
            continue


        node = node_map[node_id]
        node_type = node.get('type')
        definition = get_definition(node_type)
        agent_instance = agent_instances[node_id]

        if not definition or not definition.get('execute_function'):
            logger.warning(f"[{run_id}] No definition or execute_function for node {node_id} ({node_type}). Skipping.")
            output_log.append(f"\n--- Node: {node_id} ({node_type}) ---")
            output_log.append(f"Status: SKIPPED (No execute function defined)")
            continue

        # Gather input data: Start with defaults/data from the node config,
        # then overwrite/add data received from connected upstream nodes.
        current_node_inputs = node.get('data', {}).copy()
        # Filter node data to only include defined inputs (prevent passing 'label' etc.)
        defined_input_names = set(definition.get('inputs', {}).keys())
        current_node_inputs = {k: v for k, v in current_node_inputs.items() if k in defined_input_names}

        # Add data from incoming edges (already stripped by upstream nodes)
        current_node_inputs.update(node_input_data[node_id])

        # Check for missing required inputs that were expected via edges
        missing_required = False
        for logical_name, details in definition.get('inputs', {}).items():
            is_required = details.get('required', False)
            was_connected = connected_logical_inputs.get(node_id, {}).get(logical_name, False)
            if is_required and was_connected and logical_name not in current_node_inputs:
                 logger.error(f"[{run_id}] Node {node_id}: Required input '{logical_name}' was connected but data is missing.")
                 output_log.append(f"\n--- Node: {node_id} ({node_type}) ---")
                 output_log.append(f"Status: FAILED")
                 output_log.append(f"Error: Missing required input data for '{logical_name}' from connected edge.")
                 missing_required = True
                 break # Stop processing this node

        if missing_required:
             continue # Move to next node in queue

        logger.info(f"[{run_id}] Executing Node: {node_id} ({node_type}) with inputs: { {k:str(v)[:50]+'...' if isinstance(v, str) and len(v)>50 else v for k,v in current_node_inputs.items()} }")
        output_log.append(f"\n--- Node: {node_id} ({node_type}) ---")

        try:
            # Execute the node's logic
            raw_node_outputs = await definition['execute_function'](agent_instance, current_node_inputs)

            if not isinstance(raw_node_outputs, dict):
                 logger.warning(f"[{run_id}] Node {node_id} execution function did not return a dictionary. Result: {raw_node_outputs}")
                 # Attempt to wrap if there's a single logical output defined
                 output_keys = list(definition.get('outputs', {}).keys())
                 if len(output_keys) == 1:
                      raw_node_outputs = {output_keys[0]: raw_node_outputs}
                 else:
                      # Fallback: wrap in a generic 'output' key
                      raw_node_outputs = {"output": str(raw_node_outputs)}

            # *** NEW: Strip <think> tags from string outputs ***
            processed_node_outputs = {}
            for logical_out_name, out_value in raw_node_outputs.items():
                if isinstance(out_value, str):
                    stripped_value = strip_think_tags(out_value)
                    if stripped_value != out_value: # Log if stripping actually happened
                         logger.info(f"[{run_id}] Node {node_id}: Stripped <think> tags from output '{logical_out_name}'.")
                    processed_node_outputs[logical_out_name] = stripped_value
                else:
                    processed_node_outputs[logical_out_name] = out_value # Keep non-strings as is


            execution_results[node_id] = processed_node_outputs # Store *stripped* results
            executed_nodes.add(node_id)

            # Log success and *stripped* output
            output_log.append(f"Status: Success")
            for logical_out_name, stripped_value in processed_node_outputs.items():
                 output_log.append(f"Output '{logical_out_name}':\n{str(stripped_value)}") # Log each named *stripped* output

            logger.info(f"[{run_id}] Node {node_id} execution successful.")

            # Process downstream nodes (pass *stripped* data and decrement in_degree)
            for target_id, source_handle, target_handle in adj[node_id]:
                 target_node = node_map.get(target_id)
                 target_definition = get_definition(target_node.get('type')) if target_node else None

                 if target_node and target_definition:
                    # Find the logical names for the connection
                    logical_output_name = find_logical_name_for_handle(definition, source_handle, 'outputs')
                    logical_input_name = find_logical_name_for_handle(target_definition, target_handle, 'inputs')

                    if logical_output_name and logical_input_name:
                        # Get the *stripped* value using the logical output name
                        output_value_to_pass = processed_node_outputs.get(logical_output_name)

                        if output_value_to_pass is not None:
                            # Store using the logical input name for the target
                            node_input_data[target_id][logical_input_name] = output_value_to_pass # Pass stripped value
                            logger.info(f"[{run_id}] Passing output '{logical_output_name}' from {node_id} (handle '{source_handle}') to input '{logical_input_name}' of {target_id} (handle '{target_handle}')")
                        else:
                             logger.warning(f"[{run_id}] Logical output '{logical_output_name}' (from handle '{source_handle}') not found in processed results of node {node_id}. Cannot pass data to {target_id}.")
                    else:
                        logger.warning(f"[{run_id}] Could not map handles for edge {node_id}[{source_handle}] -> {target_id}[{target_handle}]. Cannot pass data.")

                    # Decrement in_degree and check readiness
                    in_degree[target_id] -= 1
                    if in_degree[target_id] == 0:
                         # Check if all *required connected* inputs have arrived (more robust check)
                         is_ready = True
                         target_reqs = target_definition.get('inputs', {})
                         for req_logical_name, details in target_reqs.items():
                              is_req = details.get('required', False)
                              was_connected = connected_logical_inputs.get(target_id, {}).get(req_logical_name, False)
                              # Check node_input_data which now holds the stripped values passed from upstream
                              if is_req and was_connected and req_logical_name not in node_input_data[target_id]:
                                   is_ready = False
                                   logger.debug(f"[{run_id}] Node {target_id} still waiting for required connected input '{req_logical_name}'.")
                                   break

                         if is_ready:
                            if target_id not in executed_nodes and target_id not in queue:
                                logger.info(f"[{run_id}] Node {target_id} is now ready (in_degree 0 and required inputs met). Adding to queue.")
                                queue.append(target_id)
                         elif target_id not in executed_nodes:
                              logger.debug(f"[{run_id}] Node {target_id} has in_degree 0 but still waiting for inputs.")

        except Exception as e:
            logger.error(f"[{run_id}] Error during execution or downstream processing for node {node_id} ({node_type}): {e}", exc_info=True)
            output_log.append(f"Status: FAILED")
            output_log.append(f"Error:\n{e}")
            # Stop processing downstream for this node, but others continue

    # 4. Compile Final Output Log
    output_log.append(f"\n--- Execution Summary ({run_id}) ---")
    executed_count = len(executed_nodes)
    total_nodes = len(all_node_ids)
    if executed_count == total_nodes:
         output_log.append("All nodes executed successfully.")
    else:
         output_log.append(f"Executed {executed_count}/{total_nodes} nodes.")
         failed_or_skipped = all_node_ids - executed_nodes
         if failed_or_skipped:
             output_log.append(f"Failed/Skipped/Waiting nodes: {', '.join(failed_or_skipped)}")

    end_time = time.time()
    output_log.append(f"\n--- Flow Execution End ({run_id}) ---")
    output_log.append(f"Total execution time: {end_time - start_time:.2f} seconds")
    logger.info(f"--- Dynamic Flow Execution Finished ({run_id}) ---")

    return "\n".join(output_log)

# Example usage (for testing if run directly, though typically called from elsewhere)
if __name__ == '__main__':
    async def main():
        # Define a simple test flow
        test_nodes = [
            {"id": "node_1", "type": "TextInput", "data": {"text": "<think>This is internal thought.</think>Hello World!"}},
            {"id": "node_2", "type": "ConsoleOutput", "data": {}}, # Requires 'text' input
        ]
        test_edges = [
            {"source": "node_1", "sourceHandle": "text_output", "target": "node_2", "targetHandle": "text_input"}
        ]

        # Mock agent definitions for testing
        MOCK_DEFINITIONS = {
            "TextInput": {
                "constructor": lambda model: None, # Doesn't need model
                "execute_function": lambda instance, inputs: {"text_output": inputs.get("text", "Default Text")},
                "inputs": {"text": {"handle_id": "text_input_unused", "required": False}}, # Input usually set via node data
                "outputs": {"text_output": {"handle_id": "text_output"}}
            },
            "ConsoleOutput": {
                "constructor": lambda model: None,
                "execute_function": lambda instance, inputs: {"status": f"Received: {inputs.get('text_input', 'NOTHING')}"},
                "inputs": {"text_input": {"handle_id": "text_input", "required": True}},
                "outputs": {"status": {"handle_id": "status_output"}}
            }
        }

        original_get_definition = get_definition # Backup
        def mock_get_definition(node_type: str):
             return MOCK_DEFINITIONS.get(node_type)

        # Replace get_definition with mock
        import agent_definitions
        agent_definitions.get_definition = mock_get_definition

        print("--- Running Test Flow ---")
        result_log = await run_flow(test_nodes, test_edges)
        print("\n--- Execution Log ---")
        print(result_log)
        print("--- End Test Flow ---")

        # Restore original get_definition
        agent_definitions.get_definition = original_get_definition

    asyncio.run(main())