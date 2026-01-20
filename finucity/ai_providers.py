"""
Multi-AI Provider System for Finucity
Supports multiple free AI providers with automatic fallback
Author: Sumeet Sangwan
"""

import os
import requests
from typing import Dict, Any, Optional
import time

class AIProviderManager:
    """Manages multiple AI providers with automatic fallback"""
    
    def __init__(self):
        self.providers = {
            'groq': {
                'name': 'Groq',
                'api_key': os.getenv('GROQ_API_KEY'),
                'url': 'https://api.groq.com/openai/v1/chat/completions',
                'model': 'llama-3.1-8b-instant',
                'enabled': bool(os.getenv('GROQ_API_KEY'))
            },
            'together': {
                'name': 'Together AI',
                'api_key': os.getenv('TOGETHER_API_KEY'),
                'url': 'https://api.together.xyz/v1/chat/completions',
                'model': 'meta-llama/Llama-3-8b-chat-hf',
                'enabled': bool(os.getenv('TOGETHER_API_KEY'))
            },
            'huggingface': {
                'name': 'Hugging Face',
                'api_key': os.getenv('HUGGINGFACE_API_KEY'),
                'url': 'https://api-inference.huggingface.co/models/meta-llama/Meta-Llama-3-8B-Instruct',
                'model': 'meta-llama/Meta-Llama-3-8B-Instruct',
                'enabled': bool(os.getenv('HUGGINGFACE_API_KEY'))
            }
        }
        
        self.provider_order = ['groq', 'together', 'huggingface']
        print(f"🤖 AI Providers initialized:")
        for name, config in self.providers.items():
            status = "✅ Ready" if config['enabled'] else "❌ Disabled"
            print(f"   {config['name']}: {status}")
    
    def get_response(self, message: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Get AI response with automatic provider fallback
        """
        last_error = None
        
        for provider_key in self.provider_order:
            provider = self.providers[provider_key]
            
            if not provider['enabled']:
                continue
            
            try:
                print(f"🔄 Trying {provider['name']}...")
                response = self._call_provider(provider_key, message, context)
                
                if response['success']:
                    print(f"✅ {provider['name']} succeeded")
                    response['provider'] = provider['name']
                    return response
                else:
                    last_error = response.get('error', 'Unknown error')
                    print(f"⚠️ {provider['name']} failed: {last_error}")
                    
            except Exception as e:
                last_error = str(e)
                print(f"❌ {provider['name']} error: {e}")
                continue
        
        # All providers failed, return fallback
        print("⚠️ All AI providers failed, using fallback response")
        return self._get_fallback_response(message, last_error)
    
    def _call_provider(self, provider_key: str, message: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Call specific AI provider"""
        provider = self.providers[provider_key]
        
        if provider_key in ['groq', 'together']:
            return self._call_openai_compatible(provider, message, context)
        elif provider_key == 'huggingface':
            return self._call_huggingface(provider, message, context)
        else:
            return {'success': False, 'error': 'Unknown provider'}
    
    def _call_openai_compatible(self, provider: Dict, message: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Call OpenAI-compatible APIs (Groq, Together)"""
        try:
            headers = {
                'Authorization': f"Bearer {provider['api_key']}",
                'Content-Type': 'application/json'
            }
            
            system_prompt = self._build_system_prompt(context)
            
            payload = {
                'model': provider['model'],
                'messages': [
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': message}
                ],
                'temperature': 0.7,
                'max_tokens': 1024
            }
            
            response = requests.post(
                provider['url'],
                headers=headers,
                json=payload,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                ai_response = data['choices'][0]['message']['content']
                
                return {
                    'success': True,
                    'response': ai_response.strip(),
                    'provider': provider['name'],
                    'tokens': data.get('usage', {}).get('total_tokens', 0)
                }
            else:
                return {
                    'success': False,
                    'error': f"API returned {response.status_code}"
                }
                
        except requests.exceptions.Timeout:
            return {'success': False, 'error': 'Request timeout'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _call_huggingface(self, provider: Dict, message: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Call Hugging Face Inference API"""
        try:
            headers = {
                'Authorization': f"Bearer {provider['api_key']}"
            }
            
            system_prompt = self._build_system_prompt(context)
            full_prompt = f"{system_prompt}\n\nUser: {message}\nAssistant:"
            
            payload = {
                'inputs': full_prompt,
                'parameters': {
                    'max_new_tokens': 1024,
                    'temperature': 0.7,
                    'return_full_text': False
                }
            }
            
            response = requests.post(
                provider['url'],
                headers=headers,
                json=payload,
                timeout=20
            )
            
            if response.status_code == 200:
                data = response.json()
                ai_response = data[0]['generated_text'] if isinstance(data, list) else data.get('generated_text', '')
                
                return {
                    'success': True,
                    'response': ai_response.strip(),
                    'provider': provider['name'],
                    'tokens': 0
                }
            else:
                return {
                    'success': False,
                    'error': f"API returned {response.status_code}"
                }
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _build_system_prompt(self, context: Optional[Dict] = None) -> str:
        """Build system prompt for AI"""
        base_prompt = """You are Finucity AI, an expert Chartered Accountant specializing in Indian financial laws, taxation, and business compliance.

Your expertise includes:
- Indian Income Tax Act and regulations
- GST (Goods and Services Tax)
- Investment planning and portfolio management
- Business registration and compliance
- Financial planning and wealth management

Provide accurate, professional advice. Always mention that users should consult a certified CA for personalized guidance."""
        
        return base_prompt
    
    def _get_fallback_response(self, message: str, error: str = None) -> Dict[str, Any]:
        """Generate intelligent fallback response"""
        
        message_lower = message.lower()
        
        # Tax-related queries
        if any(word in message_lower for word in ['tax', '80c', 'deduction', 'itr', 'return']):
            response = """For tax-related queries in India:

**Section 80C Deductions (₹1.5 lakh limit):**
- ELSS Mutual Funds (3-year lock-in)
- PPF (15-year tenure, tax-free returns)
- Life Insurance Premiums
- NSC, Tax-saving FDs

**Section 80D:** Health insurance premiums (up to ₹25,000)
**Section 80CCD(1B):** NPS additional ₹50,000

**ITR Filing Deadlines:**
- Salaried: July 31
- Business: September 30

For personalized tax planning, please consult a certified Chartered Accountant."""
        
        # Investment queries
        elif any(word in message_lower for word in ['invest', 'mutual fund', 'stock', 'sip', 'portfolio']):
            response = """For investment planning:

**Recommended Portfolio Allocation:**
- Large-cap equity funds: 40%
- Mid/small-cap funds: 30%
- Debt funds: 20%
- Gold/International: 10%

**Popular Investment Options:**
- SIP in Index Funds (low-cost, diversified)
- ELSS for tax savings (80C benefit)
- PPF for safe returns
- NPS for retirement

**Start with:** ₹5,000-10,000 monthly SIP
**Time Horizon:** Minimum 5-7 years for equity

Consult a financial advisor for personalized recommendations."""
        
        # GST queries
        elif any(word in message_lower for word in ['gst', 'gstr', 'registration', 'invoice']):
            response = """GST in India:

**Registration Required:**
- Turnover > ₹40 lakhs (goods)
- Turnover > ₹20 lakhs (services)
- All interstate suppliers

**GST Returns:**
- GSTR-1: Sales (11th of next month)
- GSTR-3B: Summary (20th of next month)
- GSTR-9: Annual return

**GST Rates:** 0%, 5%, 12%, 18%, 28%

File returns on: https://www.gst.gov.in
For compliance help, contact a GST practitioner."""
        
        else:
            response = """I'm Finucity AI, your financial assistant. I can help with:

✓ Income Tax planning and ITR filing
✓ Investment advice (SIP, Mutual Funds, Stocks)
✓ GST registration and compliance
✓ Business setup and registration
✓ Financial planning and budgeting

Please ask me specific questions about Indian taxation, investments, or business finance.

Note: All AI providers are currently experiencing high load. Your query has been received."""
        
        return {
            'success': True,
            'response': response,
            'provider': 'Fallback System',
            'tokens': 0,
            'fallback': True
        }

# Global instance
ai_manager = AIProviderManager()

def get_ai_response(message: str, context: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Main function to get AI response
    Use this in your routes
    """
    return ai_manager.get_response(message, context)
