from flask import Flask, request, jsonify, render_template
from chatbot.ollama_handler import OllamaHandler
from database.db_handler import DatabaseHandler
from config.settings import DATABASE_URI, Config

app = Flask(__name__)
app.config.from_object(Config)

ollama_handler = OllamaHandler()
db_handler = DatabaseHandler()

@app.route('/')
def home():
    return render_template('chat.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get('message')
    if not user_input:
        return jsonify({'error': 'No message provided'}), 400

    response = ollama_handler.get_response(user_input)
    return jsonify({'response': response})

@app.route('/info', methods=['GET'])
def info():
    company_info = db_handler.get_company_info()
    return jsonify(company_info)

if __name__ == '__main__':
    app.run(debug=True)