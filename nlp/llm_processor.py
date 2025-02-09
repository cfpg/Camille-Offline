import json
import logging
from typing import Dict, Optional, List, Any
from .memory import Memory
from .tool import Tool
from .types import ToolFunc
from .prompts import get_system_prompt
from .api_client import OpenAIClient
from tools import get_all_tools
from config import Config
from utils.colors import colors
from utils.log import print_log

logger = logging.getLogger(__name__)

class LLMProcessor:
    def __init__(self, model: str, ai_name: str, user_name: str):
        self.ai_name = ai_name
        self.user_name = user_name
        self.tools: Dict[str, Tool] = {}
        self.api_client = OpenAIClient(
            model=model,
            api_base=Config.OPENAI_API_BASE,
            api_key=Config.OPENAI_KEY
        )
        self.memory = Memory(self.api_client)
        
        self._register_tools()
        self._initialize_system_prompt()
    
    def _initialize_system_prompt(self) -> None:
        self.system_prompt = get_system_prompt(self.ai_name)
        self.memory.add_message("system", self.system_prompt)

    def register_tool(self, func: ToolFunc, name: Optional[str] = None, description: Optional[str] = None):
        tool_name = name or func.__name__
        tool_description = description or func.__doc__ or "No description available"
        self.tools[tool_name] = Tool(func, tool_name, tool_description)
        return func
    
    def _register_tools(self):
        try:
            print(f"{colors['yellow']}Registering tools: {get_all_tools().items()}{colors['reset']}")
            for name, func in get_all_tools().items():
                self.register_tool(func, name=name)
        except Exception as e:
            logger.error(f"Failed to register tools: {e}")
            raise

    def _get_openai_tools(self) -> List[Dict[str, Any]]:
        return [tool.to_openai_schema() for tool in self.tools.values()]

    def _handle_tool_call(self, response: Dict[str, Any]) -> str:
        try:
            # If no tool calls, return the content directly
            if "tool_calls" not in response:
                return response.get("content", "I apologize, but I couldn't process that request.")

            # Handle tool calls
            tool_calls = response.get("tool_calls", [])
            if not tool_calls:
                return response.get("content", "I apologize, but I couldn't process that request.")

            # Process each tool call
            for tool_call in tool_calls:
                if tool_call["type"] != "function":
                    continue

                function_call = tool_call["function"]
                tool_name = function_call["name"]
                tool_args = json.loads(function_call["arguments"])

                if tool_name not in self.tools:
                    return f"I apologize, but I don't have access to the {tool_name} tool."

                print_log(f"Calling tool {tool_name} with args {tool_args}", "yellow")
                tool_result = self.tools[tool_name](**tool_args)

                # Add tool result to memory
                self.memory.add_message(
                    "tool", 
                    json.dumps({
                        "tool_call_id": tool_call["id"],
                        "name": tool_name,
                        "result": tool_result
                    })
                )

            # Get new response from LLM with tool results
            messages = self.memory.get_messages()
            final_response = self.api_client.get_completion(
                messages, 
                tools=self._get_openai_tools()
            )
            return final_response.get("content", "I apologize, but I couldn't process the tool results.")

        except Exception as e:
            logger.error(f"Tool call failed: {e}")
            return f"I encountered an error while trying to help you: {str(e)}"

    def process_input(self, input_text: str) -> str:
        self.memory.add_message("user", input_text)
        messages = self.memory.get_messages()
        
        response = self.api_client.get_completion(
            messages, 
            tools=self._get_openai_tools()
        )
        final_response = self._handle_tool_call(response)
        
        self.memory.add_message("assistant", final_response)
        return final_response
    
    def clear_memory(self):
        self.memory.clear()
        self.memory.add_message("system", self.system_prompt)
