import sqlite3
import os

DB_FILE = os.path.join(os.path.dirname(__file__), "fitbit_data.sqlite")

def get_connection():
    return sqlite3.connect(DB_FILE)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Create the daily_activity table
    # We use 'date' as the primary key since we only want one record per day.
    # We also add an 'updated_at' column to track when the data was last fetched.
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_activity (
            date TEXT PRIMARY KEY,
            steps INTEGER,
            distance REAL,
            calories_out INTEGER,
            very_active_minutes INTEGER,
            fairly_active_minutes INTEGER,
            lightly_active_minutes INTEGER,
            sedentary_minutes INTEGER,
            resting_heart_rate INTEGER,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Store user profile information
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_profile (
            id TEXT PRIMARY KEY,
            full_name TEXT,
            display_name TEXT,
            avatar_url TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print(f"Database initialized at {DB_FILE}")

def upsert_daily_activity(date, metrics):
    """
    Insert or update daily metrics for a specific date.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO daily_activity (
            date, steps, distance, calories_out, 
            very_active_minutes, fairly_active_minutes, 
            lightly_active_minutes, sedentary_minutes,
            resting_heart_rate, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(date) DO UPDATE SET
            steps=excluded.steps,
            distance=excluded.distance,
            calories_out=excluded.calories_out,
            very_active_minutes=excluded.very_active_minutes,
            fairly_active_minutes=excluded.fairly_active_minutes,
            lightly_active_minutes=excluded.lightly_active_minutes,
            sedentary_minutes=excluded.sedentary_minutes,
            resting_heart_rate=excluded.resting_heart_rate,
            updated_at=CURRENT_TIMESTAMP
    ''', (
        date,
        metrics.get('steps', 0),
        metrics.get('distance', 0.0),
        metrics.get('calories_out', 0),
        metrics.get('very_active_minutes', 0),
        metrics.get('fairly_active_minutes', 0),
        metrics.get('lightly_active_minutes', 0),
        metrics.get('sedentary_minutes', 0),
        metrics.get('resting_heart_rate', None)
    ))
    
    conn.commit()
    conn.close()

def upsert_user_profile(profile_data):
    """
    Insert or update user profile information.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO user_profile (
            id, full_name, display_name, avatar_url, updated_at
        )
        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(id) DO UPDATE SET
            full_name=excluded.full_name,
            display_name=excluded.display_name,
            avatar_url=excluded.avatar_url,
            updated_at=CURRENT_TIMESTAMP
    ''', (
        profile_data.get('encodedId', 'unknown'),
        profile_data.get('fullName', ''),
        profile_data.get('displayName', ''),
        profile_data.get('avatar', '')
    ))
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
