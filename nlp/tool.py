import json
from typing import Optional, get_type_hints, Dict, Any
from inspect import signature
from .types import ToolFunc, Tool as ToolType, ToolFunction

class Tool:
    def __init__(self, func: ToolFunc, name: str, description: str):
        self.func = func
        self.name = name
        self.description = description
        self.signature = signature(func)
        self.type_hints = get_type_hints(func)

    def __call__(self, *args, **kwargs) -> str:
        return self.func(*args, **kwargs)

    def to_openai_schema(self) -> ToolType:
        """Convert tool to OpenAI's function calling format."""
        parameters: Dict[str, Any] = {
            "type": "object",
            "properties": {},
            "required": []
        }
        
        for param_name, param in self.signature.parameters.items():
            param_type = self.type_hints.get(param_name, Any)
            param_schema = {"type": "string"}  # Default to string
            
            # Map Python types to JSON Schema types
            if param_type in (int, float):
                param_schema["type"] = "number"
            elif param_type == bool:
                param_schema["type"] = "boolean"
            elif param_type == dict:
                param_schema["type"] = "object"
            elif param_type == list:
                param_schema["type"] = "array"
            
            parameters["properties"][param_name] = param_schema
            
            if param.default is param.empty:
                parameters["required"].append(param_name)
        
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": parameters
            }
        }
