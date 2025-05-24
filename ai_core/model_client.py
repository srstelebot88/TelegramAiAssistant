import os
import requests
import json
from typing import Optional, Dict, Any, List
from utils.logger import get_logger

logger = get_logger(__name__)

class AIModelClient:
    """Client for interacting with Together.ai API for AI responses"""
    
    def __init__(self):
        self.api_key = os.environ.get('TOGETHER_API_KEY')
        if not self.api_key:
            logger.error("TOGETHER_API_KEY environment variable not set")
            raise ValueError("TOGETHER_API_KEY is required")
        
        self.base_url = "https://api.together.xyz/v1"
        self.default_model = "meta-llama/Llama-3.2-3B-Instruct-Turbo"
        self.max_tokens = 2048
        self.temperature = 0.7
        
        # Fallback to other providers if Together.ai fails
        self.anthropic_key = os.environ.get('ANTHROPIC_API_KEY')
        self.openai_key = os.environ.get('OPENAI_API_KEY')
        
    def generate_response(self, prompt: str, model: str = None, 
                         max_tokens: int = None, temperature: float = None) -> Optional[str]:
        """Generate AI response using Together.ai API"""
        try:
            # Try Together.ai first
            response = self._call_together_ai(
                prompt, 
                model or self.default_model,
                max_tokens or self.max_tokens,
                temperature or self.temperature
            )
            
            if response:
                return response
            
            logger.warning("Together.ai failed, trying fallback providers")
            
            # Try Anthropic as fallback
            if self.anthropic_key:
                response = self._call_anthropic(prompt)
                if response:
                    return response
            
            # Try OpenAI as last resort (if available)
            if self.openai_key:
                response = self._call_openai(prompt)
                if response:
                    return response
            
            logger.error("All AI providers failed")
            return None
            
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            return None
    
    def _call_together_ai(self, prompt: str, model: str, max_tokens: int, temperature: float) -> Optional[str]:
        """Call Together.ai API"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Format prompt for chat completion
            messages = [
                {"role": "user", "content": prompt}
            ]
            
            payload = {
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "stop": ["Human:", "User:", "\n\nUser:"]
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'choices' in data and len(data['choices']) > 0:
                    content = data['choices'][0]['message']['content']
                    logger.debug(f"Together.ai response received: {len(content)} characters")
                    return content.strip()
            else:
                logger.error(f"Together.ai API error: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"Error calling Together.ai: {e}")
        
        return None
    
    def _call_anthropic(self, prompt: str) -> Optional[str]:
        """Call Anthropic Claude API as fallback"""
        try:
            import anthropic
            
            # the newest Anthropic model is "claude-3-5-sonnet-20241022" which was released October 22, 2024
            client = anthropic.Anthropic(api_key=self.anthropic_key)
            
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[{"role": "user", "content": prompt}]
            )
            
            if response.content:
                content = response.content[0].text
                logger.debug(f"Anthropic response received: {len(content)} characters")
                return content.strip()
                
        except Exception as e:
            logger.error(f"Error calling Anthropic: {e}")
        
        return None
    
    def _call_openai(self, prompt: str) -> Optional[str]:
        """Call OpenAI API as last resort fallback"""
        try:
            import openai
            
            client = openai.OpenAI(api_key=self.openai_key)
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            if response.choices:
                content = response.choices[0].message.content
                logger.debug(f"OpenAI response received: {len(content)} characters")
                return content.strip()
                
        except Exception as e:
            logger.error(f"Error calling OpenAI: {e}")
        
        return None
    
    def get_available_models(self) -> List[Dict[str, Any]]:
        """Get list of available models from Together.ai"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(
                f"{self.base_url}/models",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json().get('data', [])
            else:
                logger.error(f"Failed to get models: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error getting available models: {e}")
        
        return []
    
    def check_api_status(self) -> Dict[str, bool]:
        """Check status of different AI providers"""
        status = {
            'together_ai': False,
            'anthropic': False,
            'openai': False
        }
        
        # Check Together.ai
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            response = requests.get(f"{self.base_url}/models", headers=headers, timeout=5)
            status['together_ai'] = response.status_code == 200
        except:
            pass
        
        # Check Anthropic
        if self.anthropic_key:
            try:
                import anthropic
                client = anthropic.Anthropic(api_key=self.anthropic_key)
                # Simple test call
                response = client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=10,
                    messages=[{"role": "user", "content": "Hi"}]
                )
                status['anthropic'] = bool(response.content)
            except:
                pass
        
        # Check OpenAI
        if self.openai_key:
            try:
                import openai
                client = openai.OpenAI(api_key=self.openai_key)
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": "Hi"}],
                    max_tokens=10
                )
                status['openai'] = bool(response.choices)
            except:
                pass
        
        return status
    
    def estimate_tokens(self, text: str) -> int:
        """Rough estimation of token count"""
        # Simple estimation: ~4 characters per token
        return len(text) // 4
    
    def truncate_to_tokens(self, text: str, max_tokens: int) -> str:
        """Truncate text to approximate token limit"""
        estimated_tokens = self.estimate_tokens(text)
        
        if estimated_tokens <= max_tokens:
            return text
        
        # Calculate how much to keep
        ratio = max_tokens / estimated_tokens
        target_length = int(len(text) * ratio * 0.9)  # 90% to be safe
        
        return text[:target_length] + "..."
