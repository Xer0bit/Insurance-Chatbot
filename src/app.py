from quart import Quart, request, jsonify, render_template
from chatbot.ollama_handler import OllamaHandler
from database.db_handler import DatabaseHandler
from config.settings import DATABASE_URI, Config

app = Quart(__name__)
app.config.from_object(Config)

ollama_handler = OllamaHandler()
db_handler = DatabaseHandler()

@app.route('/')
async def home():
    return await render_template('chat.html')

@app.route('/chat', methods=['POST'])
async def chat():
    data = await request.get_json()
    user_input = data.get('message')
    if not user_input:
        return jsonify({'error': 'No message provided'}), 400

    response = await ollama_handler.get_response(user_input)
    return jsonify({'response': response})

@app.route('/info', methods=['GET'])
async def info():
    company_info = db_handler.get_company_info()
    return await jsonify(company_info)

@app.route('/submit-contact', methods=['POST'])
async def submit_contact():
    contact_data = await request.get_json()
    try:
        success, message = db_handler.save_contact_form(contact_data)
        if success:
            return await jsonify({
                'status': 'success',
                'message': 'Thank you! Your contact information has been saved.'
            })
        else:
            raise Exception(message)
    except Exception as e:
        return await jsonify({
            'status': 'error',
            'message': f"Failed to save contact information: {str(e)}"
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)