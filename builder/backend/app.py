import os
import asyncio
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import the flow execution logic
from flow_executor import run_flow, get_model # Import get_model for potential cleanup

# Basic logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("FlaskServer")

app = Flask(__name__)
# Allow requests from your frontend development server
CORS(app, resources={r"/api/*": {"origins": "http://localhost:5173"}}) # Adjust port if needed

# Create necessary directories if they don't exist
# These paths should align with flow_executor.py and .env
required_dirs = [
    "example_outputs",
    "generated_website",
    "build_artifacts",
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
    return "Backend is running. Use the /api/run endpoint."

@app.route('/api/run', methods=['POST'])
async def handle_run_flow():
    """
    Handles requests to execute a flow defined by nodes and edges.
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

    logger.info(f"Received {len(nodes)} nodes and {len(edges)} edges.")
    # Log node types received for debugging
    node_types = [n.get('type', 'unknown') for n in nodes]
    logger.debug(f"Node types received: {node_types}")


    try:
        # Run the flow execution logic asynchronously
        result_log = await run_flow(nodes, edges)
        logger.info("Flow execution completed successfully.")
        return jsonify({"output": result_log})
    except RuntimeError as e:
         logger.error(f"Runtime error during flow execution: {e}", exc_info=True)
         return jsonify({"error": f"Runtime Error: {e}"}), 500
    except ImportError as e:
        logger.error(f"Import error, likely tframex issue: {e}", exc_info=True)
        return jsonify({"error": f"Import Error: {e}. Is tframex installed correctly?"}), 500
    except Exception as e:
        logger.error(f"An unexpected error occurred during flow execution: {e}", exc_info=True)
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500


# --- Application Entry Point ---
if __name__ == '__main__':
    # Check if tframex components were imported (basic check)
    try:
        from tframex.model import VLLMModel # Check again
    except ImportError:
         logger.error("CRITICAL: tframex library not found or import failed. Backend cannot function.")
         # Exit or prevent server start? For now, just log critical error.

    # Get Flask configuration from environment or use defaults
    host = os.getenv('FLASK_RUN_HOST', '127.0.0.1')
    port = int(os.getenv('FLASK_RUN_PORT', 5001)) # Use a different port than default 5000
    debug = os.getenv('FLASK_ENV') == 'development'

    logger.info(f"Starting Flask server on {host}:{port} (Debug: {debug})")
    app.run(host=host, port=port, debug=debug)

    # Optional: Add cleanup logic here if needed when the server stops
    # async def cleanup():
    #     model = await get_model() # Get the instance (even if None)
    #     if model and hasattr(model, 'close_client'):
    #         try:
    #             await model.close_client()
    #             logger.info("VLLM Model client closed on server shutdown.")
    #         except Exception as e:
    #             logger.error(f"Error closing model client on shutdown: {e}")
    #
    # try:
    #     # Run cleanup in the event loop if possible when shutting down
    #     loop = asyncio.get_event_loop()
    #     loop.run_until_complete(cleanup())
    # except Exception as e:
    #      logger.error(f"Error during final cleanup: {e}")