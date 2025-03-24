from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base, CompanyInfo, ContactForm
from config.settings import DATABASE_URI
from datetime import datetime

class DatabaseHandler:
    def __init__(self):
        self.engine = create_engine(DATABASE_URI)
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def get_company_info(self):
        company = self.session.query(CompanyInfo).first()
        if company:
            return {
                'name': company.name,
                'description': company.description,
                'contact_info': company.contact_info
            }
        return {'error': 'Company information not found'}

    def save_contact_form(self, contact_data):
        try:
            contact_form = ContactForm(
                name=contact_data['name'],
                email=contact_data['email'],
                phone=contact_data['phone'],
                message=contact_data['message'],
                submission_date=datetime.utcnow()
            )
            self.session.add(contact_form)
            self.session.commit()
            return True, "Contact information saved successfully"
        except Exception as e:
            self.session.rollback()
            return False, str(e)

    def get_contact_forms(self, status='new'):
        return self.session.query(ContactForm).filter_by(status=status).all()

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