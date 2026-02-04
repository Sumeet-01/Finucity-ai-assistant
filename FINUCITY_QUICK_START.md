# FINUCITY - QUICK START GUIDE
# Get Up and Running in 5 Minutes

## 🚀 IMMEDIATE SETUP

### Step 1: Run Database Migration
```bash
# In Supabase SQL Editor, run:
\i database/migrations/004_comprehensive_tax_services.sql

# Or copy-paste the entire file content
```

### Step 2: Test the New Routes
```bash
# Start your Flask app
python app.py

# Test these URLs in browser:
http://localhost:5000/services/
http://localhost:5000/calculators/
http://localhost:5000/calculators/income-tax
```

### Step 3: Verify Everything Works
- ✅ Services home page loads
- ✅ Calculator home page loads
- ✅ Income tax calculator works
- ✅ No import errors

---

## 📁 NEW FILES CREATED

### Core Service Modules:
```
finucity/services/
├── income_tax.py          # 9 ITR services
├── gst.py                 # 8 GST services  
├── business_compliance.py # 9 business services
├── tax_planning.py        # 6 tax planning services
├── calculators.py         # 10 financial calculators
└── tax_ai.py             # AI intelligence layer
```

### Routes:
```
finucity/
└── services_routes.py     # All service & calculator routes
```

### Database:
```
database/migrations/
└── 004_comprehensive_tax_services.sql  # 10 new tables
```

### Templates:
```
finucity/templates/
├── services/
│   └── home.html         # Services homepage
└── calculators/
    ├── home.html         # Calculator directory
    └── income_tax.html   # Income tax calculator
```

### Documentation:
```
COMPREHENSIVE_UPGRADE_COMPLETE.md  # Full documentation
FINUCITY_QUICK_START.md           # This file
```

---

## 🎯 WHAT YOU CAN DO NOW

### 1. Browse Services
- Navigate to `/services/`
- See all service categories
- View service descriptions and pricing

### 2. Use Calculators
- Go to `/calculators/`
- Try the income tax calculator
- Get instant results

### 3. Access APIs
```bash
# Test income tax calculation API
curl -X POST http://localhost:5000/calculators/api/income-tax \
  -H "Content-Type: application/json" \
  -d '{
    "income": 1000000,
    "age_group": "below_60",
    "regime": "new"
  }'
```

### 4. View Service Details
```python
# In Python shell or Jupyter
from finucity.services import IncomeTaxService

# Get all services
services = IncomeTaxService.get_all_services()

# Get specific service
itr_service = IncomeTaxService.get_service_by_code('ITR_SELF_FILE')

# Calculate pricing
pricing = IncomeTaxService.calculate_price('ITR_SELF_FILE', is_urgent=True)
```

---

## 🔑 KEY SERVICE CODES

### Income Tax:
- `ITR_SELF_FILE` - Self ITR (₹499)
- `ITR_CA_ASSISTED` - CA-assisted (₹1,999)
- `ITR_REVISED` - Revised return (₹1,499)
- `CAPITAL_GAINS` - Capital gains (₹2,999)
- `NRI_TAX_FILING` - NRI filing (₹3,499)

### GST:
- `GST_REGISTRATION` - Registration (₹1,999)
- `GST_FILING_MONTHLY` - Monthly filing (₹999)
- `GST_FILING_QUARTERLY` - Quarterly (₹799)

### Business:
- `COMPANY_REGISTRATION` - Pvt Ltd (₹9,999)
- `LLP_REGISTRATION` - LLP (₹7,999)
- `STATUTORY_AUDIT` - Audit (₹15,999+)

---

## 🧮 CALCULATOR USAGE

### Income Tax Calculator:
```python
from finucity.services import FinancialCalculators

calc = FinancialCalculators()

result = calc.income_tax_calculator(
    income=1000000,
    age_group='below_60',
    regime='new'
)

print(f"Total Tax: ₹{result['total_tax']:,.0f}")
print(f"Take Home: ₹{result['take_home']:,.0f}")
```

### HRA Calculator:
```python
hra_result = calc.hra_calculator(
    basic_salary=500000,
    hra_received=200000,
    rent_paid=180000,
    is_metro=True
)

print(f"HRA Exemption: ₹{hra_result['exemption_amount']:,.0f}")
```

### SIP Calculator:
```python
sip_result = calc.sip_calculator(
    monthly_investment=10000,
    expected_return_annual=12,
    tenure_years=10
)

print(f"Maturity Value: ₹{sip_result['maturity_value']:,.0f}")
```

---

## 🤖 AI FEATURES USAGE

### Deduction Discovery:
```python
from finucity.services import TaxAI
from finucity.ai import FinucityAI

ai = FinucityAI()
tax_ai = TaxAI(ai)

user_profile = {
    'age': 30,
    'is_salaried': True,
    'pays_rent': True,
    'city_metro': True,
    'rent_paid': 180000
}

income_data = {
    'total_income': 1200000,
    'deductions': {'80c': 50000},
    'basic_salary': 500000,
    'hra_received': 200000
}

suggestions = tax_ai.suggest_deductions(user_profile, income_data)
print(f"Potential Savings: ₹{suggestions['potential_tax_savings']:,.0f}")
```

### Compliance Check:
```python
user_data = {
    'pan_aadhaar_linked': False,
    'is_nri': False
}

filing_data = {
    'cash_deposits': 500000,
    'form16_tds': 120000,
    'form26as_tds': 125000
}

risks = tax_ai.check_compliance_risks(user_data, filing_data)
print(f"Risk Level: {risks['risk_level']}")
print(f"Critical Risks: {len(risks['critical_risks'])}")
```

---

## 📊 DATABASE QUICK REFERENCE

### Service Catalog:
```sql
-- View all services
SELECT service_code, service_name, category, base_price 
FROM service_catalog 
WHERE is_active = true 
ORDER BY category, base_price;
```

### Service Bookings:
```sql
-- Recent bookings
SELECT booking_number, status, total_amount, created_at 
FROM service_bookings 
ORDER BY created_at DESC 
LIMIT 10;
```

### Calculator History:
```sql
-- Popular calculators
SELECT calculator_type, COUNT(*) as usage_count 
FROM calculator_history 
GROUP BY calculator_type 
ORDER BY usage_count DESC;
```

---

## 🎨 CUSTOMIZATION

### Add New Service:
```python
# In finucity/services/income_tax.py
SERVICES = {
    'NEW_SERVICE_CODE': {
        'name': 'New Service Name',
        'category': 'income_tax',
        'description': '...',
        'features': [...],
        'base_price': 999,
        'diy_enabled': False,
        'ca_assisted': True,
        'estimated_days': 3
    }
}
```

### Add New Calculator:
```python
# In finucity/services/calculators.py
class FinancialCalculators:
    @staticmethod
    def new_calculator(param1: float, param2: str) -> Dict:
        """New calculator logic"""
        result = # ... calculation
        return {
            'input': param1,
            'output': result,
            'explanation': '...'
        }
```

---

## 🐛 TROUBLESHOOTING

### Import Errors:
```bash
# Make sure services __init__.py is updated
cat finucity/services/__init__.py

# Should show all new imports
```

### Database Errors:
```bash
# Check if migration ran successfully
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name LIKE '%service%';

# Should show: service_catalog, service_bookings
```

### Route Not Found:
```python
# Verify blueprint registration in app.py
from finucity.services_routes import services_bp, calculators_bp
app.register_blueprint(services_bp)
app.register_blueprint(calculators_bp)
```

---

## 📱 TESTING ENDPOINTS

### Service APIs:
```bash
# Get all income tax services
curl http://localhost:5000/services/income-tax

# Book a service (requires login)
curl -X POST http://localhost:5000/services/book/ITR_SELF_FILE \
  -H "Content-Type: application/json" \
  -d '{
    "service_type": "diy",
    "is_urgent": false
  }'
```

### Calculator APIs:
```bash
# Income tax
curl -X POST http://localhost:5000/calculators/api/income-tax \
  -H "Content-Type: application/json" \
  -d '{"income": 1000000, "regime": "new", "age_group": "below_60"}'

# HRA
curl -X POST http://localhost:5000/calculators/api/hra \
  -H "Content-Type: application/json" \
  -d '{"basic_salary": 500000, "hra_received": 200000, "rent_paid": 180000, "is_metro": true}'

# SIP
curl -X POST http://localhost:5000/calculators/api/sip \
  -H "Content-Type: application/json" \
  -d '{"monthly_investment": 10000, "expected_return": 12, "tenure_years": 10}'
```

---

## ✅ VERIFICATION CHECKLIST

- [ ] Database migration completed
- [ ] No import errors on startup
- [ ] `/services/` page loads
- [ ] `/calculators/` page loads
- [ ] Income tax calculator works
- [ ] Service booking API responds
- [ ] Calculator APIs return results
- [ ] No console errors
- [ ] Database tables exist
- [ ] RLS policies active

---

## 🎓 NEXT ACTIONS

### Immediate (Today):
1. Run database migration
2. Test all routes
3. Try calculators
4. Review service catalog

### This Week:
1. Complete remaining calculator UIs
2. Build service detail pages
3. Create booking flow
4. Test payment integration

### This Month:
1. Launch services
2. Onboard CAs
3. Marketing campaigns
4. User acquisition

---

## 💡 PRO TIPS

1. **Start with Calculators** - They're ready to use immediately
2. **Test APIs First** - Verify backend before building UI
3. **Use Service Codes** - They're unique identifiers for everything
4. **Check RLS Policies** - Security is built-in
5. **Read Full Docs** - COMPREHENSIVE_UPGRADE_COMPLETE.md has everything

---

## 🔗 USEFUL LINKS

- **Full Documentation:** `COMPREHENSIVE_UPGRADE_COMPLETE.md`
- **Service Catalog:** `/services/`
- **Calculator Home:** `/calculators/`
- **Admin Panel:** `/admin/dashboard`
- **CA Dashboard:** `/ca/dashboard`

---

## 📞 SUPPORT

For issues or questions:
1. Check full documentation
2. Review code comments
3. Test with curl/Postman
4. Check Supabase logs
5. Verify RLS policies

---

**You're Ready to Go! 🚀**

Start with `/services/` and `/calculators/` to see the new platform in action.

---

**Last Updated:** February 4, 2026
**Version:** 2.0.0
