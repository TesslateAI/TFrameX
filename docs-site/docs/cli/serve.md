---
sidebar_position: 5
title: tframex serve
---

# tframex serve

The `tframex serve` command launches a web interface for your TFrameX agents, providing a browser-based chat experience with REST API endpoints.

## Overview

```bash
tframex serve [--host HOST] [--port PORT]
```

This command:
- Starts a Flask web server
- Provides a chat interface
- Exposes REST API endpoints
- Supports session management
- Works with any TFrameX agent

## Quick Start

```bash
# Install web dependencies
pip install tframex[web]

# Start server
tframex serve

# Open in browser
open http://localhost:8000
```

## Options

| Option | Default | Description |
|--------|---------|-------------|
| `--host` | `localhost` | Host to bind to |
| `--port` | `8000` | Port to bind to |

## Examples

### Default Server

```bash
tframex serve
# Starts at http://localhost:8000
```

### Custom Port

```bash
tframex serve --port 3000
# Starts at http://localhost:3000
```

### All Interfaces

```bash
tframex serve --host 0.0.0.0 --port 8080
# Accessible from any network interface
```

### Production Deployment

```bash
# Behind a reverse proxy
tframex serve --host 127.0.0.1 --port 8000

# Direct exposure (use with caution)
tframex serve --host 0.0.0.0 --port 80
```

## Web Interface

### Features

The web interface provides:
- **Clean Chat UI** - Message history with formatting
- **Real-time Interaction** - Instant responses
- **Status Indicators** - Shows when AI is processing
- **Mobile Responsive** - Works on all devices
- **Session Persistence** - Maintains conversation context

### Interface Elements

```
┌─────────────────────────────────────┐
│   🚀 TFrameX Web Interface          │
│   Interactive AI Assistant          │
├─────────────────────────────────────┤
│                                     │
│  Assistant: Hello! How can I help?  │
│                                     │
│  You: What's the weather?           │
│                                     │
│  Assistant: I'll help you with...   │
│                                     │
├─────────────────────────────────────┤
│ [Type a message...        ] [Send]  │
└─────────────────────────────────────┘
```

## API Endpoints

### GET /

Returns the HTML chat interface.

**Response:**
```html
<!DOCTYPE html>
<html>
  <!-- Chat interface -->
</html>
```

### POST /chat

Send a message and receive AI response.

**Request:**
```json
{
  "message": "What is the capital of France?"
}
```

**Response:**
```json
{
  "response": "The capital of France is Paris."
}
```

**Example with cURL:**
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello"}'
```

**Example with Python:**
```python
import requests

response = requests.post(
    "http://localhost:8000/chat",
    json={"message": "What time is it?"}
)
print(response.json()["response"])
```

## Configuration

### Environment Variables

The serve command uses the same environment configuration as other TFrameX commands:

```bash
# OpenAI
export OPENAI_API_KEY="sk-..."
export OPENAI_MODEL_NAME="gpt-3.5-turbo"

# Anthropic
export ANTHROPIC_API_KEY="sk-ant-..."
export OPENAI_API_BASE="https://api.anthropic.com/v1"

# Then start server
tframex serve
```

### Custom Configuration

For advanced setups, create a custom server:

```python
# custom_server.py
from flask import Flask, render_template_string, request, jsonify
from tframex import TFrameXApp
import asyncio

app = Flask(__name__)
tframex_app = create_configured_app()  # Your app setup

@app.route('/')
def index():
    return render_template_string(CUSTOM_TEMPLATE)

@app.route('/chat', methods=['POST'])
def chat():
    message = request.json['message']
    
    async def get_response():
        async with tframex_app.run_context() as rt:
            return await rt.call_agent("Assistant", message)
    
    response = asyncio.run(get_response())
    return jsonify({"response": response})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
```

## Security Considerations

### Local Development

Default configuration is secure for local development:
- Binds to `localhost` only
- No external access
- No authentication required

### Production Deployment

For production, consider:

#### 1. Use a Reverse Proxy

**Nginx configuration:**
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**Apache configuration:**
```apache
<VirtualHost *:80>
    ServerName your-domain.com
    
    ProxyPass / http://127.0.0.1:8000/
    ProxyPassReverse / http://127.0.0.1:8000/
</VirtualHost>
```

#### 2. Add Authentication

```python
from flask_httpauth import HTTPBasicAuth

auth = HTTPBasicAuth()

@auth.verify_password
def verify_password(username, password):
    # Implement authentication
    return username == "admin" and password == "secret"

@app.route('/chat', methods=['POST'])
@auth.login_required
def chat():
    # Protected endpoint
    pass
```

#### 3. Implement Rate Limiting

```python
from flask_limiter import Limiter

limiter = Limiter(
    app,
    key_func=lambda: request.remote_addr,
    default_limits=["100 per hour"]
)

@app.route('/chat', methods=['POST'])
@limiter.limit("10 per minute")
def chat():
    # Rate limited endpoint
    pass
```

#### 4. Use HTTPS

```bash
# With Let's Encrypt and Certbot
certbot --nginx -d your-domain.com

# Or with self-signed for testing
openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365
```

## Customization

### Custom HTML Template

Modify the interface by creating a custom template:

```python
CUSTOM_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>My Custom TFrameX Chat</title>
    <style>
        /* Custom styles */
        body { 
            font-family: 'Your Font', sans-serif;
            background: #custom-color;
        }
    </style>
</head>
<body>
    <!-- Your custom interface -->
</body>
</html>
'''
```

### Adding Features

Extend functionality:

```python
@app.route('/history', methods=['GET'])
def get_history():
    """Return chat history."""
    return jsonify({"history": session.get('history', [])})

@app.route('/clear', methods=['POST'])
def clear_history():
    """Clear chat history."""
    session.clear()
    return jsonify({"status": "cleared"})

@app.route('/export', methods=['GET'])
def export_chat():
    """Export chat as text file."""
    history = session.get('history', [])
    return '\n'.join(history), 200, {
        'Content-Type': 'text/plain',
        'Content-Disposition': 'attachment; filename=chat_export.txt'
    }
```

### WebSocket Support

For real-time streaming:

```python
from flask_socketio import SocketIO, emit

socketio = SocketIO(app)

@socketio.on('message')
async def handle_message(data):
    """Handle WebSocket messages."""
    response = await get_ai_response(data['message'])
    emit('response', {'text': response})

# Run with: socketio.run(app)
```

## Performance Optimization

### Connection Pooling

```python
# Reuse TFrameX app instance
tframex_app = TFrameXApp()

# Create runtime context once
runtime_context = None

async def get_runtime():
    global runtime_context
    if runtime_context is None:
        runtime_context = await tframex_app.run_context().__aenter__()
    return runtime_context
```

### Caching

```python
from functools import lru_cache
from flask_caching import Cache

cache = Cache(app, config={'CACHE_TYPE': 'simple'})

@app.route('/chat', methods=['POST'])
@cache.cached(timeout=300, key_prefix='chat')
def chat():
    # Cached responses for common queries
    pass
```

### Async Handling

```python
from flask import Flask
from asgiref.wsgi import WsgiToAsgi
import uvicorn

# Convert Flask to ASGI
asgi_app = WsgiToAsgi(app)

# Run with uvicorn for better performance
if __name__ == '__main__':
    uvicorn.run(asgi_app, host="0.0.0.0", port=8000)
```

## Monitoring

### Logging

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

@app.before_request
def log_request():
    logger.info(f"Request: {request.method} {request.path}")

@app.after_request
def log_response(response):
    logger.info(f"Response: {response.status_code}")
    return response
```

### Metrics

```python
from prometheus_flask_exporter import PrometheusMetrics

metrics = PrometheusMetrics(app)

# Custom metrics
chat_counter = metrics.counter(
    'chat_requests_total',
    'Total number of chat requests'
)

@app.route('/chat', methods=['POST'])
def chat():
    chat_counter.inc()
    # Handle request
```

## Troubleshooting

### Flask Not Installed

```
❌ Flask is required for web server functionality.
   Install with: pip install flask
```

**Solution:**
```bash
pip install tframex[web]
# or
pip install flask>=3.0.0
```

### Port Already in Use

```
❌ Error starting web server: [Errno 48] Address already in use
```

**Solution:**
```bash
# Find process using port
lsof -i :8000  # Mac/Linux
netstat -ano | findstr :8000  # Windows

# Use different port
tframex serve --port 3000
```

### Connection Refused

```
Failed to connect to http://localhost:8000
```

**Solution:**
```bash
# Check if server is running
ps aux | grep tframex

# Check firewall settings
sudo ufw status  # Ubuntu
```

### Slow Response Times

**Causes:**
- Large conversation history
- Slow LLM API
- Network latency

**Solutions:**
- Implement conversation limits
- Use faster models
- Add response caching

## Deployment Examples

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN pip install tframex[web]

# Copy application
COPY . .

# Configure environment
ENV OPENAI_API_KEY=""
ENV FLASK_APP=tframex.cli

# Expose port
EXPOSE 8000

# Run server
CMD ["tframex", "serve", "--host", "0.0.0.0", "--port", "8000"]
```

### Systemd Service

```ini
[Unit]
Description=TFrameX Web Server
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/tframex
Environment="OPENAI_API_KEY=sk-..."
ExecStart=/usr/local/bin/tframex serve --host 127.0.0.1 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: tframex-web
spec:
  replicas: 3
  selector:
    matchLabels:
      app: tframex-web
  template:
    metadata:
      labels:
        app: tframex-web
    spec:
      containers:
      - name: tframex
        image: your-registry/tframex:latest
        ports:
        - containerPort: 8000
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: api-keys
              key: openai
        command: ["tframex", "serve", "--host", "0.0.0.0"]
```

## Advanced Usage

### Multi-Agent Interface

```python
@app.route('/agents', methods=['GET'])
def list_agents():
    """List available agents."""
    agents = ["Assistant", "Researcher", "Writer"]
    return jsonify({"agents": agents})

@app.route('/chat/<agent_name>', methods=['POST'])
def chat_with_agent(agent_name):
    """Chat with specific agent."""
    message = request.json['message']
    # Route to specific agent
    response = get_agent_response(agent_name, message)
    return jsonify({"response": response})
```

### File Upload Support

```python
from werkzeug.utils import secure_filename

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file uploads."""
    if 'file' not in request.files:
        return jsonify({"error": "No file"}), 400
    
    file = request.files['file']
    filename = secure_filename(file.filename)
    file.save(os.path.join('uploads', filename))
    
    # Process with agent
    response = process_file_with_agent(filename)
    return jsonify({"response": response})
```

## Next Steps

- Customize the interface for your needs
- Add authentication for production
- Implement advanced features
- Deploy with proper security
- Monitor usage and performance

## Related Documentation

- [CLI Overview](overview) - General CLI information
- [Basic Command](basic) - Interactive sessions
- [Setup Command](setup) - Project creation
- [Enterprise Deployment](../enterprise/deployment) - Production guidance