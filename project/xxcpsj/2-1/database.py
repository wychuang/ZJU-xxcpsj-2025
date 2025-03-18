import sqlite3

CONVERSATIONS_DATABASE = 'conversations.db'

def init_db():
    with sqlite3.connect(CONVERSATIONS_DATABASE) as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS conversations
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                      message TEXT NOT NULL)''')
        conn.commit()