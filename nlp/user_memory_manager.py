from dataclasses import dataclass
from typing import List, Optional
from utils.log import print_log
from config import Config

@dataclass
class SetupQuestion:
    key: str
    question: str
    memory_template: str

class UserMemoryManager:
    def __init__(self, db):
        self.db = db
        self.is_setup = not self.needs_setup()
        self.setup_questions = [
            SetupQuestion("name", "What is your name?", "My name is {value}"),
            SetupQuestion("city", "Which city do you live in?", "I live in {value}"),
            SetupQuestion("occupation", "What do you do for a living?", "I work as {value}")
        ]

    def get_memories(self, source: str = 'setup') -> List[str]:
        cursor = self.db.conn.execute("SELECT memory, source FROM user_memories WHERE source = ?", (source,))
        return cursor.fetchall()

    def save_memory(self, memory: str, source: str = 'setup') -> None:
        print_log(f"Saving memory: {memory} (source: {source})", "cyan")
        self.db.conn.execute(
            "INSERT INTO user_memories (memory, source) VALUES (?, ?)",
            (memory, source)
        )
        self.db.conn.commit()
        
    def needs_setup(self) -> bool:
        cursor = self.db.conn.execute("SELECT COUNT(*) FROM user_memories WHERE source = 'setup'")
        return cursor.fetchone()[0] == 0

    def get_setup_questions(self):
        return self.setup_questions

    def save_setup_question(self, question: SetupQuestion, value: str) -> None:
        print_log(f"Saving setup question: {question.question}", "cyan")
        memory = question.memory_template.format(value=value)
        self.save_memory(memory)

