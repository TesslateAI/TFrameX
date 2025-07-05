# AWS Documentation MCP Integration Example

This example demonstrates how to integrate TFrameX with the AWS Documentation MCP Server to create an intelligent AWS documentation assistant.

## Features

- **AWS Documentation Reading**: Fetch AWS documentation in markdown format
- **Smart Search**: Use AWS official search API to find relevant documentation
- **Content Recommendations**: Get related content suggestions
- **Service Discovery**: List available AWS services (including China regions)
- **Interactive Chat**: Chat with an AI assistant that has access to AWS docs

## Prerequisites

1. Python 3.10 or newer
2. `uv` package manager installed
3. OpenAI API key (or compatible LLM API)

## Installation

1. **Install uv** (if not already installed):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Set up the virtual environment**:
   ```bash
   cd /path/to/TFrameX/examples/03-integration-examples/aws-documentation-mcp
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   uv pip install -r requirements.txt
   ```

4. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your LLM API credentials
   ```

## Configuration

The example uses `servers_config.json` to configure the AWS Documentation MCP Server:

```json
{
  "mcpServers": {
    "aws_docs": {
      "command": "uvx",
      "args": ["awslabs.aws-documentation-mcp-server@latest"],
      "env": {
        "FASTMCP_LOG_LEVEL": "ERROR",
        "AWS_DOCUMENTATION_PARTITION": "aws"
      }
    }
  }
}
```

## Usage

Run the interactive chat:
```bash
python main.py
```

### Example Interactions

1. **Read AWS Documentation**:
   - "Read the S3 bucket naming documentation"
   - "Show me the EC2 instance types documentation"

2. **Search Documentation**:
   - "Search for Lambda cold start optimization"
   - "Find documentation about VPC security groups"

3. **Get Recommendations**:
   - "What related content do you recommend for S3 security?"
   - "Show me related documentation for this AWS service"

4. **Service Discovery**:
   - "What AWS services are available?"
   - "List all AWS services in China regions"

## Files

- `main.py`: Main application with TFrameX integration
- `servers_config.json`: MCP server configuration
- `requirements.txt`: Python dependencies
- `.env.example`: Environment variables template
- `README.md`: This documentation

## How It Works

1. **TFrameX App**: Initializes with MCP support and default LLM
2. **AWS Docs Agent**: Configured with access to AWS documentation tools
3. **MCP Integration**: Connects to AWS Documentation MCP Server via `uvx`
4. **Interactive Chat**: Provides a conversational interface to explore AWS docs

## Troubleshooting

- **MCP Server Issues**: Check that `uvx` is installed and in PATH
- **LLM Connection**: Verify your API credentials in `.env`
- **Network Issues**: Ensure internet connectivity for AWS documentation access

## Advanced Usage

The AWS Documentation Assistant can:
- Combine multiple AWS documentation sources
- Provide context-aware recommendations
- Search across all AWS services
- Integrate with your existing AWS workflows