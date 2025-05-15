# TFrameX Extension Guide

## Table of Contents
1. [Introduction](#introduction)
2. [Custom Agents](#custom-agents)
   - [Creating a Custom Agent Class](#creating-a-custom-agent-class)
   - [Overriding Behavior in Existing Agent Types](#overriding-behavior-in-existing-agent-types)
3. [Custom Patterns](#custom-patterns)
   - [Creating a Custom Pattern Class](#creating-a-custom-pattern-class)
4. [Custom LLM Wrappers](#custom-llm-wrappers)
   - [Implementing `BaseLLMWrapper`](#implementing-basellmwrapper)
5. [Custom Memory Stores](#custom-memory-stores)
   - [Implementing `BaseMemoryStore`](#implementing-basememorystore)
6. [Custom Tools (Advanced)](#custom-tools-advanced)
   - [Tools with Complex Initialization](#tools-with-complex-initialization)
7. [Best Practices for Extensions](#best-practices-for-extensions)

## 1. Introduction

TFrameX is built with extensibility in mind. This guide provides instructions and best practices for developers looking to create custom components or integrate TFrameX with other systems. The primary extension points are custom agents, patterns, LLM wrappers, and memory stores.

## 2. Custom Agents

While `LLMAgent` and `ToolAgent` cover many use cases, you might need agents with unique logic, state management, or different ways of interacting with LLMs or external services.

### Creating a Custom Agent Class
Inherit from `tframex.agents.base.BaseAgent` and implement the abstract `run` method.

```python
from tframex.agents.base import BaseAgent
from tframex.models.primitives import Message
from tframex.util.llms import BaseLLMWrapper # If your custom agent uses an LLM
from tframex.util.engine import Engine # If it needs to call other agents/tools
from typing import Union, Optional, List, Dict, Any

class MyRuleBasedAgent(BaseAgent):
    def __init__(self, agent_id: str, rules: Dict[str, str], **kwargs):
        # Pass through common BaseAgent params, even if not directly used by this simple agent
        super().__init__(agent_id=agent_id, **kwargs)
        self.rules = rules # Custom parameter for this agent type

    async def run(self, input_message: Union[str, Message], **kwargs: Any) -> Message:
        content = input_message.content if isinstance(input_message, Message) else input_message
        
        response_content = "I don't have a rule for that."
        for pattern, response in self.rules.items():
            if pattern.lower() in content.lower():
                response_content = response
                break
        
        return Message(role="assistant", content=response_content)

# Registering your custom agent:
# app = TFrameXApp(...)
# @app.agent(
#     name="RuleAgent1",
#     agent_class=MyRuleBasedAgent,
#     rules={"hello": "Hi there!", "bye": "Goodbye!"} # Custom params are passed via **agent_config
# )
# async def rule_agent_placeholder(): # Placeholder is still needed for @app.agent
#     pass 
```
**Key points for custom agents:**
- The `agent_id` (which includes a context suffix) is passed by the `Engine`.
- Other parameters like `llm`, `tools`, `memory`, `system_prompt_template`, etc., are resolved by the `Engine` and passed if the custom agent's `__init__` accepts them.
- The `run` method must accept `input_message: Union[str, Message]` and `**kwargs` and return a `Message`.
- If your agent needs to call other agents or tools, it will need an `Engine` instance, typically passed during instantiation (as `LLMAgent` does).

### Overriding Behavior in Existing Agent Types
You can also subclass `LLMAgent` or `ToolAgent` to modify their behavior.
```python
from tframex.agents.llm_agent import LLMAgent
from tframex.models.primitives import Message

class MyEnhancedLLMAgent(LLMAgent):
    async def run(self, input_message: Union[str, Message], **kwargs: Any) -> Message:
        # Custom pre-processing of input
        if isinstance(input_message, Message) and input_message.content:
            input_message.content = f"[ENHANCED PREAMBLE] {input_message.content}"
        
        response = await super().run(input_message, **kwargs)
        
        # Custom post-processing of output
        if response.content:
            response.content = f"{response.content} [ENHANCED POSTAMBLE]"
        return response

# @app.agent(name="EnhancedLLMAgent1", agent_class=MyEnhancedLLMAgent, system_prompt="...")
# async def enhanced_llm_placeholder(): pass
```

## 3. Custom Patterns

Patterns define reusable interaction logic within flows.

### Creating a Custom Pattern Class
Inherit from `tframex.patterns.base_pattern.BasePattern` and implement `execute()` and `reset_agents()`.

```python
import asyncio
import logging
from tframex.patterns.base_pattern import BasePattern
from tframex.flows.flow_context import FlowContext
from tframex.util.engine import Engine
from tframex.models.primitives import Message
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class RequestResponseRetryPattern(BasePattern):
    def __init__(self, pattern_name: str, request_agent: str, validator_agent: str, max_retries: int = 3):
        super().__init__(pattern_name)
        self.request_agent = request_agent
        self.validator_agent = validator_agent
        self.max_retries = max_retries
        self.agents_to_reset = [request_agent, validator_agent]

    async def execute(
        self,
        flow_ctx: FlowContext,
        engine: Engine,
        agent_call_kwargs: Optional[Dict[str, Any]] = None,
    ) -> FlowContext:
        logger.info(f"Executing RequestResponseRetryPattern '{self.pattern_name}'")
        current_input = flow_ctx.current_message

        for attempt in range(self.max_retries + 1):
            logger.info(f"Attempt {attempt + 1}/{self.max_retries + 1}")
            
            # 1. Call request agent
            response_message = await engine.call_agent(
                self.request_agent, current_input, **(agent_call_kwargs or {})
            )
            flow_ctx.history.append(response_message) # Log request agent's response

            # 2. Call validator agent with the response from request_agent
            validation_input = Message(
                role="user", # Validator typically expects user role for the content to validate
                content=f"Please validate the following content: {response_message.content}"
            )
            validation_result_msg = await engine.call_agent(
                self.validator_agent, validation_input, **(agent_call_kwargs or {})
            )
            flow_ctx.history.append(validation_result_msg) # Log validator's response

            if "valid" in (validation_result_msg.content or "").lower():
                logger.info(f"Validation successful for '{self.pattern_name}' on attempt {attempt + 1}.")
                flow_ctx.update_current_message(response_message) # Final output is the validated response
                return flow_ctx
            
            logger.warning(f"Validation failed on attempt {attempt + 1}. Validator said: {validation_result_msg.content}")
            # For next retry, the input to request_agent could be modified based on validator's feedback
            # For simplicity, we'll reuse the original input or could use validator's feedback
            current_input = Message(
                role=current_input.role, # Keep original role
                content=f"Previous attempt was invalid. Validator said: '{validation_result_msg.content}'. Please try generating again based on the original request: '{flow_ctx.history[0].content}'"
            )
            # Reset agents for a fresh attempt if they are stateful (or their memory influences retries)
            await self.reset_agents(engine)


        logger.error(f"Pattern '{self.pattern_name}' failed after {self.max_retries + 1} attempts.")
        error_message = Message(role="assistant", content="Failed to get a valid response after multiple retries.")
        flow_ctx.update_current_message(error_message)
        return flow_ctx

    async def reset_agents(self, engine: Engine) -> None:
        logger.debug(f"Resetting agents for {self.pattern_name}: {self.agents_to_reset}")
        for agent_name in self.agents_to_reset:
            await engine.reset_agent(agent_name)

# Using the custom pattern in a Flow:
# my_retry_pattern = RequestResponseRetryPattern(
#     pattern_name="GenerateAndValidate",
#     request_agent="ContentGeneratorAgent",
#     validator_agent="ContentValidatorAgent",
#     max_retries=2
# )
# my_flow.add_step(my_retry_pattern)
```

## 4. Custom LLM Wrappers

To integrate with LLM providers not covered by `OpenAIChatLLM`, implement `BaseLLMWrapper`.

### Implementing `BaseLLMWrapper`
Inherit from `tframex.util.llms.BaseLLMWrapper`.

```python
from tframex.util.llms import BaseLLMWrapper
from tframex.models.primitives import Message, MessageChunk, ToolCall # And other primitives
from typing import List, Dict, Any, Optional, Union, AsyncGenerator, Coroutine
import httpx # Or your preferred HTTP client

class MyCustomLLM(BaseLLMWrapper):
    def __init__(self, model_id: str, api_endpoint: str, custom_api_key: str, **kwargs):
        super().__init__(model_id=model_id, api_key=custom_api_key, api_base_url=api_endpoint, **kwargs)
        self.endpoint = api_endpoint # Or construct full endpoint from api_base_url

    async def chat_completion(
        self,
        messages: List[Message],
        stream: bool = False,
        **kwargs: Any,
    ) -> Coroutine[Any, Any, Union[Message, AsyncGenerator[MessageChunk, None]]]:
        client = await self._get_client() # Gets an httpx.AsyncClient from BaseLLMWrapper
        
        # 1. Transform tframex.Message list to your LLM's expected format
        payload_messages = [{"role": msg.role, "content": msg.content} for msg in messages]
        
        api_payload = {
            "model": self.model_id,
            "messages": payload_messages,
            "stream": stream,
            **kwargs # Pass through other LLM params like temperature, max_tokens
        }
        
        # Add tool definitions if present and supported by your LLM
        if "tools" in kwargs and kwargs["tools"]:
            # Adapt tframex.ToolDefinition to your LLM's format
            api_payload["tools"] = self._adapt_tools_for_my_llm(kwargs["tools"])
            if "tool_choice" in kwargs:
                api_payload["tool_choice"] = kwargs["tool_choice"] # Adapt if necessary

        if stream:
            return self._handle_streaming_response(client, self.endpoint, api_payload)
        else:
            return await self._handle_non_streaming_response(client, self.endpoint, api_payload)

    async def _handle_non_streaming_response(self, client: httpx.AsyncClient, url: str, payload: Dict) -> Message:
        try:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            response_data = response.json()
            
            # 2. Parse your LLM's response back into tframex.Message format
            # Example parsing (highly dependent on your LLM's API)
            assistant_content = response_data.get("choices", [{}])[0].get("message", {}).get("content")
            
            tool_calls_data = response_data.get("choices", [{}])[0].get("message", {}).get("tool_calls")
            parsed_tool_calls = []
            if tool_calls_data:
                for tc_data in tool_calls_data:
                    # Adapt your LLM's tool call format to tframex.ToolCall
                    parsed_tool_calls.append(
                        ToolCall(id=tc_data.get("id"), type="function", 
                                 function={"name": tc_data.get("function_name"), 
                                           "arguments": tc_data.get("function_args_json_string")})
                    )
            
            return Message(role="assistant", content=assistant_content, tool_calls=parsed_tool_calls or None)
        except httpx.HTTPStatusError as e:
            # Handle API errors, return an error Message
            return Message(role="assistant", content=f"LLM API Error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            return Message(role="assistant", content=f"Error during LLM call: {str(e)}")

    async def _handle_streaming_response(self, client: httpx.AsyncClient, url: str, payload: Dict) -> AsyncGenerator[MessageChunk, None]:
        try:
            async with client.stream("POST", url, json=payload) as response:
                response.raise_for_status() # Check for initial errors
                async for line in response.aiter_lines():
                    if line.startswith("data:"): # Assuming SSE
                        data_content = line[len("data:") :].strip()
                        if data_content == "[DONE]": break
                        chunk_json = json.loads(data_content)
                        
                        # 3. Parse stream chunk and yield tframex.MessageChunk
                        delta = chunk_json.get("choices", [{}])[0].get("delta", {})
                        content_chunk = delta.get("content")
                        # Handle tool call streaming if your LLM supports it
                        
                        if content_chunk:
                             yield MessageChunk(role="assistant", content=content_chunk)
                        # ... handle other parts of the chunk like tool_calls delta ...
        except httpx.HTTPStatusError as e:
            yield MessageChunk(role="assistant", content=f"LLM Stream Error: {e.response.status_code} - {await e.response.aread()}")
        except Exception as e:
            yield MessageChunk(role="assistant", content=f"Stream error: {str(e)}")
            
    def _adapt_tools_for_my_llm(self, tframex_tools: List[Dict]) -> List[Dict]:
        # Convert from tframex.ToolDefinition.model_dump() format to your LLM's expected format
        adapted_tools = []
        for tool_def_dict in tframex_tools:
            # Assuming tframex_tools is a list of dicts from ToolDefinition.model_dump()
            # Example: tool_def_dict['function']['name'], tool_def_dict['function']['description'], etc.
            adapted_tools.append({
                "toolName": tool_def_dict.get("function", {}).get("name"),
                "toolDescription": tool_def_dict.get("function", {}).get("description"),
                "parametersSchema": tool_def_dict.get("function", {}).get("parameters") 
                # Further adaptation of parametersSchema might be needed
            })
        return adapted_tools


# Usage:
# custom_llm_instance = MyCustomLLM(model_id="my-model-v1", api_endpoint="...", custom_api_key="...")
# app = TFrameXApp(default_llm=custom_llm_instance)
```

## 5. Custom Memory Stores

To persist conversation history in a database or other storage, implement `BaseMemoryStore`.

### Implementing `BaseMemoryStore`
Inherit from `tframex.util.memory.BaseMemoryStore`.

```python
import asyncio
from tframex.util.memory import BaseMemoryStore
from tframex.models.primitives import Message
from typing import List, Optional
# Example: using a dummy list for a "database"
dummy_db: Dict[str, List[Message]] = {} # conversation_id -> List[Message]

class MyDatabaseMemoryStore(BaseMemoryStore):
    async def add_message(self, message: Message, conversation_id: str = "default_conv") -> None:
        if conversation_id not in dummy_db:
            dummy_db[conversation_id] = []
        dummy_db[conversation_id].append(message)
        # In a real scenario, persist to DB here

    async def get_history(
        self,
        conversation_id: str = "default_conv",
        limit: Optional[int] = None,
        offset: int = 0,
        roles: Optional[List[str]] = None,
    ) -> List[Message]:
        history = dummy_db.get(conversation_id, [])
        
        if roles:
            history = [msg for msg in history if msg.role in roles]
        
        # Apply offset and limit (basic implementation)
        start = offset
        end = len(history) if limit is None else offset + limit
        return history[start:end]

    async def clear(self, conversation_id: str = "default_conv") -> None:
        if conversation_id in dummy_db:
            dummy_db[conversation_id] = []
            
# Usage:
# db_memory_factory = lambda: MyDatabaseMemoryStore()
# app = TFrameXApp(default_memory_store_factory=db_memory_factory)
# Or for a specific agent:
# my_agent_memory = MyDatabaseMemoryStore()
# @app.agent(name="PersistentAgent", memory_store=my_agent_memory)
```

## 6. Custom Tools (Advanced)

While `@app.tool` is convenient, you can manually create `Tool` instances if you need more control, for example, if your tool requires complex initialization or state.

### Tools with Complex Initialization
```python
from tframex.util.tools import Tool, ToolParameters, ToolParameterProperty
from tframex import TFrameXApp

class MyComplexToolService:
    def __init__(self, api_key: str):
        self.api_key = api_key
        # ... other setup ...

    async def perform_action(self, item_id: str, quantity: int) -> Dict:
        # Actual logic using self.api_key
        return {"status": "success", "item_id": item_id, "processed_quantity": quantity}

# Instantiate your service
my_service = MyComplexToolService(api_key="your_complex_service_key")

# Create the TFrameX Tool instance, wrapping a method of your service
complex_tool = Tool(
    name="process_item_complex",
    func=my_service.perform_action, # Bind to the instance method
    description="Processes an item using the complex service.",
    parameters_schema=ToolParameters(
        properties={
            "item_id": ToolParameterProperty(type="string", description="The ID of the item."),
            "quantity": ToolParameterProperty(type="integer", description="The quantity to process.")
        },
        required=["item_id", "quantity"]
    )
)

# Register it with the app manually (if not using @app.tool)
# app = TFrameXApp(...)
# app._tools[complex_tool.name] = complex_tool 
# Make sure the agent that uses this tool refers to it by "process_item_complex".
```

## 7. Best Practices for Extensions

- **Type Hinting:** Use Python type hints extensively. TFrameX relies on them for schema inference (e.g., for tools).
- **Asynchronous Operations:** Design custom components to be async (`async def`) if they involve I/O operations (network requests, file access, database calls) to leverage TFrameX's asyncio-based nature.
- **Immutability (where possible):** For data objects passed around (like `Message`), treat them as immutable if possible to avoid side effects. Pydantic models are generally immutable by default unless configured otherwise.
- **Clear Naming:** Use descriptive names for custom agents, patterns, tools, etc.
- **Error Handling:** Implement robust error handling in your custom components. Return informative `Message` objects in case of agent/pattern failures.
- **Logging:** Utilize Python's `logging` module within your extensions for better observability. TFrameX sets up a global logger.
- **Configuration:** For custom components requiring configuration (API keys, endpoints), consider using environment variables (loaded via `python-dotenv`) or pass configuration during instantiation.
- **Testing:** Write unit tests for your custom components, mocking external dependencies as needed.

By following these guidelines, you can effectively extend TFrameX to build powerful and tailored AI agentic systems.