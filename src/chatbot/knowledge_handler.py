import json
from pathlib import Path
import logging
from typing import Dict, List, Optional
from datetime import datetime
from .conversation_manager import ConversationManager

logger = logging.getLogger(__name__)

class KnowledgeHandler:
    def __init__(self):
        self.knowledge_base = self._load_knowledge_base()
        self.templates = self.knowledge_base.get("response_templates", {})
        self.last_context = None
        self.context_count = {}
        self.lead_collection_state = {
            "collecting": False,
            "name": None,
            "email": None,
            "phone": None,
            "project_type": None
        }
        self.previous_context = None
        self.context_keywords = set()
        self.unclear_responses = ['?', 'what', 'huh', 'what?', 'huh?']
        self.conversation_manager = ConversationManager()
        self.current_session_id = None

    def _load_knowledge_base(self):
        try:
            kb_path = Path(__file__).parent.parent / "knowledge_base" / "company_data.json"
            with open(kb_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading knowledge base: {e}")
            return {}

    def start_new_session(self, user_id: str):
        """Start new conversation session"""
        self.current_session_id = self.conversation_manager.create_session(user_id)

    def get_context(self, query: str, user_id: str = None) -> str:
        """Enhanced context matching with conversation tracking"""
        if not self.current_session_id and user_id:
            self.start_new_session(user_id)
            
        # Track the conversation
        self.conversation_manager.add_message(
            self.current_session_id,
            "user",
            query
        )
        
        response = self._generate_response(query)
        
        # Track bot response
        self.conversation_manager.add_message(
            self.current_session_id,
            "bot",
            response
        )
        
        return response

    def _generate_response(self, query: str) -> str:
        """Generate response (moved from get_context)"""
        # Handle unclear queries
        if query.strip() in self.unclear_responses:
            if self.previous_context:
                return ("I notice you might be confused. Let me clarify: "
                       "I'm here to help you with software development needs. "
                       "Could you please provide more details about what you're looking for?")
            return ("I'm here to help you with software development services. "
                   "Could you please let me know what kind of solution you're looking for? "
                   "For example, a mobile app, website, or business software?")

        # Handle completely irrelevant queries
        if not self._is_relevant_to_previous_context(query):
            if any(word in query.lower() for word in ['food', 'burger', 'pizza', 'restaurant']):
                return ("I apologize, but I can only assist with software development related queries. "
                       "I cannot help with food orders or restaurant recommendations. "
                       "Would you like to discuss your software development needs instead?")
            return ("I apologize, but I can only assist with software development related topics. "
                   "Could you please ask a question about our software services?")

        # First check if we're collecting lead information
        if self.lead_collection_state["collecting"]:
            return self._handle_lead_collection(query)

        # Check if query is irrelevant to previous context
        if not self._is_relevant_to_previous_context(query):
            return ("I apologize, but that seems unrelated to our previous discussion. "
                   "Could you please clarify how it relates to what we were discussing? "
                   "Or would you like to start a new topic about our services?")

        # First check if it's an initial greeting
        greeting_words = ['hi', 'hello', 'hey', 'greetings']
        if any(word == query.lower().strip() for word in greeting_words):
            return self.get_greeting()
            
        # Check for service-related queries
        if any(service in query.lower() for service in ['development', 'integration', 'automation', 'consulting']):
            services = self.knowledge_base['services']
            return f"We specialize in {services['general']}. Our key services include {', '.join(services['specific'])}. Would you like to know more about any specific service?"
            
        # Handle AI/chatbot specific queries
        if any(term in query.lower() for term in ['ai', 'chatbot', 'bot']):
            return """We offer comprehensive AI and chatbot solutions including:
• Custom AI-powered chatbots
• Natural Language Processing integration
• Business workflow automation
• Multi-platform deployment

Would you like to discuss your specific requirements?"""
        
        # Check for development process queries
        if any(term in query.lower() for term in ['process', 'approach', 'methodology']):
            process = self.knowledge_base['custom_solutions']['development_process']
            return f"Our development process includes: {', '.join(process)}"
            
        # Then check for location and other queries
        if 'location' in query.lower() or 'where' in query.lower():
            return f"Bitlogicx is located at {self.knowledge_base['company']['location']}"
        
        if self._shows_interest(query):
            return self._get_sales_context(query)

        # Check for project interest keywords
        project_keywords = ['app', 'application', 'mobile', 'website', 'software', 'system']
        if any(keyword in query.lower() for keyword in project_keywords):
            self.lead_collection_state["collecting"] = True
            self.lead_collection_state["project_type"] = next((k for k in project_keywords if k in query.lower()), None)
            return """Great! We specialize in building custom mobile applications. To better understand your requirements and provide you with detailed information, could you please share:

1. Your name
2. Email address
3. Phone number
4. Brief description of your project

Please start by telling me your name."""

        context = self._get_general_context(query)
        self._update_context_keywords(context)
        return context

    def _get_general_context(self, query: str) -> str:
        """Get general context for basic queries"""
        if any(word in query.lower() for word in ['where', 'located', 'address', 'place']):
            return f"We are located at {self.knowledge_base['company']['location']}. Would you like to schedule a visit or discuss your requirements?"

    def _is_business_query(self, query: str) -> bool:
        business_keywords = ['cost', 'price', 'quote', 'service', 'develop', 'build', 'create']
        return any(keyword in query for keyword in business_keywords)

    def _is_technical_query(self, query: str) -> bool:
        tech_keywords = ['app', 'website', 'software', 'system', 'platform', 'integration']
        return any(keyword in query for keyword in tech_keywords)

    def _get_business_context(self, query: str) -> list:
        context = []
        if 'app' in query or 'mobile' in query:
            context.append("We offer comprehensive mobile app development services using React Native and Flutter.")
        elif 'website' in query or 'web' in query:
            context.append("Our web development team specializes in creating modern, responsive websites.")
        return context

    def _get_technical_context(self, query: str) -> list:
        # Add technical context based on query
        context = []
        technologies = self.knowledge_base.get("custom_solutions", {}).get("technologies", {})
        if technologies:
            relevant_tech = []
            if 'app' in query or 'mobile' in query:
                relevant_tech = technologies.get("frontend", [])
            elif 'backend' in query or 'server' in query:
                relevant_tech = technologies.get("backend", [])
            
            if relevant_tech:
                context.append(f"We work with various technologies including: {', '.join(relevant_tech)}")
        
        return context

    def _find_relevant_products(self, query: str) -> List[Dict]:
        """Find products relevant to the query"""
        products = self.knowledge_base.get("products", [])
        scored_products = []
        
        for product in products:
            score = self._calculate_relevance(query, product)
            if score > 0:
                scored_products.append((score, product))
        
        return [p[1] for p in sorted(scored_products, reverse=True)]

    def _calculate_relevance(self, query: str, product: Dict) -> float:
        """Calculate relevance score for a product"""
        score = 0
        if product["name"].lower() in query:
            score += 2
        if any(word in product["description"].lower() for word in query.split()):
            score += 1
        if product["use_case"].lower() in query:
            score += 1.5
        return score

    def _is_service_query(self, query: str) -> bool:
        """Determine if query is about services"""
        service_keywords = ["service", "consulting", "development", "solution"]
        return any(keyword in query for keyword in service_keywords)

    def _get_service_context(self) -> List[str]:
        """Get service-related context"""
        services = self.knowledge_base["services"]
        return [services["general"]] + services["specific"]

    def get_greeting(self) -> str:
        """Get initial greeting message with a professional tone"""
        return "Hello! I'm Bito, your AI assistant from Bitlogicx. How can I help you today?"

    def _get_lead_collection_state(self, query: str) -> dict:
        """Track lead collection progress"""
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        phone_pattern = r'[\d\+\-\(\) ]{10,}'
        
        return {
            'has_email': bool(re.search(email_pattern, query)),
            'has_phone': bool(re.search(phone_pattern, query)),
            'has_interest': self._shows_interest(query)
        }

    def _shows_interest(self, query: str) -> bool:
        """Detect if user shows interest in services"""
        interest_signals = [
            'interested', 'want', 'need', 'looking for', 'how much',
            'price', 'cost', 'develop', 'create', 'build'
        ]
        return any(signal in query.lower() for signal in interest_signals)

    def _get_sales_context(self, query: str) -> str:
        """Get sales-focused context prioritizing services"""
        context = []
        
        # Lead with services
        if any(service in query.lower() for service in ['software', 'development', 'solution']):
            context.append(self.knowledge_base['custom_solutions']['description'])
            context.append("Our process includes requirements analysis, design, development, testing, deployment, and ongoing support.")
        
        # Add specific service context
        if 'app' in query.lower() or 'mobile' in query.lower():
            context.append("We specialize in mobile app development using React Native.")
        elif 'web' in query.lower() or 'website' in query.lower():
            context.append("Our web development team creates modern, responsive websites.")
            
        # Add call to action
        context.append("To provide you with accurate information and pricing, we'd love to learn more about your project requirements.")
        
        return " ".join(context)

    def _handle_lead_collection(self, query: str) -> str:
        """Handle lead collection flow"""
        state = self.lead_collection_state
        
        if not state["name"]:
            state["name"] = query
            return f"Nice to meet you {query}! Could you please share your email address?"
            
        if not state["email"]:
            if self.validate_email(query):
                state["email"] = query
                return "Perfect! What's the best phone number to reach you at?"
            return "Please provide a valid email address so our team can contact you."
            
        if not state["phone"]:
            if self._validate_phone(query):
                state["phone"] = query
                # Save lead to database
                self._save_lead()
                return f"""Thank you for providing your information! Our team will contact you shortly to discuss your {state['project_type']} project.
                
In the meantime, would you like to know more about our development process or previous similar projects?"""
            return "Please provide a valid phone number."
            
        return self._get_sales_context(query)

    def _save_lead(self) -> None:
        """Save lead information to database"""
        from database.db_handler import DatabaseHandler
        db = DatabaseHandler()
        db.save_contact_form({
            "name": self.lead_collection_state["name"],
            "email": self.lead_collection_state["email"],
            "phone": self.lead_collection_state["phone"],
            "message": f"Interested in {self.lead_collection_state['project_type']} development"
        })
        
    def _validate_phone(self, phone: str) -> bool:
        """Validate phone number"""
        import re
        pattern = r'[\d\+\-\(\) ]{10,}'
        return bool(re.match(pattern, phone))

    def validate_email(self, email: str) -> bool:
        """Basic email validation"""
        import re
        pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        return bool(re.match(pattern, email))

    def _is_relevant_to_previous_context(self, query: str) -> bool:
        """Check if the current query is relevant to previous context"""
        if not self.previous_context or not self.context_keywords:
            return True
        
        query_words = set(query.lower().split())
        return bool(query_words & self.context_keywords)

    def _update_context_keywords(self, context: str):
        """Update context keywords for relevancy checking"""
        # Important keywords that indicate context
        important_words = ['development', 'integration', 'automation', 'consulting', 
                         'ai', 'chatbot', 'website', 'app', 'mobile', 'service']
        self.context_keywords = set(word for word in context.lower().split() 
                                  if word in important_words)
        self.previous_context = context

    def summarize_conversation(self, session_id: Optional[str] = None) -> str:
        """Get conversation summary"""
        sid = session_id or self.current_session_id
        return self.conversation_manager.get_summary(sid)
