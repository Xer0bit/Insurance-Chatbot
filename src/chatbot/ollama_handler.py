import requests
import os
import logging
import json
import time
from typing import Optional
from .knowledge_handler import KnowledgeHandler
from .langchain_handler import LangChainHandler
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class OllamaHandler:
    def __init__(self):
        # Default to local Ollama instance
        self.api_url = os.getenv("OLLAMA_API_URL", "http://localhost:11434/api/chat")
        self.model = "vicuna:7b"  # Specify the model you're using
        self.knowledge_handler = KnowledgeHandler()
        self.system_prompt = """I am Bito, a professional assistant from BITLogix. My primary goals are:
        1. Introduce myself to new users
        2. Collect customer information (name, email, service interest)
        3. Provide accurate information about BITLogix products and services
        4. Stay focused on company-related topics
        5. Help schedule consultations

        Keep responses concise and professional. Always ask for contact details if the user shows interest in our services."""
        self.response_guidelines = {
            "max_length": 150,  # Target length for responses
            "style": "conversational",
            "format": "direct"
        }
        self.requests_per_hour = 100  # Adjust this based on your needs
        self.request_timestamps = []
        self.window_size = 3600  # 1 hour in seconds
        self.conversation_state = {
            "initialized": False,
            "customer_data": {
                "name": None,
                "email": None,
                "service_interest": None
            }
        }
        self.conversation_history = []
        self.last_context = None
        kb_path = Path(__file__).parent.parent / "knowledge_base" / "company_data.json"
        self.langchain_handler = LangChainHandler(kb_path)
        logger.debug(f"Initialized OllamaHandler with API URL: {self.api_url} and rate limit: {self.requests_per_hour} requests per hour")

    def _check_rate_limit(self) -> bool:
        """Check if we're within rate limits"""
        current_time = time.time()
        # Remove timestamps older than our window
        self.request_timestamps = [ts for ts in self.request_timestamps 
                                 if current_time - ts < self.window_size]
        
        return len(self.request_timestamps) < self.requests_per_hour

    def _update_rate_limit(self):
        """Update the request timestamps"""
        self.request_timestamps.append(time.time())

    def send_query_to_ollama(self, query: str, context: str) -> Optional[str]:
        """
        Sends a query to the Ollama API and returns the response.
        """
        if not self._check_rate_limit():
            wait_time = self.window_size - (time.time() - self.request_timestamps[0])
            logger.warning(f"Rate limit exceeded. Please wait {int(wait_time/60)} minutes.")
            return "I'm currently handling too many requests. Please try again in a few minutes."

        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "system", "content": f"Context: {context}"} if context else {"role": "system", "content": "No specific context available."},
            {"role": "user", "content": query}
        ]
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True  # Enable streaming
        }

        logger.debug(f"Sending request to Ollama API with payload: {payload}")

        try:
            with requests.post(self.api_url, json=payload, stream=True) as response:
                logger.debug(f"Response status code: {response.status_code}")
                
                if response.status_code == 200:
                    self._update_rate_limit()  # Only count successful requests
                    full_response = ""
                    for line in response.iter_lines():
                        if line:
                            try:
                                json_response = json.loads(line)
                                if 'message' in json_response:
                                    content = json_response['message'].get('content', '')
                                    if content:
                                        full_response += content
                                        logger.debug(f"Received content: {content}")
                            except json.JSONDecodeError as e:
                                logger.error(f"JSON decode error: {str(e)}")
                                continue
                    
                    return full_response or "No response content"
                elif response.status_code == 429:  # Too Many Requests
                    logger.warning("Rate limit exceeded on API side")
                    return "The service is currently busy. Please try again in a few minutes."
                else:
                    logger.error(f"API request failed with status code: {response.status_code}")
                    return f"Error: API request failed with status code {response.status_code}"

        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error: {str(e)}")
            return "Error: Could not connect to Ollama API. Make sure Ollama is running locally."
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return f"Error: {str(e)}"

    async def get_response(self, user_input: str) -> str:
        """Process user input with LangChain integration"""
        logger.debug(f"Processing user input: {user_input}")

        # Handle initial greeting
        if user_input == "START_CHAT" and not self.conversation_state["initialized"]:
            self.conversation_state["initialized"] = True
            return self.knowledge_handler.get_greeting()

        # Get response using LangChain
        response = await self.langchain_handler.get_response(user_input)

        # Check for business intent and enhance response if needed
        if self._detect_business_intent(user_input):
            response = self._enhance_business_response(response, user_input)

        return response

    def _enhance_business_response(self, initial_response: str, user_input: str) -> str:
        # Add business-specific information to the response
        if not any(greeting in initial_response.lower() for greeting in ["hi there", "hello", "greetings"]):
            response_parts = [initial_response]
            
            # Add call-to-action if not present
            if "contact" not in initial_response.lower():
                response_parts.append("\nWould you like to discuss your project requirements? "
                                   "I can help schedule a consultation with our team.")
            
            return " ".join(response_parts)
        
        return initial_response

    def _detect_business_intent(self, user_input: str) -> bool:
        business_keywords = [
            'app', 'development', 'website', 'software', 'service',
            'price', 'cost', 'quote', 'project', 'build'
        ]
        return any(keyword in user_input.lower() for keyword in business_keywords)

    def _handle_business_inquiry(self, user_input: str, initial_response: str) -> str:
        # Extract relevant information from knowledge base
        services = self.knowledge_handler.knowledge_base.get("services", {})
        products = self.knowledge_handler.knowledge_base.get("products", [])
        
        response_parts = []
        
        # Add initial response if it's not a generic greeting
        if not any(greeting in initial_response.lower() for greeting in ["hi there", "hello", "greetings"]):
            response_parts.append(initial_response)
        
        # Add relevant service/product information
        if any(keyword in user_input.lower() for keyword in ['app', 'mobile']):
            response_parts.append("We specialize in mobile app development using React Native and Flutter. "
                                "Would you like to discuss your specific requirements? "
                                "I can help schedule a consultation with our development team.")
        
        elif any(keyword in user_input.lower() for keyword in ['website', 'web']):
            response_parts.append("Our web development team creates responsive, modern websites "
                                "using the latest technologies. Could you tell me more about your project needs?")
        
        # Add call-to-action
        response_parts.append("To better assist you, could you share:\n"
                            "1. Your project timeline\n"
                            "2. Specific features you need\n"
                            "3. Your contact information for a detailed discussion")

        return " ".join(response_parts)

    def _should_collect_data(self, user_input: str) -> bool:
        """Check if we should collect customer data"""
        interest_keywords = ["interested", "want", "looking for", "need", "help", "contact"]
        return any(keyword in user_input.lower() for keyword in interest_keywords)

    def _get_data_collection_response(self) -> str:
        """Get appropriate data collection response"""
        if not self.conversation_state["customer_data"]["email"]:
            return "Great! I'd be happy to help. Could you please share your email address so we can follow up with you?"
        elif not self.conversation_state["customer_data"]["service_interest"]:
            return "Which of our services are you most interested in?"
        return "Thank you for your interest. Our team will contact you soon at your provided email address."

    def _format_response(self, response: str) -> str:
        """Format the response according to guidelines"""
        # Truncate long responses while preserving complete sentences
        if len(response) > self.response_guidelines["max_length"]:
            sentences = response.split('. ')
            shortened = []
            total_length = 0
            for sentence in sentences:
                if total_length + len(sentence) <= self.response_guidelines["max_length"]:
                    shortened.append(sentence)
                    total_length += len(sentence) + 2  # +2 for ". "
                else:
                    break
            response = '. '.join(shortened) + ('.' if not shortened[-1].endswith('.') else '')
        
        logger.debug(f"Got response: {response}")
        return response