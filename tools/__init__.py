from importlib import import_module
from pathlib import Path
from typing import Dict, Callable
from utils.log import print_log
from config import *  # Import all config here

_tools: Dict[str, Callable] = {}

def register_tool(func: Callable) -> Callable:
    _tools[func.__name__] = func
    return func

def get_all_tools() -> Dict[str, Callable]:
    return _tools.copy()

def auto_discover_tools():
    """Automatically discover and import all tools in the tools directory."""
    tools_dir = Path(__file__).parent
    for file in tools_dir.glob("*.py"):
        if file.stem != "__init__":
            try:
                module_name = f"tools.{file.stem}"
                import_module(module_name)
                print_log(f"Imported tool module: {module_name}", "yellow")
            except ImportError as e:
                print_log(f"Failed to import tool module {module_name}: {e}", "red")

# Automatically discover tools when the package is imported
auto_discover_tools()
