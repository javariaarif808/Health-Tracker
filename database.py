import sqlite3, os
from datetime import date

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "healthtrack.db")


def get_connection() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def initialize_database() -> None:
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
                age INTEGER NOT NULL, weight_kg REAL NOT NULL, height_cm REAL NOT NULL,
                gender TEXT NOT NULL DEFAULT 'male', activity_level TEXT NOT NULL,
                health_goal TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT (date('now'))
            );
            CREATE TABLE IF NOT EXISTS meals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                food_name TEXT NOT NULL, calories REAL NOT NULL,
                protein_g REAL NOT NULL DEFAULT 0, carbs_g REAL NOT NULL DEFAULT 0,
                fats_g REAL NOT NULL DEFAULT 0, logged_at TEXT NOT NULL DEFAULT (date('now'))
            );
            CREATE TABLE IF NOT EXISTS water_intake (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                amount_ml REAL NOT NULL, logged_at TEXT NOT NULL DEFAULT (date('now'))
            );
        """)


def create_user(name, age, weight_kg, height_cm, gender, activity_level, health_goal) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO users (name,age,weight_kg,height_cm,gender,activity_level,health_goal) VALUES (?,?,?,?,?,?,?)",
            (name, age, weight_kg, height_cm, gender, activity_level, health_goal))
        return cur.lastrowid


def get_user_by_name(name: str):
    with get_connection() as conn:
        return conn.execute("SELECT * FROM users WHERE LOWER(name)=LOWER(?)", (name,)).fetchone()


def get_all_users() -> list:
    with get_connection() as conn:
        return conn.execute("SELECT id, name FROM users ORDER BY name").fetchall()


def update_user(user_id, weight_kg, height_cm, age, activity_level, health_goal) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE users SET weight_kg=?,height_cm=?,age=?,activity_level=?,health_goal=? WHERE id=?",
            (weight_kg, height_cm, age, activity_level, health_goal, user_id))


def log_meal(user_id, food_name, calories, protein_g, carbs_g, fats_g) -> None:
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO meals (user_id,food_name,calories,protein_g,carbs_g,fats_g) VALUES (?,?,?,?,?,?)",
            (user_id, food_name, calories, protein_g, carbs_g, fats_g))


def get_meals_for_user(user_id: int, for_date: str = None) -> list:
    with get_connection() as conn:
        if for_date:
            return conn.execute(
                "SELECT * FROM meals WHERE user_id=? AND logged_at=? ORDER BY id DESC",
                (user_id, for_date)).fetchall()
        return conn.execute(
            "SELECT * FROM meals WHERE user_id=? ORDER BY logged_at DESC, id DESC",
            (user_id,)).fetchall()


def get_daily_calorie_totals(user_id: int, days: int = 7) -> list:
    with get_connection() as conn:
        return conn.execute(
            "SELECT logged_at AS day, SUM(calories) AS total_calories FROM meals "
            "WHERE user_id=? AND logged_at >= date('now', ? || ' days') "
            "GROUP BY logged_at ORDER BY logged_at",
            (user_id, f"-{days-1}")).fetchall()


def get_macro_totals_today(user_id: int):
    with get_connection() as conn:
        return conn.execute(
            "SELECT SUM(calories) AS calories, SUM(protein_g) AS protein_g, "
            "SUM(carbs_g) AS carbs_g, SUM(fats_g) AS fats_g "
            "FROM meals WHERE user_id=? AND logged_at=?",
            (user_id, str(date.today()))).fetchone()


def delete_meal(meal_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM meals WHERE id=?", (meal_id,))


def log_water(user_id: int, amount_ml: float) -> None:
    with get_connection() as conn:
        conn.execute("INSERT INTO water_intake (user_id,amount_ml) VALUES (?,?)", (user_id, amount_ml))


def get_water_today(user_id: int) -> float:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT SUM(amount_ml) AS total FROM water_intake WHERE user_id=? AND logged_at=?",
            (user_id, str(date.today()))).fetchone()
        return row["total"] or 0.0


def get_all_data_for_export(user_id: int) -> dict:
    with get_connection() as conn:
        return {
            "meals": conn.execute("SELECT * FROM meals WHERE user_id=? ORDER BY logged_at", (user_id,)).fetchall(),
            "water": conn.execute("SELECT * FROM water_intake WHERE user_id=? ORDER BY logged_at", (user_id,)).fetchall(),
        }
