from typing import List, Dict
from .types import Message
from utils.log import print_log

class Memory:
    def __init__(self):
        self.messages: List[Message] = []
    
    def add_message(self, role: str, content: str):
        print_log(f"Adding message to memory: {role}: {content}", "green")
        self.messages.append(Message(role=role, content=content))
    
    def get_messages(self) -> List[Dict[str, str]]:
        return [{"role": msg.role, "content": msg.content} for msg in self.messages]
    
    def clear(self):
        self.messages = []
