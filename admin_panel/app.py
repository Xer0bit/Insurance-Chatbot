from flask import Flask, render_template, request, redirect, url_for, session, send_file
import sqlite3
import os
from functools import wraps
from openpyxl import Workbook
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this to a secure secret key

# Update database path to use the existing database
DATABASE_PATH = '../database.db'

# Ensure database and tables exist
def init_db():
    if not os.path.exists(DATABASE_PATH):
        from init_db import init_db as create_db
        create_db()

# Initialize database on startup
init_db()

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def get_db_connection():
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == 'admin' and password == 'admin123':  # Change these credentials
            session['admin_logged_in'] = True
            return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/dashboard')
@admin_required
def dashboard():
    try:
        conn = get_db_connection()
        if not conn:
            return "Database error", 500
            
        cursor = conn.cursor()
        
        # Get total counts
        cursor.execute('SELECT COUNT(*) FROM chat_messages')
        total_messages = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(DISTINCT session_id) FROM chat_messages')
        total_sessions = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM contact_forms')
        total_contacts = cursor.fetchone()[0]
        
        # Get recent sessions
        cursor.execute('''
            SELECT 
                cm.session_id,
                cm.content as last_message,
                MAX(cm.timestamp) as last_time
            FROM chat_messages cm
            GROUP BY cm.session_id
            ORDER BY last_time DESC
            LIMIT 5
        ''')
        recent_sessions = cursor.fetchall()
        
        conn.close()
        return render_template('dashboard.html', 
                             total_messages=total_messages,
                             total_sessions=total_sessions,
                             total_contacts=total_contacts,
                             recent_sessions=recent_sessions)
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return "Database error", 500

@app.route('/chats')
@admin_required
def view_chats():
    try:
        conn = get_db_connection()
        if not conn:
            return "Database error", 500
            
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, session_id, sender, content, timestamp 
            FROM chat_messages 
            ORDER BY timestamp DESC
        ''')
        chats = cursor.fetchall()
        conn.close()
        return render_template('chats.html', chats=chats)
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return "Database error", 500

@app.route('/sessions')
@admin_required
def view_sessions():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT session_id, 
                   COUNT(*) as message_count, 
                   MIN(timestamp) as start_time,
                   MAX(timestamp) as end_time
            FROM chat_messages 
            GROUP BY session_id 
            ORDER BY start_time DESC
        ''')
        sessions = cursor.fetchall()
        conn.close()
        return render_template('sessions.html', sessions=sessions)
    except sqlite3.Error as e:
        return "Database error", 500

@app.route('/session/<session_id>')
@admin_required
def session_detail(session_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM chat_messages 
            WHERE session_id = ? 
            ORDER BY timestamp ASC
        ''', [session_id])
        messages = cursor.fetchall()
        conn.close()
        return render_template('session_detail.html', 
                             messages=messages, 
                             session_id=session_id)
    except sqlite3.Error as e:
        return "Database error", 500

@app.route('/contacts')
@admin_required
def view_contacts():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM contact_forms ORDER BY submission_date DESC')
        contacts = cursor.fetchall()
        conn.close()
        return render_template('contacts.html', contacts=contacts)
    except sqlite3.Error as e:
        return "Database error", 500

@app.route('/export')
@admin_required
def export_data():
    try:
        conn = get_db_connection()
        if not conn:
            return "Database error", 500
            
        # Create a new workbook
        wb = Workbook()
        
        # Create Chats sheet
        ws_chats = wb.active
        ws_chats.title = "Chat Messages"
        ws_chats.append(['Session ID', 'Sender', 'Message', 'Timestamp'])
        
        cursor = conn.cursor()
        cursor.execute('SELECT session_id, sender, content, timestamp FROM chat_messages ORDER BY timestamp')
        chat_rows = cursor.fetchall()
        for row in chat_rows:
            # Convert Row object to list
            ws_chats.append([row['session_id'], row['sender'], row['content'], row['timestamp']])
            
        # Create Contacts sheet
        ws_contacts = wb.create_sheet("Contact Forms")
        ws_contacts.append(['Name', 'Email', 'Phone', 'Message', 'Submission Date'])
        
        cursor.execute('SELECT name, email, phone, message, submission_date FROM contact_forms ORDER BY submission_date')
        contact_rows = cursor.fetchall()
        for row in contact_rows:
            # Convert Row object to list
            ws_contacts.append([row['name'], row['email'], row['phone'], row['message'], row['submission_date']])
            
        conn.close()
        
        # Save the file
        filename = f'bito_data_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        filepath = os.path.join(os.path.dirname(__file__), 'exports', filename)
        
        # Create exports directory if it doesn't exist
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        wb.save(filepath)
        return send_file(filepath, as_attachment=True)
        
    except Exception as e:
        print(f"Export error: {e}")
        return "Export failed", 500

if __name__ == '__main__':
    app.run(port=5001)  # Running on a different port than the main application
