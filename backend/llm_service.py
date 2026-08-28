"""
CampusFix AI - LLM Service
Clean implementation using Groq Python SDK
"""

import os
from groq import Groq
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from project root
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

class LLMService:
    """Service for interacting with Groq LLM"""
    
    def __init__(self):
        """Initialize Groq client"""
        # Get API key from environment
        self.api_key = os.getenv('GROQ_API_KEY')
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")
        
        # Get model from environment or use default
        self.model = os.getenv('GROQ_MODEL', 'openai/gpt-oss-120b')
        self.temperature = 0.7
        self.max_tokens = 2048
        
        # Initialize Groq client
        try:
            self.client = Groq(api_key=self.api_key)
            print(f"✓ Groq client initialized successfully")
            print(f"✓ Model: {self.model}")
            print(f"✓ Temperature: {self.temperature}")
        except Exception as e:
            print(f"✗ Failed to initialize Groq client: {str(e)}")
            raise
        
        # System prompt for general-purpose assistant
        self.system_prompt = """You are Fixie, a helpful AI assistant for CampusFix AI.

You can help with:
- General questions and explanations
- Programming and coding help
- Academic subjects (Java, DBMS, algorithms, data structures, etc.)
- Technology and IT troubleshooting
- Campus IT support when needed

Answer questions naturally based on what the user asks. Do NOT force every conversation into an IT troubleshooting workflow. If someone asks about programming, explain programming. If they ask about Wi-Fi issues, help with troubleshooting.

Be helpful, clear, and conversational.

Do not invent campus-specific URLs, phone numbers, buildings, rooms, Wi-Fi SSIDs,
policies, support addresses, or resolution estimates. If those details are not
provided in approved campus knowledge, say that the user should contact the campus
IT support team.

Format responses as clean Markdown suitable for a chat interface. Use short headings,
numbered or bulleted lists, tables only when they improve comparison, and fenced code
blocks for code. Do not emit raw HTML, unstructured delimiter rows, or unnecessarily
long responses. Keep URLs as valid Markdown links."""
    
    def build_messages(self, conversation_history, user_firstName=None, knowledge_context=None):
        """
        Build messages array for Groq API
        
        Args:
            conversation_history: List of {role, content, timestamp} dicts from MongoDB
            user_firstName: Optional user's first name for personalization
        
        Returns:
            List of messages in Groq format
        """
        messages = []
        
        # Add system prompt with optional personalization
        system_content = self.system_prompt
        if user_firstName:
            system_content += f"\n\nThe user's name is {user_firstName}. You can address them by name when appropriate."
        if knowledge_context:
            system_content += f"\n\nRelevant approved campus knowledge:\n{knowledge_context}\nUse this context when relevant, but do not invent campus policies."
        
        messages.append({
            "role": "system",
            "content": system_content
        })
        
        # Add conversation history (limit to last 10 messages)
        recent_history = conversation_history[-10:] if len(conversation_history) > 10 else conversation_history
        
        for msg in recent_history:
            messages.append({
                "role": msg['role'],
                "content": msg['content']
            })
        
        return messages
    
    def get_response(self, user_message, conversation_history=None, user_firstName=None, knowledge_context=None):
        """
        Get LLM response for user message
        
        Args:
            user_message: Current user message string
            conversation_history: List of previous messages from MongoDB
            user_firstName: Optional user's first name
        
        Returns:
            dict with success, message, and optional error
        """
        try:
            # Build messages
            if conversation_history is None:
                conversation_history = []
            
            messages = self.build_messages(conversation_history, user_firstName, knowledge_context)
            
            # Add current user message
            messages.append({
                "role": "user",
                "content": user_message
            })
            
            # Log request (for debugging)
            print(f"\n=== LLM REQUEST ===")
            print(f"Model: {self.model}")
            print(f"Temperature: {self.temperature}")
            print(f"Message count: {len(messages)}")
            print(f"User message: {user_message[:100]}...")
            print(f"===================\n")
            
            # Call Groq API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            # Extract response
            assistant_message = response.choices[0].message.content
            
            # Log response (for debugging)
            print(f"\n=== LLM RESPONSE ===")
            print(f"Response: {assistant_message[:150]}...")
            print(f"Usage: {response.usage}")
            print(f"====================\n")
            
            return {
                'success': True,
                'message': assistant_message,
                'usage': {
                    'prompt_tokens': response.usage.prompt_tokens,
                    'completion_tokens': response.usage.completion_tokens,
                    'total_tokens': response.usage.total_tokens
                },
                'model': self.model
            }
            
        except Exception as e:
            error_msg = str(e)
            print(f"\n=== LLM ERROR ===")
            print(f"Error: {error_msg}")
            print(f"=================\n")
            
            return {
                'success': False,
                'message': f"LLM Error: {error_msg}",
                'error': error_msg
            }
    
    def test_connection(self):
        """
        Test LLM connection with a simple request
        
        Returns:
            dict with success status and message
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Say 'Connection successful' if you can read this."}
                ],
                temperature=0.7,
                max_tokens=50
            )
            
            return {
                'success': True,
                'model': self.model,
                'message': 'LLM connection successful',
                'test_response': response.choices[0].message.content
            }
            
        except Exception as e:
            return {
                'success': False,
                'model': self.model,
                'error': str(e)
            }


# Singleton instance
_llm_service = None

def get_llm_service():
    """Get or create LLM service instance"""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
