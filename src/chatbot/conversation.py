def start_conversation():
    print("Welcome to the Insurance Chatbot!")
    print("How can I assist you today?")

def handle_user_input(user_input):
    # Here you would implement logic to process user input
    # and generate appropriate responses based on the input.
    response = "I'm here to help you with your insurance needs."
    return response

def main():
    start_conversation()
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            print("Thank you for chatting with us. Goodbye!")
            break
        response = handle_user_input(user_input)
        print(f"Chatbot: {response}")

if __name__ == "__main__":
    main()