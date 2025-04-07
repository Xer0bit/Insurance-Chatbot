import sqlite3
import os

DATABASE_PATH = '../chatbot.db'

def init_db():
    # Create database directory if it doesn't exist
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Create chats table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS chats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        message TEXT NOT NULL,
        response TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')

    # Add some sample data
    cursor.execute('''INSERT OR IGNORE INTO chats (user_id, message, response)
                     VALUES 
                     ('user1', 'Hello', 'Hi there!'),
                     ('user2', 'How are you?', 'I am doing well!')''')

    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
