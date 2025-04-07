from quart import Quart, request, jsonify, render_template, session
from chatbot.ollama_handler import OllamaHandler
from database.db_handler import DatabaseHandler
from config.settings import DATABASE_URI, Config
from admin.routes import admin
import logging
import os

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

app = Quart(__name__)
app.config.from_object(Config)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key')
app.register_blueprint(admin)

ollama_handler = OllamaHandler()
db_handler = DatabaseHandler()

@app.route('/')
async def home():
    return await render_template('chat.html')

@app.route('/chat', methods=['POST'])
async def chat():
    try:
        data = await request.get_json()
        user_input = data.get('message', '').strip()
        
        # Handle initial connection
        if user_input == "START_CHAT":
            return jsonify({
                'response': "Hello! I'm Bito from Bitlogicx. How can I assist you with your software development needs today?"
            })
        
        if not user_input:
            return jsonify({'error': 'No message provided'}), 400

        response = await ollama_handler.get_response(user_input)
        
        # Check if lead was collected
        if 'Thank you for providing your information!' in response:
            # Trigger email notification to sales team
            await notify_sales_team(ollama_handler.knowledge_handler.lead_collection_state)
            
        return jsonify({'response': response})
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'response': 'I apologize, but I encountered an error. Please try again.'
        }), 500

async def notify_sales_team(lead_info):
    """Notify sales team about new lead"""
    # Implement notification logic here
    logger.info(f"New lead collected: {lead_info}")

@app.route('/info', methods=['GET'])
async def info():
    company_info = db_handler.get_company_info()
    return await jsonify(company_info)

@app.route('/submit-contact', methods=['POST'])
async def submit_contact():
    try:
        contact_data = await request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'email', 'phone']
        if not all(field in contact_data for field in required_fields):
            return jsonify({
                'status': 'error',
                'message': 'Missing required fields'
            }), 400
        
        # Add message field if not present
        if 'message' not in contact_data:
            contact_data['message'] = ''
            
        # Save to database using the database handler
        success, message = await db_handler.save_contact_form(contact_data)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': 'Thank you! Your contact information has been saved.'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': f'Failed to save contact information: {message}'
            }), 500
            
    except Exception as e:
        logger.error(f"Error in submit_contact: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'An unexpected error occurred'
        }), 500

@app.route('/reset-chat', methods=['POST'])
async def reset_chat():
    try:
        response = await ollama_handler.reset_conversation()
        return jsonify({'response': response})
    except Exception as e:
        logger.error(f"Error resetting chat: {e}")
        return jsonify({
            'error': 'Failed to reset chat',
            'response': 'Sorry, there was an error resetting the chat. Please try again.'
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)