import requests
import os
import logging
from typing import Optional

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class OllamaHandler:
    def __init__(self):
        # Default to local Ollama instance
        self.api_url = os.getenv("OLLAMA_API_URL", "http://localhost:11434/api/chat")
        self.model = "vicuna:7b"  # Specify the model you're using
        logger.debug(f"Initialized OllamaHandler with API URL: {self.api_url}")

    def send_query_to_ollama(self, query: str) -> Optional[str]:
        """
        Sends a query to the Ollama API and returns the response.
        """
        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": query}
            ]
        }

        logger.debug(f"Sending request to Ollama API with payload: {payload}")

        try:
            response = requests.post(self.api_url, json=payload)
            logger.debug(f"Response status code: {response.status_code}")
            logger.debug(f"Response content: {response.text}")

            if response.status_code == 200:
                return response.json().get("message", {}).get("content", "No response content")
            else:
                logger.error(f"API request failed with status code: {response.status_code}")
                return f"Error: API request failed with status code {response.status_code}"

        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error: {str(e)}")
            return "Error: Could not connect to Ollama API. Make sure Ollama is running locally."
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return f"Error: {str(e)}"

    def get_response(self, user_input: str) -> str:
        """
        Processes user input and interacts with the Ollama API.
        """
        logger.debug(f"Processing user input: {user_input}")
        response = self.send_query_to_ollama(user_input)
        logger.debug(f"Got response: {response}")
        return response