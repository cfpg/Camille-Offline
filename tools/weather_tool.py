from tools import register_tool


@register_tool
def get_weather(city: str) -> str:
    """Get the current weather for a specific city. 
    Only accepts real city names as input.
    """
    return f"The weather in {city} is 72°F and sunny."
