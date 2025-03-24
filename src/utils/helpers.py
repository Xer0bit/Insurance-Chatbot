def format_response(response):
    # Format the chatbot's response for better readability
    return response.strip()

def validate_user_input(user_input):
    # Validate the user's input to ensure it meets the required criteria
    if not user_input:
        raise ValueError("Input cannot be empty.")
    return True

def extract_information(user_input):
    # Extract relevant information from the user's input
    # This is a placeholder for more complex extraction logic
    return user_input.split()  # Simple split for demonstration purposes

def log_conversation(user_input, bot_response):
    # Log the conversation for future reference
    with open("conversation_log.txt", "a") as log_file:
        log_file.write(f"User: {user_input}\nBot: {bot_response}\n")