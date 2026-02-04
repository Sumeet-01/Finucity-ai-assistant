"""
Financial Calculators Module
Comprehensive tax and financial calculators
Author: Sumeet Sangwan
"""

from typing import Dict, List
import math

class FinancialCalculators:
    """Collection of financial and tax calculators"""
    
    @staticmethod
    def income_tax_calculator(income: float, age_group: str = 'below_60',
                             regime: str = 'new', deductions: Dict = None) -> Dict:
        """
        Calculate income tax
        age_group: 'below_60', '60_to_80', 'above_80'
        regime: 'old', 'new'
        """
        if deductions is None:
            deductions = {}
        
        # Calculate based on regime
        if regime == 'old':
            return FinancialCalculators._old_regime_tax(income, age_group, deductions)
        else:
            return FinancialCalculators._new_regime_tax(income, age_group)
    
    @staticmethod
    def _new_regime_tax(income: float, age_group: str) -> Dict:
        """Calculate tax under new regime"""
        tax = 0
        slabs = []
        
        if income <= 300000:
            tax = 0
            slabs.append({'range': '0 - 3,00,000', 'rate': '0%', 'tax': 0})
        elif income <= 600000:
            tax = (income - 300000) * 0.05
            slabs.append({'range': '0 - 3,00,000', 'rate': '0%', 'tax': 0})
            slabs.append({'range': '3,00,001 - 6,00,000', 'rate': '5%', 'tax': tax})
        elif income <= 900000:
            tax = 15000 + (income - 600000) * 0.10
            slabs.append({'range': '0 - 3,00,000', 'rate': '0%', 'tax': 0})
            slabs.append({'range': '3,00,001 - 6,00,000', 'rate': '5%', 'tax': 15000})
            slabs.append({'range': '6,00,001 - 9,00,000', 'rate': '10%', 'tax': tax - 15000})
        elif income <= 1200000:
            tax = 45000 + (income - 900000) * 0.15
            slabs.append({'range': '0 - 3,00,000', 'rate': '0%', 'tax': 0})
            slabs.append({'range': '3,00,001 - 6,00,000', 'rate': '5%', 'tax': 15000})
            slabs.append({'range': '6,00,001 - 9,00,000', 'rate': '10%', 'tax': 30000})
            slabs.append({'range': '9,00,001 - 12,00,000', 'rate': '15%', 'tax': tax - 45000})
        elif income <= 1500000:
            tax = 90000 + (income - 1200000) * 0.20
            slabs.append({'range': '0 - 3,00,000', 'rate': '0%', 'tax': 0})
            slabs.append({'range': '3,00,001 - 6,00,000', 'rate': '5%', 'tax': 15000})
            slabs.append({'range': '6,00,001 - 9,00,000', 'rate': '10%', 'tax': 30000})
            slabs.append({'range': '9,00,001 - 12,00,000', 'rate': '15%', 'tax': 45000})
            slabs.append({'range': '12,00,001 - 15,00,000', 'rate': '20%', 'tax': tax - 90000})
        else:
            tax = 150000 + (income - 1500000) * 0.30
            slabs.append({'range': '0 - 3,00,000', 'rate': '0%', 'tax': 0})
            slabs.append({'range': '3,00,001 - 6,00,000', 'rate': '5%', 'tax': 15000})
            slabs.append({'range': '6,00,001 - 9,00,000', 'rate': '10%', 'tax': 30000})
            slabs.append({'range': '9,00,001 - 12,00,000', 'rate': '15%', 'tax': 45000})
            slabs.append({'range': '12,00,001 - 15,00,000', 'rate': '20%', 'tax': 60000})
            slabs.append({'range': 'Above 15,00,000', 'rate': '30%', 'tax': tax - 150000})
        
        # Rebate under section 87A
        rebate = 0
        if income <= 700000:
            rebate = min(tax, 25000)
            tax = tax - rebate
        
        # Cess 4%
        cess = tax * 0.04
        total_tax = tax + cess
        
        return {
            'gross_income': income,
            'taxable_income': income,
            'tax_regime': 'New',
            'total_deductions': 0,
            'tax_before_rebate': tax + cess if rebate == 0 else tax + rebate,
            'rebate_87a': rebate,
            'tax_after_rebate': tax,
            'cess_4_percent': cess,
            'total_tax': total_tax,
            'effective_rate': (total_tax / income * 100) if income > 0 else 0,
            'monthly_tax': total_tax / 12,
            'take_home': income - total_tax,
            'tax_slabs': slabs
        }
    
    @staticmethod
    def _old_regime_tax(income: float, age_group: str, deductions: Dict) -> Dict:
        """Calculate tax under old regime"""
        # Standard deduction
        standard_deduction = min(deductions.get('standard_deduction', 50000), 50000)
        
        # Section 80C
        sec_80c = min(deductions.get('80c', 0), 150000)
        
        # Section 80D (Medical insurance)
        sec_80d_limit = 25000 if age_group == 'below_60' else 50000
        sec_80d = min(deductions.get('80d', 0), sec_80d_limit)
        
        # Other deductions
        other_deductions = sum([
            min(deductions.get('80ccd_1b', 0), 50000),  # NPS additional
            deductions.get('80e', 0),  # Education loan interest (no limit)
            min(deductions.get('80g', 0), income * 0.10),  # Donations
            deductions.get('hra', 0),
            deductions.get('home_loan_interest', 0)
        ])
        
        total_deductions = standard_deduction + sec_80c + sec_80d + other_deductions
        taxable_income = max(0, income - total_deductions)
        
        # Tax calculation
        tax = 0
        slabs = []
        
        # Basic exemption based on age
        basic_exemption = 250000
        if age_group == '60_to_80':
            basic_exemption = 300000
        elif age_group == 'above_80':
            basic_exemption = 500000
        
        if taxable_income <= basic_exemption:
            tax = 0
            slabs.append({'range': f'0 - {basic_exemption:,}', 'rate': '0%', 'tax': 0})
        elif taxable_income <= 500000:
            tax = (taxable_income - basic_exemption) * 0.05
            slabs.append({'range': f'0 - {basic_exemption:,}', 'rate': '0%', 'tax': 0})
            slabs.append({'range': f'{basic_exemption+1:,} - 5,00,000', 'rate': '5%', 'tax': tax})
        elif taxable_income <= 1000000:
            tax = (500000 - basic_exemption) * 0.05 + (taxable_income - 500000) * 0.20
            slabs.append({'range': f'0 - {basic_exemption:,}', 'rate': '0%', 'tax': 0})
            slabs.append({'range': f'{basic_exemption+1:,} - 5,00,000', 'rate': '5%', 
                         'tax': (500000 - basic_exemption) * 0.05})
            slabs.append({'range': '5,00,001 - 10,00,000', 'rate': '20%', 
                         'tax': (taxable_income - 500000) * 0.20})
        else:
            tax = ((500000 - basic_exemption) * 0.05 + 500000 * 0.20 + 
                   (taxable_income - 1000000) * 0.30)
            slabs.append({'range': f'0 - {basic_exemption:,}', 'rate': '0%', 'tax': 0})
            slabs.append({'range': f'{basic_exemption+1:,} - 5,00,000', 'rate': '5%', 
                         'tax': (500000 - basic_exemption) * 0.05})
            slabs.append({'range': '5,00,001 - 10,00,000', 'rate': '20%', 'tax': 100000})
            slabs.append({'range': 'Above 10,00,000', 'rate': '30%', 
                         'tax': (taxable_income - 1000000) * 0.30})
        
        # Rebate under section 87A
        rebate = 0
        if taxable_income <= 500000:
            rebate = min(tax, 12500)
            tax = tax - rebate
        
        # Cess 4%
        cess = tax * 0.04
        total_tax = tax + cess
        
        return {
            'gross_income': income,
            'taxable_income': taxable_income,
            'tax_regime': 'Old',
            'total_deductions': total_deductions,
            'deduction_breakdown': {
                'standard_deduction': standard_deduction,
                '80c': sec_80c,
                '80d': sec_80d,
                'other': other_deductions
            },
            'tax_before_rebate': tax + cess if rebate == 0 else tax + rebate,
            'rebate_87a': rebate,
            'tax_after_rebate': tax,
            'cess_4_percent': cess,
            'total_tax': total_tax,
            'effective_rate': (total_tax / income * 100) if income > 0 else 0,
            'monthly_tax': total_tax / 12,
            'take_home': income - total_tax,
            'tax_slabs': slabs
        }
    
    @staticmethod
    def hra_calculator(basic_salary: float, hra_received: float, 
                      rent_paid: float, is_metro: bool) -> Dict:
        """Calculate HRA exemption"""
        # Three conditions for HRA exemption
        actual_hra = hra_received
        rent_minus_10 = max(0, rent_paid - (0.10 * basic_salary))
        percentage = 0.50 if is_metro else 0.40
        percentage_salary = basic_salary * percentage
        
        exemption = min(actual_hra, rent_minus_10, percentage_salary)
        taxable_hra = max(0, hra_received - exemption)
        
        # Tax savings (assuming 30% bracket)
        tax_saved_30 = exemption * 0.30
        tax_saved_20 = exemption * 0.20
        
        return {
            'hra_received': hra_received,
            'rent_paid': rent_paid,
            'basic_salary': basic_salary,
            'is_metro': is_metro,
            'calculations': {
                'actual_hra_received': actual_hra,
                'rent_minus_10_percent_salary': rent_minus_10,
                f'{"50" if is_metro else "40"}_percent_salary': percentage_salary
            },
            'exemption_amount': exemption,
            'taxable_hra': taxable_hra,
            'tax_savings': {
                'at_30_percent_bracket': tax_saved_30,
                'at_20_percent_bracket': tax_saved_20
            },
            'recommendation': 'Optimal rent' if rent_minus_10 == exemption else 'Can optimize rent amount'
        }
    
    @staticmethod
    def capital_gains_calculator(purchase_price: float, sale_price: float,
                                 holding_period_months: int, asset_type: str = 'equity') -> Dict:
        """
        Calculate capital gains tax
        asset_type: 'equity', 'property', 'debt'
        """
        is_long_term = False
        
        # Determine long/short term based on asset type
        if asset_type == 'equity':
            is_long_term = holding_period_months >= 12
        elif asset_type == 'property':
            is_long_term = holding_period_months >= 24
        elif asset_type == 'debt':
            is_long_term = holding_period_months >= 36
        
        capital_gain = sale_price - purchase_price
        
        if capital_gain <= 0:
            return {
                'capital_gain': capital_gain,
                'gain_type': 'Loss',
                'tax': 0,
                'message': 'Capital loss can be set off against capital gains'
            }
        
        tax = 0
        tax_rate = 0
        
        if is_long_term:
            if asset_type == 'equity':
                # LTCG on equity: 10% above 1 lakh
                exemption = 100000
                taxable_gain = max(0, capital_gain - exemption)
                tax = taxable_gain * 0.10
                tax_rate = 10
            elif asset_type == 'property':
                # LTCG on property: 20% with indexation
                # Simplified: using 20% without indexation for now
                tax = capital_gain * 0.20
                tax_rate = 20
            elif asset_type == 'debt':
                # LTCG on debt: 20% with indexation
                tax = capital_gain * 0.20
                tax_rate = 20
        else:
            # Short term capital gains
            if asset_type == 'equity':
                # STCG on equity: 15%
                tax = capital_gain * 0.15
                tax_rate = 15
            else:
                # STCG on other assets: at slab rates (assuming 30%)
                tax = capital_gain * 0.30
                tax_rate = 30
        
        return {
            'purchase_price': purchase_price,
            'sale_price': sale_price,
            'capital_gain': capital_gain,
            'holding_period_months': holding_period_months,
            'asset_type': asset_type,
            'gain_type': 'Long Term' if is_long_term else 'Short Term',
            'tax_rate': f'{tax_rate}%',
            'tax_amount': tax,
            'net_gain': capital_gain - tax,
            'exemptions_available': ['Section 54' if asset_type == 'property' else 'Section 54F']
        }
    
    @staticmethod
    def sip_calculator(monthly_investment: float, expected_return_annual: float,
                      tenure_years: int) -> Dict:
        """Calculate SIP returns"""
        monthly_rate = expected_return_annual / 12 / 100
        total_months = tenure_years * 12
        
        # Future value of SIP
        if monthly_rate == 0:
            future_value = monthly_investment * total_months
        else:
            future_value = monthly_investment * (
                ((1 + monthly_rate) ** total_months - 1) / monthly_rate
            ) * (1 + monthly_rate)
        
        total_invested = monthly_investment * total_months
        total_returns = future_value - total_invested
        
        # Calculate yearly breakdown
        yearly_breakdown = []
        for year in range(1, tenure_years + 1):
            months = year * 12
            if monthly_rate == 0:
                fv = monthly_investment * months
            else:
                fv = monthly_investment * (
                    ((1 + monthly_rate) ** months - 1) / monthly_rate
                ) * (1 + monthly_rate)
            invested = monthly_investment * months
            returns = fv - invested
            
            yearly_breakdown.append({
                'year': year,
                'invested': invested,
                'value': fv,
                'returns': returns
            })
        
        return {
            'monthly_investment': monthly_investment,
            'tenure_years': tenure_years,
            'expected_return': f'{expected_return_annual}%',
            'total_invested': total_invested,
            'total_returns': total_returns,
            'maturity_value': future_value,
            'roi_percentage': (total_returns / total_invested * 100) if total_invested > 0 else 0,
            'yearly_breakdown': yearly_breakdown
        }
    
    @staticmethod
    def gst_calculator(amount: float, gst_rate: float = 18, 
                      calculation_type: str = 'exclusive') -> Dict:
        """
        Calculate GST
        calculation_type: 'exclusive' (add GST) or 'inclusive' (extract GST)
        """
        if calculation_type == 'exclusive':
            # Amount is without GST, add GST
            gst_amount = amount * (gst_rate / 100)
            total = amount + gst_amount
            
            # For CGST + SGST (intra-state) or IGST (inter-state)
            cgst = gst_amount / 2
            sgst = gst_amount / 2
            igst = gst_amount
            
            return {
                'base_amount': amount,
                'gst_rate': f'{gst_rate}%',
                'gst_amount': gst_amount,
                'total_amount': total,
                'breakdown_intra_state': {
                    'cgst': cgst,
                    'sgst': sgst
                },
                'breakdown_inter_state': {
                    'igst': igst
                }
            }
        else:
            # Amount includes GST, extract GST
            base_amount = amount / (1 + gst_rate / 100)
            gst_amount = amount - base_amount
            
            cgst = gst_amount / 2
            sgst = gst_amount / 2
            igst = gst_amount
            
            return {
                'total_amount': amount,
                'base_amount': base_amount,
                'gst_rate': f'{gst_rate}%',
                'gst_amount': gst_amount,
                'breakdown_intra_state': {
                    'cgst': cgst,
                    'sgst': sgst
                },
                'breakdown_inter_state': {
                    'igst': igst
                }
            }
    
    @staticmethod
    def tds_calculator(income: float, tds_section: str = '194J') -> Dict:
        """Calculate TDS based on section"""
        tds_rates = {
            '194J': 0.10,  # Professional services
            '194C': 0.01,  # Contractor payments (individual)
            '194H': 0.05,  # Commission
            '194I': 0.10,  # Rent
            '194M': 0.05,  # Contractor payments (individuals not in business)
        }
        
        rate = tds_rates.get(tds_section, 0.10)
        tds_amount = income * rate
        net_payment = income - tds_amount
        
        return {
            'gross_amount': income,
            'tds_section': tds_section,
            'tds_rate': f'{rate * 100}%',
            'tds_amount': tds_amount,
            'net_payment': net_payment,
            'note': f'TDS deducted under section {tds_section}'
        }
    
    @staticmethod
    def gratuity_calculator(basic_salary: float, years_of_service: float,
                           is_covered: bool = True) -> Dict:
        """Calculate gratuity amount"""
        if years_of_service < 5:
            return {
                'eligible': False,
                'gratuity_amount': 0,
                'message': 'Minimum 5 years of service required for gratuity'
            }
        
        if is_covered:
            # Covered under Gratuity Act
            gratuity = (basic_salary * 15 * years_of_service) / 26
            max_limit = 2000000  # 20 lakhs
            gratuity = min(gratuity, max_limit)
        else:
            # Not covered under Act
            gratuity = (basic_salary * 15 * years_of_service) / 30
        
        # Gratuity is tax-free up to 20 lakhs
        tax_free_limit = 2000000
        taxable_gratuity = max(0, gratuity - tax_free_limit)
        
        return {
            'eligible': True,
            'years_of_service': years_of_service,
            'basic_salary': basic_salary,
            'gratuity_amount': gratuity,
            'tax_free_amount': min(gratuity, tax_free_limit),
            'taxable_amount': taxable_gratuity,
            'formula': f'(Basic Salary × 15 × Years) / {"26" if is_covered else "30"}'
        }
