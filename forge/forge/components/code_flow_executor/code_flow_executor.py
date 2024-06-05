"""Commands to generate images based on text input"""

import inspect
import logging
from typing import Any, Iterator

from forge.agent.protocols import CommandProvider
from forge.command import Command, command
from forge.models.json_schema import JSONSchema

MAX_RESULT_LENGTH = 1000
logger = logging.getLogger(__name__)


class CodeFlowExecutionComponent(CommandProvider):
    """A component that provides commands to execute code flow."""

    def __init__(self):
        self._enabled = True
        self.available_functions = {}

    def set_available_functions(self, functions: list[Command]):
        self.available_functions = {
            name: function for function in functions for name in function.names
        }

    def get_commands(self) -> Iterator[Command]:
        yield self.execute_code_flow

    @command(
        parameters={
            "python_code": JSONSchema(
                type=JSONSchema.Type.STRING,
                description="The Python code to execute",
                required=True,
            ),
            "plan_text": JSONSchema(
                type=JSONSchema.Type.STRING,
                description="The plan to written in a natural language",
                required=False,
            ),
        },
    )
    async def execute_code_flow(self, python_code: str, plan_text: str) -> str:
        """Execute the code flow.

        Args:
            python_code (str): The Python code to execute
            callables (dict[str, Callable]): The dictionary of [name, callable] pairs to use in the code

        Returns:
            str: The result of the code execution
        """
        code_header = "import inspect\n" + "\n".join(
            [
                f"""
async def {name}(*args, **kwargs):
    result = {name}_func(*args, **kwargs)
    if inspect.isawaitable(result):
        result = await result
    return result
"""
                for name in self.available_functions.keys()
            ]
        )
        locals: dict[str, Any] = {
            name + "_func": func for name, func in self.available_functions.items()
        }
        code = (
            f"{code_header}\n"
            f"{python_code}\n\n"
            f"exec_output = main()"
        )
        logger.debug(f"Code-Flow Execution code:\n{python_code}")
        exec(code, locals)
        result = await locals["exec_output"]
        logger.debug(f"Code-Flow Execution result:\n{result}")
        if inspect.isawaitable(result):
            result = await result

        # limit the result to limit the characters
        if len(result) > MAX_RESULT_LENGTH:
            result = result[:MAX_RESULT_LENGTH] + "...[Truncated, Content is too long]"
        return f"Execution Plan:\n{plan_text}\n\nExecution Output:\n{result}"
