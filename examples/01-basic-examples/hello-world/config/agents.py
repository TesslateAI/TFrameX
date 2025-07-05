"""
Agent definitions for Hello World example.

This module demonstrates basic agent setup with different personalities
and system prompt configurations.
"""

from tframex import TFrameXApp


def setup_agents(app: TFrameXApp):
    """Configure all agents for the Hello World example."""
    
    @app.agent(
        name="GreeterAgent",
        description="A friendly greeting agent that welcomes users warmly",
        system_prompt=(
            "You are a friendly and enthusiastic greeter named Alex. "
            "Your job is to welcome users warmly and make them feel comfortable. "
            "You should:\n"
            "- Always be polite and cheerful\n"
            "- Ask how you can help them today\n"
            "- Keep responses concise but warm\n"
            "- If a user_name is provided, use it naturally in conversation\n"
            "Template variables available: {user_name} (if provided)"
        )
    )
    async def greeter_agent():
        """
        Basic greeter agent.
        
        The actual logic is handled by TFrameX's LLMAgent class.
        This function serves as a placeholder and registration point.
        """
        pass
    
    # Example of an agent with different personality
    @app.agent(
        name="FormalGreeterAgent", 
        description="A formal, professional greeting agent",
        system_prompt=(
            "You are a professional and formal assistant. "
            "Greet users politely and professionally. "
            "Always maintain a business-appropriate tone. "
            "Ask how you may assist them today in a formal manner."
        )
    )
    async def formal_greeter_agent():
        """Formal greeter agent with professional tone."""
        pass
    
    # Example agent with template variables
    @app.agent(
        name="PersonalizedGreeterAgent",
        description="A greeter that uses personalization",
        system_prompt=(
            "You are a personalized assistant. "
            "Always address the user by name if provided: {user_name}. "
            "Make the conversation feel personal and tailored. "
            "If no name is provided, ask for their name politely."
        )
    )
    async def personalized_greeter_agent():
        """Personalized greeter that uses template variables."""
        pass