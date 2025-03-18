from importlib import import_module
from pathlib import Path
from typing import Dict, Any, Callable
from utils.log import print_log
from config import *  # Import all config here
from nlp.types import ToolFunc

_tools: Dict[str, ToolFunc] = {}
_initialized = False

def register_tool(func: ToolFunc) -> ToolFunc:
    """
    Register a tool function.
    The function must return a string and can take any parameters.
    """
    _tools[func.__name__] = func
    return func

def _initialize_tools() -> None:
    """Initialize tools if not already initialized."""
    global _initialized
    if _initialized:
        return
        
    tools_dir = Path(__file__).parent
    for file in tools_dir.glob("*.py"):
        if file.stem != "__init__":
            try:
                module_name = f"tools.{file.stem}"
                import_module(module_name)
                print_log(f"Imported tool module: {module_name}", "yellow")
            except ImportError as e:
                print_log(f"Failed to import tool module {module_name}: {e}", "red")
    
    _initialized = True

def get_all_tools() -> Dict[str, ToolFunc]:
    """
    Get a copy of all registered tools.
    Returns:
        Dict[str, ToolFunc]: Dictionary of tool name to tool function mappings
    """
    if not _initialized:
        _initialize_tools()
    return _tools.copy()
