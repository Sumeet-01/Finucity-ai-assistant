"""
Standalone fallback module for Finucity AI Assistant
This provides responses when the main AI service isn't working
"""

import os
import json
import random
import requests
from datetime import datetime

class FinucityFallback:
    """Fallback AI service for when the primary AI is unavailable"""
    
    def __init__(self):
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        self.model_name = os.getenv("AI_MODEL_NAME", "llama-3.1-8b-instant")
        
        # Log initialization
        print("✅ Fallback AI service initialized")
    
    def get_response(self, question, category="general"):
        """Try to get a response from GROQ API with simplified error handling"""
        
        # First try the API directly with minimal parameters
        if self.groq_api_key:
            try:
                print(f"\n[FALLBACK] Trying direct API call with question: {question[:50]}...")
                
                headers = {
                    "Authorization": f"Bearer {self.groq_api_key}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "model": self.model_name,
                    "messages": [
                        {"role": "system", "content": "You are Finucity AI, a financial advisor. Keep your answers concise."},
                        {"role": "user", "content": question}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 500
                }
                
                response = requests.post(
                    self.api_url,
                    headers=headers,
                    json=payload,
                    timeout=10
                )
                
                if response.status_code == 200:
                    result = response.json()
                    ai_content = result['choices'][0]['message']['content']
                    print("[FALLBACK] API call successful!")
                    
                    return {
                        'success': True,
                        'response': ai_content.strip(),
                        'category': category,
                        'confidence': 0.9,
                        'disclaimer': "This financial advice is for informational purposes only. Consult a professional for personalized guidance.",
                        'model_used': self.model_name
                    }
                else:
                    print(f"[FALLBACK] API error: {response.status_code}, {response.text[:100]}")
            except Exception as e:
                print(f"[FALLBACK] API exception: {str(e)}")
        
        # If API fails or no API key, use hard-coded responses
        print("[FALLBACK] Using hard-coded response")
        fallback_text = self._get_fallback_text(question, category)
        
        return {
            'success': True,
            'response': fallback_text,
            'category': category,
            'confidence': 0.7,
            'disclaimer': "This is a pre-generated response. Online AI service may be unavailable.",
            'model_used': 'fallback'
        }
    
    def _get_fallback_text(self, question, category):
        """Generate a relevant fallback response based on category and question"""
        
        # Common tax responses
        tax_responses = [
            "Based on current tax regulations, Section 80C allows deductions up to ₹1,50,000 for investments in PPF, ELSS mutual funds, life insurance premiums, and other eligible instruments. For AY 2025-26, you should consider maximizing this deduction by diversifying across these options based on your risk profile and financial goals.",
            
            "For AY 2025-26, you can optimize tax savings under Section 80C through these investments:\n\n1. ELSS Mutual Funds: 3-year lock-in with potential for higher returns\n2. PPF: 15-year tenure with tax-free interest (current rate ~7.1%)\n3. Tax-saving FDs: 5-year lock-in with guaranteed returns\n4. NPS: Additional deduction of ₹50,000 under Section 80CCD(1B)\n\nThe best approach is to allocate funds based on your risk tolerance and liquidity needs.",
            
            "Under the current tax laws, you can save tax under Section 80C by investing in:\n\n• PPF (Public Provident Fund)\n• ELSS Mutual Funds\n• National Savings Certificate (NSC)\n• Tax-saving Fixed Deposits\n• Life Insurance Premiums\n• Home Loan Principal Repayment\n\nThe maximum deduction available is ₹1,50,000. I recommend distributing this amount across different instruments based on your financial goals and risk appetite."
        ]
        
        # Common investment responses
        investment_responses = [
            "For long-term wealth creation in India, consider a balanced portfolio with 60-70% allocation to equity (through index funds and diversified mutual funds), 20-30% to debt instruments for stability, and 5-10% to gold as a hedge. With current market conditions, focus on systematic investment plans (SIPs) rather than lump sum investments to average out market volatility.",
            
            "A well-diversified investment portfolio should include:\n\n1. Large-cap funds for stability (40%)\n2. Mid and small-cap funds for growth (30%)\n3. Debt funds for regular income and stability (20%)\n4. Gold and international funds for diversification (10%)\n\nFor tax efficiency, consider ELSS funds for equity exposure and debt funds with indexation benefits for long-term debt allocation.",
            
            "When starting investments in 2025, follow this sequence:\n\n1. First, build an emergency fund covering 6 months of expenses using liquid funds\n2. Secure adequate term life insurance (10-15x annual income) and health insurance\n3. Start SIPs in index funds or diversified equity funds for long-term goals\n4. Consider PPF for tax-efficient debt allocation\n5. For retirement, combine NPS, equity funds, and PPF\n\nReview your portfolio annually and rebalance as needed."
        ]
        
        # Common GST responses
        gst_responses = [
            "GST registration is mandatory for businesses with turnover exceeding ₹40 lakhs (₹20 lakhs in special category states). To register, visit the GST portal (gst.gov.in), complete Form GST REG-01, and submit documents including PAN, address proof, business registration documents, and bank account details. The process typically takes 3-7 working days after document verification.",
            
            "For GSTR-1 filing, follow these steps:\n\n1. Compile all sales invoices for the tax period\n2. Categorize transactions (B2B, B2C, exports, etc.)\n3. Log in to the GST portal and navigate to 'Services > Returns > File Return'\n4. Upload invoice details or enter them manually\n5. Submit the return before the deadline (11th of the following month)\n\nEnsure all invoice details are accurate, as errors can lead to compliance issues and input tax credit rejection for your buyers.",
            
            "Input Tax Credit (ITC) allows businesses to claim credit for GST paid on purchases used for business purposes. Key requirements for claiming ITC:\n\n• The supplier must have filed their returns and paid tax to the government\n• You must have valid tax invoices or debit notes\n• You must have received the goods/services\n• Payment to the supplier must be made within 180 days\n\nMaintain proper documentation to support your ITC claims during GST audits."
        ]
        
        # Common business finance responses
        business_responses = [
            "For a small business startup in India, focus on these key financial areas:\n\n1. Business structure selection (Proprietorship/LLP/Pvt Ltd) based on liability and funding needs\n2. Compliance setup (GST, business registration, industry-specific licenses)\n3. Banking setup with separate business accounts\n4. Accounting system implementation (software like Tally or Zoho Books)\n5. Working capital management with cash flow forecasting\n\nConsider government schemes like MUDRA loans for initial funding if you're eligible.",
            
            "Effective working capital management involves:\n\n• Inventory optimization: Maintain adequate stock without overstocking\n• Accounts receivable management: Clear credit policies and follow-up procedures\n• Accounts payable strategies: Negotiate favorable terms with suppliers\n• Cash management: Forecast cash flows and maintain adequate reserves\n• Short-term financing: Explore options like cash credit, overdraft facilities\n\nReview your working capital cycle monthly and identify bottlenecks for improvement.",
            
            "For business tax planning in FY 2025-26:\n\n1. Ensure timely advance tax payments to avoid interest penalties\n2. Maintain clear segregation between business and personal expenses\n3. Claim depreciation on eligible assets and consider additional depreciation if applicable\n4. Optimize tax-saving investments under Section 80C, 80D, etc.\n5. Consider presumptive taxation scheme under Section 44AD if applicable\n\nConsult a CA to ensure compliance with all tax provisions applicable to your business structure."
        ]
        
        # Determine the most relevant category based on keywords
        question_lower = question.lower()
        
        if category == "tax" or any(term in question_lower for term in ["tax", "section 80", "deduction", "exemption", "itr", "income tax"]):
            return random.choice(tax_responses)
        elif category == "investment" or any(term in question_lower for term in ["invest", "mutual fund", "sip", "portfolio", "stock", "share"]):
            return random.choice(investment_responses)
        elif category == "gst" or any(term in question_lower for term in ["gst", "input tax", "invoice", "gstr", "filing"]):
            return random.choice(gst_responses)
        elif category == "business" or any(term in question_lower for term in ["business", "startup", "company", "entrepreneur"]):
            return random.choice(business_responses)
        else:
            # If no category matches, combine all responses and select one
            all_responses = tax_responses + investment_responses + gst_responses + business_responses
            return random.choice(all_responses)

# Create a singleton instance
fallback_ai = FinucityFallback()

def get_fallback_response(question, category="general"):
    """Helper function to get a fallback response"""
    return fallback_ai.get_response(question, category)