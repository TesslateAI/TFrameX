"""
Tool configurations for this TFrameX project.
"""
from tframex.util.tools import Tool, ToolParameters


def setup_tools(app):
    """Setup and register tools with the app."""
    
    # Register basic tools
    def get_current_time() -> str:
        """Get the current date and time."""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    time_tool = Tool(
        name="get_current_time",
        func=get_current_time,
        description="Get the current date and time",
        parameters_schema=ToolParameters(properties={}, required=None)
    )
    app.register_tool(time_tool)
    
    # Add more tools here as needed
    # Example:
    # def custom_function(param1: str, param2: int = 10) -> str:
    #     return f"Custom result: {param1} with {param2}"
    # 
    # custom_tool = Tool(
    #     name="custom_tool",
    #     func=custom_function,
    #     description="A custom tool example"
    # )
    # app.register_tool(custom_tool)
