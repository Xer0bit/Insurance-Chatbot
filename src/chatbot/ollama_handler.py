import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import os
import logging
import json
import time
from typing import Optional
from pathlib import Path
from .knowledge_handler import KnowledgeHandler
from .langchain_handler import LangChainHandler

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class OllamaHandler:
    def __init__(self):
        # Create session with retry strategy
        self.session = requests.Session()
        retries = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[502, 503, 504],
            allowed_methods=["POST"]
        )
        self.session.mount('http://', HTTPAdapter(max_retries=retries))
        
        # Initialize other attributes
        self.api_url = os.getenv("OLLAMA_API_URL", "http://localhost:11434/api/chat")
        self.model = "vicuna:7b"  # Specify the model you're using
        kb_path = Path(__file__).parent.parent / "knowledge_base" / "company_data.json"
        self.langchain_handler = LangChainHandler(kb_path)
        self.knowledge_handler = KnowledgeHandler()
        self.system_prompt = """I am Bito, a professional assistant from Bitlogicx. My primary goals are:
        1. Introduce myself to new users
        2. Collect customer information (name, email, service interest)
        3. Provide accurate information about Bitlogicx products and services
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

    def send_query_to_ollama(self, query: str, context: str, timeout: tuple = (5, 30)) -> Optional[str]:
        """Sends a query to the Ollama API with improved error handling"""
        try:
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": self.system_prompt},
                    {"role": "system", "content": f"Context: {context}"} if context else {"role": "system", "content": "No specific context available."},
                    {"role": "user", "content": query}
                ],
                "stream": False  # Disable streaming for better error handling
            }

            response = self.session.post(
                self.api_url,
                json=payload,
                timeout=timeout
            )
            
            response.raise_for_status()
            return response.json().get('message', {}).get('content', '')
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {str(e)}")
            if isinstance(e, requests.exceptions.ConnectionError):
                return "Error: Could not connect to Ollama API. Please ensure the service is running."
            elif isinstance(e, requests.exceptions.Timeout):
                return "Error: The request timed out. Please try again."
            return "Error: Failed to process your request. Please try again."
            
        except Exception as e:
            logger.error(f"Unexpected error in send_query_to_ollama: {str(e)}")
            return None

    async def reset_conversation(self):
        """Reset both Ollama and LangChain conversation states"""
        try:
            # Reset LangChain conversation
            response = await self.langchain_handler.reset_conversation()
            
            # Reset local state
            self.conversation_history = []
            self.last_context = None
            
            logger.debug("Chat session reset successfully")
            return response
            
        except Exception as e:
            logger.error(f"Error resetting conversation: {e}")
            return "I've reset our conversation. How can I help you today?"

    async def get_response(self, user_input: str) -> str:
        try:
            # Add timeout for API calls
            timeout = (5, 30)  # (connect timeout, read timeout)
            
            # First try LangChain handler
            try:
                return await self.langchain_handler.get_response(user_input)
            except Exception as e:
                logger.warning(f"LangChain handler failed: {e}, falling back to direct Ollama API")
                
                # Fallback to direct Ollama API
                response = self.send_query_to_ollama(user_input, "", timeout=timeout)
                if response:
                    return response
                
                raise Exception("Both handlers failed to generate response")
                
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            logger.error(f"Connection error with Ollama API: {e}")
            return "I apologize, but I'm having trouble connecting to my language model. Please try again in a moment."
            
        except Exception as e:
            logger.error(f"Unexpected error in get_response: {e}")
            return "I apologize, but I encountered an error. Please try again or rephrase your question."

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