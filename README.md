# README.md

# Insurance Chatbot

This project is an Insurance Chatbot designed to interact with customers, gather information, and provide assistance regarding insurance-related queries. The chatbot leverages the Ollama API for natural language processing and utilizes a local SQLite database to store and manage user data.

## Project Structure

```
insurance-chatbot
├── src
│   ├── app.py                # Main entry point of the chatbot application
│   ├── config
│   │   ├── __init__.py       # Marks the config directory as a package
│   │   └── settings.py       # Configuration settings for the application
│   ├── database
│   │   ├── __init__.py       # Marks the database directory as a package
│   │   ├── models.py         # Defines database models using an ORM
│   │   └── db_handler.py     # Functions for interacting with the database
│   ├── chatbot
│   │   ├── __init__.py       # Marks the chatbot directory as a package
│   │   ├── ollama_handler.py  # Handles interactions with the Ollama API
│   │   └── conversation.py    # Manages the conversation flow
│   ├── utils
│   │   ├── __init__.py       # Marks the utils directory as a package
│   │   └── helpers.py        # Utility functions for various tasks
│   └── knowledge_base
│       ├── __init__.py       # Marks the knowledge_base directory as a package
│       └── company_info.py    # Contains information about the company
├── requirements.txt           # Lists project dependencies
├── .env                       # Contains environment variables
└── README.md                  # Documentation for the project
```

## Setup Instructions

1. Clone the repository:
   ```
   git clone https://github.com/Xer0bit/Insurance-Chatbot/
   cd insurance-chatbot
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up your environment variables in the `.env` file.

4. Run the application:
   ```
   python src/app.py
   ```

## Usage Guidelines

- The chatbot can assist customers with various inquiries related to insurance.
- Users can interact with the chatbot through a web interface or messaging platform.
- Ensure that the knowledge base is updated with relevant company information for accurate responses.

## Contributing

Contributions are welcome! Please submit a pull request or open an issue for any enhancements or bug fixes.
