from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from .models import Base, CompanyInfo, ContactForm, ChatMessage, ChatSession
from config.settings import DATABASE_URI
from datetime import datetime
import logging
import aiosqlite
from sqlalchemy import select

logger = logging.getLogger(__name__)

class DatabaseHandler:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseHandler, cls).__new__(cls)
        return cls._instance

    async def initialize(self):
        if not self._initialized:
            try:
                self.engine = create_async_engine(
                    DATABASE_URI.replace('sqlite:///', 'sqlite+aiosqlite:///'),
                    echo=True,
                    pool_pre_ping=True,
                    pool_recycle=3600
                )
                self.async_session = async_sessionmaker(
                    self.engine,
                    class_=AsyncSession,
                    expire_on_commit=False
                )
                async with self.engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)
                self._initialized = True
                logger.info("Database initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize database: {e}")
                raise

    async def save_contact_form(self, contact_data):
        """Save contact form data using SQLAlchemy models"""
        try:
            logger.debug(f"Attempting to save contact form: {contact_data}")
            
            async with self.async_session() as session:
                # Create new contact form instance
                contact_form = ContactForm(
                    name=contact_data['name'],
                    email=contact_data['email'],
                    phone=contact_data['phone'],
                    message=contact_data.get('message', ''),
                    session_id=contact_data.get('session_id'),
                    submission_date=datetime.utcnow(),
                    status='new'
                )
                
                session.add(contact_form)
                try:
                    await session.commit()
                    logger.info(f"Successfully saved contact form for {contact_data['email']}")
                    return True, "Contact form saved successfully"
                except Exception as e:
                    await session.rollback()
                    logger.error(f"Database error while committing: {str(e)}")
                    return False, f"Failed to save contact form: {str(e)}"
                
        except Exception as e:
            logger.error(f"Error in save_contact_form: {str(e)}")
            return False, f"Error processing contact form: {str(e)}"

    async def get_contact_forms(self, status=None):
        """Get all contact forms with optional status filter"""
        async with self.async_session() as session:
            try:
                query = select(ContactForm)
                if status:
                    query = query.filter(ContactForm.status == status)
                query = query.order_by(ContactForm.submission_date.desc())
                
                result = await session.execute(query)
                return result.scalars().all()
            except Exception as e:
                logger.error(f"Error fetching contact forms: {e}")
                return []

    async def update_lead_status(self, lead_id: int, status: str):
        """Update lead status"""
        async with self.async_session() as session:
            try:
                lead = await session.get(ContactForm, lead_id)
                if lead:
                    lead.status = status
                    await session.commit()
                    return True
            except Exception as e:
                logger.error(f"Error updating lead status: {e}")
                return False

    async def save_chat_message(self, session_id: str, sender: str, content: str):
        """Save chat message to database"""
        async with self.async_session() as session:
            try:
                chat_message = ChatMessage(
                    session_id=session_id,
                    sender=sender,
                    content=content,
                    timestamp=datetime.utcnow()
                )
                session.add(chat_message)
                await session.commit()
                logger.info(f"Chat message saved for session {session_id}")
                return True
            except Exception as e:
                await session.rollback()
                logger.error(f"Error saving chat message: {e}")
                return False

    async def create_chat_session(self, user_id: str):
        """Create new chat session"""
        async with self.async_session() as session:
            try:
                chat_session = ChatSession(
                    user_id=user_id,
                    start_time=datetime.utcnow()
                )
                session.add(chat_session)
                await session.commit()
                return str(chat_session.session_id)
            except Exception as e:
                await session.rollback()
                logger.error(f"Error creating chat session: {e}")
                return None

    async def verify_contact_form(self, email: str):
        """Verify if contact form exists"""
        async with self.async_session() as session:
            try:
                query = select(ContactForm).where(ContactForm.email == email)
                result = await session.execute(query)
                contact = result.scalar_one_or_none()
                return contact is not None
            except Exception as e:
                logger.error(f"Error verifying contact form: {e}")
                return False

    async def verify_chat_message(self, session_id: str):
        """Verify if chat messages exist"""
        async with self.async_session() as session:
            try:
                query = select(ChatMessage).where(ChatMessage.session_id == session_id)
                result = await session.execute(query)
                messages = result.scalars().all()
                return len(messages) > 0
            except Exception as e:
                logger.error(f"Error verifying chat messages: {e}")
                return False

def connect_to_db():
    import sqlite3
    from sqlite3 import Error

    conn = None
    try:
        conn = sqlite3.connect('database.db')
        print("Connection to SQLite DB successful")
    except Error as e:
        print(f"The error '{e}' occurred")

    return conn


def create_table(conn):
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        insurance_type TEXT,
        meeting_time TEXT
    );
    """
    try:
        cursor = conn.cursor()
        cursor.execute(create_table_sql)
        print("Table created successfully")
    except Error as e:
        print(f"The error '{e}' occurred")


def insert_user(conn, user):
    sql = """
    INSERT INTO users (name, email, insurance_type, meeting_time)
    VALUES (?, ?, ?, ?);
    """
    try:
        cursor = conn.cursor()
        cursor.execute(sql, user)
        conn.commit()
        print("User inserted successfully")
    except Error as e:
        print(f"The error '{e}' occurred")


def query_users(conn):
    sql = "SELECT * FROM users;"
    cursor = conn.cursor()
    cursor.execute(sql)
    return cursor.fetchall()