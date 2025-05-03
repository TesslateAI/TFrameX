# backend/app.py
import os
import asyncio
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import the NEW flow execution logic and agent definitions
from flow_executor import run_flow # The main execution function
from agent_definitions import get_definitions # Function to get available agents

# Basic logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("FlaskServer")

app = Flask(__name__)
# Allow requests from your frontend development server
CORS(app, resources={r"/api/*": {"origins": "http://localhost:5173"}}) # Adjust port if needed

# Create necessary directories (ensure paths align with agent_definitions.py if needed)
required_dirs = [
    "example_outputs",
    os.path.join("example_outputs", "ex4_multi_call_outputs") # Specific subdir for MultiCall
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
    """Returns the list of available agent/system definitions."""
    logger.info("Request received on /api/agents")
    try:
        definitions = get_definitions()
        # Only return frontend-relevant info (id, name, description, type, inputs, outputs)
        frontend_definitions = [
            {
                "id": d["id"],
                "name": d["name"],
                "description": d.get("description", ""),
                "type": d.get("type", "unknown"),
                "inputs": d.get("inputs", {}),
                "outputs": d.get("outputs", {}),
            } for d in definitions
        ]
        return jsonify(frontend_definitions)
    except Exception as e:
        logger.error(f"Error getting agent definitions: {e}", exc_info=True)
        return jsonify({"error": "Failed to load agent definitions"}), 500


@app.route('/api/run', methods=['POST'])
async def handle_run_flow():
    """
    Handles requests to execute a flow defined by nodes and edges.
    Uses the new dynamic flow executor.
    """
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


# --- Application Entry Point ---
if __name__ == '__main__':
    # Check if agent definitions seem okay (basic check)
    try:
        defs = get_definitions()
        if not defs:
             logger.warning("Agent definitions list is empty. Check agent_definitions.py")
        else:
             logger.info(f"Loaded {len(defs)} agent/system definitions.")
    except Exception as e:
         logger.error(f"CRITICAL: Failed to load agent definitions: {e}", exc_info=True)

    host = os.getenv('FLASK_RUN_HOST', '127.0.0.1')
    port = int(os.getenv('FLASK_RUN_PORT', 5001))
    debug = os.getenv('FLASK_ENV') == 'development'

    logger.info(f"Starting Flask server on {host}:{port} (Debug: {debug})")
    # Use asyncio.run() if running directly with python app.py and using async routes
    # When using `flask run`, Flask's runner handles the async loop.
    app.run(host=host, port=port, debug=debug)