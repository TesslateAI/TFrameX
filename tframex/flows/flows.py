import inspect
import logging
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Union

import yaml  # NEW IMPORT

from ..models.primitives import Message
from ..patterns.patterns import (
    BasePattern,
    DiscussionPattern,
    ParallelPattern,
    RouterPattern,
    SequentialPattern,
)
from ..util.engine import Engine
from .flow_context import FlowContext

logger = logging.getLogger(__name__)


class Flow:
    """
    Represents a defined sequence of operations (agents or patterns) to be executed.
    """

    def __init__(self, flow_name: str, description: Optional[str] = None):
        self.flow_name = flow_name
        self.description = description
        self.steps: List[Union[str, BasePattern]] = (
            []
        )  # str for agent_name, or BasePattern instance
        logger.debug(f"Flow '{self.flow_name}' initialized.")

    def add_step(self, step: Union[str, BasePattern]):
        """Adds a step to the flow. A step can be an agent name or a Pattern instance."""
        if not isinstance(step, (str, BasePattern)):
            raise TypeError(
                "Flow step must be an agent name (str) or a BasePattern instance."
            )
        self.steps.append(step)
        logger.debug(
            f"Flow '{self.flow_name}': Added step '{str(step)}'. Total steps: {len(self.steps)}."
        )
        return self

    async def execute(
        self,
        initial_input: Message,
        engine: Engine,
        initial_shared_data: Optional[Dict[str, Any]] = None,
        flow_template_vars: Optional[Dict[str, Any]] = None,
    ) -> FlowContext:
        """
        Executes the flow with the given initial input and runtime context.
        Returns the final FlowContext after all steps.
        """
        logger.info(
            f"Executing Flow '{self.flow_name}' with {len(self.steps)} steps. Initial input: {str(initial_input.content)[:50]}..."
        )

        flow_ctx = FlowContext(
            initial_input=initial_input, shared_data=initial_shared_data
        )
        agent_call_kwargs = (
            {"template_vars": flow_template_vars} if flow_template_vars else {}
        )

        for i, step in enumerate(self.steps):
            step_name = str(step) if isinstance(step, BasePattern) else step
            logger.info(
                f"Flow '{self.flow_name}' - Step {i+1}/{len(self.steps)}: Executing '{step_name}'. Current input: {str(flow_ctx.current_message.content)[:50]}..."
            )

            try:
                if isinstance(step, str):
                    output_message = await engine.call_agent(
                        step, flow_ctx.current_message, **agent_call_kwargs
                    )
                    flow_ctx.update_current_message(output_message)
                elif isinstance(step, BasePattern):
                    # Patterns need to be aware of flow_template_vars if they call agents directly
                    # Pass agent_call_kwargs to pattern's execute method
                    flow_ctx = await step.execute(
                        flow_ctx, engine, agent_call_kwargs=agent_call_kwargs
                    )
                else:
                    raise TypeError(
                        f"Invalid step type in flow '{self.flow_name}': {type(step)}"
                    )

                logger.info(
                    f"Flow '{self.flow_name}' - Step {i+1} ('{step_name}') completed. Output: {str(flow_ctx.current_message.content)[:50]}..."
                )

                if flow_ctx.shared_data.get("STOP_FLOW", False):
                    logger.info(
                        f"Flow '{self.flow_name}' - STOP_FLOW signal received. Halting execution."
                    )
                    break

            except Exception as e:
                logger.error(
                    f"Error during Flow '{self.flow_name}' at step '{step_name}': {e}",
                    exc_info=True,
                )
                error_msg = Message(
                    role="assistant",
                    content=f"Error in flow '{self.flow_name}' at step '{step_name}': {e}",
                )
                flow_ctx.update_current_message(error_msg)
                return flow_ctx

        logger.info(
            f"Flow '{self.flow_name}' completed. Final output: {str(flow_ctx.current_message.content)[:50]}..."
        )
        return flow_ctx

    # --- Documentation Generation Methods ---

    def generate_documentation(self, app: "TFrameXApp") -> Tuple[str, str]:
        """
        Generates a Mermaid diagram string and a YAML representation for the entire flow.
        Requires a TFrameXApp instance to look up agent and tool details.
        """
        if not TYPE_CHECKING:  # Runtime imports if not already loaded by type checker
            from ..agents.llm_agent import LLMAgent
            from ..models.primitives import ToolDefinition
            from ..util.tools import ToolParameterProperty, ToolParameters

        yaml_data = self._generate_yaml_data(app)
        # Pass yaml_data to Mermaid generation to reuse processed structure and IDs if needed,
        # though current Mermaid generator re-traverses for simplicity.
        mermaid_string = self._generate_mermaid_string(app, yaml_data)

        yaml_string = yaml.dump(
            yaml_data, sort_keys=False, indent=2, width=120, default_flow_style=False
        )
        return mermaid_string, yaml_string

    def _get_tool_details_for_yaml(
        self, tool_name: str, app: "TFrameXApp"
    ) -> Dict[str, Any]:
        from ..util.tools import (  # Ensure available at runtime
            ToolParameterProperty,
            ToolParameters,
        )

        tool_obj = app.get_tool(tool_name)
        if not tool_obj:
            return {"name": tool_name, "error": "Tool not found in app registry"}

        params_repr = {}
        if tool_obj.parameters and tool_obj.parameters.properties:
            for p_name, p_prop_model in tool_obj.parameters.properties.items():
                # p_prop_model is ToolParameterProperty instance
                params_repr[p_name] = {
                    "type": p_prop_model.type,
                    "description": p_prop_model.description,
                }
                if p_prop_model.enum:
                    params_repr[p_name]["enum"] = p_prop_model.enum

        required_params = []
        if tool_obj.parameters and tool_obj.parameters.required:
            required_params = tool_obj.parameters.required

        return {
            "name": tool_obj.name,
            "description": tool_obj.description,
            "parameters": (
                {"properties": params_repr, "required": required_params}
                if params_repr
                else "No parameters defined"
            ),
        }

    def _get_agent_details_for_yaml(
        self, agent_name: str, app: "TFrameXApp"
    ) -> Dict[str, Any]:
        from ..agents.llm_agent import LLMAgent  # For default type
        from ..models.primitives import ToolDefinition
        from ..util.tools import ToolParameterProperty, ToolParameters

        if agent_name not in app._agents:
            return {"name": agent_name, "error": "Agent not registered in app"}

        reg_info = app._agents[agent_name]
        config = reg_info["config"]

        # Determine agent class, defaulting to LLMAgent if not specified or not a class
        agent_class_ref = config.get("agent_class_ref", LLMAgent)
        agent_type_name = (
            agent_class_ref.__name__
            if inspect.isclass(agent_class_ref)
            else LLMAgent.__name__
        )

        agent_details = {
            "name": agent_name,
            "type": agent_type_name,
            "description": config.get("description"),
            "system_prompt": config.get("system_prompt_template"),
            "strip_think_tags": config.get("strip_think_tags", False),
        }

        llm_override = config.get("llm_instance_override")
        if llm_override:
            agent_details["llm"] = {
                "model_id": llm_override.model_id,
                "api_base_url": llm_override.api_base_url,
            }
        else:
            agent_details["llm"] = "Uses context/app default LLM"

        tool_names = config.get("tool_names", [])
        if tool_names:
            agent_details["tools"] = [
                self._get_tool_details_for_yaml(tn, app) for tn in tool_names
            ]

        callable_agent_names_for_this_agent = config.get("callable_agent_names", [])
        if callable_agent_names_for_this_agent:
            callable_agents_tool_defs = []
            for ca_name_to_call in callable_agent_names_for_this_agent:
                if ca_name_to_call in app._agents:
                    called_agent_reg_info = app._agents[ca_name_to_call]
                    called_agent_desc = (
                        called_agent_reg_info["config"].get("description")
                        or f"Agent '{ca_name_to_call}' performing its designated role."
                    )

                    agent_tool_params_dict = ToolParameters(
                        properties={
                            "input_message": ToolParameterProperty(
                                type="string",
                                description=f"The specific query, task, or input content to pass to the '{ca_name_to_call}' agent.",
                            ),
                        },
                        required=["input_message"],
                    ).model_dump(exclude_none=True)

                    tool_def_for_ca = ToolDefinition(
                        type="function",
                        function={
                            "name": ca_name_to_call,
                            "description": called_agent_desc,
                            "parameters": agent_tool_params_dict,
                        },
                    )
                    callable_agents_tool_defs.append(tool_def_for_ca.model_dump())
                else:
                    callable_agents_tool_defs.append(
                        {
                            "name": ca_name_to_call,
                            "error": "Callable agent not registered",
                        }
                    )
            if callable_agents_tool_defs:  # Only add if not empty
                agent_details["callable_agents_as_tools"] = callable_agents_tool_defs
        return agent_details

    def _generate_yaml_data_recursive(
        self, step_or_task: Union[str, BasePattern], app: "TFrameXApp"
    ) -> Dict[str, Any]:
        if isinstance(step_or_task, str):
            return {
                "type": "agent",
                **self._get_agent_details_for_yaml(step_or_task, app),
            }
        elif isinstance(step_or_task, BasePattern):
            pattern_data: Dict[str, Any] = {
                "type": "pattern",
                "pattern_type": step_or_task.__class__.__name__,
                "name": step_or_task.pattern_name,
            }
            if isinstance(step_or_task, SequentialPattern):
                pattern_data["steps"] = [
                    self._generate_yaml_data_recursive(s, app)
                    for s in step_or_task.steps
                ]
            elif isinstance(step_or_task, ParallelPattern):
                pattern_data["tasks"] = [
                    self._generate_yaml_data_recursive(t, app)
                    for t in step_or_task.tasks
                ]
            elif isinstance(step_or_task, RouterPattern):
                pattern_data["router_agent"] = self._get_agent_details_for_yaml(
                    step_or_task.router_agent_name, app
                )
                routes_yaml = {}
                for key, target_step in step_or_task.routes.items():
                    routes_yaml[key] = self._generate_yaml_data_recursive(
                        target_step, app
                    )
                pattern_data["routes"] = routes_yaml
                if step_or_task.default_route:
                    pattern_data["default_route"] = self._generate_yaml_data_recursive(
                        step_or_task.default_route, app
                    )
            elif isinstance(step_or_task, DiscussionPattern):
                pattern_data["participants"] = [
                    self._get_agent_details_for_yaml(p_name, app)
                    for p_name in step_or_task.participant_agent_names
                ]
                if step_or_task.moderator_agent_name:
                    pattern_data["moderator"] = self._get_agent_details_for_yaml(
                        step_or_task.moderator_agent_name, app
                    )
                pattern_data["rounds"] = step_or_task.discussion_rounds
                pattern_data["stop_phrase"] = step_or_task.stop_phrase
            return pattern_data
        else:
            return {"error": f"Unknown step type: {type(step_or_task)}"}

    def _generate_yaml_data(self, app: "TFrameXApp") -> Dict[str, Any]:
        flow_data = {
            "flow": {
                "name": self.flow_name,
                "description": self.description,
                "steps": [
                    self._generate_yaml_data_recursive(step, app) for step in self.steps
                ],
            }
        }
        return flow_data

    def _generate_mermaid_string(
        self, app: "TFrameXApp", yaml_data_for_ids: Dict[str, Any]
    ) -> str:
        # yaml_data_for_ids is passed but not explicitly used to re-fetch IDs in this version.
        # The traversal logic for Mermaid is self-contained here.

        mermaid_lines = ["graph TD"]
        node_counter = 0  # Used for unique node IDs

        def escape_mermaid_label(label: str) -> str:
            """Escapes characters in labels and wraps in quotes."""
            if not label:
                return '""'
            # Replace quotes with HTML entity, backticks with spaces (or other entity if preferred)
            escaped = (
                label.replace('"', "#quot;").replace("`", "`").replace("\n", "\\n")
            )
            return f'"{escaped}"'

        def get_item_name(item_data_dict_or_str: Union[str, Dict[str, Any]]) -> str:
            if isinstance(item_data_dict_or_str, str):  # Agent name string
                return item_data_dict_or_str
            # For dicts (parsed YAML structure for an item)
            name = item_data_dict_or_str.get("name", "UnnamedItem")
            if item_data_dict_or_str.get("type") == "pattern":
                name = f"{item_data_dict_or_str.get('pattern_type', 'Pattern')}_{name}"
            return name

        # Main recursive function to add elements to Mermaid
        def add_mermaid_element(
            element_data: Union[
                str, Dict[str, Any]
            ],  # Can be agent name string or dict from YAML parse
            parent_id_prefix: str,
            prev_node_id_in_sequence: str,
            edge_label: Optional[str] = None,
        ) -> str:
            nonlocal node_counter

            # If element_data is a string, it's an agent name. Fetch its details.
            if isinstance(element_data, str):
                element_name_for_id = element_data
                # This agent's details are not yet fetched in this path, but we need them for the label.
                # For Mermaid, we might not need full YAML details, just name and type.
                # This implies _generate_mermaid_string should probably traverse the *original* flow steps,
                # not the YAML data, to have access to BasePattern instances etc.
                # Let's adjust: _generate_mermaid_string should call a new recursive helper that works on flow.steps directly.
                # For now, I will adapt to use the YAML structure that `yaml_data_for_ids` provides.
                # The `element_data` will be the dict from the YAML structure.
                if not isinstance(
                    element_data, dict
                ):  # Should not happen if called with YAML structure
                    logger.error(
                        f"Mermaid generator expected dict, got {type(element_data)}: {element_data}"
                    )
                    return prev_node_id_in_sequence
            else:  # It's a dict
                element_name_for_id = get_item_name(element_data)

            current_node_id = f"{parent_id_prefix}_{element_name_for_id.replace(' ', '_')}_{node_counter}"
            node_counter += 1

            label_text = ""
            if element_data.get("type") == "agent":
                label_text = f"Agent: {element_data.get('name', 'UnknownAgent')}"
                if element_data.get("tools"):
                    label_text += f"\\nTools: {len(element_data['tools'])}"
                if element_data.get("callable_agents_as_tools"):
                    label_text += (
                        f"\\nCalls: {len(element_data['callable_agents_as_tools'])}"
                    )
                mermaid_lines.append(
                    f"    {current_node_id}[{escape_mermaid_label(label_text)}]"
                )

            elif element_data.get("type") == "pattern":
                pattern_type = element_data.get("pattern_type", "UnknownPattern")
                pattern_name = element_data.get("name", "UnnamedPattern")
                label_text = f"Pattern: {pattern_type}\\n({pattern_name})"

                # Define subgraph for the pattern
                mermaid_lines.append(
                    f"    subgraph {current_node_id}_sub [{escape_mermaid_label(label_text)}]"
                )
                mermaid_lines.append("        direction LR")  # Default for patterns

                pattern_internal_start_id = f"{current_node_id}_start"
                pattern_internal_end_id = f"{current_node_id}_end"
                mermaid_lines.append(
                    f"        {pattern_internal_start_id}((:))"
                )  # Smaller start/end for pattern internals
                mermaid_lines.append(f"        {pattern_internal_end_id}((:))")

                # Link from previous sequence node to pattern's internal start
                connection_str = (
                    f" -->|{escape_mermaid_label(edge_label)}|"
                    if edge_label
                    else " -->"
                )
                mermaid_lines.append(
                    f"    {prev_node_id_in_sequence}{connection_str} {pattern_internal_start_id}"
                )

                # Process pattern-specific content
                if pattern_type == "SequentialPattern":
                    prev_in_pattern = pattern_internal_start_id
                    for sub_step_data in element_data.get("steps", []):
                        prev_in_pattern = add_mermaid_element(
                            sub_step_data, current_node_id, prev_in_pattern
                        )
                    mermaid_lines.append(
                        f"        {prev_in_pattern} --> {pattern_internal_end_id}"
                    )

                elif pattern_type == "ParallelPattern":
                    for task_data in element_data.get("tasks", []):
                        task_output_node = add_mermaid_element(
                            task_data, current_node_id, pattern_internal_start_id
                        )
                        mermaid_lines.append(
                            f"        {task_output_node} --> {pattern_internal_end_id}"
                        )

                elif pattern_type == "RouterPattern":
                    router_agent_data = element_data.get("router_agent", {})
                    # router_agent_node_id = add_mermaid_element(router_agent_data, current_node_id, pattern_internal_start_id)
                    # Simplified router agent node definition:
                    router_agent_name = router_agent_data.get("name", "RouterAgent")
                    router_agent_node_id = (
                        f"{current_node_id}_{router_agent_name.replace(' ','_')}"
                    )
                    mermaid_lines.append(
                        f"        {router_agent_node_id}[{escape_mermaid_label(f'Router: {router_agent_name}')}]"
                    )
                    mermaid_lines.append(
                        f"        {pattern_internal_start_id} --> {router_agent_node_id}"
                    )

                    for route_key, target_data in element_data.get(
                        "routes", {}
                    ).items():
                        target_output_node = add_mermaid_element(
                            target_data,
                            current_node_id,
                            router_agent_node_id,
                            edge_label=route_key,
                        )
                        mermaid_lines.append(
                            f"        {target_output_node} --> {pattern_internal_end_id}"
                        )
                    if element_data.get("default_route"):
                        default_target_output = add_mermaid_element(
                            element_data["default_route"],
                            current_node_id,
                            router_agent_node_id,
                            edge_label="Default",
                        )
                        mermaid_lines.append(
                            f"        {default_target_output} --> {pattern_internal_end_id}"
                        )

                elif pattern_type == "DiscussionPattern":
                    # Simplified: Just list participants and moderator if any
                    if element_data.get("moderator"):
                        mod_data = element_data.get("moderator")
                        mod_output = add_mermaid_element(
                            mod_data,
                            current_node_id,
                            pattern_internal_start_id,
                            edge_label="Moderates",
                        )
                        mermaid_lines.append(
                            f"        {mod_output} --> {pattern_internal_end_id}"
                        )  # Moderator leads to end
                    for p_data in element_data.get("participants", []):
                        p_output = add_mermaid_element(
                            p_data, current_node_id, pattern_internal_start_id
                        )  # All participants start from beginning
                        mermaid_lines.append(
                            f"        {p_output} --> {pattern_internal_end_id}"
                        )  # And contribute to end

                mermaid_lines.append("    end")  # End subgraph
                # The "output" of a pattern subgraph for sequential linking is its internal end node
                current_node_id = pattern_internal_end_id
                # However, the connection from prev_node_id_in_sequence was already made to pattern_internal_start_id.
                # The current_node_id to be returned should be the one that the *next* sequential step connects *from*.
                # So, if this was a pattern, the next step connects from its internal_end_id.
                # This is correct.

            else:  # Should not happen if YAML structure is correct
                mermaid_lines.append(
                    f"    {current_node_id}[{escape_mermaid_label(f'Unknown: {element_name_for_id}')}]"
                )

            # Connect previous step to current step (if not a pattern, where connection is handled differently)
            if element_data.get("type") != "pattern":
                connection_str = (
                    f" -->|{escape_mermaid_label(edge_label)}|"
                    if edge_label
                    else " -->"
                )
                mermaid_lines.append(
                    f"    {prev_node_id_in_sequence}{connection_str} {current_node_id}"
                )

            return (
                current_node_id  # Return the ID of the last main node of this element
            )

        # --- Start Mermaid generation ---
        flow_id_main = self.flow_name.replace(" ", "_")
        mermaid_lines.append(
            f"subgraph {flow_id_main}_overall [{escape_mermaid_label(f'Flow: {self.flow_name}')}]"
        )
        mermaid_lines.append("    direction TD")

        flow_start_node = f"{flow_id_main}_FlowStart"
        flow_end_node = f"{flow_id_main}_FlowEnd"
        mermaid_lines.append(f'    {flow_start_node}(("Start"))')
        mermaid_lines.append(f'    {flow_end_node}(("End"))')

        last_node_in_flow_sequence = flow_start_node
        flow_steps_data = yaml_data_for_ids.get("flow", {}).get("steps", [])

        for step_data_item in flow_steps_data:
            last_node_in_flow_sequence = add_mermaid_element(
                step_data_item, flow_id_main, last_node_in_flow_sequence
            )

        mermaid_lines.append(f"    {last_node_in_flow_sequence} --> {flow_end_node}")
        mermaid_lines.append("end")  # End main flow subgraph

        return "\n".join(mermaid_lines)
