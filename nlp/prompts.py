def get_system_prompt(ai_name: str) -> str:
    return (
        f"You are {ai_name}, an AI assistant with access to external tools. "
        "Use the provided tools when appropriate to help users. "
        "Keep responses concise (1-4 sentences)."
    )
