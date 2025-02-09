from typing import List, Dict, Optional
from .types import Message
from utils.log import print_log
from db.database import Database

class Memory:
    def __init__(self):
        self.db = Database()
        self.current_conversation_id = self.db.create_conversation()
        self.messages: List[Message] = []
    
    def start_new_conversation(self):
        print_log("Starting new conversation", "magenta")
        self.current_conversation_id = self.db.create_conversation()
        self.messages = []
    
    def add_message(self, role: str, content: str):
        print_log(f"Adding message to memory: {role}: {content}", "magenta")
        if role == "tool":
            import json
            tool_data = json.loads(content)
            message = Message(
                role="assistant",
                content=None,
                function_call={
                    "id": tool_data["tool_call_id"],
                    "name": tool_data["name"],
                    "arguments": tool_data["result"]
                }
            )
        else:
            message = Message(role=role, content=content)
        
        self.messages.append(message)
        self.db.add_message(self.current_conversation_id, role, content)
    
    def get_messages(self) -> List[Dict[str, str]]:
        return [{"role": msg.role, "content": msg.content} for msg in self.messages]
    
    def clear(self):
        self.start_new_conversation()
