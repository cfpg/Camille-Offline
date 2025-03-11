from datetime import datetime, timedelta, time
import json
from tools import register_tool
from db.database import Database
from typing import Optional, List, Dict, Union

class TaskManager:
    def __init__(self):
        self.db = Database()

    def add_task(self, description: str, deadline: Optional[str] = None) -> Dict:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            deadline_ts = None
            if deadline:
                try:
                    deadline_ts = datetime.fromisoformat(deadline)
                except ValueError:
                    return {"error": f"Invalid deadline format: {deadline}"}
            
            cursor.execute(
                "INSERT INTO tasks (description, deadline, status) VALUES (?, ?, ?)",
                (description, deadline_ts, "pending")
            )
            conn.commit()
            return {"success": True, "task_id": cursor.lastrowid}

    def get_tasks(self, filter_type: str = "all") -> List[Dict]:
        cursor = self.db.conn.cursor()
        
        if filter_type == "today":
            cursor.execute("""
                SELECT id, description, deadline, status 
                FROM tasks 
                WHERE date(deadline) = date('now')
                AND status = 'pending'
                ORDER BY deadline
            """)
        elif filter_type == "pending":
            cursor.execute("""
                SELECT id, description, deadline, status 
                FROM tasks 
                WHERE status = 'pending'
                ORDER BY deadline
            """)
        else:
            cursor.execute("""
                SELECT id, description, deadline, status 
                FROM tasks 
                ORDER BY 
                    CASE WHEN status = 'pending' THEN 0 ELSE 1 END,
                    deadline
            """)
        
        return [
            {
                "id": row[0],
                "description": row[1],
                "deadline": row[2],
                "status": row[3]
            }
            for row in cursor.fetchall()
        ]

    def complete_task(self, task_description: str) -> Dict:
        cursor = self.db.conn.cursor()
        cursor.execute(
            """
            UPDATE tasks 
            SET status = 'completed', completed_at = CURRENT_TIMESTAMP 
            WHERE description LIKE ? AND status = 'pending'
            """,
            (f"%{task_description}%",)
        )
        self.db.conn.commit()
        return {"success": True, "updated_count": cursor.rowcount}

    def manage_tasks(self, action: str, details: Union[str, Dict]) -> str:
        """
        Manage tasks based on the specified action.
        Args:
            action: The action to perform ('add', 'list', 'update', etc.)
            details: Task details as either JSON string or dict
        Returns:
            JSON string with the result
        """
        try:
            # Convert details to dict if it's a JSON string
            if isinstance(details, str):
                details = json.loads(details)
            
            if action == "add":
                return self._add_task(details)
            elif action == "list":
                return self._list_tasks(details)
            
            return json.dumps({"error": f"Unknown action: {action}"})
            
        except Exception as e:
            return json.dumps({"error": f"Error managing tasks: {str(e)}"})

    def _add_task(self, details: Dict) -> str:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            deadline_ts = None
            if details.get('deadline'):
                try:
                    deadline_ts = datetime.fromisoformat(details['deadline'])
                except ValueError:
                    return json.dumps({"error": f"Invalid deadline format: {details['deadline']}"})
            
            cursor.execute(
                "INSERT INTO tasks (description, deadline, status) VALUES (?, ?, ?)",
                (details['description'], deadline_ts, "pending")
            )
            conn.commit()
            return json.dumps({"success": True, "task_id": cursor.lastrowid})

    def _list_tasks(self, details: Dict) -> str:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            filter_type = details.get('filter', 'all')
            
            now = datetime.now()
            query = """
                SELECT id, description, deadline, status 
                FROM tasks 
                WHERE 1=1
            """
            params = []

            # Handle different time-based filters
            if filter_type == 'today':
                query += " AND date(deadline) = date(?)"
                params.append(now.date())
            elif filter_type == 'tomorrow':
                tomorrow = now.date() + timedelta(days=1)
                query += " AND date(deadline) = date(?)"
                params.append(tomorrow)
            elif filter_type == 'this_week':
                week_start = now.date() - timedelta(days=now.weekday())
                week_end = week_start + timedelta(days=6)
                query += " AND date(deadline) BETWEEN date(?) AND date(?)"
                params.extend([week_start, week_end])
            elif filter_type == 'next_week':
                next_week_start = now.date() + timedelta(days=7-now.weekday())
                next_week_end = next_week_start + timedelta(days=6)
                query += " AND date(deadline) BETWEEN date(?) AND date(?)"
                params.extend([next_week_start, next_week_end])
            elif filter_type == 'overdue':
                query += " AND deadline < ? AND status != 'completed'"
                params.append(now)
            
            query += " ORDER BY deadline"
            
            cursor.execute(query, params)
            tasks = []
            for row in cursor.fetchall():
                deadline = row[2]
                if isinstance(deadline, str):
                    deadline = datetime.fromisoformat(deadline)
                
                tasks.append({
                    "id": row[0],
                    "description": row[1],
                    "deadline": deadline.isoformat() if deadline else None,
                    "status": row[3]
                })
            
            return json.dumps({
                "success": True, 
                "tasks": tasks,
                "filter": filter_type
            })

task_manager = TaskManager()

@register_tool
def manage_tasks(action: str, details: str) -> str:
    """
    Manage tasks/todos with various actions: add, list, or complete.
    
    Args:
        action: The action to perform ('add', 'list', or 'complete')
        details: JSON string containing action details:
                For 'add': {"description": "task description", "deadline": "YYYY-MM-DD HH:MM:SS"} (deadline optional)
                For 'list': {"filter": "all|today|pending"}
                For 'complete': {"description": "task description to mark as complete"}
    
    Returns:
        Result of the operation as a formatted string
    """
    try:
        details_dict = json.loads(details)
        
        result = task_manager.manage_tasks(action, details_dict)
        return result
            
    except Exception as e:
        return json.dumps({"error": f"Error managing tasks: {str(e)}"}) 