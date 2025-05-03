# backend/flow_executor.py
import asyncio
import os
import logging
import time
from typing import List, Dict, Any, Set, Optional, Tuple
from collections import deque, defaultdict
from dotenv import load_dotenv

# Import agent definitions and model setup
from agent_definitions import get_definition # Import only the getter
from tframex.model import VLLMModel

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("FlowExecutor")

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

# --- Helper Function for Handle Mapping ---
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
        return handle_id
    return None

# --- Dynamic Flow Execution Logic ---
async def run_flow(nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]) -> str:
    """
    Executes the flow topologically based on nodes and edges.
    Passes data between nodes according to edge connections and handle mapping.
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
            else:
                logger.warning(f"[{run_id}] Edge target handle '{target_handle}' on node {target_id} does not map to a defined logical input.")
        else:
            logger.warning(f"[{run_id}] Skipping invalid edge: {edge}")

    # 2. Initialize Execution State
    queue = deque([node_id for node_id in all_node_ids if in_degree[node_id] == 0])
    execution_results: Dict[str, Dict[str, Any]] = {} # node_id -> {logical_output_name: value}
    node_input_data: Dict[str, Dict[str, Any]] = defaultdict(dict) # node_id -> {logical_input_name: value}
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
                # Consider failing fast or marking node as failed

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
            logger.warning(f"[{run_id}] Node {node_id} ({node_map[node_id].get('type')}) failed instantiation. Skipping execution.")
            # Decrement in_degree for downstream nodes as this one won't provide output
            for target_id, _, _ in adj[node_id]:
                 in_degree[target_id] -= 1
                 # Check readiness? Risky if other inputs were expected. Better to let flow fail naturally.
            continue


        node = node_map[node_id]
        node_type = node.get('type')
        definition = get_definition(node_type)
        agent_instance = agent_instances[node_id]

        if not definition or not definition.get('execute_function'):
            logger.warning(f"[{run_id}] No definition or execute_function for node {node_id} ({node_type}). Skipping.")
            continue

        # Gather input data: Start with defaults/data from the node config,
        # then overwrite/add data received from connected upstream nodes.
        current_node_inputs = node.get('data', {}).copy()
        # Filter node data to only include defined inputs (prevent passing 'label' etc.)
        defined_input_names = set(definition.get('inputs', {}).keys())
        current_node_inputs = {k: v for k, v in current_node_inputs.items() if k in defined_input_names}

        # Add data from incoming edges
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
            node_outputs = await definition['execute_function'](agent_instance, current_node_inputs)

            if not isinstance(node_outputs, dict):
                 logger.warning(f"[{run_id}] Node {node_id} execution function did not return a dictionary. Result: {node_outputs}")
                 # Attempt to wrap if there's a single logical output defined
                 output_keys = list(definition.get('outputs', {}).keys())
                 if len(output_keys) == 1:
                      node_outputs = {output_keys[0]: node_outputs}
                 else:
                      node_outputs = {"output": str(node_outputs)} # Fallback


            execution_results[node_id] = node_outputs # Store results keyed by logical output name
            executed_nodes.add(node_id)

            # Log success and output
            output_log.append(f"Status: Success")
            for logical_out_name, out_value in node_outputs.items():
                 output_log.append(f"Output '{logical_out_name}':\n{str(out_value)}") # Log each named output

            logger.info(f"[{run_id}] Node {node_id} execution successful.")

            # Process downstream nodes (pass data and decrement in_degree)
            for target_id, source_handle, target_handle in adj[node_id]:
                 target_node = node_map.get(target_id)
                 target_definition = get_definition(target_node.get('type')) if target_node else None

                 if target_node and target_definition:
                    # Find the logical names for the connection
                    logical_output_name = find_logical_name_for_handle(definition, source_handle, 'outputs')
                    logical_input_name = find_logical_name_for_handle(target_definition, target_handle, 'inputs')

                    if logical_output_name and logical_input_name:
                        # Get the value using the logical output name
                        output_value = node_outputs.get(logical_output_name)

                        if output_value is not None:
                            # Store using the logical input name for the target
                            node_input_data[target_id][logical_input_name] = output_value
                            logger.info(f"[{run_id}] Passing output '{logical_output_name}' from {node_id} (handle '{source_handle}') to input '{logical_input_name}' of {target_id} (handle '{target_handle}')")
                        else:
                             logger.warning(f"[{run_id}] Logical output '{logical_output_name}' (from handle '{source_handle}') not found in results of node {node_id}. Cannot pass data to {target_id}.")
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