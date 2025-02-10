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
        self.user_memories = self.get_user_memories()
        self.has_been_setup = len(self.user_memories) > 0
        self.setup_questions = [
            SetupQuestion("name", "What is your name?", "My name is {value}"),
            SetupQuestion("city", "Which city do you live in?", "I live in {value}"),
            SetupQuestion("occupation", "What do you do for a living?", "I work as {value}")
        ]

    def get_user_memories(self, source: str = 'setup') -> List[str]:
        return self.db.get_user_memories(source)

    def save_user_memory(self, memory: str, source: str = 'setup') -> None:
        self.db.add_user_memory(memory, source)
        
    def needs_setup(self) -> bool:
        if self.has_been_setup:
            return False
        
        cursor = self.db.conn.execute("SELECT COUNT(*) FROM user_memories WHERE source = 'setup'")
        self.has_been_setup = cursor.fetchone()[0] >= 1
        return not self.has_been_setup

    def get_setup_questions(self):
        return self.setup_questions

    def save_setup_question(self, question: SetupQuestion, value: str) -> None:
        print_log(f"Saving setup question: {question.question}", "cyan")
        memory = question.memory_template.format(value=value)
        self.save_user_memory(memory)

