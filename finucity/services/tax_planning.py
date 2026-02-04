"""
Tax Planning & Optimization Services Module
AI-powered tax planning and regime comparison
Author: Sumeet Sangwan
"""

from typing import Dict, List, Optional

class TaxPlanningService:
    """Tax planning and optimization services"""
    
    SERVICES = {
        'TAX_REGIME_ANALYSIS': {
            'name': 'Old vs New Regime Analysis',
            'category': 'tax_planning',
            'sub_category': 'optimization',
            'description': 'AI-powered comparison to choose best tax regime',
            'features': [
                'Detailed comparison',
                'Scenario analysis',
                'Investment suggestions',
                'Personalized recommendations',
                'Tax saving report'
            ],
            'base_price': 999,
            'diy_enabled': True,
            'ca_assisted': False,
            'estimated_days': 1
        },
        'TAX_PLANNING_CONSULTATION': {
            'name': 'Comprehensive Tax Planning',
            'category': 'tax_planning',
            'sub_category': 'planning',
            'description': 'Expert CA creates personalized tax-saving strategy',
            'features': [
                '1-hour CA consultation',
                'Income analysis',
                'Deduction maximization (80C, 80D, etc.)',
                'Investment planning',
                'HRA optimization',
                'Written tax plan'
            ],
            'deliverables': [
                'Tax planning report',
                'Investment roadmap',
                'Month-wise action plan',
                'Expected savings estimate'
            ],
            'base_price': 2999,
            'diy_enabled': False,
            'ca_assisted': True,
            'estimated_days': 3
        },
        'DEDUCTION_DISCOVERY': {
            'name': 'AI Deduction Discovery',
            'category': 'tax_planning',
            'sub_category': 'optimization',
            'description': 'AI scans your profile to find all eligible deductions',
            'features': [
                'Section 80C opportunities',
                'Section 80D medical insurance',
                'HRA calculation',
                'Home loan benefits',
                'NPS benefits',
                'Charity deductions'
            ],
            'base_price': 499,
            'diy_enabled': True,
            'ca_assisted': False,
            'estimated_days': 1
        },
        'HRA_OPTIMIZATION': {
            'name': 'HRA Optimization Service',
            'category': 'tax_planning',
            'sub_category': 'salary',
            'description': 'Maximize your HRA tax benefit',
            'features': [
                'Rent vs HRA analysis',
                'Optimal rent amount suggestion',
                'Documentation guidance',
                'Multiple scenario comparison'
            ],
            'base_price': 299,
            'diy_enabled': True,
            'ca_assisted': False,
            'estimated_days': 1
        },
        'ADVANCE_TAX_PLANNING': {
            'name': 'Advance Tax Planning',
            'category': 'tax_planning',
            'sub_category': 'planning',
            'description': 'Plan and optimize advance tax payments',
            'features': [
                'Income estimation',
                'Quarterly payment calculation',
                'Interest saving tips',
                'Calendar reminders',
                'TDS adjustment'
            ],
            'base_price': 1499,
            'diy_enabled': False,
            'ca_assisted': True,
            'estimated_days': 2
        },
        'INVESTMENT_TAX_PLANNING': {
            'name': 'Investment-Linked Tax Planning',
            'category': 'tax_planning',
            'sub_category': 'investment',
            'description': 'Tax-efficient investment strategy',
            'features': [
                'Tax-saving investment options',
                'ELSS vs PPF vs NPS comparison',
                'Risk-return analysis',
                'Goal-based planning',
                'Portfolio review'
            ],
            'base_price': 1999,
            'diy_enabled': False,
            'ca_assisted': True,
            'estimated_days': 3
        }
    }
    
    @staticmethod
    def get_all_services() -> List[Dict]:
        """Get all tax planning services"""
        services = []
        for code, details in TaxPlanningService.SERVICES.items():
            service = details.copy()
            service['service_code'] = code
            services.append(service)
        return services
    
    @staticmethod
    def compare_tax_regimes(income: float, deductions: Dict) -> Dict:
        """Compare old vs new tax regime"""
        
        # Old regime calculation
        old_regime_tax = TaxPlanningService._calculate_old_regime(income, deductions)
        
        # New regime calculation (no deductions)
        new_regime_tax = TaxPlanningService._calculate_new_regime(income)
        
        difference = old_regime_tax - new_regime_tax
        recommended = 'new' if new_regime_tax < old_regime_tax else 'old'
        
        return {
            'old_regime': {
                'taxable_income': income - sum(deductions.values()),
                'tax_amount': old_regime_tax,
                'effective_rate': (old_regime_tax / income * 100) if income > 0 else 0
            },
            'new_regime': {
                'taxable_income': income,
                'tax_amount': new_regime_tax,
                'effective_rate': (new_regime_tax / income * 100) if income > 0 else 0
            },
            'difference': abs(difference),
            'savings': max(difference, 0),
            'recommended': recommended,
            'recommendation_reason': f'You save ₹{abs(difference):,.0f} with {recommended} regime'
        }
    
    @staticmethod
    def _calculate_old_regime(income: float, deductions: Dict) -> float:
        """Calculate tax under old regime"""
        taxable_income = income - sum(deductions.values())
        
        # Standard deduction (already in deductions)
        # 80C, 80D, etc. (already in deductions)
        
        tax = 0
        if taxable_income <= 250000:
            tax = 0
        elif taxable_income <= 500000:
            tax = (taxable_income - 250000) * 0.05
        elif taxable_income <= 1000000:
            tax = 12500 + (taxable_income - 500000) * 0.20
        else:
            tax = 112500 + (taxable_income - 1000000) * 0.30
        
        # Add cess
        tax = tax * 1.04
        
        return tax
    
    @staticmethod
    def _calculate_new_regime(income: float) -> float:
        """Calculate tax under new regime (FY 2023-24)"""
        tax = 0
        if income <= 300000:
            tax = 0
        elif income <= 600000:
            tax = (income - 300000) * 0.05
        elif income <= 900000:
            tax = 15000 + (income - 600000) * 0.10
        elif income <= 1200000:
            tax = 45000 + (income - 900000) * 0.15
        elif income <= 1500000:
            tax = 90000 + (income - 1200000) * 0.20
        else:
            tax = 150000 + (income - 1500000) * 0.30
        
        # Rebate under 87A if income <= 7 lakhs
        if income <= 700000:
            tax = max(0, tax - 25000)
        
        # Add cess
        tax = tax * 1.04
        
        return tax
    
    @staticmethod
    def calculate_hra_exemption(salary: float, hra_received: float, 
                                rent_paid: float, city_metro: bool) -> Dict:
        """Calculate HRA tax exemption"""
        # Actual HRA received
        actual_hra = hra_received
        
        # Rent paid - 10% of salary
        rent_minus_10 = rent_paid - (0.10 * salary)
        
        # 50% of salary (metro) or 40% (non-metro)
        percentage = 0.50 if city_metro else 0.40
        percentage_salary = salary * percentage
        
        # Minimum of the three
        exemption = min(actual_hra, rent_minus_10, percentage_salary)
        exemption = max(0, exemption)  # Can't be negative
        
        taxable_hra = hra_received - exemption
        
        return {
            'hra_received': hra_received,
            'rent_paid': rent_paid,
            'exemption_amount': exemption,
            'taxable_hra': taxable_hra,
            'tax_saved': exemption * 0.30,  # Assuming 30% tax bracket
            'city_type': 'Metro' if city_metro else 'Non-Metro',
            'recommendation': f'Your HRA exemption is ₹{exemption:,.0f}'
        }
    
    @staticmethod
    def suggest_80c_investments(target_amount: float = 150000, 
                               risk_profile: str = 'moderate') -> List[Dict]:
        """Suggest Section 80C investment options"""
        options = []
        
        if risk_profile == 'conservative':
            options = [
                {'instrument': 'PPF', 'allocation': 0.40, 'amount': target_amount * 0.40, 
                 'returns': '7-8%', 'lock_in': '15 years', 'risk': 'Very Low'},
                {'instrument': 'NSC', 'allocation': 0.30, 'amount': target_amount * 0.30,
                 'returns': '7-7.5%', 'lock_in': '5 years', 'risk': 'Very Low'},
                {'instrument': 'Tax Saver FD', 'allocation': 0.30, 'amount': target_amount * 0.30,
                 'returns': '6-7%', 'lock_in': '5 years', 'risk': 'Very Low'}
            ]
        elif risk_profile == 'moderate':
            options = [
                {'instrument': 'ELSS Mutual Funds', 'allocation': 0.50, 'amount': target_amount * 0.50,
                 'returns': '12-15%', 'lock_in': '3 years', 'risk': 'Moderate'},
                {'instrument': 'PPF', 'allocation': 0.30, 'amount': target_amount * 0.30,
                 'returns': '7-8%', 'lock_in': '15 years', 'risk': 'Very Low'},
                {'instrument': 'Life Insurance', 'allocation': 0.20, 'amount': target_amount * 0.20,
                 'returns': '5-6%', 'lock_in': 'Till maturity', 'risk': 'Low'}
            ]
        else:  # aggressive
            options = [
                {'instrument': 'ELSS Mutual Funds', 'allocation': 0.80, 'amount': target_amount * 0.80,
                 'returns': '12-15%', 'lock_in': '3 years', 'risk': 'Moderate-High'},
                {'instrument': 'NPS', 'allocation': 0.20, 'amount': target_amount * 0.20,
                 'returns': '10-12%', 'lock_in': 'Till 60 years', 'risk': 'Moderate'}
            ]
        
        return options
