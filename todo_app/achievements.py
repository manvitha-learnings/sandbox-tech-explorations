import sqlite3
from datetime import datetime, timedelta
import database

BADGE_DEFINITIONS = {
    "First Step": "Complete your first task.",
    "Consistent Planner": "Complete 5 tasks in total.",
    "Task Master": "Complete 20 tasks in total.",
    "Streak Starter": "Achieve a 3-day streak of completing tasks.",
    "Unstoppable": "Achieve a 7-day streak of completing tasks.",
    "Achievement Hunter": "Log 3 manual achievements."
}

def calculate_current_streak():
    """
    Calculates the streak dynamically by looking at completion dates in the tasks table.
    A streak is active if tasks are completed today or yesterday.
    """
    conn = database.get_connection()
    cursor = conn.cursor()
    
    # Select all distinct dates where at least one task was completed
    cursor.execute("SELECT DISTINCT date FROM tasks WHERE completed = 1")
    completed_dates_raw = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    if not completed_dates_raw:
        return 0
        
    # Convert string dates to datetime.date objects and sort them descending
    completed_dates = []
    for d_str in completed_dates_raw:
        try:
            completed_dates.append(datetime.strptime(d_str, "%Y-%m-%d").date())
        except ValueError:
            continue
            
    completed_dates = sorted(completed_dates, reverse=True)
    
    if not completed_dates:
        return 0
        
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    
    # If the last completion was before yesterday, streak is broken
    if completed_dates[0] < yesterday:
        return 0
        
    # Calculate streak count
    current_streak = 1
    # Check if the streak continues back in time
    expected_date = completed_dates[0] - timedelta(days=1)
    
    for d in completed_dates[1:]:
        if d == expected_date:
            current_streak += 1
            expected_date = d - timedelta(days=1)
        elif d < expected_date:
            # We skipped a day, so the streak ends here
            break
        # If d == expected_date + 1, it's a duplicate of the same day, ignore
        
    return current_streak

def update_streak_and_get_stats():
    """
    Calculates current streak, updates max streak in db if needed, and returns stats.
    """
    current_streak = calculate_current_streak()
    db_streak_info = database.get_streak_info()
    
    max_streak = db_streak_info["max_streak"]
    if current_streak > max_streak:
        max_streak = current_streak
        
    today_str = datetime.now().strftime("%Y-%m-%d")
    database.update_streak_info(current_streak, max_streak, today_str if current_streak > 0 else db_streak_info["last_activity_date"])
    
    return {
        "current_streak": current_streak,
        "max_streak": max_streak
    }

def check_and_unlock_badges(date_str=None):
    """
    Checks all badge criteria and unlocks any newly achieved badges.
    Returns a list of newly unlocked badge dictionaries.
    """
    if not date_str:
        date_str = datetime.now().strftime("%Y-%m-%d")
        
    conn = database.get_connection()
    cursor = conn.cursor()
    
    # 1. Get total completed tasks
    cursor.execute("SELECT COUNT(*) FROM tasks WHERE completed = 1")
    total_completed_tasks = cursor.fetchone()[0]
    
    # 2. Get total manual achievements
    cursor.execute("SELECT COUNT(*) FROM achievements WHERE completed_task_id IS NULL")
    total_manual_achievements = cursor.fetchone()[0]
    
    conn.close()
    
    # 3. Get streak info
    streak_stats = update_streak_and_get_stats()
    current_streak = streak_stats["current_streak"]
    
    newly_unlocked = []
    
    # Evaluate badge criteria
    checks = {
        "First Step": total_completed_tasks >= 1,
        "Consistent Planner": total_completed_tasks >= 5,
        "Task Master": total_completed_tasks >= 20,
        "Streak Starter": current_streak >= 3,
        "Unstoppable": current_streak >= 7,
        "Achievement Hunter": total_manual_achievements >= 3
    }
    
    for badge_name, condition_met in checks.items():
        if condition_met:
            desc = BADGE_DEFINITIONS[badge_name]
            unlocked = database.unlock_badge(badge_name, desc, date_str)
            if unlocked:
                newly_unlocked.append({
                    "badge_name": badge_name,
                    "description": desc,
                    "unlocked_at": date_str
                })
                
    return newly_unlocked
