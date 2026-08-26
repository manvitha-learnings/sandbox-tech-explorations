import sqlite3
import os
from datetime import datetime, timedelta

DB_NAME = os.path.join(os.path.dirname(__file__), "todo.db")

def get_connection():
    return sqlite3.connect(DB_NAME)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Create Tasks table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            date TEXT NOT NULL, -- YYYY-MM-DD
            completed INTEGER DEFAULT 0, -- 0 for False, 1 for True
            priority TEXT DEFAULT 'Medium' -- Low, Medium, High
        )
    """)
    
    # 2. Create Achievements table (for manual logs and auto logs)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS achievements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            date TEXT NOT NULL, -- YYYY-MM-DD
            completed_task_id INTEGER DEFAULT NULL -- Reference to tasks.id if auto-logged
        )
    """)
    
    # 3. Create Badges table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS badges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            badge_name TEXT UNIQUE NOT NULL,
            description TEXT NOT NULL,
            unlocked_at TEXT NOT NULL -- YYYY-MM-DD
        )
    """)
    
    # 4. Create Streaks table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS streaks (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            current_streak INTEGER DEFAULT 0,
            max_streak INTEGER DEFAULT 0,
            last_activity_date TEXT DEFAULT NULL -- YYYY-MM-DD
        )
    """)
    
    # Initialize streaks table if empty
    cursor.execute("SELECT COUNT(*) FROM streaks")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO streaks (id, current_streak, max_streak, last_activity_date) VALUES (1, 0, 0, NULL)")
        
    conn.commit()
    conn.close()

# --- Task Operations ---
def add_task(title, date, priority='Medium'):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO tasks (title, date, priority) VALUES (?, ?, ?)", (title, date, priority))
    conn.commit()
    conn.close()

def get_tasks_by_date(date):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, completed, priority FROM tasks WHERE date = ?", (date,))
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "title": r[1], "completed": bool(r[2]), "priority": r[3]} for r in rows]

def toggle_task_completed(task_id, completed):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE tasks SET completed = ? WHERE id = ?", (1 if completed else 0, task_id))
    
    # Handle achievements auto-sync
    if completed:
        # Retrieve task title & date to add to achievements
        cursor.execute("SELECT title, date FROM tasks WHERE id = ?", (task_id,))
        task_info = cursor.fetchone()
        if task_info:
            title, date = task_info
            # Check if already added to achievements to prevent duplicates
            cursor.execute("SELECT id FROM achievements WHERE completed_task_id = ?", (task_id,))
            if not cursor.fetchone():
                cursor.execute(
                    "INSERT INTO achievements (title, date, completed_task_id) VALUES (?, ?, ?)",
                    (f"Completed: {title}", date, task_id)
                )
    else:
        # If uncompleted, remove from achievements
        cursor.execute("DELETE FROM achievements WHERE completed_task_id = ?", (task_id,))
        
    conn.commit()
    conn.close()

def delete_task(task_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    cursor.execute("DELETE FROM achievements WHERE completed_task_id = ?", (task_id,))
    conn.commit()
    conn.close()

# --- Achievement Operations ---
def add_manual_achievement(title, date):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO achievements (title, date, completed_task_id) VALUES (?, ?, NULL)", (title, date))
    conn.commit()
    conn.close()

def get_achievements_by_date(date):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, completed_task_id FROM achievements WHERE date = ?", (date,))
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "title": r[1], "is_manual": r[2] is None} for r in rows]

def delete_achievement(achievement_id):
    conn = get_connection()
    cursor = conn.cursor()
    # Check if this was an auto-logged achievement. If so, we also uncheck the task.
    cursor.execute("SELECT completed_task_id FROM achievements WHERE id = ?", (achievement_id,))
    row = cursor.fetchone()
    if row and row[0] is not None:
        task_id = row[0]
        cursor.execute("UPDATE tasks SET completed = 0 WHERE id = ?", (task_id,))
    cursor.execute("DELETE FROM achievements WHERE id = ?", (achievement_id,))
    conn.commit()
    conn.close()

# --- Badge Operations ---
def get_unlocked_badges():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT badge_name, description, unlocked_at FROM badges ORDER BY unlocked_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [{"badge_name": r[0], "description": r[1], "unlocked_at": r[2]} for r in rows]

def unlock_badge(badge_name, description, date):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO badges (badge_name, description, unlocked_at) VALUES (?, ?, ?)",
            (badge_name, description, date)
        )
        conn.commit()
        unlocked = True
    except sqlite3.IntegrityError:
        unlocked = False # Badge already unlocked
    conn.close()
    return unlocked

# --- Streak Operations ---
def get_streak_info():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT current_streak, max_streak, last_activity_date FROM streaks WHERE id = 1")
    row = cursor.fetchone()
    conn.close()
    return {"current_streak": row[0], "max_streak": row[1], "last_activity_date": row[2]}

def update_streak_info(current_streak, max_streak, last_activity_date):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE streaks SET current_streak = ?, max_streak = ?, last_activity_date = ? WHERE id = 1",
        (current_streak, max_streak, last_activity_date)
    )
    conn.commit()
    conn.close()
