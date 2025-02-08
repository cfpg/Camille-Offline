from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Callable

@dataclass
class Message:
    role: str
    content: str

ToolFunc = Callable[..., str]
