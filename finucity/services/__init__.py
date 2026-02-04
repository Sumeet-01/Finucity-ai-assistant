# Finucity Services Package
# This file makes the services directory a Python package

from .ca_ecosystem import CAEcosystemService, ComplaintService, DocumentService
from .income_tax import IncomeTaxService
from .gst import GSTService
from .business_compliance import BusinessComplianceService
from .tax_planning import TaxPlanningService
from .calculators import FinancialCalculators
from .tax_ai import TaxAI

__all__ = [
    'CAEcosystemService', 
    'ComplaintService', 
    'DocumentService',
    'IncomeTaxService',
    'GSTService',
    'BusinessComplianceService',
    'TaxPlanningService',
    'FinancialCalculators',
    'TaxAI'
]

