"""
Agent configurations for this TFrameX project.
"""
import os
from tframex.agents.llm_agent import LLMAgent
from tframex.util.llms import OpenAIChatLLM


def setup_agents(app):
    """Setup and register agents with the app."""
    
    # Configure LLM
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("LLAMA_API_KEY")
    if not api_key:
        raise ValueError("Please set OPENAI_API_KEY or LLAMA_API_KEY environment variable")
    
    base_url = os.getenv("OPENAI_API_BASE") or os.getenv("LLAMA_BASE_URL")
    model_name = os.getenv("OPENAI_MODEL_NAME") or os.getenv("LLAMA_MODEL") or "gpt-3.5-turbo"
    
    llm = OpenAIChatLLM(
        model_name=model_name,
        api_key=api_key,
        api_base_url=base_url,
        parse_text_tool_calls=True
    )
    
    # Create main assistant agent
    assistant = LLMAgent(
        name="Assistant",
        description="A helpful AI assistant",
        llm=llm,
        system_prompt="""You are a helpful AI assistant with access to various tools.
        
You can help with:
- General questions and conversations
- Using available tools to solve problems
- Providing information and assistance

Always be helpful, accurate, and engaging."""
    )
    
    # Register agents
    app.register_agent(assistant)
    
    # Add more agents here as needed
