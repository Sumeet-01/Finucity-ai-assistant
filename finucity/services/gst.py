"""
GST Services Module
Comprehensive GST registration and compliance services
Author: Sumeet Sangwan
"""

from typing import Dict, List, Optional, Any

class GSTService:
    """Handle all GST related services"""
    
    SERVICES = {
        'GST_REGISTRATION': {
            'name': 'GST Registration',
            'category': 'gst',
            'sub_category': 'registration',
            'description': 'Complete GST registration assistance',
            'features': [
                'Document preparation',
                'Application filing',
                'Follow-up support',
                'GSTIN activation tracking',
                'Registration certificate'
            ],
            'deliverables': [
                'GST registration certificate',
                'GSTIN',
                'Login credentials',
                'Compliance calendar'
            ],
            'requirements': [
                'PAN card',
                'Aadhaar card',
                'Business address proof',
                'Bank account details',
                'Business registration proof'
            ],
            'base_price': 1999,
            'diy_enabled': False,
            'ca_assisted': True,
            'estimated_days': 7
        },
        'GST_FILING_MONTHLY': {
            'name': 'GST Monthly Filing',
            'category': 'gst',
            'sub_category': 'filing',
            'description': 'Monthly GST return filing (GSTR-1, GSTR-3B)',
            'features': [
                'Data compilation',
                'GSTR-1 filing',
                'GSTR-3B filing',
                'ITC reconciliation',
                'Payment challan'
            ],
            'base_price': 999,
            'diy_enabled': False,
            'ca_assisted': True,
            'estimated_days': 2,
            'recurring': 'monthly'
        },
        'GST_FILING_QUARTERLY': {
            'name': 'GST Quarterly Filing',
            'category': 'gst',
            'sub_category': 'filing',
            'description': 'Quarterly GST filing for composition scheme',
            'features': [
                'Composition scheme filing',
                'CMP-08 preparation',
                'Tax calculation',
                'Compliance tracking'
            ],
            'base_price': 799,
            'diy_enabled': False,
            'ca_assisted': True,
            'estimated_days': 2,
            'recurring': 'quarterly'
        },
        'GST_ANNUAL_RETURN': {
            'name': 'GST Annual Return (GSTR-9)',
            'category': 'gst',
            'sub_category': 'annual',
            'description': 'Annual GST return and reconciliation',
            'features': [
                'GSTR-9 preparation',
                'Complete reconciliation',
                'Audit support (if applicable)',
                'Tax computation'
            ],
            'base_price': 4999,
            'diy_enabled': False,
            'ca_assisted': True,
            'estimated_days': 10
        },
        'GST_NOTICE_HANDLING': {
            'name': 'GST Notice Response',
            'category': 'gst',
            'sub_category': 'compliance',
            'description': 'Expert response to GST notices',
            'features': [
                'Notice analysis',
                'Response drafting',
                'Documentation',
                'CA representation',
                'Follow-up'
            ],
            'base_price': 3999,
            'diy_enabled': False,
            'ca_assisted': True,
            'estimated_days': 5
        },
        'GST_CONSULTATION': {
            'name': 'GST Consultation',
            'category': 'gst',
            'sub_category': 'advisory',
            'description': 'Expert GST advisory and planning',
            'features': [
                '1-hour CA consultation',
                'Compliance roadmap',
                'ITC optimization',
                'Rate classification advice'
            ],
            'base_price': 1499,
            'diy_enabled': False,
            'ca_assisted': True,
            'estimated_days': 1
        },
        'GST_MODIFICATION': {
            'name': 'GST Registration Modification',
            'category': 'gst',
            'sub_category': 'modification',
            'description': 'Update GST registration details',
            'features': [
                'Business detail updates',
                'Additional place of business',
                'Director/partner changes',
                'Amendment support'
            ],
            'base_price': 1299,
            'diy_enabled': False,
            'ca_assisted': True,
            'estimated_days': 5
        },
        'GST_CANCELLATION': {
            'name': 'GST Cancellation',
            'category': 'gst',
            'sub_category': 'cancellation',
            'description': 'GST registration cancellation',
            'features': [
                'Cancellation application',
                'Final return filing',
                'Documentation',
                'Cancellation certificate'
            ],
            'base_price': 1499,
            'diy_enabled': False,
            'ca_assisted': True,
            'estimated_days': 7
        }
    }
    
    @staticmethod
    def get_all_services() -> List[Dict]:
        """Get all GST services"""
        services = []
        for code, details in GSTService.SERVICES.items():
            service = details.copy()
            service['service_code'] = code
            services.append(service)
        return services
    
    @staticmethod
    def get_service_by_code(code: str) -> Optional[Dict]:
        """Get specific service by code"""
        if code in GSTService.SERVICES:
            service = GSTService.SERVICES[code].copy()
            service['service_code'] = code
            return service
        return None
    
    @staticmethod
    def calculate_price(service_code: str, is_urgent: bool = False, 
                       turnover: Optional[float] = None) -> Dict:
        """Calculate GST service price based on turnover"""
        service = GSTService.get_service_by_code(service_code)
        if not service:
            return {'error': 'Service not found'}
        
        base_price = service['base_price']
        
        # Adjust price based on turnover for filing services
        if turnover and 'FILING' in service_code:
            if turnover > 50_00_000:  # > 50 lakhs
                base_price = int(base_price * 1.5)
            elif turnover > 1_00_00_000:  # > 1 crore
                base_price = int(base_price * 2)
        
        urgent_charges = 0
        if is_urgent:
            urgent_charges = int(base_price * 0.5)
        
        subtotal = base_price + urgent_charges
        tax_amount = int(subtotal * 0.18)
        total = subtotal + tax_amount
        
        return {
            'base_price': base_price,
            'urgent_charges': urgent_charges,
            'subtotal': subtotal,
            'tax_amount': tax_amount,
            'total_amount': total,
            'currency': 'INR'
        }
    
    @staticmethod
    def get_filing_frequency_recommendation(turnover: float) -> str:
        """Recommend filing frequency based on turnover"""
        if turnover <= 20_00_000:  # <= 20 lakhs
            return 'quarterly'  # Composition scheme eligible
        else:
            return 'monthly'  # Regular scheme
    
    @staticmethod
    def check_registration_eligibility(turnover: float, state: str, 
                                      business_type: str) -> Dict:
        """Check if GST registration is required"""
        threshold = 40_00_000  # 40 lakhs for services
        if business_type == 'goods':
            threshold = 40_00_000
        
        # Special category states have lower threshold
        special_states = ['Arunachal Pradesh', 'Manipur', 'Meghalaya', 'Mizoram', 
                         'Nagaland', 'Sikkim', 'Tripura']
        if state in special_states:
            threshold = 20_00_000
        
        required = turnover >= threshold
        
        return {
            'registration_required': required,
            'threshold': threshold,
            'current_turnover': turnover,
            'message': f'GST registration is {"mandatory" if required else "optional"} for your turnover'
        }
