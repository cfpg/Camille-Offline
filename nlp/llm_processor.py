import json
import logging
from typing import Dict, Optional
from .memory import Memory
from .tool import Tool
from .types import ToolFunc
from .prompts import get_system_prompt
from .api_client import OpenAIClient
from tools import get_all_tools
from config import Config
from utils.colors import colors


logger = logging.getLogger(__name__)

class LLMProcessor:
    def __init__(self, model: str, ai_name: str, user_name: str):
        self.ai_name = ai_name
        self.user_name = user_name
        self.memory = Memory()
        self.tools: Dict[str, Tool] = {}
        self.api_client = OpenAIClient(
            model=model,
            api_base=Config.OPENAI_API_BASE,
            api_key=Config.OPENAI_KEY
        )
        
        self._register_tools()
        self._initialize_system_prompt()
    
    def _initialize_system_prompt(self) -> None:
        tools_description = self._get_tools_description()
        self.system_prompt = get_system_prompt(self.ai_name, tools_description)
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

    def _get_tools_description(self) -> str:
        tool_descriptions = []
        for name, tool in self.tools.items():
            signature = str(tool.func.__annotations__)  # Get function signature
            tool_descriptions.append(
                f"Tool: {name}\n"
                f"Description: {tool.description}\n"
                f"Parameters: {signature}\n"
            )
        return "\n".join(tool_descriptions)

    def _handle_tool_call(self, response: str) -> str:            
        try:
            # Attempt to parse the entire response as a JSON object
            tool_call = json.loads(response)

            # Check if the expected keys "tool" and "args" are present
            if "tool" not in tool_call or "args" not in tool_call:
                return response  # Not a tool call, return original response

            tool_name = tool_call["tool"]
            tool_args = tool_call.get("args", {})

            if tool_name not in self.tools:
                return f"I apologize, but I don't have access to the {tool_name} tool."

            logger.debug(f"Calling tool {tool_name} with args {tool_args}")
            tool_result = self.tools[tool_name](**tool_args)

            # Add tool result to memory
            self.memory.add_message("system", f"Tool {tool_name} returned: {tool_result}")

            # Get new response from LLM with tool results
            messages = self.memory.get_messages()
            return self.api_client.get_completion(messages)

        except json.JSONDecodeError:
            # If JSON decoding fails, it's not a tool call, return original response
            return response
        except Exception as e:
            logger.error(f"Tool call failed: {e}")
            return f"I encountered an error while trying to help you: {str(e)}"

    def process_input(self, input_text: str) -> str:
        self.memory.add_message("user", input_text)
        messages = self.memory.get_messages()
        
        response = self.api_client.get_completion(messages)
        final_response = self._handle_tool_call(response)
        
        self.memory.add_message("assistant", final_response)
        return final_response
    
    def clear_memory(self):
        self.memory.clear()
        self.memory.add_message("system", self.system_prompt)
