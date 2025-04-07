from typing import List, Dict
from datetime import datetime

class ConversationSummarizer:
    def summarize(self, messages: List[Dict]) -> str:
        """Generate conversation summary"""
        if not messages:
            return "No conversation to summarize"
            
        # Extract key points
        topics = self._extract_topics(messages)
        user_needs = self._extract_user_needs(messages)
        action_items = self._extract_action_items(messages)
        
        summary = [
            "Conversation Summary:",
            f"Duration: {self._get_duration(messages)}",
            f"Topics Discussed: {', '.join(topics)}",
            f"User Needs: {', '.join(user_needs)}",
            f"Action Items: {', '.join(action_items)}"
        ]
        
        return "\n".join(summary)
        
    def _extract_topics(self, messages: List[Dict]) -> List[str]:
        # Add topic extraction logic
        topics = set()
        keywords = ['mobile', 'web', 'app', 'website', 'software']
        for msg in messages:
            if msg['sender'] == 'user':
                topics.update(word for word in msg['content'].lower().split() 
                            if word in keywords)
        return list(topics)
        
    def _extract_user_needs(self, messages: List[Dict]) -> List[str]:
        # Add needs extraction logic
        needs = []
        need_indicators = ['need', 'want', 'looking for', 'interested in']
        # Implementation details...
        return needs
        
    def _extract_action_items(self, messages: List[Dict]) -> List[str]:
        # Add action item extraction logic
        actions = []
        # Implementation details...
        return actions
        
    def _get_duration(self, messages: List[Dict]) -> str:
        start = datetime.fromisoformat(messages[0]['timestamp'])
        end = datetime.fromisoformat(messages[-1]['timestamp'])
        duration = end - start
        return f"{duration.seconds // 60} minutes"
