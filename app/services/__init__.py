"""
PURETEGO CRM - Services Package
"""

from .serpapi_service import SerpApiService
from .pdf_generator import PDFGenerator

__all__ = [
    'SerpApiService',
    'PDFGenerator'
]
