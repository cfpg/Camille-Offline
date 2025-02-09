from typing import List, Dict, Optional
from .types import Message
from utils.log import print_log
from db.database import Database

class Memory:
    def __init__(self, api_client):
        self.db = Database()
        self.api_client = api_client
        self.current_conversation_id = self.db.create_conversation()
        self.messages: List[Message] = []
        self.first_user_message = True
    
    def start_new_conversation(self):
        print_log("Starting new conversation", "magenta")
        self.current_conversation_id = self.db.create_conversation()
        self.messages = []
        self.first_user_message = True
    
    def generate_title(self, message: str) -> str:
        response = self.api_client.get_completion(
            messages=[{
                "role": "system",
                "content": "Generate a brief, descriptive title (max 6 words) for a conversation that starts with this message. Respond with only the title, no quotes or additional text."
            }, {
                "role": "user",
                "content": message
            }],
            temperature=0.7
        )
        return response.get("content", "Untitled Conversation").strip()
    
    def add_message(self, role: str, content: str):
        print_log(f"Adding message to memory: {role}: {content}", "magenta")
        
        # Generate title on first user message
        if role == "user" and self.first_user_message:
            print_log(f"Generating title for conversation", "magenta")
            title = self.generate_title(content)
            print_log(f"Generated title for conversation: {title}", "magenta")
            self.db.update_conversation_title(self.current_conversation_id, title)
            self.first_user_message = False
        
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
