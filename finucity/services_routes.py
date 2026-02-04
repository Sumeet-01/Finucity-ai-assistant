"""
Comprehensive Tax Services Routes
Handles all tax and financial service bookings, calculators, and tools
Author: Sumeet Sangwan
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime
import uuid

from finucity.services import (
    IncomeTaxService,
    GSTService,
    BusinessComplianceService,
    TaxPlanningService,
    FinancialCalculators,
    TaxAI
)
from finucity.database import get_supabase
from finucity.ai import FinucityAI

services_bp = Blueprint('services', __name__, url_prefix='/services')
calculators_bp = Blueprint('calculators', __name__, url_prefix='/calculators')

# Initialize services
income_tax_service = IncomeTaxService()
gst_service = GSTService()
business_service = BusinessComplianceService()
tax_planner = TaxPlanningService()
calculators = FinancialCalculators()

# Initialize AI
finucity_ai = FinucityAI()
tax_ai = TaxAI(finucity_ai)

# =====================================================
# SERVICE CATALOG ROUTES
# =====================================================

@services_bp.route('/')
def service_home():
    """Main services page"""
    return render_template('services/home.html', 
                         page_title='Tax & Financial Services')

@services_bp.route('/income-tax')
def income_tax_services():
    """Income tax services listing"""
    services = income_tax_service.get_all_services()
    return render_template('services/income_tax.html',
                         services=services,
                         page_title='Income Tax Services')

@services_bp.route('/gst')
def gst_services():
    """GST services listing"""
    services = gst_service.get_all_services()
    return render_template('services/gst.html',
                         services=services,
                         page_title='GST Services')

@services_bp.route('/business')
def business_services():
    """Business compliance services"""
    services = business_service.get_all_services()
    return render_template('services/business.html',
                         services=services,
                         page_title='Business Compliance')

@services_bp.route('/tax-planning')
def tax_planning_services():
    """Tax planning services"""
    services = tax_planner.get_all_services()
    return render_template('services/tax_planning.html',
                         services=services,
                         page_title='Tax Planning')

# =====================================================
# SERVICE DETAIL & BOOKING
# =====================================================

@services_bp.route('/<service_code>')
def service_detail(service_code):
    """Service detail page"""
    # Try to get service from all categories
    service = (income_tax_service.get_service_by_code(service_code) or
              gst_service.get_service_by_code(service_code) or
              business_service.get_service_by_code(service_code) or
              tax_planner.get_service_by_code(service_code))
    
    if not service:
        flash('Service not found', 'error')
        return redirect(url_for('services.service_home'))
    
    return render_template('services/detail.html',
                         service=service,
                         page_title=service['name'])

@services_bp.route('/book/<service_code>', methods=['GET', 'POST'])
@login_required
def book_service(service_code):
    """Book a service"""
    service = (income_tax_service.get_service_by_code(service_code) or
              gst_service.get_service_by_code(service_code) or
              business_service.get_service_by_code(service_code) or
              tax_planner.get_service_by_code(service_code))
    
    if not service:
        return jsonify({'error': 'Service not found'}), 404
    
    if request.method == 'POST':
        try:
            data = request.json
            is_urgent = data.get('is_urgent', False)
            service_type = data.get('service_type', 'ca_assisted')
            
            # Calculate pricing
            pricing = income_tax_service.calculate_price(service_code, is_urgent)
            
            # Generate booking number
            booking_number = f"FIN-{service_code}-{datetime.now().year}-{str(uuid.uuid4())[:8].upper()}"
            
            # Create booking in database
            supabase = get_supabase()
            
            # First, get service_id from catalog (or create if not exists)
            service_catalog_entry = {
                'service_code': service_code,
                'service_name': service['name'],
                'display_name': service['name'],
                'category': service['category'],
                'sub_category': service.get('sub_category'),
                'base_price': service['base_price'],
                'is_diy_enabled': service.get('diy_enabled', False),
                'is_ca_assisted': service.get('ca_assisted', True),
                'estimated_days': service.get('estimated_days'),
            }
            
            # Insert or get service catalog entry
            catalog_result = supabase.table('service_catalog').upsert(
                service_catalog_entry,
                on_conflict='service_code'
            ).execute()
            
            service_id = catalog_result.data[0]['id'] if catalog_result.data else None
            
            # Create booking
            booking_data = {
                'booking_number': booking_number,
                'user_id': current_user.id,
                'service_id': service_id,
                'service_type': service_type,
                'is_urgent': is_urgent,
                'status': 'pending',
                'base_amount': pricing['base_price'],
                'urgent_charges': pricing['urgent_charges'],
                'discount_amount': pricing['discount_amount'],
                'tax_amount': pricing['tax_amount'],
                'total_amount': pricing['total_amount'],
                'payment_status': 'pending'
            }
            
            result = supabase.table('service_bookings').insert(booking_data).execute()
            
            if result.data:
                booking = result.data[0]
                return jsonify({
                    'success': True,
                    'booking_id': booking['id'],
                    'booking_number': booking_number,
                    'total_amount': pricing['total_amount'],
                    'redirect_url': url_for('services.booking_payment', 
                                          booking_id=booking['id'])
                })
            else:
                return jsonify({'error': 'Failed to create booking'}), 500
                
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return render_template('services/book.html',
                         service=service,
                         page_title=f'Book {service["name"]}')

@services_bp.route('/booking/<booking_id>/payment')
@login_required
def booking_payment(booking_id):
    """Payment page for booking"""
    try:
        supabase = get_supabase()
        result = supabase.table('service_bookings')\
            .select('*, service_catalog(*)')\
            .eq('id', booking_id)\
            .eq('user_id', current_user.id)\
            .single()\
            .execute()
        
        if result.data:
            booking = result.data
            return render_template('services/payment.html',
                                 booking=booking,
                                 page_title='Payment')
        else:
            flash('Booking not found', 'error')
            return redirect(url_for('services.my_bookings'))
            
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('services.my_bookings'))

@services_bp.route('/my-bookings')
@login_required
def my_bookings():
    """User's service bookings"""
    try:
        supabase = get_supabase()
        result = supabase.table('service_bookings')\
            .select('*, service_catalog(*)')\
            .eq('user_id', current_user.id)\
            .order('created_at', desc=True)\
            .execute()
        
        bookings = result.data if result.data else []
        
        return render_template('services/my_bookings.html',
                             bookings=bookings,
                             page_title='My Bookings')
    except Exception as e:
        flash(f'Error loading bookings: {str(e)}', 'error')
        return render_template('services/my_bookings.html',
                             bookings=[],
                             page_title='My Bookings')

# =====================================================
# CALCULATOR ROUTES
# =====================================================

@calculators_bp.route('/')
def calculator_home():
    """All calculators listing"""
    calculator_list = [
        {'id': 'income-tax', 'name': 'Income Tax Calculator', 'icon': '💰', 'popular': True},
        {'id': 'hra', 'name': 'HRA Calculator', 'icon': '🏠', 'popular': True},
        {'id': 'capital-gains', 'name': 'Capital Gains Calculator', 'icon': '📈', 'popular': True},
        {'id': 'sip', 'name': 'SIP Calculator', 'icon': '💵', 'popular': True},
        {'id': 'gst', 'name': 'GST Calculator', 'icon': '🧾', 'popular': False},
        {'id': 'tds', 'name': 'TDS Calculator', 'icon': '📊', 'popular': False},
        {'id': 'gratuity', 'name': 'Gratuity Calculator', 'icon': '💼', 'popular': False},
        {'id': 'tax-regime', 'name': 'Tax Regime Comparison', 'icon': '⚖️', 'popular': True},
    ]
    
    return render_template('calculators/home.html',
                         calculators=calculator_list,
                         page_title='Financial Calculators')

@calculators_bp.route('/income-tax')
def income_tax_calculator():
    """Income tax calculator page"""
    return render_template('calculators/income_tax.html',
                         page_title='Income Tax Calculator')

@calculators_bp.route('/api/income-tax', methods=['POST'])
def calculate_income_tax():
    """API: Calculate income tax"""
    try:
        data = request.json
        result = calculators.income_tax_calculator(
            income=float(data.get('income', 0)),
            age_group=data.get('age_group', 'below_60'),
            regime=data.get('regime', 'new'),
            deductions=data.get('deductions', {})
        )
        
        # Save to history if user logged in
        if current_user.is_authenticated:
            try:
                supabase = get_supabase()
                supabase.table('calculator_history').insert({
                    'user_id': current_user.id,
                    'calculator_type': 'income_tax',
                    'input_data': data,
                    'output_data': result,
                    'financial_year': '2024-25'
                }).execute()
            except:
                pass  # Don't fail if history save fails
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@calculators_bp.route('/hra')
def hra_calculator():
    """HRA calculator page"""
    return render_template('calculators/hra.html',
                         page_title='HRA Calculator')

@calculators_bp.route('/api/hra', methods=['POST'])
def calculate_hra():
    """API: Calculate HRA"""
    try:
        data = request.json
        result = calculators.hra_calculator(
            basic_salary=float(data.get('basic_salary', 0)),
            hra_received=float(data.get('hra_received', 0)),
            rent_paid=float(data.get('rent_paid', 0)),
            is_metro=data.get('is_metro', False)
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@calculators_bp.route('/capital-gains')
def capital_gains_calculator():
    """Capital gains calculator page"""
    return render_template('calculators/capital_gains.html',
                         page_title='Capital Gains Calculator')

@calculators_bp.route('/api/capital-gains', methods=['POST'])
def calculate_capital_gains():
    """API: Calculate capital gains"""
    try:
        data = request.json
        result = calculators.capital_gains_calculator(
            purchase_price=float(data.get('purchase_price', 0)),
            sale_price=float(data.get('sale_price', 0)),
            holding_period_months=int(data.get('holding_period_months', 0)),
            asset_type=data.get('asset_type', 'equity')
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@calculators_bp.route('/sip')
def sip_calculator():
    """SIP calculator page"""
    return render_template('calculators/sip.html',
                         page_title='SIP Calculator')

@calculators_bp.route('/api/sip', methods=['POST'])
def calculate_sip():
    """API: Calculate SIP returns"""
    try:
        data = request.json
        result = calculators.sip_calculator(
            monthly_investment=float(data.get('monthly_investment', 0)),
            expected_return_annual=float(data.get('expected_return', 12)),
            tenure_years=int(data.get('tenure_years', 10))
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@calculators_bp.route('/gst')
def gst_calculator():
    """GST calculator page"""
    return render_template('calculators/gst.html',
                         page_title='GST Calculator')

@calculators_bp.route('/api/gst', methods=['POST'])
def calculate_gst():
    """API: Calculate GST"""
    try:
        data = request.json
        result = calculators.gst_calculator(
            amount=float(data.get('amount', 0)),
            gst_rate=float(data.get('gst_rate', 18)),
            calculation_type=data.get('calculation_type', 'exclusive')
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@calculators_bp.route('/tds')
def tds_calculator():
    """TDS calculator page"""
    return render_template('calculators/tds.html',
                         page_title='TDS Calculator')

@calculators_bp.route('/api/tds', methods=['POST'])
def calculate_tds():
    """API: Calculate TDS"""
    try:
        data = request.json
        result = calculators.tds_calculator(
            income=float(data.get('income', 0)),
            tds_section=data.get('tds_section', '194J')
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@calculators_bp.route('/gratuity')
def gratuity_calculator():
    """Gratuity calculator page"""
    return render_template('calculators/gratuity.html',
                         page_title='Gratuity Calculator')

@calculators_bp.route('/api/gratuity', methods=['POST'])
def calculate_gratuity():
    """API: Calculate gratuity"""
    try:
        data = request.json
        result = calculators.gratuity_calculator(
            basic_salary=float(data.get('basic_salary', 0)),
            years_of_service=float(data.get('years_of_service', 0)),
            is_covered=data.get('is_covered', True)
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@calculators_bp.route('/tax-regime')
def tax_regime_calculator():
    """Tax regime comparison calculator"""
    return render_template('calculators/tax_regime.html',
                         page_title='Old vs New Tax Regime')

@calculators_bp.route('/api/tax-regime', methods=['POST'])
def compare_tax_regime():
    """API: Compare tax regimes"""
    try:
        data = request.json
        result = tax_planner.compare_tax_regimes(
            income=float(data.get('income', 0)),
            deductions=data.get('deductions', {})
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# =====================================================
# AI-POWERED FEATURES
# =====================================================

@services_bp.route('/ai/deduction-discovery', methods=['POST'])
@login_required
def ai_deduction_discovery():
    """AI-powered deduction discovery"""
    try:
        data = request.json
        
        # Get user profile
        user_profile = {
            'age': data.get('age', 30),
            'is_salaried': data.get('is_salaried', True),
            'pays_rent': data.get('pays_rent', False),
            'has_home_loan': data.get('has_home_loan', False),
            'has_education_loan': data.get('has_education_loan', False),
            'city_metro': data.get('city_metro', False),
            'rent_paid': data.get('rent_paid', 0)
        }
        
        income_data = {
            'total_income': float(data.get('income', 0)),
            'deductions': data.get('current_deductions', {}),
            'basic_salary': float(data.get('basic_salary', 0)),
            'hra_received': float(data.get('hra_received', 0))
        }
        
        result = tax_ai.suggest_deductions(user_profile, income_data)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@services_bp.route('/ai/compliance-check', methods=['POST'])
@login_required
def ai_compliance_check():
    """AI-powered compliance risk assessment"""
    try:
        data = request.json
        
        user_data = {
            'pan_aadhaar_linked': data.get('pan_aadhaar_linked', False),
            'is_nri': data.get('is_nri', False)
        }
        
        filing_data = {
            'cash_deposits': float(data.get('cash_deposits', 0)),
            'form16_tds': float(data.get('form16_tds', 0)),
            'form26as_tds': float(data.get('form26as_tds', 0)),
            'property_purchase': float(data.get('property_purchase', 0)),
            'business_income': float(data.get('business_income', 0)),
            'books_maintained': data.get('books_maintained', False),
            'schedule_fa_filled': data.get('schedule_fa_filled', False),
            'form16': data.get('form16'),
            'form26as': data.get('form26as'),
            'ais_tis': data.get('ais_tis')
        }
        
        result = tax_ai.check_compliance_risks(user_data, filing_data)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@services_bp.route('/ai/tax-tips')
@login_required
def ai_tax_tips():
    """Get personalized AI tax tips"""
    try:
        # Get user profile from database
        supabase = get_supabase()
        profile = supabase.table('tax_profiles')\
            .select('*')\
            .eq('user_id', current_user.id)\
            .single()\
            .execute()
        
        user_profile = profile.data if profile.data else {}
        
        tips = tax_ai.generate_tax_tips(user_profile)
        
        return jsonify({'tips': tips})
    except Exception as e:
        return jsonify({'error': str(e)}), 400
