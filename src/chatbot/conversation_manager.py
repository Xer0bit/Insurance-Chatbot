import uuid
from datetime import datetime
from typing import List, Dict
from database.db_handler import DatabaseHandler  # Changed from relative import
from .summarizer import ConversationSummarizer

class ConversationManager:
    def __init__(self):
        self.db = DatabaseHandler()
        self.summarizer = ConversationSummarizer()
        
    def create_session(self, user_id: str) -> str:
        """Create new conversation session"""
        session_id = str(uuid.uuid4())
        self.db.execute("""
            INSERT INTO conversations (session_id, user_id, start_time)
            VALUES (?, ?, ?)
        """, (session_id, user_id, datetime.now()))
        return session_id
        
    def add_message(self, session_id: str, sender: str, content: str):
        """Add message to conversation"""
        self.db.execute("""
            INSERT INTO messages (session_id, sender, content, timestamp)
            VALUES (?, ?, ?, ?)
        """, (session_id, sender, content, datetime.now()))
        
    def get_summary(self, session_id: str) -> str:
        """Get conversation summary"""
        messages = self.db.fetch_all("""
            SELECT sender, content, timestamp
            FROM messages
            WHERE session_id = ?
            ORDER BY timestamp
        """, (session_id,))
        
        return self.summarizer.summarize(messages)
        
    def get_user_conversations(self, user_id: str) -> List[Dict]:
        """Get all conversations for a user"""
        return self.db.fetch_all("""
            SELECT c.*, 
                   COUNT(m.id) as message_count,
                   MAX(m.timestamp) as last_activity
            FROM conversations c
            LEFT JOIN messages m ON c.session_id = m.session_id
            WHERE c.user_id = ?
            GROUP BY c.session_id
        """, (user_id,))
