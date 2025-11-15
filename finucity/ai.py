"""
Enhanced AI module for Finucity using Groq API
Clean separation of AI logic from routing logic
Author: Sumeet Sangwan
"""

import os
import json
import requests
from datetime import datetime
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class FinucityAI:
    """
    Main AI class for Finucity financial assistant
    Handles all AI-related operations using Groq API
    """
    
    def __init__(self):
        # Initialize Groq API client
        self.api_key = os.getenv("GROQ_API_KEY")
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        self.model_name = os.getenv("AI_MODEL_NAME", "llama-3.1-8b-instant")
        self.max_tokens = int(os.getenv("AI_MAX_TOKENS", "1500"))
        self.temperature = float(os.getenv("AI_TEMPERATURE", "0.7"))
        
        # AI capabilities check
        self.is_available = bool(self.api_key)
        if not self.is_available:
            print("⚠️ Warning: GROQ_API_KEY not found. AI features will use fallback responses.")
        else:
            print("✅ Groq AI initialized successfully")
            
        # Load financial knowledge base
        self.categories = self._load_categories()
        self.disclaimers = self._load_disclaimers()
        self.context_templates = self._load_context_templates()
        
    def get_response(self, question: str, category: str = "general", context: Dict = None) -> Dict[str, Any]:
        """
        Main method to get AI response for user questions
        
        Args:
            question (str): User's question
            category (str): Question category (tax, gst, investment, etc.)
            context (Dict): Additional context (files, history, etc.)
            
        Returns:
            Dict: AI response with metadata
        """
        try:
            # Validate inputs
            if not question or not question.strip():
                return self._create_error_response("Empty question provided")
            
            question = question.strip()
            category = category.lower() if category else "general"
            
            # Get AI response
            if self.is_available:
                response = self._call_groq_api(question, category, context or {})
            else:
                response = self._generate_fallback_response(question, category)
            
            # Enhance response with metadata
            enhanced_response = self._enhance_response(response, category, question)
            
            return enhanced_response
            
        except Exception as e:
            print(f"❌ Error in get_response: {e}")
            return self._create_error_response(f"AI processing error: {str(e)}")
    
    def _call_groq_api(self, question: str, category: str, context: Dict) -> Dict[str, Any]:
        """Call Groq API with proper error handling"""
        try:
            # Build the system prompt
            system_prompt = self._build_system_prompt(category, context)
            
            # Build the user message with context
            user_message = self._build_user_message(question, context)
            
            # Prepare API request
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model_name,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
                "stream": False
            }
            
            # Add conversation history if available
            if context.get('user_history'):
                history_messages = context['user_history'][-6:]  # Last 6 messages
                # Insert history before user message
                payload["messages"] = [
                    {"role": "system", "content": system_prompt}
                ] + history_messages + [
                    {"role": "user", "content": user_message}
                ]
            
            # Make API call
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            # Handle response
            if response.status_code == 200:
                result = response.json()
                ai_content = result['choices'][0]['message']['content']
                
                return {
                    'success': True,
                    'response': ai_content.strip(),
                    'model_used': self.model_name,
                    'tokens_used': result.get('usage', {}).get('total_tokens', 0)
                }
            else:
                error_msg = f"Groq API error: {response.status_code}"
                try:
                    error_data = response.json()
                    if 'error' in error_data:
                        error_msg += f" - {error_data['error'].get('message', 'Unknown error')}"
                except:
                    error_msg += f" - {response.text[:100]}"
                
                print(f"❌ {error_msg}")
                return self._generate_fallback_response(question, category)
                
        except requests.exceptions.Timeout:
            print("❌ Groq API timeout")
            return self._generate_fallback_response(question, category, "API timeout")
        except requests.exceptions.ConnectionError:
            print("❌ Groq API connection error")
            return self._generate_fallback_response(question, category, "Connection error")
        except Exception as e:
            print(f"❌ Groq API call error: {e}")
            return self._generate_fallback_response(question, category, str(e))
    
    def _build_system_prompt(self, category: str, context: Dict) -> str:
        """Build comprehensive system prompt for the AI"""
        base_prompt = """You are Finucity AI, a professional Indian Chartered Accountant and Financial Advisor. You specialize in Indian tax laws, GST compliance, investment strategies, and business finance.

CORE DIRECTIVES:
1. Provide accurate, actionable financial advice specific to Indian regulations
2. Always mention current tax year (AY 2025-26) and applicable dates
3. Include specific amounts, percentages, and deadlines when relevant
4. Suggest practical next steps for implementation
5. Maintain professional yet friendly tone

RESPONSE STRUCTURE:
- Start with a direct answer to the user's question
- Provide detailed explanation with current rates/limits
- Include practical examples with ₹ amounts
- End with actionable recommendations
- Always add appropriate disclaimers"""

        # Add category-specific context
        category_context = self.context_templates.get(category, self.context_templates['general'])
        
        # Add file context if available
        file_context = ""
        if context.get('files'):
            file_context = "\n\nFILE CONTEXT:\nThe user has uploaded files with the following information:\n"
            for file_info in context['files'][:3]:  # Limit to 3 files
                file_context += f"- {file_info['name']}: {file_info.get('content', 'Binary file')[:500]}...\n"
        
        return f"{base_prompt}\n\n{category_context}{file_context}"
    
    def _build_user_message(self, question: str, context: Dict) -> str:
        """Build the user message with context"""
        message = f"User Question: {question}"
        
        # Add context about files if uploaded
        if context.get('files'):
            message += f"\n\n[User has uploaded {len(context['files'])} file(s) for analysis]"
        
        return message
    
    def _enhance_response(self, response: Dict, category: str, question: str) -> Dict[str, Any]:
        """Enhance the AI response with metadata and suggestions"""
        try:
            if not response.get('success'):
                return response
            
            # Get category info
            category_info = self.categories.get(category, self.categories['general'])
            
            # Generate follow-up suggestions
            follow_ups = self._generate_follow_up_suggestions(category, question)
            
            # Enhanced response
            enhanced = {
                'success': True,
                'response': response['response'],
                'category': category_info['display_name'],
                'confidence': response.get('confidence', 0.95),
                'disclaimer': self.disclaimers.get(category, self.disclaimers['general']),
                'follow_up_suggestions': follow_ups,
                'model_used': response.get('model_used', 'fallback'),
                'timestamp': datetime.now().isoformat()
            }
            
            # Add tokens info if available
            if 'tokens_used' in response:
                enhanced['tokens_used'] = response['tokens_used']
            
            return enhanced
            
        except Exception as e:
            print(f"❌ Error enhancing response: {e}")
            return response
    
    def _generate_fallback_response(self, question: str, category: str, error_msg: str = None) -> Dict[str, Any]:
        """Generate fallback response when AI API is unavailable"""
        
        fallback_responses = {
            'income_tax': """**Income Tax Guidance**

Based on your query about income tax, here are the key points for AY 2025-26:

**Current Tax Rates & Limits:**
• Standard Deduction: ₹75,000 (New Tax Regime)
• Section 80C Limit: ₹1,50,000 (investments like ELSS, PPF, NSC)
• Section 80D: ₹25,000 for health insurance (₹50,000 if senior citizen)
• ITR Filing Deadline: July 31, 2025

**Immediate Action Items:**
1. Review your current tax-saving investments
2. Optimize salary structure with your employer
3. Maintain proper documentation for all deductions
4. Consider switching between old vs new tax regime based on your profile

**Investment Options for Tax Saving:**
• ELSS Mutual Funds (3-year lock-in, market returns)
• Public Provident Fund (15-year tenure, ~7-8% returns)
• National Savings Certificate (5-year tenure, ~6.8% returns)
• Life Insurance (Term + Investment combination)

For personalized tax planning, consult a qualified Chartered Accountant.""",

            'gst': """**GST Compliance Guide**

Here's comprehensive GST guidance for your query:

**Registration Requirements:**
• Goods: ₹40 lakh annual turnover (₹20 lakh for NE states)
• Services: ₹20 lakh annual turnover (₹10 lakh for NE states)
• E-commerce: Mandatory registration regardless of turnover

**Key GST Rates (Current):**
• Essential items: 0% (cereals, milk, etc.)
• Daily necessities: 5% (tea, coffee, spices)
• Standard items: 12% (computers, processed food)
• Luxury items: 18% (AC, refrigerator, restaurants)
• Premium items: 28% (automobiles, luxury goods)

**Filing Deadlines:**
• GSTR-1: 11th of next month
• GSTR-3B: 20th of next month  
• Annual Return (GSTR-9): December 31st

**Input Tax Credit (ITC) Rules:**
1. Invoice must be in your name
2. Supplier must file their returns
3. Payment to supplier must be made within 180 days
4. Goods/services must be for business use

Always verify current rates on the official GST portal as they change frequently.""",

            'investment': """**Investment Advisory**

Based on your investment query, here's professional guidance:

**Investment Fundamentals:**
• Emergency Fund: 6-12 months of expenses in liquid funds
• Risk Assessment: Understand your risk tolerance before investing
• Time Horizon: Align investments with your financial goals
• Diversification: Spread risk across different asset classes

**Recommended Asset Allocation:**
**Conservative (Low Risk):**
- Debt Funds: 70%, Equity: 20%, Gold: 10%

**Moderate (Medium Risk):**
- Equity Funds: 60%, Debt Funds: 30%, Gold: 10%

**Aggressive (High Risk):**
- Equity Funds: 80%, Debt Funds: 15%, Gold: 5%

**Top Investment Options for 2025:**
• **ELSS Funds**: Tax saving + wealth creation (3-year lock-in)
• **Index Funds**: Low cost, diversified equity exposure
• **Large Cap Funds**: Stable blue-chip companies
• **Mid & Small Cap**: Higher growth potential, higher risk
• **Debt Funds**: Capital preservation, regular income

**SIP Strategy:**
Start with ₹5,000-10,000 monthly SIP in diversified equity funds. Increase by 10-15% annually as income grows.

Remember: Past performance doesn't guarantee future returns. Consult SEBI-registered advisors for personalized advice.""",

            'business': """**Business Finance Guidance**

Here's comprehensive business finance guidance:

**Business Registration Process:**
1. **Sole Proprietorship**: Simplest form, unlimited liability
2. **Partnership**: Shared responsibility, partnership deed required  
3. **LLP**: Limited liability, minimum 2 partners
4. **Private Limited**: Separate legal entity, minimum ₹1 lakh capital

**Essential Registrations:**
• PAN Card (Mandatory for all businesses)
• GST Registration (if turnover > ₹40 lakh)
• Professional Tax (state-specific)
• ESI & PF (if employees > 20/10 respectively)
• Trade License (from local municipal authority)

**Funding Options:**
**Bank Loans:**
- MUDRA Loans: Up to ₹10 lakh for micro enterprises
- MSME Loans: Up to ₹25 crore with collateral
- Working Capital: For daily operational needs

**Government Schemes:**
- Stand-up India: ₹10 lakh to ₹1 crore for SC/ST/Women
- PMEGP: Up to ₹25 lakh for manufacturing, ₹10 lakh for services
- Startup India: Tax benefits, easier compliance

**Financial Management:**
1. Maintain separate business bank account
2. Use accounting software for record keeping
3. Regular GST filing and TDS compliance
4. Monthly financial statements review

For detailed business planning, consult a qualified business advisor.""",

            'general': """**General Financial Guidance**

Thank you for your financial query. Here's comprehensive guidance:

**Financial Planning Basics:**
• **Budgeting**: Follow 50-30-20 rule (Needs-Wants-Savings)
• **Emergency Fund**: Build 6-12 months expense corpus
• **Goal Setting**: Define short, medium, and long-term objectives
• **Regular Review**: Monthly financial health checkups

**Wealth Building Strategy:**
1. **Start Early**: Time is your greatest asset in wealth creation
2. **Automate**: Set up SIPs and auto-transfers to savings
3. **Diversify**: Spread investments across asset classes
4. **Stay Disciplined**: Avoid emotional financial decisions

**Key Areas to Focus:**
**Income Optimization:**
- Skill development for career growth
- Multiple income streams creation
- Tax-efficient salary structuring

**Expense Management:**
- Track all expenses for 3 months
- Identify and eliminate unnecessary costs
- Negotiate better rates for utilities, insurance

**Investment Planning:**
- Start with liquid funds for emergency
- Graduate to equity mutual funds via SIP
- Consider tax-saving instruments under 80C

**Common Financial Mistakes to Avoid:**
• Living beyond your means
• No emergency fund
• Delaying investments
• Emotional investment decisions
• Ignoring insurance needs

Remember: Financial planning is a journey, not a destination. Start small, stay consistent, and seek professional advice when needed."""
        }
        
        # Select appropriate response
        response_text = fallback_responses.get(category, fallback_responses['general'])
        
        # Add error context if provided
        if error_msg:
            response_text = f"[Note: Using offline response due to {error_msg}]\n\n{response_text}"
        
        return {
            'success': True,
            'response': response_text,
            'confidence': 0.85,
            'model_used': 'fallback_system'
        }
    
    def _generate_follow_up_suggestions(self, category: str, question: str) -> List[str]:
        """Generate contextual follow-up suggestions"""
        suggestions_map = {
            'income_tax': [
                'What documents do I need for tax filing?',
                'How do I choose between old and new tax regime?',
                'What are the best tax-saving investments for 2025?',
                'How do I calculate advance tax payments?'
            ],
            'gst': [
                'How do I file GST returns online?',
                'What is input tax credit and how do I claim it?',
                'When do I need to register for GST?',
                'What are the current GST rates for my business?'
            ],
            'investment': [
                'How much should I invest in SIPs monthly?',
                'What is the difference between growth and dividend funds?',
                'How do I build a diversified portfolio?',
                'When should I review and rebalance my investments?'
            ],
            'business': [
                'How do I register my business online?',
                'What are the compliance requirements for my business?',
                'How can I get a business loan?',
                'What accounting software should I use?'
            ],
            'general': [
                'How do I create a monthly budget?',
                'What should be my emergency fund target?',
                'How do I start investing with limited money?',
                'What insurance policies do I need?'
            ]
        }
        
        return suggestions_map.get(category, suggestions_map['general'])
    
    def _create_error_response(self, error_msg: str) -> Dict[str, Any]:
        """Create standardized error response"""
        return {
            'success': False,
            'response': f"I apologize, but I encountered an issue: {error_msg}. Please try again or contact support.",
            'error': error_msg,
            'category': 'Error',
            'confidence': 0.0,
            'follow_up_suggestions': [
                'Try rephrasing your question',
                'Check if all required information is provided',
                'Contact support if the issue persists'
            ]
        }
    
    def _load_categories(self) -> Dict[str, Dict[str, str]]:
        """Load category configurations"""
        return {
            'income_tax': {
                'display_name': 'Income Tax Advisory',
                'icon': 'fas fa-file-invoice-dollar',
                'color': '#28a745'
            },
            'gst': {
                'display_name': 'GST Compliance',
                'icon': 'fas fa-receipt',
                'color': '#dc3545'
            },
            'investment': {
                'display_name': 'Investment Planning',
                'icon': 'fas fa-chart-line',
                'color': '#007bff'
            },
            'business': {
                'display_name': 'Business Finance',
                'icon': 'fas fa-building',
                'color': '#fd7e14'
            },
            'insurance': {
                'display_name': 'Insurance Planning',
                'icon': 'fas fa-shield-alt',
                'color': '#6610f2'
            },
            'general': {
                'display_name': 'General Financial Guidance',
                'icon': 'fas fa-comment-dots',
                'color': '#FBA002'
            }
        }
    
    def _load_disclaimers(self) -> Dict[str, str]:
        """Load appropriate disclaimers for each category"""
        return {
            'income_tax': 'Tax laws change frequently. Please verify current rates and rules with official sources or consult a qualified Chartered Accountant for personalized advice.',
            'gst': 'GST rules and rates are subject to change. Always verify with the official GST portal or consult a GST practitioner for compliance matters.',
            'investment': 'Investment advice is for educational purposes only. Past performance doesn\'t guarantee future returns. Please consult SEBI-registered investment advisors for personalized strategies.',
            'business': 'Business advice is general in nature. Specific compliance requirements may vary by state and business type. Consult qualified professionals for your specific situation.',
            'insurance': 'Insurance recommendations are general guidelines. Assess your specific needs and consult licensed insurance advisors before making purchase decisions.',
            'general': 'This is AI-generated financial guidance for educational purposes. Please consult qualified financial professionals for personalized advice and decision-making.'
        }
    
    def _load_context_templates(self) -> Dict[str, str]:
        """Load context templates for different categories"""
        return {
            'income_tax': """
INCOME TAX SPECIALIZATION:
- Current Assessment Year: 2025-26
- Filing Deadline: July 31, 2025
- Standard Deduction: ₹75,000 (New Regime)
- Section 80C Limit: ₹1,50,000
- Always provide specific amounts and deadlines
- Mention both old and new tax regime implications
""",
            'gst': """
GST SPECIALIZATION:
- Current GST rates and slabs
- Registration thresholds: ₹40L goods, ₹20L services
- Filing deadlines: GSTR-1 (11th), GSTR-3B (20th)
- Input Tax Credit rules and conditions
- State-wise variations where applicable
""",
            'investment': """
INVESTMENT SPECIALIZATION:
- Indian mutual fund categories and performance
- SIP strategies and benefits
- Tax-saving investment options (ELSS, PPF, NSC)
- Risk assessment and asset allocation
- Current market trends and economic factors
""",
            'business': """
BUSINESS FINANCE SPECIALIZATION:
- Business registration processes in India
- MSME benefits and schemes
- Working capital management
- Government funding schemes
- Compliance requirements by business type
""",
            'general': """
GENERAL FINANCIAL ADVISORY:
- Comprehensive financial planning approach
- Indian financial products and services
- Budgeting and expense management
- Goal-based financial planning
- Insurance and risk management
"""
        }

# Create global AI instance
finucity_ai = FinucityAI()

def get_ai_response(question: str, category: str = "general", context: Dict = None) -> Dict[str, Any]:
    """
    Main function to get AI response - used by the chat routes
    
    Args:
        question (str): User's question
        category (str): Question category
        context (Dict): Additional context
    
    Returns:
        Dict: AI response with metadata
    """
    return finucity_ai.get_response(question, category, context)

# Additional utility functions for the AI module
def validate_api_key() -> bool:
    """Validate if Groq API key is available and working"""
    return finucity_ai.is_available

def get_model_info() -> Dict[str, Any]:
    """Get information about the current AI model"""
    return {
        'model_name': finucity_ai.model_name,
        'max_tokens': finucity_ai.max_tokens,
        'temperature': finucity_ai.temperature,
        'api_available': finucity_ai.is_available
    }

def get_categories() -> Dict[str, Dict[str, str]]:
    """Get available categories for the frontend"""
    return finucity_ai.categories