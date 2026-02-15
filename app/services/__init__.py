"""
PURETEGO CRM - Services Package
"""

from .serpapi_service import SerpApiService
from .pdf_generator import PDFGenerator
from .proposal_service import ProposalService

__all__ = [
    'SerpApiService',
    'PDFGenerator',
    'ProposalService'
]
