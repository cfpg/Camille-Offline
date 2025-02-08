from typing import List, Dict
from .types import Message
from utils.log import print_log

class Memory:
    def __init__(self):
        self.messages: List[Message] = []
    
    def add_message(self, role: str, content: str):
        print_log(f"Adding message to memory: {role}: {content}", "green")
        if role == "tool":
            # Parse tool response and format it as a function response
            tool_data = json.loads(content)
            self.messages.append(Message(
                role="assistant",
                content=None,
                function_call={
                    "id": tool_data["tool_call_id"],
                    "name": tool_data["name"],
                    "arguments": tool_data["result"]
                }
            ))
        else:
            self.messages.append(Message(role=role, content=content))
    
    def get_messages(self) -> List[Dict[str, str]]:
        return [{"role": msg.role, "content": msg.content} for msg in self.messages]
    
    def clear(self):
        self.messages = []
