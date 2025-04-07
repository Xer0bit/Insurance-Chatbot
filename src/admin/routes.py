from quart import Blueprint, render_template, request, session, redirect, url_for
from functools import wraps
from database.db_handler import DatabaseHandler
import bcrypt
import os

admin = Blueprint('admin', __name__)
db = DatabaseHandler()

def hash_password(password: str) -> bytes:
    """Hash password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt)

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except:
        return False

def admin_required(f):
    @wraps(f)
    async def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin.login'))
        return await f(*args, **kwargs)
    return decorated_function

@admin.route('/admin/login', methods=['GET', 'POST'])
async def login():
    if request.method == 'POST':
        form = await request.form
        username = form.get('username')
        password = form.get('password')
        
        admin_username = os.getenv('ADMIN_USERNAME')
        admin_password_hash = os.getenv('ADMIN_PASSWORD')
        
        if username == admin_username and verify_password(password, admin_password_hash):
            session['admin_logged_in'] = True
            return redirect(url_for('admin.dashboard'))
        return await render_template('admin/login.html', error='Invalid credentials')
    
    return await render_template('admin/login.html')

@admin.route('/admin/dashboard')
@admin_required
async def dashboard():
    leads = await db.get_contact_forms()
    return await render_template('admin/dashboard.html', leads=leads)

@admin.route('/admin/logout')
async def logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin.login'))
