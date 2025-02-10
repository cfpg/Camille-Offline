def get_system_prompt(ai_name: str, appendStr: str = "") -> str:
    return (
        f"You are {ai_name}, an AI personal assistant with access to external tools. "
        "Use the provided tools when appropriate to help users. "
        "Keep responses concise (1-4 sentences). "
        f"{appendStr}"
    )
