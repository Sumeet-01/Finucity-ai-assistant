"""
Business Compliance Services Module
Company registration, audit, and compliance services
Author: Sumeet Sangwan
"""

from typing import Dict, List, Optional

class BusinessComplianceService:
    """Handle business registration and compliance services"""
    
    SERVICES = {
        'COMPANY_REGISTRATION': {
            'name': 'Private Limited Company Registration',
            'category': 'business_compliance',
            'sub_category': 'registration',
            'description': 'Complete Pvt Ltd company incorporation',
            'features': [
                'Name reservation (2 options)',
                'DIN & DSC for directors',
                'MOA & AOA drafting',
                'Incorporation certificate',
                'PAN & TAN',
                'Bank account opening support'
            ],
            'deliverables': [
                'Certificate of Incorporation',
                'PAN & TAN',
                'Company Master Data',
                'MOA & AOA',
                'Share certificates'
            ],
            'requirements': [
                'Director KYC (2 minimum)',
                'Registered office proof',
                'Capital details',
                'Business activity'
            ],
            'base_price': 9999,
            'diy_enabled': False,
            'ca_assisted': True,
            'estimated_days': 15
        },
        'LLP_REGISTRATION': {
            'name': 'LLP Registration',
            'category': 'business_compliance',
            'sub_category': 'registration',
            'description': 'Limited Liability Partnership registration',
            'features': [
                'Name approval',
                'DPIN for partners',
                'LLP agreement drafting',
                'PAN & TAN',
                'LLP incorporation'
            ],
            'base_price': 7999,
            'diy_enabled': False,
            'ca_assisted': True,
            'estimated_days': 12
        },
        'STARTUP_COMPLIANCE': {
            'name': 'Startup Compliance Package',
            'category': 'business_compliance',
            'sub_category': 'compliance',
            'description': 'Annual compliance for startups',
            'features': [
                'ROC annual filing',
                'Board meetings (4 per year)',
                'Income tax filing',
                'GST compliance',
                'Statutory audit',
                'Statutory registers maintenance'
            ],
            'base_price': 24999,
            'diy_enabled': False,
            'ca_assisted': True,
            'estimated_days': 365,
            'recurring': 'annual'
        },
        'ROC_ANNUAL_FILING': {
            'name': 'ROC Annual Filing',
            'category': 'business_compliance',
            'sub_category': 'filing',
            'description': 'MCA annual return and financial statement filing',
            'features': [
                'Form AOC-4 filing',
                'Form MGT-7 filing',
                'Digital signature',
                'Late fee calculation (if any)'
            ],
            'base_price': 4999,
            'diy_enabled': False,
            'ca_assisted': True,
            'estimated_days': 7
        },
        'STATUTORY_AUDIT': {
            'name': 'Statutory Audit',
            'category': 'business_compliance',
            'sub_category': 'audit',
            'description': 'Annual statutory audit of accounts',
            'features': [
                'Financial statement audit',
                'Audit report',
                'Tax audit (if required)',
                'Management letter',
                'Compliance review'
            ],
            'base_price': 15999,
            'diy_enabled': False,
            'ca_assisted': True,
            'estimated_days': 20
        },
        'ACCOUNTING_SERVICES': {
            'name': 'Monthly Accounting Services',
            'category': 'business_compliance',
            'sub_category': 'accounting',
            'description': 'Complete bookkeeping and accounting',
            'features': [
                'Daily transaction recording',
                'Bank reconciliation',
                'MIS reports',
                'Financial statements',
                'Expense tracking',
                'Dedicated accountant'
            ],
            'base_price': 4999,
            'diy_enabled': False,
            'ca_assisted': True,
            'estimated_days': 30,
            'recurring': 'monthly'
        },
        'TDS_RETURN_FILING': {
            'name': 'TDS Return Filing',
            'category': 'business_compliance',
            'sub_category': 'tds',
            'description': 'Quarterly TDS return preparation and filing',
            'features': [
                'TDS computation',
                'Form 24Q/26Q/27Q preparation',
                'Return filing',
                'TDS certificates (Form 16/16A)',
                'Payment assistance'
            ],
            'base_price': 1999,
            'diy_enabled': False,
            'ca_assisted': True,
            'estimated_days': 3,
            'recurring': 'quarterly'
        },
        'DIRECTOR_KYC': {
            'name': 'Director KYC (e-KYC)',
            'category': 'business_compliance',
            'sub_category': 'kyc',
            'description': 'Annual director KYC filing',
            'features': [
                'DIR-3 KYC filing',
                'Document verification',
                'OTP-based authentication',
                'Compliance certificate'
            ],
            'base_price': 499,
            'diy_enabled': False,
            'ca_assisted': True,
            'estimated_days': 2
        },
        'COMPANY_CLOSURE': {
            'name': 'Company Strike-off / Closure',
            'category': 'business_compliance',
            'sub_category': 'closure',
            'description': 'Complete company closure process',
            'features': [
                'STK-2 application',
                'Asset & liability settlement',
                'Final returns filing',
                'Strike-off certificate',
                'Bank account closure support'
            ],
            'base_price': 12999,
            'diy_enabled': False,
            'ca_assisted': True,
            'estimated_days': 60
        }
    }
    
    @staticmethod
    def get_all_services() -> List[Dict]:
        """Get all business compliance services"""
        services = []
        for code, details in BusinessComplianceService.SERVICES.items():
            service = details.copy()
            service['service_code'] = code
            services.append(service)
        return services
    
    @staticmethod
    def get_service_by_code(code: str) -> Optional[Dict]:
        """Get specific service by code"""
        if code in BusinessComplianceService.SERVICES:
            service = BusinessComplianceService.SERVICES[code].copy()
            service['service_code'] = code
            return service
        return None
    
    @staticmethod
    def calculate_audit_price(revenue: float, complexity: str = 'simple') -> Dict:
        """Calculate audit price based on revenue and complexity"""
        base_price = 15999
        
        # Revenue-based pricing
        if revenue > 1_00_00_000:  # > 1 crore
            base_price = 25999
        if revenue > 5_00_00_000:  # > 5 crore
            base_price = 49999
        if revenue > 10_00_00_000:  # > 10 crore
            base_price = 79999
        
        # Complexity multiplier
        multipliers = {
            'simple': 1.0,
            'moderate': 1.3,
            'complex': 1.6
        }
        
        final_price = int(base_price * multipliers.get(complexity, 1.0))
        tax_amount = int(final_price * 0.18)
        
        return {
            'base_price': base_price,
            'complexity_adjustment': int(final_price - base_price),
            'subtotal': final_price,
            'tax_amount': tax_amount,
            'total_amount': final_price + tax_amount,
            'currency': 'INR'
        }
    
    @staticmethod
    def get_compliance_checklist(entity_type: str) -> List[Dict]:
        """Get compliance checklist for entity type"""
        checklists = {
            'private_limited': [
                {'task': 'Board Meetings', 'frequency': 'Quarterly', 'penalty': 'Rs 25,000'},
                {'task': 'AGM (Annual General Meeting)', 'frequency': 'Annual', 'penalty': 'Rs 1,00,000'},
                {'task': 'ROC Annual Filing (AOC-4, MGT-7)', 'frequency': 'Annual', 'penalty': 'Rs 100/day'},
                {'task': 'Income Tax Return', 'frequency': 'Annual', 'penalty': 'Interest + Penalty'},
                {'task': 'GST Returns', 'frequency': 'Monthly', 'penalty': 'Late fee + Interest'},
                {'task': 'TDS Returns', 'frequency': 'Quarterly', 'penalty': 'Rs 200/day'},
                {'task': 'Director KYC', 'frequency': 'Annual', 'penalty': 'Rs 5,000'},
                {'task': 'Statutory Audit', 'frequency': 'Annual', 'penalty': 'Penalty + Disqualification'}
            ],
            'llp': [
                {'task': 'Annual Filing (Form 11)', 'frequency': 'Annual', 'penalty': 'Rs 100/day'},
                {'task': 'Income Tax Return', 'frequency': 'Annual', 'penalty': 'Interest + Penalty'},
                {'task': 'GST Returns', 'frequency': 'Monthly', 'penalty': 'Late fee + Interest'},
                {'task': 'Partner KYC', 'frequency': 'Annual', 'penalty': 'Rs 5,000'},
            ],
            'proprietorship': [
                {'task': 'Income Tax Return', 'frequency': 'Annual', 'penalty': 'Interest + Penalty'},
                {'task': 'GST Returns', 'frequency': 'Monthly/Quarterly', 'penalty': 'Late fee + Interest'},
            ]
        }
        
        return checklists.get(entity_type, [])
