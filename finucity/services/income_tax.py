"""
Income Tax Services Module
Comprehensive ITR filing and tax services
Author: Sumeet Sangwan
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid

class IncomeTaxService:
    """Handle all income tax related services"""
    
    # Service definitions
    SERVICES = {
        'ITR_SELF_FILE': {
            'name': 'Self ITR Filing (AI Guided)',
            'category': 'income_tax',
            'sub_category': 'filing',
            'description': 'File your income tax return yourself with AI guidance',
            'features': [
                'AI-powered form filling',
                'Automatic deduction suggestions',
                'Form 16 auto-parsing',
                'Real-time validation',
                'E-filing support',
                'Acknowledgment tracking'
            ],
            'deliverables': [
                'Filed ITR',
                'Acknowledgment receipt',
                'Tax computation sheet',
                'Refund tracking'
            ],
            'requirements': [
                'PAN card',
                'Aadhaar card',
                'Form 16 (for salaried)',
                'Bank account details',
                'Investment proofs'
            ],
            'base_price': 499,
            'diy_enabled': True,
            'ca_assisted': False,
            'estimated_days': 1
        },
        'ITR_CA_ASSISTED': {
            'name': 'CA-Assisted ITR Filing',
            'category': 'income_tax',
            'sub_category': 'filing',
            'description': 'Expert CA files your ITR with personalized advice',
            'features': [
                'Dedicated CA support',
                'Tax optimization advice',
                'Multiple income sources',
                'Capital gains handling',
                'Notice support (30 days)',
                'Filing consultation'
            ],
            'deliverables': [
                'Filed ITR by certified CA',
                'Tax planning report',
                'Acknowledgment receipt',
                'CA certificate',
                'Post-filing support'
            ],
            'requirements': [
                'PAN card',
                'Aadhaar card',
                'Income documents',
                'Investment proofs',
                'Bank statements'
            ],
            'base_price': 1999,
            'diy_enabled': False,
            'ca_assisted': True,
            'estimated_days': 3
        },
        'ITR_REVISED': {
            'name': 'Revised Return Filing',
            'category': 'income_tax',
            'sub_category': 'filing',
            'description': 'Correct and refile your income tax return',
            'features': [
                'Error correction',
                'Updated information filing',
                'CA review',
                'Compliance check'
            ],
            'base_price': 1499,
            'diy_enabled': False,
            'ca_assisted': True,
            'estimated_days': 2
        },
        'ITR_BELATED': {
            'name': 'Belated Return Filing',
            'category': 'income_tax',
            'sub_category': 'filing',
            'description': 'File return after due date with penalty calculation',
            'features': [
                'Late fee calculation',
                'Interest computation',
                'CA assistance',
                'Penalty optimization'
            ],
            'base_price': 2499,
            'diy_enabled': False,
            'ca_assisted': True,
            'estimated_days': 3
        },
        'CAPITAL_GAINS': {
            'name': 'Capital Gains Filing',
            'category': 'income_tax',
            'sub_category': 'capital_gains',
            'description': 'Expert filing for capital gains from stocks, property, mutual funds',
            'features': [
                'LTCG/STCG calculation',
                'Indexation benefit',
                'Set-off and carry forward',
                'Section 54 exemption guidance'
            ],
            'base_price': 2999,
            'diy_enabled': False,
            'ca_assisted': True,
            'estimated_days': 4
        },
        'TAX_NOTICE_RESPONSE': {
            'name': 'Tax Notice Response',
            'category': 'income_tax',
            'sub_category': 'compliance',
            'description': 'Expert assistance in responding to income tax notices',
            'features': [
                'Notice analysis',
                'Documentation preparation',
                'CA representation',
                'Follow-up support'
            ],
            'base_price': 3999,
            'diy_enabled': False,
            'ca_assisted': True,
            'estimated_days': 7
        },
        'NRI_TAX_FILING': {
            'name': 'NRI Tax Filing',
            'category': 'income_tax',
            'sub_category': 'nri',
            'description': 'Specialized ITR filing for Non-Resident Indians',
            'features': [
                'DTAA benefits',
                'Foreign income reporting',
                'TDS refund',
                'Form 15CA/15CB',
                'Residential status determination'
            ],
            'base_price': 3499,
            'diy_enabled': False,
            'ca_assisted': True,
            'estimated_days': 5
        },
        'BUSINESS_INCOME_FILING': {
            'name': 'Business Income Filing',
            'category': 'income_tax',
            'sub_category': 'business',
            'description': 'ITR for business and professional income',
            'features': [
                'Book-keeping review',
                'Profit & loss preparation',
                'Balance sheet preparation',
                'Presumptive taxation (44AD/44ADA)',
                'Depreciation calculation'
            ],
            'base_price': 4999,
            'diy_enabled': False,
            'ca_assisted': True,
            'estimated_days': 7
        },
        'FREELANCER_FILING': {
            'name': 'Freelancer ITR Filing',
            'category': 'income_tax',
            'sub_category': 'freelancer',
            'description': 'Specialized filing for freelancers and gig workers',
            'features': [
                'Multiple income sources',
                'TDS computation',
                'Advance tax calculation',
                'Expense deductions',
                'Professional tax optimization'
            ],
            'base_price': 2499,
            'diy_enabled': True,
            'ca_assisted': True,
            'estimated_days': 3
        }
    }
    
    @staticmethod
    def get_all_services() -> List[Dict]:
        """Get all income tax services"""
        services = []
        for code, details in IncomeTaxService.SERVICES.items():
            service = details.copy()
            service['service_code'] = code
            services.append(service)
        return services
    
    @staticmethod
    def get_service_by_code(code: str) -> Optional[Dict]:
        """Get specific service by code"""
        if code in IncomeTaxService.SERVICES:
            service = IncomeTaxService.SERVICES[code].copy()
            service['service_code'] = code
            return service
        return None
    
    @staticmethod
    def calculate_price(service_code: str, is_urgent: bool = False, 
                       discount_code: Optional[str] = None) -> Dict:
        """Calculate final price with urgency and discounts"""
        service = IncomeTaxService.get_service_by_code(service_code)
        if not service:
            return {'error': 'Service not found'}
        
        base_price = service['base_price']
        urgent_charges = 0
        discount_amount = 0
        
        if is_urgent:
            urgent_charges = int(base_price * 0.5)  # 50% urgency charge
        
        # Discount logic (can be extended)
        if discount_code == 'FIRST50':
            discount_amount = int((base_price + urgent_charges) * 0.10)  # 10% off
        
        subtotal = base_price + urgent_charges - discount_amount
        tax_amount = int(subtotal * 0.18)  # 18% GST
        total = subtotal + tax_amount
        
        return {
            'base_price': base_price,
            'urgent_charges': urgent_charges,
            'discount_amount': discount_amount,
            'subtotal': subtotal,
            'tax_amount': tax_amount,
            'total_amount': total,
            'currency': 'INR'
        }
    
    @staticmethod
    def get_required_documents(service_code: str) -> List[str]:
        """Get required documents for a service"""
        service = IncomeTaxService.get_service_by_code(service_code)
        if service:
            return service.get('requirements', [])
        return []
    
    @staticmethod
    def get_services_by_user_type(user_type: str) -> List[Dict]:
        """Get services applicable for user type"""
        applicable_services = []
        
        for code, details in IncomeTaxService.SERVICES.items():
            # Logic to filter by user type
            service = details.copy()
            service['service_code'] = code
            
            if user_type == 'individual':
                if code in ['ITR_SELF_FILE', 'ITR_CA_ASSISTED', 'ITR_REVISED', 'CAPITAL_GAINS']:
                    applicable_services.append(service)
            elif user_type == 'business':
                if code in ['BUSINESS_INCOME_FILING', 'ITR_CA_ASSISTED']:
                    applicable_services.append(service)
            elif user_type == 'nri':
                if code in ['NRI_TAX_FILING', 'ITR_CA_ASSISTED']:
                    applicable_services.append(service)
            elif user_type == 'freelancer':
                if code in ['FREELANCER_FILING', 'ITR_SELF_FILE']:
                    applicable_services.append(service)
        
        return applicable_services
    
    @staticmethod
    def validate_eligibility(service_code: str, user_data: Dict) -> Dict:
        """Check if user is eligible for a service"""
        service = IncomeTaxService.get_service_by_code(service_code)
        if not service:
            return {'eligible': False, 'reason': 'Service not found'}
        
        # Basic validation
        if not user_data.get('pan_number'):
            return {'eligible': False, 'reason': 'PAN card is required'}
        
        # Service-specific validation
        if service_code == 'NRI_TAX_FILING':
            if user_data.get('residential_status') != 'non_resident':
                return {'eligible': False, 'reason': 'Only for NRIs'}
        
        return {'eligible': True, 'reason': 'Eligible for service'}
