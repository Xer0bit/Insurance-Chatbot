import sqlite3
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class DatabaseHandler:
    def __init__(self):
        self.db_path = Path(__file__).parent / "chatbot.db"
        self._create_tables()

    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()

    def _create_tables(self):
        """Create necessary tables if they don't exist"""
        queries = [
            """CREATE TABLE IF NOT EXISTS conversations (
                session_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                start_time TIMESTAMP NOT NULL
            )""",
            """CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                sender TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                FOREIGN KEY (session_id) REFERENCES conversations(session_id)
            )""",
            """CREATE TABLE IF NOT EXISTS contact_forms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                phone TEXT NOT NULL,
                message TEXT,
                submission_date TIMESTAMP NOT NULL,
                status TEXT DEFAULT 'new'
            )"""
        ]
        
        with self.get_connection() as conn:
            for query in queries:
                conn.execute(query)

    def execute(self, query: str, params: tuple = ()) -> None:
        """Execute a query with no return value"""
        try:
            with self.get_connection() as conn:
                conn.execute(query, params)
                logger.debug(f"Successfully executed query: {query}")
        except Exception as e:
            logger.error(f"Error executing query {query}: {e}")
            raise

    def fetch_all(self, query: str, params: tuple = ()) -> List[Dict]:
        """Execute a query and return all results"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error fetching data: {e}")
            return []

    def fetch_one(self, query: str, params: tuple = ()) -> Optional[Dict]:
        """Execute a query and return one result"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(query, params)
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Error fetching data: {e}")
            return None

    def save_contact_form(self, data: Dict[str, Any]) -> bool:
        """Save contact form data"""
        try:
            query = """
                INSERT INTO contact_forms (name, email, phone, message, submission_date, status)
                VALUES (?, ?, ?, ?, datetime('now'), 'new')
            """
            params = (data['name'], data['email'], data['phone'], data['message'])
            
            with self.get_connection() as conn:
                conn.execute(query, params)
                logger.info(f"Successfully saved contact form for {data['email']}")
                return True
        except Exception as e:
            logger.error(f"Error saving contact form: {e}")
            return False
