# backend/agent_definitions.py
import os
import logging
from dotenv import load_dotenv

# Import tframex components needed for instantiation
from tframex.model import VLLMModel
from tframex.agents import BasicAgent, ContextAgent
from tframex.systems import ChainOfAgents, MultiCallSystem

# Import the execution functions
from agents.basic import execute_basic_agent
from agents.context import execute_context_agent
from agents.chain import execute_chain_system
from agents.multi_call import execute_multi_call_system

load_dotenv()
logger = logging.getLogger(__name__)

# --- Central Model Configuration (lazy loaded in flow_executor) ---
# Configuration from Environment (can be used by constructors if needed)
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
    """
    Helper to register agent/system definitions.
    Inputs/Outputs map logical_name -> details_dict {handle_id, description, required?, type?}
    """
    if agent_id in AGENT_REGISTRY:
        # Log a warning instead of crashing if hot-reloading might cause issues
        logger.warning(f"Agent/System with ID '{agent_id}' is being re-registered.")
        # raise ValueError(f"Agent/System with ID '{agent_id}' already registered.")

    # Validate basic structure
    for logical_name, details in inputs.items():
        if not isinstance(details, dict) or 'handle_id' not in details:
            raise ValueError(f"Input '{logical_name}' for agent '{agent_id}' is missing 'handle_id' in its definition.")
    for logical_name, details in outputs.items():
         if not isinstance(details, dict) or 'handle_id' not in details:
            raise ValueError(f"Output '{logical_name}' for agent '{agent_id}' is missing 'handle_id' in its definition.")

    AGENT_REGISTRY[agent_id] = {
        "id": agent_id,
        "name": name,
        "description": description,
        "type": agent_type, # 'agent' or 'system'
        "inputs": inputs, # Dict: { logical_name: { handle_id: str, description: str, required?: bool, type?: str } }
        "outputs": outputs, # Dict: { logical_name: { handle_id: str, description: str, type?: str } }
        "constructor": constructor, # Function/Class to create an instance (takes model)
        "execute_function": execute_function # Async function that runs the logic
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

# --- Functions to Access Definitions ---
def get_definitions():
    """Returns a list of definitions suitable for the frontend."""
    frontend_definitions = []
    for agent_id, definition in AGENT_REGISTRY.items():
         # Simplify inputs/outputs for frontend if needed, or send full details
        frontend_definitions.append({
            "id": definition["id"],
            "name": definition["name"],
            "description": definition.get("description", ""),
            "type": definition.get("type", "unknown"),
            # Send simplified inputs/outputs (name: description) or full structure
            "inputs": { lname: details.get("description", "") for lname, details in definition.get("inputs", {}).items() },
            "outputs": { lname: details.get("description", "") for lname, details in definition.get("outputs", {}).items() },
            # Optionally send handle IDs if frontend needs them for validation?
            "input_handles": { lname: details["handle_id"] for lname, details in definition.get("inputs", {}).items() },
            "output_handles": { lname: details["handle_id"] for lname, details in definition.get("outputs", {}).items() },
        })
    return frontend_definitions

def get_definition(agent_id):
    """Returns the full internal definition for an agent ID."""
    return AGENT_REGISTRY.get(agent_id)

logger.info(f"Agent Registry loaded with {len(AGENT_REGISTRY)} definitions.")