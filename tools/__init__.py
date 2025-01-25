from importlib import import_module
from pathlib import Path
from langchain.tools import tool

# Registry dictionary to hold all tools
TOOL_REGISTRY = {}


def register_tool(func):
    """
    Decorator to register a tool function.
    Creates a proper LangChain tool object.
    """
    # Create a LangChain tool object
    tool_obj = tool(func)
    TOOL_REGISTRY[tool_obj.name] = tool_obj
    return tool_obj


def get_all_tools():
    """Return a list of all registered tools."""
    return list(TOOL_REGISTRY.values())


def auto_discover_tools():
    """Automatically discover and import all tools in the tools directory."""
    tools_dir = Path(__file__).parent
    for file in tools_dir.glob("*.py"):
        if file.stem != "__init__":
            module_name = f"tools.{file.stem}"
            import_module(module_name)


# Automatically discover tools when the package is imported
auto_discover_tools()
