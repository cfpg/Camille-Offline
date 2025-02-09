import json
from typing import List, Dict, Optional
from .types import Message, FunctionCall
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
                "content": "Generate a brief, descriptive title (max 6 words) for a conversation that starts with this message, this title will be used to allow the user to find the conversation in the future and should be descriptive written from the perspective of the command that the user asked. Respond with only the title, no quotes or additional text."
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
            print_log(f"Title generated for conversation: {title}", "magenta")
            self.db.update_conversation_title(self.current_conversation_id, title)
            self.first_user_message = False
        
        if role == "tool":
            tool_data = json.loads(content)

            # Add the assistant's function call with the original arguments
            function_call = FunctionCall(
                id=tool_data["tool_call_id"],
                name=tool_data["name"],
                arguments=json.dumps(tool_data["arguments"])
            )
            assistant_message = Message(role="assistant", content=None, function_call=function_call)
            self.messages.append(assistant_message)
            self.db.add_message(self.current_conversation_id, "assistant", json.dumps({
                "function_call": {
                    "id": tool_data["tool_call_id"],
                    "name": tool_data["name"],
                    "arguments": json.dumps(tool_data["arguments"])
                }
            }))
            
            # Add the function's response with name
            function_message = Message(
                role="tool", 
                content=tool_data["result"],
                function_call=FunctionCall(
                    id=tool_data["tool_call_id"],
                    name=tool_data["name"],
                    arguments=""
                )
            )
            self.messages.append(function_message)
            self.db.add_message(self.current_conversation_id, "tool", tool_data["result"])
        else:
            message = Message(role=role, content=content)
            self.messages.append(message)
            self.db.add_message(self.current_conversation_id, role, content)
    
    def get_messages(self) -> List[Dict[str, str]]:
        messages = []
        for msg in self.messages:
            if msg.role == "assistant" and msg.function_call:
                messages.append({
                    "role": msg.role,
                    "content": "",
                    "function_call": {
                        "name": msg.function_call["name"],
                        "arguments": msg.function_call["arguments"]
                    }
                })
            elif msg.role == "tool":
                messages.append({
                    "role": msg.role,
                    "name": msg.function_call["name"] if msg.function_call else None,
                    "content": msg.content
                })
            else:
                messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
        return messages
    
    def clear(self):
        self.start_new_conversation()
