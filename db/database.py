import sqlite3
import uuid
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict
from utils.log import print_log

class Database:
    def __init__(self, db_path: str = "db/chat.db"):
        Path(db_path).parent.mkdir(exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.create_tables()
    
    def create_tables(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                title TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id TEXT,
                role TEXT NOT NULL,
                content TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id)
            );
            
            CREATE TABLE IF NOT EXISTS user_memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        self.conn.commit()
    
    def create_conversation(self) -> str:
        conversation_id = str(uuid.uuid4())
        print_log(f"INSERTING new conversation#{conversation_id} into DB", "green")
        self.conn.execute("INSERT INTO conversations (id) VALUES (?)", (conversation_id,))
        self.conn.commit()
        return conversation_id
    
    def update_conversation_title(self, conversation_id: str, title: str):
        print_log(f"UPDATING title for conversation#{conversation_id}: {title}", "green")
        self.conn.execute(
            "UPDATE conversations SET title = ? WHERE id = ?",
            (title, conversation_id)
        )
        self.conn.commit()
    
    def add_message(self, conversation_id: str, role: str, content: str):
        print_log(f"INSERTING new message into conversation#{conversation_id}", "green")
        self.conn.execute(
            "INSERT INTO messages (conversation_id, role, content) VALUES (?, ?, ?)",
            (conversation_id, role, content)
        )
        self.conn.commit()
    
    def get_conversation_messages(self, conversation_id: str) -> List[Dict[str, str]]:
        print_log(f"FETCHING messages for conversation#{conversation_id}", "green")
        cursor = self.conn.execute(
            "SELECT role, content FROM messages WHERE conversation_id = ? ORDER BY created_at",
            (conversation_id,)
        )
        return [{"role": role, "content": content} for role, content in cursor.fetchall()]
    
    def close(self):
        self.conn.close()
