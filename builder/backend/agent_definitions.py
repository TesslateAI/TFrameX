# backend/agent_definitions.py
import os
import logging
from dotenv import load_dotenv

# Import tframex components needed for instantiation
from tframex.model import VLLMModel
from tframex.agents import BasicAgent, ContextAgent # BasicAgent is needed for FlowBuilder
from tframex.systems import ChainOfAgents, MultiCallSystem

# Import the execution functions
from agents.basic import execute_basic_agent
from agents.context import execute_context_agent
from agents.chain import execute_chain_system
from agents.multi_call import execute_multi_call_system
from agents.flow_builder import execute_flow_builder_agent # <-- NEW IMPORT

load_dotenv()
logger = logging.getLogger(__name__)

# --- Configs (remain the same) ---
API_URL = os.getenv("API_URL")
API_KEY = os.getenv("API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME")
DEFAULT_MAX_TOKENS = int(os.getenv("MAX_TOKENS", 32000))
DEFAULT_TEMPERATURE = float(os.getenv("TEMPERATURE", 0.7))
MULTI_CALL_OUTPUT_DIR = os.getenv("MULTI_CALL_OUTPUT_DIR", "example_outputs/ex4_multi_call_outputs")
CHAIN_CHUNK_SIZE = int(os.getenv("CHAIN_CHUNK_SIZE", 2000))
CHAIN_CHUNK_OVERLAP = int(os.getenv("CHAIN_CHUNK_OVERLAP", 200))

# --- Agent/System Definition Registry ---
AGENT_REGISTRY = {}

def register_agent(agent_id, name, description, agent_type, inputs, outputs, constructor, execute_function):
    """Helper to register agent/system definitions."""
    if agent_id in AGENT_REGISTRY:
        logger.warning(f"Agent/System with ID '{agent_id}' is being re-registered.")

    # Basic validation
    for logical_name, details in inputs.items():
        if not isinstance(details, dict) or 'handle_id' not in details:
             # Allow simple descriptions for agents like flowBuilder that don't use visual handles
             if not isinstance(details, dict) or 'description' not in details:
                  raise ValueError(f"Input '{logical_name}' for agent '{agent_id}' lacks details.")
    for logical_name, details in outputs.items():
        if not isinstance(details, dict) or 'description' not in details: # Output might not need handle_id
             raise ValueError(f"Output '{logical_name}' for agent '{agent_id}' lacks details.")

    AGENT_REGISTRY[agent_id] = {
        "id": agent_id,
        "name": name,
        "description": description,
        "type": agent_type,
        "inputs": inputs,
        "outputs": outputs,
        "constructor": constructor,
        "execute_function": execute_function
    }
    logger.debug(f"Registered agent/system: {agent_id}")

# --- Define Your Agents/Systems with Explicit Handles ---

# Basic Agent
register_agent(
    agent_id="basicAgent",
    name="Basic Agent",
    description="A simple agent that takes a prompt and returns a response.",
    agent_type="agent",
    inputs={
        "prompt": {
            "handle_id": "prompt_in",
            "description": "The main instruction or question.",
            "required": True,
            "type": "string"
        },
        "max_tokens": {
            "handle_id": "max_tokens_in",
            "description": "(Optional) Max tokens for the response.",
            "required": False,
            "type": "integer"
        }
    },
    outputs={
        "output": {
            "handle_id": "output_out",
            "description": "The generated response text.",
            "type": "string"
        }
    },
    constructor=lambda model: BasicAgent(agent_id="dynamic_basic", model=model),
    execute_function=execute_basic_agent
)

# Context Agent
register_agent(
    agent_id="contextAgent",
    name="Context Agent",
    description="An agent that considers provided context along with the prompt.",
    agent_type="agent",
    inputs={
        "prompt": {
            "handle_id": "prompt_in",
            "description": "The main instruction or question.",
            "required": True,
            "type": "string"
        },
        "context": {
            "handle_id": "context_in",
            "description": "Background text or information.",
            "required": True, # Make context required if passed via edge usually
            "type": "string"
        },
        "max_tokens": {
            "handle_id": "max_tokens_in",
            "description": "(Optional) Max tokens for the response.",
            "required": False,
            "type": "integer"
        }
    },
    outputs={
        "output": {
            "handle_id": "output_out",
            "description": "The generated response text.",
            "type": "string"
        }
    },
    constructor=lambda model: ContextAgent(agent_id="dynamic_context", model=model, context=""), # Default context empty
    execute_function=execute_context_agent
)

# Chain of Agents System
register_agent(
    agent_id="chainOfAgents",
    name="Chain of Agents",
    description="Summarizes or answers questions about long text by processing it in chunks.",
    agent_type="system",
    inputs={
        "initial_prompt": {
            "handle_id": "prompt_in",
            "description": "The prompt guiding the overall task.",
            "required": True,
            "type": "string"
        },
        "long_text": {
            "handle_id": "text_in",
            "description": "The long document to process.",
            "required": True,
            "type": "string"
        },
        "max_tokens": {
            "handle_id": "max_tokens_in",
            "description": "(Optional) Max tokens for the final combined response.",
            "required": False,
            "type": "integer"
        }
        # Note: chunk_size, chunk_overlap are configured via constructor, not input handles
    },
    outputs={
        "output": {
            "handle_id": "output_out",
            "description": "The final combined response.",
            "type": "string"
        }
    },
    constructor=lambda model: ChainOfAgents(
        system_id="dynamic_chain",
        model=model,
        chunk_size=CHAIN_CHUNK_SIZE,
        chunk_overlap=CHAIN_CHUNK_OVERLAP
    ),
    execute_function=execute_chain_system
)

# Multi Call System
register_agent(
    agent_id="multiCallSystem",
    name="Multi Call System",
    description="Runs the same prompt multiple times concurrently, saving outputs.",
    agent_type="system",
    inputs={
        "prompt": {
            "handle_id": "prompt_in",
            "description": "The prompt to run multiple times.",
            "required": True,
            "type": "string"
        },
        "num_calls": {
            "handle_id": "num_calls_in",
            "description": "Number of concurrent calls (default: 3).",
            "required": False,
            "type": "integer"
        },
        "base_filename": {
            "handle_id": "filename_in",
            "description": "Base name for output files (default: multi_output).",
            "required": False,
            "type": "string"
        },
        "max_tokens": {
            "handle_id": "max_tokens_in",
            "description": "(Optional) Max tokens for each individual call's response.",
            "required": False,
            "type": "integer"
        }
        # Note: output_dir is configured via constructor
    },
    outputs={
        "output": { # The summary log is the primary output here
            "handle_id": "output_out",
            "description": "A summary log of the file paths or errors.",
            "type": "string"
        }
    },
    constructor=lambda model: MultiCallSystem(
        system_id="dynamic_multi",
        model=model,
        default_output_dir=MULTI_CALL_OUTPUT_DIR
    ),
    execute_function=execute_multi_call_system
)

# --- Flow Builder Agent (NEW) ---
register_agent(
    agent_id="flowBuilderAgent",
    name="Flow Builder Agent",
    description="Internal agent used by the chatbot sidebar to generate/modify flows.",
    agent_type="agent", # It acts like an agent taking instructions
    inputs={
        # These inputs are not visual handles, just logical data for the execution function
        "user_message": {"description": "The natural language request from the user."},
        "available_nodes_context": {"description": "String describing available node types."},
        "current_flow_context": {"description": "JSON string of the current nodes and edges."}
    },
    outputs={
        # This output is not a visual handle, it's the raw result for the API handler
        "raw_llm_output": {"description": "The raw output from the LLM, potentially including <think> tags and JSON."}
    },
    # Use a BasicAgent instance as the underlying executor for the complex prompt
    constructor=lambda model: BasicAgent(agent_id="dynamic_flowbuilder", model=model),
    execute_function=execute_flow_builder_agent
)

# --- Functions to Access Definitions ---
def get_definitions_for_frontend():
    """Returns a list of definitions suitable for the frontend node list."""
    frontend_definitions = []
    # Exclude internal agents like flowBuilderAgent from the node list
    excluded_ids = {"flowBuilderAgent"}
    for agent_id, definition in AGENT_REGISTRY.items():
        if agent_id in excluded_ids:
            continue

        frontend_definitions.append({
            "id": definition["id"],
            "name": definition["name"],
            "description": definition.get("description", ""),
            "type": definition.get("type", "unknown"),
            "inputs": { lname: details.get("description", "") for lname, details in definition.get("inputs", {}).items() if details.get("handle_id")}, # Only show handle inputs
            "outputs": { lname: details.get("description", "") for lname, details in definition.get("outputs", {}).items() if details.get("handle_id")}, # Only show handle outputs
            "input_handles": { lname: details["handle_id"] for lname, details in definition.get("inputs", {}).items() if details.get("handle_id")},
            "output_handles": { lname: details["handle_id"] for lname, details in definition.get("outputs", {}).items() if details.get("handle_id")},
        })
    return frontend_definitions

def get_definition(agent_id):
    """Returns the full internal definition for an agent ID."""
    return AGENT_REGISTRY.get(agent_id)

logger.info(f"Agent Registry loaded with {len(AGENT_REGISTRY)} definitions.")
