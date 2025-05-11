import inspect
import json
import asyncio
import logging
from typing import Callable, Dict, Any, Optional, List, Coroutine

from tframex.primitives import ToolParameterProperty, ToolParameters, ToolDefinition

logger = logging.getLogger(__name__)

class Tool:
    def __init__(self, name: str, func: Callable[..., Any], description: Optional[str] = None,
                 parameters_schema: Optional[ToolParameters] = None):
        self.name = name
        self.func = func
        self.description = description or inspect.getdoc(func) or f"Tool named '{name}'."
        
        if parameters_schema:
            self.parameters = parameters_schema
        else:
            self.parameters = self._infer_schema_from_func(func)
        
        logger.debug(f"Tool '{self.name}' initialized. Schema: {self.parameters.model_dump_json(indent=2)}")

    def _infer_schema_from_func(self, func: Callable) -> ToolParameters:
        sig = inspect.signature(func)
        properties: Dict[str, ToolParameterProperty] = {}
        required_params: List[str] = []

        for param_name, param in sig.parameters.items():
            if param_name in ["self", "cls", "rt_ctx", "runtime_context", "loop", "_loop"]: # Skip common bound/context args
                continue
            
            # Basic type mapping (can be expanded significantly)
            param_type_str = "string" # Default
            param_description = f"Parameter '{param_name}'"

            if param.annotation != inspect.Parameter.empty:
                if param.annotation == int: param_type_str = "integer"
                elif param.annotation == float: param_type_str = "number"
                elif param.annotation == bool: param_type_str = "boolean"
                elif param.annotation == list or getattr(param.annotation, '__origin__', None) == list: param_type_str = "array" # Basic list
                elif param.annotation == dict or getattr(param.annotation, '__origin__', None) == dict: param_type_str = "object" # Basic dict
                # For more complex annotations (e.g., List[str], MyPydanticModel), more advanced parsing is needed.
                # Type hints in docstrings could also be parsed.

            properties[param_name] = ToolParameterProperty(type=param_type_str, description=param_description)
            if param.default == inspect.Parameter.empty:
                required_params.append(param_name)
        
        return ToolParameters(properties=properties, required=required_params or None) # None if empty list

    def get_openai_tool_definition(self) -> ToolDefinition:
        """Returns schema in OpenAI function calling format."""
        return ToolDefinition(
            type="function",
            function={
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters.model_dump(exclude_none=True) # Pydantic handles required list correctly
            }
        )

    async def execute(self, arguments_json_str: str) -> Any:
        logger.info(f"Executing tool '{self.name}' with JSON arguments: {arguments_json_str}")
        try:
            kwargs = json.loads(arguments_json_str)
        except json.JSONDecodeError as e:
            err_msg = f"Invalid JSON arguments for tool '{self.name}': {arguments_json_str}. Error: {e}"
            logger.error(err_msg)
            return {"error": err_msg } # Return a dict for error consistency

        # TODO: Add Pydantic validation of kwargs against self.parameters schema here for robustness

        try:
            if asyncio.iscoroutinefunction(self.func):
                return await self.func(**kwargs)
            else:
                # Consider context for to_thread if event loop isn't guaranteed to be the one expected by func's potential side effects
                return await asyncio.to_thread(self.func, **kwargs)
        except Exception as e:
            logger.error(f"Error during execution of tool '{self.name}': {e}", exc_info=True)
            return {"error": f"Execution error in tool '{self.name}': {str(e)}" }