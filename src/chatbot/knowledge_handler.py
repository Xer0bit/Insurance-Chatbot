import json
from pathlib import Path
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class KnowledgeHandler:
    def __init__(self):
        self.knowledge_base = self._load_knowledge_base()
        self.templates = self.knowledge_base.get("response_templates", {})
        self.last_context = None
        self.context_count = {}

    def _load_knowledge_base(self):
        try:
            kb_path = Path(__file__).parent.parent / "knowledge_base" / "company_data.json"
            with open(kb_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading knowledge base: {e}")
            return {}

    def get_context(self, query: str) -> str:
        """Enhanced context matching focused on lead generation"""
        if self._shows_interest(query):
            return self._get_sales_context(query)
        return super().get_context(query)

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
        """Get initial greeting message"""
        return """Hello! I'm Bito, BITLogix's AI assistant. We specialize in custom software solutions for businesses.

How may I help you today? I can:
1. Discuss our software products and services
2. Share information about our development expertise
3. Help schedule a consultation with our team"""

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
        """Get sales-focused context"""
        context = []
        
        # Add relevant product/service info
        if 'app' in query.lower() or 'mobile' in query.lower():
            context.append("We specialize in mobile app development using React Native.")
        elif 'web' in query.lower() or 'website' in query.lower():
            context.append("Our web development team creates modern, responsive websites.")
            
        # Add call to action
        context.append("To provide you with accurate information and pricing, we'd love to learn more about your project requirements.")
        
        return " ".join(context)

    def validate_email(self, email: str) -> bool:
        """Basic email validation"""
        import re
        pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        return bool(re.match(pattern, email))
