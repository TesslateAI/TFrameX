# backend/app.py
import os
import asyncio
import json # Import json for parsing
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import backend components
# Use the specific function names from the first snippet
from flow_executor import run_flow, get_model, strip_think_tags
from agent_definitions import get_definitions_for_frontend, get_definition

# Basic logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("FlaskServer")

app = Flask(__name__)
# Allow requests from your frontend development server
CORS(app, resources={r"/api/*": {"origins": "http://localhost:5173"}}) # Adjust port if needed

# Create necessary directories (ensure paths align with agent_definitions.py if needed)
# Keep this section from the second snippet as it's robust
required_dirs = [
    "example_outputs",
    os.path.join("example_outputs", "ex4_multi_call_outputs") # Specific subdir for MultiCall if used
]
for dir_path in required_dirs:
    if not os.path.exists(dir_path):
        try:
            os.makedirs(dir_path, exist_ok=True)
            logger.info(f"Created directory: {dir_path}")
        except OSError as e:
            logger.error(f"Failed to create directory {dir_path}: {e}")

# --- API Endpoints ---

@app.route('/')
def index():
    return "Backend is running. Use API endpoints."

@app.route('/api/agents', methods=['GET'])
def list_agents():
    """Returns the list of agent definitions suitable for the frontend sidebar."""
    # This implementation uses the specific getter from the first snippet
    logger.info("Request received on /api/agents")
    try:
        # Use the specific getter for frontend definitions
        definitions = get_definitions_for_frontend()
        return jsonify(definitions)
    except Exception as e:
        logger.error(f"Error getting agent definitions: {e}", exc_info=True)
        return jsonify({"error": "Failed to load agent definitions"}), 500

@app.route('/api/run', methods=['POST'])
async def handle_run_flow():
    """
    Handles requests to execute a flow defined by nodes and edges.
    Uses the dynamic flow executor.
    """
    # This implementation is largely the same as both snippets, keep the detailed logging one.
    logger.info("Received request on /api/run")
    if not request.is_json:
        logger.warning("Request is not JSON")
        return jsonify({"error": "Request must be JSON"}), 400

    data = request.get_json()
    nodes = data.get('nodes')
    edges = data.get('edges')

    if nodes is None or edges is None:
        logger.warning("Missing 'nodes' or 'edges' in request data")
        return jsonify({"error": "Missing 'nodes' or 'edges' in request data"}), 400

    logger.info(f"Received {len(nodes)} nodes and {len(edges)} edges for dynamic execution.")
    node_types = [n.get('type', 'unknown') for n in nodes]
    logger.debug(f"Node types received: {node_types}")

    try:
        # Run the dynamic flow execution logic asynchronously
        result_log = await run_flow(nodes, edges)
        logger.info("Dynamic flow execution completed.")
        return jsonify({"output": result_log})
    except RuntimeError as e:
         logger.error(f"Runtime error during flow execution: {e}", exc_info=True)
         return jsonify({"error": f"Runtime Error: {e}"}), 500
    except ImportError as e:
        logger.error(f"Import error, check agent definitions/imports: {e}", exc_info=True)
        return jsonify({"error": f"Import Error: {e}. Check backend agent setup."}), 500
    except Exception as e:
        logger.error(f"An unexpected error occurred during flow execution: {e}", exc_info=True)
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500


# --- NEW: Chatbot Endpoint (from the first snippet) ---
@app.route('/api/chatbot', methods=['POST'])
async def handle_chatbot():
    """Handles requests to the flow builder chatbot."""
    logger.info("Received request on /api/chatbot")
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    data = request.get_json()
    user_message = data.get('message')
    current_nodes = data.get('nodes', [])
    current_edges = data.get('edges', [])
    available_defs_frontend = data.get('definitions', []) # Definitions sent from frontend

    if not user_message:
        return jsonify({"error": "Missing 'message' in request data"}), 400

    try:
        # 1. Prepare Context for the Agent
        # Format available nodes info (simple string representation)
        # Ensure we access fields correctly based on get_definitions_for_frontend output
        available_nodes_str = "\n".join([
            f"- ID: {d['id']}, Name: {d['name']}, Type: {d['type']}, Desc: {d.get('description', 'No description')}"
            for d in available_defs_frontend
        ])
        # Format current flow state as JSON string
        current_flow_str = json.dumps({"nodes": current_nodes, "edges": current_edges}, indent=2)

        # 2. Get the Flow Builder Agent Instance
        agent_id = "flowBuilderAgent" # The specific ID for your chatbot agent
        definition = get_definition(agent_id) # Use the specific getter
        if not definition or not definition.get('constructor') or not definition.get('execute_function'):
            logger.error(f"Flow Builder Agent ('{agent_id}') not defined correctly.")
            return jsonify({"reply": "Error: Chatbot agent is not configured on the server.", "flow": None}), 500

        model = await get_model() # Ensure model is ready
        agent_instance = definition['constructor'](model)

        # 3. Execute the Agent
        input_payload = {
            # Ensure these keys match the expected inputs defined for 'flowBuilderAgent'
            "user_message": user_message,
            "available_nodes_context": available_nodes_str,
            "current_flow_context": current_flow_str
        }
        agent_result = await definition['execute_function'](agent_instance, input_payload)
        # Ensure this output key matches the definition for 'flowBuilderAgent'
        raw_output = agent_result.get('raw_llm_output', '')

        # 4. Parse and Validate the Response
        logger.debug(f"Raw Chatbot LLM Output:\n{raw_output}")
        # Use the imported strip_think_tags function
        json_string = strip_think_tags(raw_output)
        logger.debug(f"Stripped Chatbot LLM Output (attempting parse):\n{json_string}")

        parsed_flow = None
        reply_message = "Sorry, I couldn't understand or process your request properly." # Default error reply

        if not json_string:
             reply_message = "Sorry, I received an empty response after processing. Please try again."
             logger.warning("Chatbot returned empty string after stripping tags.")
        else:
            try:
                # Attempt to parse the stripped string as JSON
                parsed_data = json.loads(json_string)

                # Basic Validation: Check if keys 'nodes' and 'edges' exist and are lists
                if isinstance(parsed_data, dict) and \
                   'nodes' in parsed_data and isinstance(parsed_data.get('nodes'), list) and \
                   'edges' in parsed_data and isinstance(parsed_data.get('edges'), list):
                    # Further validation could be added here (e.g., node types exist, edge sources/targets exist)
                    parsed_flow = parsed_data # Store the valid flow
                    reply_message = "Okay, I've updated the flow based on your request." # Success reply
                    logger.info(f"Chatbot successfully generated a valid flow update.")
                else:
                    reply_message = "Sorry, I generated a response, but it wasn't in the expected flow format. Please try rephrasing."
                    logger.warning(f"Chatbot output failed validation (expected dict with nodes/edges lists). Parsed data type: {type(parsed_data)}, Data: {str(parsed_data)[:500]}") # Log snippet of invalid data

            except json.JSONDecodeError as json_err:
                reply_message = "Sorry, I couldn't generate a valid flow update. My internal response was not valid JSON."
                logger.error(f"Chatbot output failed JSON parsing: {json_err}. String was: {json_string}")
            except Exception as parse_err:
                 reply_message = f"Sorry, an unexpected error occurred while processing my response: {parse_err}"
                 logger.error(f"Chatbot unexpected parsing error: {parse_err}", exc_info=True)


        # 5. Return Result to Frontend
        return jsonify({
            "reply": reply_message,
            "flow": parsed_flow # Send null if parsing/validation failed, otherwise send the updated flow
        })

    except RuntimeError as e: # Catch model init errors specifically
         logger.error(f"Runtime error during chatbot request (model init?): {e}", exc_info=True)
         return jsonify({"reply": f"Server Runtime Error: {e}. Cannot process chat.", "flow": None}), 500
    except Exception as e:
        logger.error(f"An unexpected error occurred during chatbot request: {e}", exc_info=True)
        return jsonify({"reply": f"An unexpected server error occurred: {e}", "flow": None}), 500


# --- Application Entry Point ---
if __name__ == '__main__':
    # Check if agent definitions seem okay (using the frontend getter)
    try:
        # Use the getter that the /api/agents endpoint uses
        defs = get_definitions_for_frontend()
        if not defs:
             logger.warning("Agent definitions list for frontend is empty. Check agent_definitions.py and get_definitions_for_frontend()")
        else:
             logger.info(f"Loaded {len(defs)} agent/system definitions for frontend.")
             # Optionally check if the specific chatbot agent exists
             if not any(d['id'] == 'flowBuilderAgent' for d in defs):
                 logger.warning("Flow Builder Agent ('flowBuilderAgent') definition not found for frontend.")

    except Exception as e:
         logger.error(f"CRITICAL: Failed to load agent definitions for frontend: {e}", exc_info=True)
         # Consider exiting if definitions are critical for startup
         # exit(1)

    host = os.getenv('FLASK_RUN_HOST', '127.0.0.1')
    port = int(os.getenv('FLASK_RUN_PORT', 5001))
    debug = os.getenv('FLASK_ENV') == 'development'

    logger.info(f"Starting Flask server on {host}:{port} (Debug: {debug})")
    # Use asyncio.run() if running directly with python app.py and using async routes
    # When using `flask run`, Flask's runner handles the async loop.
    app.run(host=host, port=port, debug=debug)