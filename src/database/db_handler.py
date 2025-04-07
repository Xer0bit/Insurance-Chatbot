from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from .models import Base, CompanyInfo, ContactForm
from config.settings import DATABASE_URI
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class DatabaseHandler:
    def __init__(self):
        # Convert SQLite URI to async
        self.engine = create_async_engine(
            DATABASE_URI.replace('sqlite:///', 'sqlite+aiosqlite:///')
        )
        self.async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def initialize(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def save_contact_form(self, contact_data):
        async with self.async_session() as session:
            try:
                contact_form = ContactForm(
                    name=contact_data['name'],
                    email=contact_data['email'],
                    phone=contact_data['phone'],
                    message=contact_data.get('message', ''),
                    submission_date=datetime.utcnow(),
                    status='new'
                )
                
                session.add(contact_form)
                await session.commit()
                
                logger.info(f"Contact form saved for {contact_data['email']}")
                return True, "Contact information saved successfully"
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Error saving contact form: {str(e)}")
                return False, str(e)

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