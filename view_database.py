import sqlite3
from pathlib import Path

def view_database_contents():
    try:
        # Find the database file
        db_path = Path(__file__).parent / "database.db"
        if not db_path.exists():
            db_path = Path(__file__).parent / "src" / "database.db"
        
        if not db_path.exists():
            print("Database file not found!")
            return

        print(f"Database located at: {db_path}")
        
        # Connect to database
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # View contact forms
        print("\n=== Contact Forms ===")
        cursor.execute("SELECT * FROM contact_forms")
        contacts = cursor.fetchall()
        for contact in contacts:
            print(f"\nID: {contact[0]}")
            print(f"Name: {contact[1]}")
            print(f"Email: {contact[2]}")
            print(f"Phone: {contact[3]}")
            print(f"Message: {contact[4]}")
            print(f"Date: {contact[5]}")
            print(f"Status: {contact[6]}")
            
        # View chat messages
        print("\n=== Chat Messages ===")
        cursor.execute("SELECT * FROM chat_messages")
        messages = cursor.fetchall()
        for msg in messages:
            print(f"\nSession: {msg[1]}")
            print(f"Sender: {msg[2]}")
            print(f"Content: {msg[3]}")
            print(f"Time: {msg[4]}")
            
        conn.close()
        
    except Exception as e:
        print(f"Error viewing database: {e}")

if __name__ == "__main__":
    view_database_contents()
