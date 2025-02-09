from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Callable, Literal, TypedDict, NotRequired


class FunctionCall(TypedDict):
    id: str
    name: str
    arguments: str

@dataclass
class Message:
    role: str
    content: str
    function_call: Optional[FunctionCall] = None

class ToolFunction(TypedDict):
    name: str
    description: str
    parameters: Dict[str, Any]

class Tool(TypedDict):
    type: Literal["function"]
    function: ToolFunction

ToolFunc = Callable[..., str]
