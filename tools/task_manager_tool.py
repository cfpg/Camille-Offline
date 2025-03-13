from datetime import datetime, timedelta, time
import json
from tools import register_tool
from db.database import Database
from typing import Optional, List, Dict, Union
import re

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
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
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

    def complete_task(self, tasks: Union[Dict, List[Dict]]) -> Dict:
        """
        Complete one or more tasks based on task model(s).
        Args:
            tasks: Either a single task dict or list of task dicts, each containing
                  at least an 'id' field
        Returns:
            Dict with success status and number of tasks updated
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Convert single task to list for uniform handling
            if isinstance(tasks, dict):
                tasks = [tasks]
                
            # Extract IDs from task models
            task_ids = [task['id'] for task in tasks if task.get('id')]
            
            if not task_ids:
                return {"success": False, "error": "No valid task IDs provided"}
                
            # Handle multiple task IDs
            placeholders = ','.join('?' * len(task_ids))
            cursor.execute(
                f"""
                UPDATE tasks 
                SET status = 'completed', completed_at = CURRENT_TIMESTAMP 
                WHERE id IN ({placeholders}) AND status = 'pending'
                """,
                task_ids
            )
            
            conn.commit()
            return {"success": True, "updated_count": cursor.rowcount}

    def complete_overdue_tasks(self) -> Dict:
        """Complete all tasks that have passed their deadline."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE tasks 
                SET status = 'completed', completed_at = CURRENT_TIMESTAMP 
                WHERE deadline < CURRENT_TIMESTAMP 
                AND status = 'pending'
                """
            )
            conn.commit()
            return {"success": True, "updated_count": cursor.rowcount}

    def manage_tasks(self, action: str, details: Union[str, Dict]) -> str:
        try:
            # Convert details to dict if it's a JSON string
            if isinstance(details, str):
                try:
                    details = json.loads(details)
                except json.JSONDecodeError:
                    return json.dumps({"error": "Invalid JSON in details"})
            
            if action == "add":
                return self._add_task(details)
            elif action == "list":
                return self._list_tasks(details)
            elif action == "complete":
                # Handle array of tasks/commands
                if isinstance(details, list):
                    # Check if we're marking overdue tasks
                    if any(task.get('overdue') for task in details):
                        result = self.complete_overdue_tasks()
                    else:
                        result = self.complete_task(details)
                # Handle single task/command
                else:
                    if details.get('overdue'):
                        result = self.complete_overdue_tasks()
                    else:
                        result = self.complete_task(details)
                return json.dumps(result)
            
            return json.dumps({"error": f"Unknown action: {action}"})
            
        except Exception as e:
            return json.dumps({"error": f"Error managing tasks: {str(e)}"})

    def parse_time_string(self, time_str: str) -> datetime:
        """
        Convert a relative time string (e.g. '15 minutes', '2 hours') to a datetime
        """
        now = datetime.now()
        
        # Parse the time string
        match = re.match(r'(\d+)\s+(minute|minutes|hour|hours|day|days)', time_str.lower())
        if not match:
            raise ValueError(f"Invalid time format: {time_str}")
        
        amount = int(match.group(1))
        unit = match.group(2)
        
        # Convert to timedelta
        if unit in ['minute', 'minutes']:
            delta = timedelta(minutes=amount)
        elif unit in ['hour', 'hours']:
            delta = timedelta(hours=amount)
        elif unit in ['day', 'days']:
            delta = timedelta(days=amount)
        else:
            raise ValueError(f"Unsupported time unit: {unit}")
        
        return now + delta

    def _add_task(self, details: Dict) -> str:
        """Add a new task with description and deadline."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            deadline_ts = None
            
            if 'dueIn' in details:
                try:
                    deadline_ts = self.parse_time_string(details['dueIn'])
                except ValueError as e:
                    return json.dumps({"error": str(e)})
            elif 'deadline' in details:
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

    def get_upcoming_tasks(self, minutes_threshold: int = 15) -> List[Dict]:
        """Get tasks that are due within the specified number of minutes."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, description, deadline
                FROM tasks
                WHERE status = 'pending'
                AND deadline IS NOT NULL
                AND deadline BETWEEN datetime('now')
                    AND datetime('now', '+' || ? || ' minutes')
            """, (minutes_threshold,))
            
            return [
                {
                    "id": row[0],
                    "description": row[1],
                    "deadline": row[2]
                }
                for row in cursor.fetchall()
            ]

task_manager = TaskManager()

@register_tool
def manage_tasks(action: str, details: str) -> str:
    """
    Manage tasks/todos with various actions: add, list, or complete.
    
    Args:
        action: The action to perform ('add', 'list', or 'complete')
        details: JSON string containing action details:
                For 'add': {
                    "description": "task description",
                    "dueIn": "15 minutes" | "2 hours" | "1 day",  # relative time
                    "deadline": "YYYY-MM-DD HH:MM:SS"  # or absolute time
                }
                For 'list': {"filter": "today|pending|all"}
                For 'complete': Either a single task object or array of task objects
    
    Returns:
        Result of the operation as a formatted string
    """
    try:
        details_dict = json.loads(details) if isinstance(details, str) else details
        
        if action == "list":
            return task_manager.manage_tasks(action, {"filter": "today"})
        elif action == "add":
            return task_manager.manage_tasks(action, {
                "description": details_dict.get("description"),
                "dueIn": details_dict.get("dueIn"),
                "deadline": details_dict.get("deadline")
            })
        elif action == "complete":
            return task_manager.manage_tasks(action, details_dict)
        else:
            return json.dumps({"error": f"Invalid action: {action}"})
            
    except Exception as e:
        return json.dumps({"error": f"Error managing tasks: {str(e)}"}) 