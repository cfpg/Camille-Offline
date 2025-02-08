from typing import Optional, get_type_hints
from inspect import signature
from .types import ToolFunc

class Tool:
    def __init__(self, func: ToolFunc, name: str, description: str):
        self.func = func
        self.name = name
        self.description = description
        self.signature = signature(func)
        self.type_hints = get_type_hints(func)

    def __call__(self, *args, **kwargs) -> str:
        return self.func(*args, **kwargs)

    @property
    def parameters(self) -> str:
        params = []
        for param_name, param in self.signature.parameters.items():
            param_type = self.type_hints.get(param_name, "Any")
            default = "" if param.default is param.empty else f" = {param.default}"
            params.append(f"{param_name}: {param_type}{default}")
        return ", ".join(params)
