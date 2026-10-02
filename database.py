import sqlite3
from datetime import datetime

DB_NAME = "fitness_bot.db"

def init_db():
    """Создает базу данных с четкими колонками под фитнес-метрики"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS workouts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            date TEXT,
            exercise TEXT,
            approach TEXT,
            weight TEXT,
            reps TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

def add_workout(user_id: int, exercise: str, approach: str, weight: str, reps: str):
    """Сохраняет тренировку, разбивая её по параметрам"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    # Записываем все 5 значений в нужные колонки
    cursor.execute(
        "INSERT INTO workouts (user_id, date, exercise, approach, weight, reps) VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, current_date, exercise, approach, weight, reps)
    )
    
    conn.commit()
    conn.close()

def get_user_workouts(user_id: int):
    """Вытаскивает упорядоченную историю тренировок"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Запрашиваем из базы сразу все нужные параметры
    cursor.execute(
        "SELECT date, exercise, approach, weight, reps FROM workouts WHERE user_id = ? ORDER BY id DESC",
        (user_id,)
    )
    rows = cursor.fetchall()
    
    conn.close()
    return rows
