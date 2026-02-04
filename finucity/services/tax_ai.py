"""
Enhanced AI Tax Intelligence Layer
Form 16 parsing, deduction discovery, compliance checking
Author: Sumeet Sangwan
"""

from typing import Dict, List, Optional, Any
import re
from datetime import datetime
from .calculators import FinancialCalculators
from .tax_planning import TaxPlanningService

class TaxAI:
    """AI-powered tax intelligence and advisory"""
    
    def __init__(self, ai_provider):
        """Initialize with existing AI provider (Groq)"""
        self.ai = ai_provider
        self.calculators = FinancialCalculators()
        self.tax_planner = TaxPlanningService()
    
    def parse_form16(self, form16_text: str) -> Dict:
        """
        Parse Form 16 and extract all relevant information
        Uses AI to extract structured data from Form 16 text
        """
        # Create AI prompt for Form 16 parsing
        prompt = f"""
        You are a tax expert. Parse this Form 16 and extract the following information in JSON format:
        
        1. Employee Details:
           - Name
           - PAN
           - Address
           
        2. Employer Details:
           - Name
           - TAN
           - Address
           
        3. Financial Year and Assessment Year
        
        4. Salary Breakdown:
           - Gross Salary
           - Basic Salary
           - HRA
           - Special Allowance
           - Other Allowances
           
        5. Deductions:
           - Standard Deduction
           - Professional Tax
           - Entertainment Allowance
           
        6. Section 80C Investments
        7. Section 80D (Medical Insurance)
        8. Other Chapter VIA Deductions
        
        9. Tax Details:
           - Total Income
           - Total Tax Payable
           - TDS Deducted
           - Relief under 89
           
        Form 16 Text:
        {form16_text}
        
        Return only valid JSON with these fields. If any field is not found, use null.
        """
        
        try:
            # Call AI to parse
            response = self.ai.get_response(
                question=prompt,
                category='tax',
                context={'task': 'form16_parsing'}
            )
            
            # Extract structured data from AI response
            # In production, you'd parse the JSON from AI response
            parsed_data = {
                'status': 'success',
                'employee': {
                    'name': self._extract_field(form16_text, r'Name[:\s]+([A-Za-z\s]+)'),
                    'pan': self._extract_field(form16_text, r'PAN[:\s]+([A-Z]{5}\d{4}[A-Z])'),
                },
                'employer': {
                    'name': self._extract_field(form16_text, r'Employer[:\s]+([A-Za-z\s]+)'),
                    'tan': self._extract_field(form16_text, r'TAN[:\s]+([A-Z]{4}\d{5}[A-Z])'),
                },
                'financial_year': self._extract_field(form16_text, r'F\.?Y\.?\s*(\d{4}-\d{2,4})'),
                'salary_breakdown': self._extract_salary_breakdown(form16_text),
                'deductions': self._extract_deductions(form16_text),
                'tax_summary': self._extract_tax_summary(form16_text),
                'ai_confidence': response.get('confidence_score', 0.8)
            }
            
            return parsed_data
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Failed to parse Form 16: {str(e)}'
            }
    
    def _extract_field(self, text: str, pattern: str) -> Optional[str]:
        """Extract field using regex pattern"""
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(1).strip() if match else None
    
    def _extract_salary_breakdown(self, text: str) -> Dict:
        """Extract salary components"""
        # Simplified extraction logic
        return {
            'gross_salary': self._extract_amount(text, r'Gross\s+Salary[:\s]+₹?\s*([\d,]+)'),
            'basic_salary': self._extract_amount(text, r'Basic\s+Salary[:\s]+₹?\s*([\d,]+)'),
            'hra': self._extract_amount(text, r'HRA[:\s]+₹?\s*([\d,]+)'),
            'special_allowance': self._extract_amount(text, r'Special\s+Allowance[:\s]+₹?\s*([\d,]+)'),
        }
    
    def _extract_deductions(self, text: str) -> Dict:
        """Extract deduction details"""
        return {
            'standard_deduction': self._extract_amount(text, r'Standard\s+Deduction[:\s]+₹?\s*([\d,]+)'),
            '80c': self._extract_amount(text, r'Section\s+80C[:\s]+₹?\s*([\d,]+)'),
            '80d': self._extract_amount(text, r'Section\s+80D[:\s]+₹?\s*([\d,]+)'),
            'professional_tax': self._extract_amount(text, r'Professional\s+Tax[:\s]+₹?\s*([\d,]+)'),
        }
    
    def _extract_tax_summary(self, text: str) -> Dict:
        """Extract tax summary"""
        return {
            'total_income': self._extract_amount(text, r'Total\s+Income[:\s]+₹?\s*([\d,]+)'),
            'tax_payable': self._extract_amount(text, r'Tax\s+Payable[:\s]+₹?\s*([\d,]+)'),
            'tds_deducted': self._extract_amount(text, r'TDS\s+Deducted[:\s]+₹?\s*([\d,]+)'),
        }
    
    def _extract_amount(self, text: str, pattern: str) -> float:
        """Extract amount from text"""
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            amount_str = match.group(1).replace(',', '')
            try:
                return float(amount_str)
            except:
                return 0.0
        return 0.0
    
    def suggest_deductions(self, user_profile: Dict, income_data: Dict) -> Dict:
        """
        AI-powered deduction discovery
        Analyzes user profile and suggests all eligible deductions
        """
        suggestions = []
        total_potential_savings = 0
        
        income = income_data.get('total_income', 0)
        current_deductions = income_data.get('deductions', {})
        
        # Section 80C Analysis (max 1.5 lakhs)
        current_80c = current_deductions.get('80c', 0)
        if current_80c < 150000:
            gap = 150000 - current_80c
            suggestions.append({
                'section': '80C',
                'title': 'Maximize Section 80C Deductions',
                'current': current_80c,
                'maximum': 150000,
                'gap': gap,
                'tax_savings': gap * 0.30,  # Assuming 30% bracket
                'priority': 'high',
                'options': [
                    'ELSS Mutual Funds (3-year lock-in)',
                    'PPF (Long-term, safe)',
                    'EPF (Employer deduction)',
                    'Life Insurance Premium',
                    'NSC (5-year)',
                    'Tax Saver FD (5-year)',
                    'Home Loan Principal',
                    'Sukanya Samriddhi Yojana'
                ],
                'recommendation': 'Invest remaining ₹{:,.0f} before March 31st'.format(gap)
            })
            total_potential_savings += gap * 0.30
        
        # Section 80D - Medical Insurance
        current_80d = current_deductions.get('80d', 0)
        age = user_profile.get('age', 30)
        max_80d = 25000 if age < 60 else 50000
        
        if current_80d < max_80d:
            gap = max_80d - current_80d
            suggestions.append({
                'section': '80D',
                'title': 'Medical Insurance Deduction',
                'current': current_80d,
                'maximum': max_80d,
                'gap': gap,
                'tax_savings': gap * 0.30,
                'priority': 'high',
                'recommendation': f'Buy health insurance worth ₹{gap:,.0f} for your family',
                'note': f'₹{max_80d:,.0f} limit for {"senior citizens" if age >= 60 else "individuals below 60"}'
            })
            total_potential_savings += gap * 0.30
        
        # Section 80CCD(1B) - Additional NPS
        current_nps = current_deductions.get('80ccd_1b', 0)
        if current_nps < 50000:
            gap = 50000 - current_nps
            suggestions.append({
                'section': '80CCD(1B)',
                'title': 'Additional NPS Deduction',
                'current': current_nps,
                'maximum': 50000,
                'gap': gap,
                'tax_savings': gap * 0.30,
                'priority': 'medium',
                'recommendation': 'Invest ₹{:,.0f} in NPS (over and above 80C)'.format(gap),
                'benefit': 'Retirement planning + tax saving'
            })
            total_potential_savings += gap * 0.30
        
        # HRA Exemption
        if user_profile.get('is_salaried') and user_profile.get('pays_rent'):
            hra_received = income_data.get('hra_received', 0)
            if hra_received > 0:
                basic_salary = income_data.get('basic_salary', income * 0.40)
                rent_paid = user_profile.get('rent_paid', 0)
                is_metro = user_profile.get('city_metro', False)
                
                hra_calc = self.calculators.hra_calculator(
                    basic_salary, hra_received, rent_paid, is_metro
                )
                
                suggestions.append({
                    'section': 'HRA',
                    'title': 'House Rent Allowance Exemption',
                    'exemption_amount': hra_calc['exemption_amount'],
                    'tax_savings': hra_calc['tax_savings']['at_30_percent_bracket'],
                    'priority': 'high',
                    'recommendation': hra_calc['recommendation'],
                    'details': hra_calc
                })
                total_potential_savings += hra_calc['tax_savings']['at_30_percent_bracket']
        
        # Section 80E - Education Loan Interest
        if user_profile.get('has_education_loan'):
            suggestions.append({
                'section': '80E',
                'title': 'Education Loan Interest Deduction',
                'maximum': 'No Upper Limit',
                'priority': 'high',
                'recommendation': 'Claim full interest paid on education loan',
                'note': 'Available for 8 years from start of repayment'
            })
        
        # Section 24 - Home Loan Interest
        if user_profile.get('has_home_loan'):
            suggestions.append({
                'section': '24',
                'title': 'Home Loan Interest Deduction',
                'maximum': 200000,
                'tax_savings': 200000 * 0.30,
                'priority': 'high',
                'recommendation': 'Claim up to ₹2,00,000 home loan interest',
                'note': 'For self-occupied property'
            })
        
        # Section 80G - Donations
        suggestions.append({
            'section': '80G',
            'title': 'Donations to Charity',
            'maximum': '10% of income',
            'priority': 'low',
            'recommendation': 'Donations to eligible charities qualify for 50% or 100% deduction',
            'note': 'Get 80G certificate from recipient'
        })
        
        return {
            'total_suggestions': len(suggestions),
            'potential_tax_savings': total_potential_savings,
            'suggestions': suggestions,
            'tax_regime_recommendation': self._recommend_tax_regime(
                income, current_deductions, total_potential_savings
            )
        }
    
    def _recommend_tax_regime(self, income: float, current_deductions: Dict, 
                             potential_savings: float) -> Dict:
        """Recommend old vs new tax regime"""
        total_deductions = sum(current_deductions.values()) + potential_savings
        
        comparison = self.tax_planner.compare_tax_regimes(income, {
            'total': total_deductions
        })
        
        return comparison
    
    def check_compliance_risks(self, user_data: Dict, filing_data: Dict) -> Dict:
        """
        AI-powered compliance risk assessment
        Flags potential issues before filing
        """
        risks = []
        warnings = []
        
        # Check PAN-Aadhaar linking
        if not user_data.get('pan_aadhaar_linked'):
            risks.append({
                'severity': 'high',
                'category': 'documentation',
                'issue': 'PAN-Aadhaar not linked',
                'impact': 'ITR filing may be rejected',
                'action': 'Link PAN with Aadhaar immediately',
                'deadline': 'Before filing'
            })
        
        # Check large cash transactions
        cash_deposits = filing_data.get('cash_deposits', 0)
        if cash_deposits > 1000000:
            warnings.append({
                'severity': 'medium',
                'category': 'cash_transactions',
                'issue': f'Large cash deposits: ₹{cash_deposits:,.0f}',
                'impact': 'May attract scrutiny',
                'action': 'Be ready to explain source of cash',
                'documents_needed': ['Bank statements', 'Source documents']
            })
        
        # Check TDS mismatch
        form16_tds = filing_data.get('form16_tds', 0)
        form26as_tds = filing_data.get('form26as_tds', 0)
        if abs(form16_tds - form26as_tds) > 1000:
            risks.append({
                'severity': 'high',
                'category': 'tds_mismatch',
                'issue': f'TDS mismatch: Form 16 (₹{form16_tds:,.0f}) vs Form 26AS (₹{form26as_tds:,.0f})',
                'impact': 'ITR processing delay or notice',
                'action': 'Reconcile with employer and update Form 16',
                'deadline': 'Before filing'
            })
        
        # Check high-value transactions (AIS/TIS)
        property_purchase = filing_data.get('property_purchase', 0)
        if property_purchase > 3000000:
            warnings.append({
                'severity': 'medium',
                'category': 'high_value_transaction',
                'issue': f'Property purchase: ₹{property_purchase:,.0f}',
                'impact': 'Visible in AIS, ensure proper reporting',
                'action': 'Report in Schedule AL (Assets & Liabilities)',
                'documents_needed': ['Sale deed', 'Payment proof']
            })
        
        # Check foreign assets/income for NRIs
        if user_data.get('is_nri'):
            if not filing_data.get('schedule_fa_filled'):
                risks.append({
                    'severity': 'high',
                    'category': 'foreign_assets',
                    'issue': 'Schedule FA not filled',
                    'impact': 'Mandatory for foreign assets/income',
                    'action': 'Fill Schedule FA for foreign assets',
                    'penalty': 'Up to ₹10 lakhs'
                })
        
        # Check business income without books
        business_income = filing_data.get('business_income', 0)
        if business_income > 0 and not filing_data.get('books_maintained'):
            warnings.append({
                'severity': 'medium',
                'category': 'business_compliance',
                'issue': 'Business income without proper books',
                'impact': 'May need audit if turnover > ₹1 crore',
                'action': 'Maintain proper books of accounts',
                'consider': 'Presumptive taxation under 44AD/44ADA'
            })
        
        # Calculate risk score
        risk_score = len(risks) * 30 + len(warnings) * 10
        risk_level = 'low' if risk_score < 30 else ('medium' if risk_score < 60 else 'high')
        
        return {
            'risk_score': risk_score,
            'risk_level': risk_level,
            'total_issues': len(risks) + len(warnings),
            'critical_risks': risks,
            'warnings': warnings,
            'recommendation': self._get_risk_recommendation(risk_level, risks),
            'pre_filing_checklist': self._generate_checklist(user_data, filing_data)
        }
    
    def _get_risk_recommendation(self, risk_level: str, risks: List) -> str:
        """Get recommendation based on risk level"""
        if risk_level == 'low':
            return '✓ Good to file. No major issues detected.'
        elif risk_level == 'medium':
            return '⚠ Review warnings before filing. Consider CA consultation.'
        else:
            return '🚨 High risk detected. CA assistance strongly recommended.'
    
    def _generate_checklist(self, user_data: Dict, filing_data: Dict) -> List[Dict]:
        """Generate pre-filing checklist"""
        checklist = [
            {'item': 'PAN card', 'status': 'required', 'completed': bool(user_data.get('pan'))},
            {'item': 'Aadhaar card', 'status': 'required', 'completed': bool(user_data.get('aadhaar'))},
            {'item': 'Bank account details', 'status': 'required', 'completed': bool(user_data.get('bank_account'))},
            {'item': 'Form 16 (if salaried)', 'status': 'required_if_salaried', 
             'completed': bool(filing_data.get('form16'))},
            {'item': 'Form 26AS', 'status': 'required', 'completed': bool(filing_data.get('form26as'))},
            {'item': 'AIS/TIS download', 'status': 'recommended', 
             'completed': bool(filing_data.get('ais_tis'))},
            {'item': 'Investment proofs (80C)', 'status': 'required_if_claiming', 
             'completed': bool(filing_data.get('investment_proofs'))},
            {'item': 'Home loan certificate', 'status': 'required_if_applicable', 
             'completed': bool(filing_data.get('home_loan_cert'))},
            {'item': 'Rent receipts (HRA)', 'status': 'required_if_claiming', 
             'completed': bool(filing_data.get('rent_receipts'))},
        ]
        
        return checklist
    
    def generate_tax_tips(self, user_profile: Dict) -> List[Dict]:
        """Generate personalized tax-saving tips"""
        tips = []
        
        # Tip based on income level
        income = user_profile.get('annual_income', 0)
        if income > 1000000:
            tips.append({
                'category': 'tax_planning',
                'title': 'Consider Tax-Saving Investments',
                'description': 'With your income level, maximizing 80C + 80CCD(1B) can save up to ₹60,000 in taxes',
                'potential_saving': 60000,
                'action': 'Invest ₹2,00,000 (₹1.5L in 80C + ₹50K in NPS)'
            })
        
        # Tip for salaried individuals
        if user_profile.get('employment_type') == 'salaried':
            tips.append({
                'category': 'hra',
                'title': 'Optimize Your HRA',
                'description': 'If you pay rent, ensure you claim HRA exemption properly',
                'action': 'Submit rent receipts to employer or claim during ITR filing'
            })
        
        # Tip for investors
        if user_profile.get('has_investments'):
            tips.append({
                'category': 'investment',
                'title': 'Long-term Capital Gains Planning',
                'description': 'LTCG on equity up to ₹1 lakh is tax-free. Plan your selling strategy',
                'action': 'Consider tax-loss harvesting and strategic timing'
            })
        
        # Tip for business owners
        if user_profile.get('has_business'):
            tips.append({
                'category': 'business',
                'title': 'Presumptive Taxation Benefits',
                'description': 'If turnover < ₹2 crore, consider 44AD for simplified compliance',
                'action': 'No need to maintain detailed books or audit'
            })
        
        return tips
