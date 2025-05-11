# flask_app.py
import asyncio
import logging
from flask import Flask, request, jsonify, render_template_string
from dotenv import load_dotenv

# Import the TFrameX app instance and Message primitive
from tframex_config import get_tframex_app
from tframex import Message # Crucial for history management

load_dotenv()

flask_app = Flask(__name__)
tframex_app_instance = get_tframex_app() # Get the configured TFrameXApp instance

# Configure Flask logging
flask_app.logger.setLevel(logging.INFO)

# In-memory session store for conversation history
# Maps session_id (str) to a list of serialized Message objects (dicts)
conversation_history_store = {}

# HTML template for the chat interface
CHAT_HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TFrameX Chatbot</title>
    <style>
        body { font-family: sans-serif; margin: 0; padding: 0; background-color: #f4f4f4; display: flex; justify-content: center; align-items: center; min-height: 100vh; }
        .chat-container { width: 100%; max-width: 600px; background-color: #fff; box-shadow: 0 0 10px rgba(0,0,0,0.1); border-radius: 8px; display: flex; flex-direction: column; height: 80vh; max-height: 700px; }
        .chat-header { background-color: #007bff; color: white; padding: 15px; text-align: center; border-top-left-radius: 8px; border-top-right-radius: 8px; }
        .chat-messages { flex-grow: 1; padding: 20px; overflow-y: auto; border-bottom: 1px solid #eee; display: flex; flex-direction: column; }
        .message { margin-bottom: 15px; padding: 10px; border-radius: 7px; line-height: 1.4; max-width: 80%; word-wrap: break-word; }
        .user-message { background-color: #007bff; color: white; align-self: flex-end; margin-left: auto; }
        .bot-message { background-color: #e9ecef; color: #333; align-self: flex-start; margin-right: auto; }
        .message-sender { font-weight: bold; margin-bottom: 5px; font-size: 0.9em; }
        .chat-input { display: flex; padding: 15px; border-top: 1px solid #ddd; background-color: #fff; border-bottom-left-radius: 8px; border-bottom-right-radius: 8px;}
        .chat-input input { flex-grow: 1; padding: 10px; border: 1px solid #ccc; border-radius: 4px; margin-right: 10px; }
        .chat-input button { padding: 10px 15px; background-color: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; }
        .chat-input button:hover { background-color: #0056b3; }
        .thinking { font-style: italic; color: #777; }
    </style>
</head>
<body>
    <div class="chat-container">
        <div class="chat-header"><h2>TFrameX Multi-Tool Chatbot</h2></div>
        <div class="chat-messages" id="chatMessages">
            <!-- Messages will be appended here -->
        </div>
        <div class="chat-input">
            <input type="text" id="userInput" placeholder="Type your message..." autocomplete="off">
            <button onclick="sendMessage()">Send</button>
        </div>
    </div>

    <script>
        const chatMessages = document.getElementById('chatMessages');
        const userInput = document.getElementById('userInput');
        // For a real app, generate a unique session ID or retrieve from localStorage/cookie
        const currentSessionId = 'test_session'; 

        async function sendMessage() {
            const messageText = userInput.value.trim();
            if (!messageText) return;

            appendMessage('You', messageText, ['user-message']);
            userInput.value = '';
            appendMessage('Bot', 'Thinking...', ['bot-message', 'thinking'], 'bot-thinking');

            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: messageText, session_id: currentSessionId })
                });
                const data = await response.json();
                
                const thinkingMessageElement = document.getElementById('bot-thinking');
                if (thinkingMessageElement) thinkingMessageElement.remove(); 

                if (data.reply) {
                    appendMessage('Bot', data.reply, ['bot-message']);
                } else if (data.error) {
                    appendMessage('Bot', 'Error: ' + data.error, ['bot-message']);
                }
            } catch (error) {
                const thinkingMessageElement = document.getElementById('bot-thinking');
                if (thinkingMessageElement) thinkingMessageElement.remove();
                appendMessage('Bot', 'Error connecting to the server.', ['bot-message']);
                console.error('Error:', error);
            }
        }

        function appendMessage(sender, text, cssClasses, id = null) {
            const messageWrapper = document.createElement('div'); // Wrapper to help with alignment
            messageWrapper.style.display = 'flex';
            if (cssClasses.includes('user-message')) {
                messageWrapper.style.justifyContent = 'flex-end';
            } else {
                messageWrapper.style.justifyContent = 'flex-start';
            }

            const messageDiv = document.createElement('div');
            messageDiv.classList.add('message');
            cssClasses.forEach(cls => messageDiv.classList.add(cls));
            if (id) messageDiv.id = id;

            const senderDiv = document.createElement('div');
            senderDiv.classList.add('message-sender');
            senderDiv.textContent = sender;
            messageDiv.appendChild(senderDiv);
            
            // Sanitize text or use a library if rendering HTML from bot
            // For plain text, createTextNode is safest
            const textLines = text.split('\\n'); // Handle newlines from bot
            textLines.forEach((line, index) => {
                messageDiv.appendChild(document.createTextNode(line));
                if (index < textLines.length - 1) {
                    messageDiv.appendChild(document.createElement('br'));
                }
            });

            messageWrapper.appendChild(messageDiv);
            chatMessages.appendChild(messageWrapper);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }

        userInput.addEventListener('keypress', function(event) {
            if (event.key === 'Enter') {
                sendMessage();
            }
        });
        // Updated welcome message
        appendMessage('Bot', 'Hello! How can I help you today? I can tell you about weather, city information, or the sentiment of a Reddit community!', ['bot-message']);
    </script>
</body>
</html>
"""

@flask_app.route('/')
def index():
    return render_template_string(CHAT_HTML_TEMPLATE)

@flask_app.route('/chat', methods=['POST'])
async def chat():
    try:
        data = request.get_json()
        user_message_content = data.get('message')
        session_id = data.get('session_id', 'default_session') # Get session ID from client

        if not user_message_content:
            return jsonify({'error': 'No message provided'}), 400

        flask_app.logger.info(f"Received message for session '{session_id}': \"{user_message_content}\"")

        async with tframex_app_instance.run_context() as rt:
            # Get the agent instance.
            # The agent name here MUST match the name defined in tframex_config.py
            agent_name_to_use = "RedditAnalystAgent" # MODIFIED HERE
            chatbot_agent = rt._get_agent_instance(agent_name_to_use)

            # 1. Load history for the current session into the agent's memory
            if chatbot_agent.memory: # Ensure agent has a memory store
                session_history_data = conversation_history_store.get(session_id, [])
                if session_history_data:
                    flask_app.logger.info(f"Loading {len(session_history_data)} messages from history for session '{session_id}' into agent '{agent_name_to_use}' memory.")
                    for msg_data in session_history_data:
                        try:
                            message_obj = Message.model_validate(msg_data)
                            await chatbot_agent.memory.add_message(message_obj)
                        except Exception as e:
                            flask_app.logger.error(f"Error rehydrating message for session '{session_id}': {msg_data}, error: {e}")
                else:
                    flask_app.logger.info(f"No prior history found for session '{session_id}'. Starting fresh for agent '{agent_name_to_use}'.")
            else:
                flask_app.logger.warning(f"Agent '{agent_name_to_use}' does not have a memory store. History will not be maintained across calls.")


            # 2. Call the agent with the new user message.
            bot_response_message = await rt.call_agent(
                agent_name_to_use, # MODIFIED HERE
                user_message_content
            )

            # 3. Save updated history
            if chatbot_agent.memory:
                updated_full_history = await chatbot_agent.memory.get_history()
                conversation_history_store[session_id] = [msg.model_dump(exclude_none=True) for msg in updated_full_history]
                flask_app.logger.info(f"Saved {len(updated_full_history)} total messages to history for session '{session_id}' (Agent: {agent_name_to_use}).")

        bot_reply_content = bot_response_message.content if bot_response_message else "Sorry, I couldn't process that."
        
        if bot_response_message and bot_response_message.tool_calls:
            flask_app.logger.warning(f"Bot response for session '{session_id}' unexpectedly included tool calls: {bot_response_message.tool_calls}")

        flask_app.logger.info(f"Bot reply for session '{session_id}': \"{bot_reply_content}\"")
        return jsonify({'reply': bot_reply_content})

    except Exception as e:
        flask_app.logger.error(f"Error in /chat endpoint: {e}", exc_info=True)
        return jsonify({'error': f"An internal server error occurred: {type(e).__name__}"}), 500

if __name__ == '__main__':
    # For robust async, use an ASGI server like Uvicorn:
    # import uvicorn
    # uvicorn.run(flask_app, host="0.0.0.0", port=5001, log_level="info", reload=True)
    # Using Flask's built-in server for development simplicity (may have limitations with async):
    flask_app.run(debug=True, port=5001, use_reloader=True)