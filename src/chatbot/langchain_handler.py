from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaEmbeddings
from langchain_ollama import OllamaLLM
from langchain.chains import LLMChain
from langchain_core.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
import json
import logging

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
            "interest": None
        }

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
        template = """You are Bito, BITLogix's professional sales assistant. Your primary goals are:
        1. Introduce yourself as BITLogix's AI assistant
        2. Ask about visitor's business needs
        3. Share relevant BITLogix products/services based on their needs
        4. Always try to collect visitor information (name, email, phone) for follow-up
        5. Keep responses focused on BITLogix offerings only
        
        Rules:
        - Keep responses under 3 sentences
        - Always mention specific BITLogix products when relevant
        - If user shows interest, ask for their contact details
        - Don't discuss topics unrelated to BITLogix services
        
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
        """Add product-specific context based on query topic"""
        product_contexts = {
            'inventory': 'Our Inventory Management System offers comprehensive features including real-time tracking, automated reordering, and detailed analytics.',
            'erp': 'BITLogix ERP provides end-to-end business management with robust inventory control features.',
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
            # Handle contact information collection
            if self.conversation_state["collecting_contact"]:
                return self._process_contact_info(user_input)
            
            # Check for interest and initiate contact collection
            if self._shows_interest(user_input):
                self.conversation_state["collecting_contact"] = True
                return "I'd be happy to help! First, could you please share your name?"

            # Normal conversation flow
            response = await self.conversation_chain.ainvoke({
                "input": user_input,
                "context": self.get_relevant_context(user_input)
            })
            
            return response["text"]
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "I apologize, but I encountered an error. Could you please rephrase your question?"

    def _shows_interest(self, text: str) -> bool:
        interest_keywords = ["interested", "want", "looking for", "need", "help", "how much", "price", "cost"]
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

    def _process_contact_info(self, input_text: str) -> str:
        """Process and validate contact information"""
        state = self.conversation_state
        
        if not state.get("name"):
            state["name"] = input_text
            return "Great! Could you please provide your email address?"
        
        elif not state.get("email"):
            if self._validate_email(input_text):
                state["email"] = input_text
                return "Perfect! What's the best phone number to reach you at?"
            return "Please provide a valid email address."
        
        elif not state.get("phone"):
            if self._validate_phone(input_text):
                state["phone"] = input_text
                state["collecting_contact"] = False
                return "Thank you! Our team will contact you soon. Is there anything else you'd like to know about our services?"
            return "Please provide a valid phone number."
            
        return "How else can I assist you today?"

    def _validate_email(self, email: str) -> bool:
        import re
        pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        return bool(re.match(pattern, email))

    def _validate_phone(self, phone: str) -> bool:
        import re
        # Basic phone validation (allows various formats)
        pattern = r'[\d\+\-\(\) ]{10,}'
        return bool(re.match(pattern, phone))
