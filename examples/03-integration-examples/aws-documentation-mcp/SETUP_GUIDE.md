# AWS Documentation MCP - Setup Guide

## ✅ **Status: FULLY TESTED AND OPTIMIZED**

This example has been successfully tested, debugged, and optimized for the best user experience! 

🎉 **Latest Improvements:**
- ✅ Fixed Llama tool calling with proper OpenAI compatibility
- ✅ Optimized agent prompts for better responses  
- ✅ Enhanced interactive UI with better guidance
- ✅ Comprehensive testing with demo mode
- ✅ Production-ready MCP integration

## 🚀 **Quick Start Instructions**

### 1. **Navigate to the Example Directory**
```bash
cd /home/smirk/TFrameX/examples/03-integration-examples/aws-documentation-mcp
```

### 2. **Configure Environment Variables**
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your Llama API key
# Get your key from https://api.llama.com/
nano .env  # or use your preferred editor
```

### 3. **Activate the Virtual Environment**
```bash
source .venv/bin/activate
```

### 4. **Run the Interactive Chat** 
```bash
python main.py
```

### 5. **Try These Example Queries**
Once the chat starts, try asking:
- `"list mcp servers"`
- `"search for S3 bucket policies"`
- `"read EC2 documentation"`
- `"what are Lambda best practices?"`
- `"switch"` (to change agents)
- `"exit"` (to quit)

## 🔧 **What's Already Configured**

✅ **Virtual Environment**: Created with `uv venv`  
✅ **Dependencies**: Installed with `uv pip install -r requirements.txt`  
✅ **LLM Configuration**: Using your Llama-4-Maverick-17B model  
✅ **MCP Server**: AWS Documentation Server configured and tested  
✅ **TFrameX Integration**: Two expert agents ready to use  

## 🎯 **Available Agents**

1. **AWSDocsExpert**: Specialized in AWS documentation lookup and search
2. **AWSArchitect**: Solutions architect with full AWS documentation access

## 🛠 **Technical Details**

### **MCP Server Configuration**
- **Server**: `awslabs.aws-documentation-mcp-server@latest`
- **Type**: stdio (command-line interface)
- **Tools Available**: 
  - `read_documentation`: Read AWS docs in markdown
  - `search_documentation`: Search AWS official docs
  - `recommend`: Get content recommendations
  - `get_available_services`: List AWS services

### **LLM Configuration**
- **Model**: Llama-4-Maverick-17B-128E-Instruct-FP8
- **API**: https://api.llama.com/compat/v1/
- **Text Tool Call Parsing**: ✅ Enabled (for Llama compatibility)
- **Status**: ✅ Connected and tested

### **TFrameX Features Used**
- Enhanced MCP integration with roots and sampling
- Native tool registration (time, URL formatting)
- Agent-to-agent communication capability
- Interactive chat interface
- Comprehensive logging

## 📋 **Test Results**

✅ **MCP Server Connection**: Successfully connected to AWS Documentation server  
✅ **Capability Negotiation**: All MCP features negotiated properly  
✅ **Tool Integration**: AWS documentation tools available to agents  
✅ **Interactive Chat**: Chat interface working correctly  
✅ **LLM Integration**: Llama-4-Maverick model responding properly  

## 🐛 **Known Issues**

- **Minor cleanup warning**: Non-critical AsyncIO cleanup warning on exit (doesn't affect functionality)
- **Tool call format**: LLM responses show tool calls in brackets - this is normal TFrameX behavior

## 🎯 **Demo Mode**

You can also run a quick demo:
```bash
python main.py --demo
```

This runs 3 automated queries to test the integration.

## 🔄 **If You Need to Restart**

If something goes wrong, you can always:
```bash
# Re-activate environment
source .venv/bin/activate

# Run the application
python main.py
```

The AWS MCP server will automatically reconnect on each run.

## 🔧 **Advanced Features**

### **Agent Switching**
```bash
# During chat, type 'switch' to change agents:
You: switch
# Choose between AWSDocsExpert and AWSArchitect
```

### **MCP Integration Testing**
```bash
# Test MCP server status:
You: list mcp servers

# Test AWS documentation search:
You: search for "EC2 instance types"

# Test architecture guidance:
You: design a serverless web application architecture
```

### **Tool Call Debugging**
The integration uses advanced text tool call parsing for Llama models:
- LLM responses like `[function_name(args)]` are automatically converted to proper tool calls
- This enables seamless integration between Llama's text-based tool calling and OpenAI's structured format
- Debug logs show the conversion process when `parse_text_tool_calls=True`

## 🚨 **Troubleshooting**

### **Tool Calling Issues**
If tool calls aren't working:
1. Check that `parse_text_tool_calls=True` in the LLM configuration
2. Verify MCP server is connected: look for "FULLY INITIALIZED" in logs
3. Test with simple queries like "list mcp servers" first

### **MCP Server Connection Issues**
If AWS MCP server fails to connect:
1. Ensure `uvx` is installed and accessible
2. Check network connectivity
3. Verify the MCP server version is compatible
4. Look for timeout errors in logs

### **Performance Optimization**
For better performance:
- Use `tool_choice="auto"` for natural conversations
- Use `tool_choice="required"` to force tool usage
- Adjust `max_tokens` and `temperature` in LLM config
- Monitor response times in debug logs

## 📈 **Production Deployment Notes**

### **Security Considerations**
- API keys are loaded from environment variables
- MCP servers run in isolated processes
- No sensitive data is logged at INFO level

### **Scaling**
- Each MCP server connection is persistent and reused
- Multiple concurrent conversations are supported
- Resource cleanup is automatic on context exit

### **Monitoring**
- Comprehensive logging at multiple levels
- MCP server health monitoring
- Tool execution timing and success tracking

---

**🎉 Ready to explore AWS documentation with AI assistance!**

**🔗 For more TFrameX examples and documentation:**
- TFrameX GitHub: https://github.com/TesslateAI/TFrameX
- More examples: `/examples/` directory