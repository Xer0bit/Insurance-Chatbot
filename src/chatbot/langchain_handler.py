from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaEmbeddings
from langchain_ollama import OllamaLLM
from langchain.chains import LLMChain
from langchain_core.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
import json
import logging
import re  # Add this import

logger = logging.getLogger(__name__)

class LangChainHandler:
    def __init__(self, knowledge_base_path):
        self.llm = OllamaLLM(model="vicuna:7b")
        self.embeddings = OllamaEmbeddings(model="vicuna:7b")
        self.memory = ConversationBufferMemory(
            memory_key="history",
            input_key="input",
            return_messages=True
        )
        self.knowledge_base = self._load_knowledge_base(knowledge_base_path)
        self.vector_store = self._create_vector_store()
        self.conversation_chain = self._create_conversation_chain()
        # Add conversation state initialization
        self.conversation_state = {
            "collecting_contact": False,
            "name": None,
            "email": None,
            "phone": None,
            "interest": None,
            "last_response": None,
            "price_discussed": False,
            "greeting_shown": False  # Add this flag
        }

    async def reset_conversation(self):
        """Reset the conversation state and memory"""
        self.conversation_state = {
            "collecting_contact": False,
            "name": None,
            "email": None,
            "phone": None,
            "interest": None,
            "last_response": None,
            "price_discussed": False,
            "greeting_shown": False
        }
        self.memory.clear()
        return "Hello! I'm Bito, how can I assist you today?"

    def _load_knowledge_base(self, path):
        with open(path, 'r') as f:
            return json.load(f)

    def _create_vector_store(self):
        # Convert knowledge base to documents
        texts = []
        metadatas = []
        
        # Add company info
        texts.append(self.knowledge_base['company']['description'])
        metadatas.append({'type': 'company_info'})
        
        # Add products
        for product in self.knowledge_base['products']:
            texts.append(f"{product['name']}: {product['description']}")
            metadatas.append({'type': 'product', 'name': product['name']})
        
        # Create vector store
        return FAISS.from_texts(texts, self.embeddings, metadatas=metadatas)

    def _create_conversation_chain(self):
        template = """You are Bito, Bitlogicx's professional sales assistant. Follow these guidelines:

        CORE RULES:
        1. Keep responses focused on understanding client needs
        2. When users mention building software/apps/websites, immediately start lead collection
        3. Don't share technical details until lead information is collected
        4. Always be professional and enthusiastic
        5. Focus on business value and solutions

        LEAD COLLECTION PRIORITY:
        1. Identify project interest
        2. Collect name
        3. Get email
        4. Get phone number
        5. Confirm team will contact

        Current conversation:
        {history}

        Context:
        {context}

        Human: {input}
        Assistant: """

        prompt = PromptTemplate(
            input_variables=["history", "context", "input"],
            template=template
        )

        return LLMChain(
            llm=self.llm,
            prompt=prompt,
            memory=self.memory,
            verbose=True,
            output_key="text"
        )

    def _enhance_product_context(self, query: str) -> str:
        # Check for pricing related queries
        if any(word in query.lower() for word in ['price', 'cost', 'pricing', 'charges']):
            self.conversation_state["price_discussed"] = True
            return "Our pricing varies based on project requirements. For accurate pricing, we'd need to understand your specific needs through a consultation."

        # Check for service-related queries
        service_contexts = {
            'development': 'We offer custom software development starting from $5000, with final pricing based on project scope.',
            'integration': 'System integration services typically range from $3000-$15000 depending on complexity.',
            'automation': 'Business process automation solutions start from $4000, varying with automation scope.',
            'consulting': 'Consultation services are available at $150/hour with package options available.'
        }
        
        for keyword, context in service_contexts.items():
            if keyword in query.lower():
                return context

        # Then check for location and product contexts
        if 'location' in query.lower() or 'where' in query.lower():
            return "Bitlogicx is located at A5 Commercial Block A, Architects Engineers Housing Society, Lahore, Pakistan"
        product_contexts = {
            'inventory': 'Our Inventory Management System offers comprehensive features including real-time tracking, automated reordering, and detailed analytics.',
            'erp': 'Bitlogicx ERP provides end-to-end business management with robust inventory control features.',
            'management': 'We offer specialized management solutions tailored to your business needs.'
        }
        
        for keyword, context in product_contexts.items():
            if keyword in query.lower():
                return context
        return ""

    def get_relevant_context(self, query):
        # Search vector store for relevant context
        docs = self.vector_store.similarity_search(query, k=2)
        return "\n".join(doc.page_content for doc in docs)

    async def get_response(self, user_input: str) -> str:
        try:
            # Check for name introduction
            name_patterns = [
                r"(?i)i am (\w+)",
                r"(?i)my name is (\w+)",
                r"(?i)this is (\w+)",
                r"(?i)(\w+) here"
            ]
            
            import re
            for pattern in name_patterns:
                match = re.search(pattern, user_input)
                if match:
                    self.conversation_state["name"] = match.group(1).capitalize()
                    if not self.conversation_state["greeting_shown"]:
                        self.conversation_state["greeting_shown"] = True
                        return f"Nice to meet you {self.conversation_state['name']}! I'm Bito, your AI assistant from Bitlogicx. How can I help you today?"

            # Use name in responses if available
            if self.conversation_state["name"] and not self._shows_interest(user_input):
                context = self.get_relevant_context(user_input)
                enhanced_context = f"Remember to address the user as {self.conversation_state['name']}. {context}"
            else:
                context = self.get_relevant_context(user_input)
                enhanced_context = context

            # Check for service-related queries
            service_keywords = ['service', 'offer', 'provide', 'help', 'do']
            if any(keyword in user_input.lower() for keyword in service_keywords):
                context = self._get_service_context()
                combined_context = f"{context}\n{self.get_relevant_context(user_input)}"
            else:
                # Enhance context with pricing information
                context = self.get_relevant_context(user_input)
                enhanced_context = self._enhance_product_context(user_input)
                combined_context = f"{context}\n{enhanced_context}" if enhanced_context else context

            # Normal conversation flow with enhanced context
            response = await self.conversation_chain.ainvoke({
                "input": user_input,
                "context": combined_context
            })
            
            # Post-process response
            processed_response = self._post_process_response(response["text"], user_input)
            self.conversation_state["last_response"] = processed_response
            return processed_response
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "I apologize, but I encountered an error. Could you please rephrase your question?"

    def _get_service_context(self) -> str:
        """Get comprehensive service context"""
        services = self.knowledge_base['services']
        solutions = self.knowledge_base['custom_solutions']
        
        return f"""
Our core services include:
• {', '.join(services['specific'])}

Development Process:
• {', '.join(solutions['development_process'])}

Industries we serve:
• {', '.join(solutions['industries_served'][:5])}

Technologies:
• Frontend: {', '.join(solutions['technologies']['frontend'][:3])}
• Backend: {', '.join(solutions['technologies']['backend'][:3])}
"""

    def _format_initial_greeting(self) -> str:
        return """**Welcome to Bitlogicx!**

I'm Bito, your AI assistant. How may I help you today?"""

    def _post_process_response(self, response: str, user_input: str) -> str:
        """Enhance response based on context and user input"""
        # Handle initial greeting
        if user_input.lower() in ['hi', 'hello', 'hey']:
            return "Hello! I'm Bito, your AI assistant from Bitlogicx. How can I help you today?"

        # Clean up response
        response = response.strip()
        
        # Ensure response maintains conversation flow
        if not any(char in response for char in '?'):
            response += " How can I assist you further with this?"

        return response

    def _process_contact_info(self, input_text: str) -> str:
        state = self.conversation_state
        
        if not state.get("name"):
            state["name"] = input_text
            return f"Thanks {input_text}! Could you please provide your email address for the meeting invitation?"
        
        elif not state.get("email"):
            if self._validate_email(input_text):
                state["email"] = input_text
                return "Great! What's the best phone number to reach you at?"
            return "Please provide a valid email address for the meeting invitation."
        
        elif not state.get("phone"):
            if self._validate_phone(input_text):
                state["phone"] = input_text
                state["collecting_contact"] = False
                meeting_msg = f"Perfect! Our team will schedule a meeting to discuss {state.get('interest', 'your requirements')}. "
                meeting_msg += "They will send an invitation to your email shortly. Is there anything specific you'd like them to prepare for the meeting?"
                return meeting_msg
            return "Please provide a valid phone number where our team can reach you."
            
        return "Our team will be in touch soon to schedule the meeting. Is there anything else you'd like to know about our services?"

    def _format_pricing_response(self) -> str:
        """Format pricing information with clean markdown"""
        return """Our service pricing:

• **Custom Software Development**: Starting from $5,000
• **System Integration**: $3,000 - $15,000
• **Business Process Automation**: Starting from $4,000
• **Consultation Services**: $150/hour

Would you like to schedule a consultation for detailed pricing based on your requirements?"""

    def _shows_interest(self, text: str) -> bool:
        interest_keywords = [
            "interested", "want", "looking for", "need", "help",
            "how much", "price", "cost", "pricing", "quote",
            "estimate", "consultation", "discuss", "more info"
        ]
        return any(keyword in text.lower() for keyword in interest_keywords)

    def _is_contact_info_request(self) -> bool:
        return self.conversation_state.get("collecting_contact", False)

    def _get_contact_collection_prompt(self) -> str:
        state = self.conversation_state
        if not state.get("name"):
            state["collecting_contact"] = True
            return "To better assist you, could you please share your name?"
        elif not state.get("email"):
            return "Great! Could you please provide your email address so our team can reach out to you?"
        elif not state.get("phone"):
            return "Perfect! Lastly, what's the best phone number to reach you at?"
        else:
            state["collecting_contact"] = False
            return "Thank you for providing your information. Our team will contact you shortly!"

    def _validate_email(self, email: str) -> bool:
        import re
        pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        return bool(re.match(pattern, email))

    def _validate_phone(self, phone: str) -> bool:
        import re
        # Basic phone validation (allows various formats)
        pattern = r'[\d\+\-\(\) ]{10,}'
        return bool(re.match(pattern, phone))
