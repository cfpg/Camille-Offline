from datetime import datetime
from config import Config
from utils.colors import colors

def print_log(text: str, color: str = "reset", force: bool = False) -> None:
    """
    Prints a log message with optional color formatting, respecting the DEBUG flag.

    Args:
        text: The text to print.
        color: The color to use (from utils/colors.py). Defaults to "reset".
        force: If True, prints the log regardless of the DEBUG flag.
    """
    if force or Config.DEBUG:
        now = datetime.now()
        timestamp = now.strftime("%Y-%m-%d %H:%M:%S")  #  strftime format the time
        color_code = colors.get(color, colors["reset"])
        print(f"{timestamp} - {color_code}{text}{colors['reset']}")
