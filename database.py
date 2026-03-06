import sqlite3

def create_table():
    conn = sqlite3.connect("interview.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS interviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        mode TEXT,
        question TEXT,
        answer TEXT,
        score INTEGER
    )
    """)

    conn.commit()
    conn.close()

def save_interview(username, mode, question, answer, score):
    conn = sqlite3.connect("interview.db")
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO interviews (username, mode, question, answer, score)
    VALUES (?, ?, ?, ?, ?)
    """, (username, mode, question, answer, score))

    conn.commit()
    conn.close()