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
    
    def handle_requirements(self, session_id: str, user_message: str) -> str:
        """Handle requirements gathering and provide appropriate response"""
        # Store requirement
        self.add_requirement(session_id, user_message)
        
        # Generate response
        response = "Thank you for sharing your requirements. We're noting everything down. "
        response += "Please feel free to share any additional details or requirements.\n\n"
        
        if self._should_suggest_meeting(session_id):
            response += "Would you like to schedule a meeting with one of our representatives "
            response += "to discuss your requirements in more detail?"
        
        return response
    
    def add_requirement(self, session_id: str, requirement: str):
        """Store user requirements"""
        self.db.execute("""
            INSERT INTO requirements (session_id, requirement, timestamp)
            VALUES (?, ?, ?)
        """, (session_id, requirement, datetime.now()))
    
    def _should_suggest_meeting(self, session_id: str) -> bool:
        """Check if we should suggest a meeting based on conversation context"""
        message_count = self.db.fetch_one("""
            SELECT COUNT(*) FROM messages WHERE session_id = ?
        """, (session_id,))[0]
        
        requirements_count = self.db.fetch_one("""
            SELECT COUNT(*) FROM requirements WHERE session_id = ?
        """, (session_id,))[0]
        
        # Suggest meeting after certain interaction threshold
        return message_count >= 3 and requirements_count >= 2
