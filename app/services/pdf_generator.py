"""
PURETEGO CRM - PDF Generator Service
Serviço de geração de orçamentos em PDF usando HTML/CSS (xhtml2pdf)
"""

from flask import render_template
from flask_babel import force_locale, gettext as _
from datetime import datetime
import os
import io

# Theme color map
THEME_COLORS = {
    'tech-teal': {
        'primary': '#14b8a6',
        'primary_dark': '#0d9488',
        'primary_light': '#ccfbf1',
        'accent': '#0f766e',
        'bg_dark': '#0a1628',
    },
    'corporate-blue': {
        'primary': '#3b82f6',
        'primary_dark': '#2563eb',
        'primary_light': '#dbeafe',
        'accent': '#1d4ed8',
        'bg_dark': '#0c1527',
    },
    'innovation-purple': {
        'primary': '#8b5cf6',
        'primary_dark': '#7c3aed',
        'primary_light': '#ede9fe',
        'accent': '#6d28d9',
        'bg_dark': '#130c25',
    },
    'energetic-orange': {
        'primary': '#f97316',
        'primary_dark': '#ea580c',
        'primary_light': '#fff7ed',
        'accent': '#c2410c',
        'bg_dark': '#1a0f05',
    },
    'premium-red': {
        'primary': '#ef4444',
        'primary_dark': '#dc2626',
        'primary_light': '#fee2e2',
        'accent': '#b91c1c',
        'bg_dark': '#1a0808',
    },
    'nature-green': {
        'primary': '#22c55e',
        'primary_dark': '#16a34a',
        'primary_light': '#dcfce7',
        'accent': '#15803d',
        'bg_dark': '#071a0e',
    },
    'maps2go-official': {
        'primary': '#14b8a6',
        'primary_dark': '#0d9488',
        'primary_light': '#ccfbf1',
        'accent': '#0f766e',
        'bg_dark': '#08202f',
    },
}


class PDFGenerator:
    """Gerador de orçamentos em PDF moderno usando WeasyPrint e Babel"""
    
    def __init__(self, output_folder=None):
        from config.settings import config
        self.output_folder = output_folder or config.PDF_OUTPUT_FOLDER
        self.company_info = config.COMPANY_INFO
        os.makedirs(self.output_folder, exist_ok=True)
    
    def preview_html(self, proposal_data, language='es', company=None):
        """Gera HTML para visualização no navegador"""
        with force_locale(language):
            context = self._get_context(proposal_data, language, company)
            return render_template('proposals/print.html', **context)

    def generate_proposal_pdf(self, proposal_data, language='es', company=None):
        """Gera PDF usando WeasyPrint"""
        with force_locale(language):
            context = self._get_context(proposal_data, language, company)
            html_content = render_template('proposals/print.html', **context)
            
            # File naming
            date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_name = "".join(
                x for x in proposal_data.get('client_name', 'proposta')
                if x.isalnum() or x in (' ', '_', '-')
            ).replace(' ', '_')
            filename = f"propuesta_{safe_name}_{date_str}.pdf"
            filepath = os.path.join(self.output_folder, filename)
            
            try:
                from weasyprint import HTML
                # WeasyPrint generation
                HTML(string=html_content).write_pdf(filepath)
            except Exception as e:
                # Fallback or clear error message if WeasyPrint fails (e.g. missing libs)
                if "gobject" in str(e).lower() or "cairo" in str(e).lower():
                    raise Exception(
                        "WeasyPrint requirements (GObject/Pango/Cairo) not found on this system. "
                        "Please install GTK+ for Windows or appropriate libraries."
                    )
                raise e
            
            return filepath

    def _get_context(self, proposal_data, language, company=None):
        """Builds the context for the template"""
        # Resolve theme
        theme_style = 'maps2go-official'
        if company and company.get('theme_style'):
            theme_style = company['theme_style']
        theme = THEME_COLORS.get(theme_style, THEME_COLORS['maps2go-official'])
        
        # Merge company
        merged_company = dict(self.company_info)
        if company:
            for key in ['name', 'email', 'phone', 'address', 'logo_url', 'slug']:
                if company.get(key):
                    merged_company[key] = company[key]
        
        return {
            'proposal': proposal_data,
            'company_info': merged_company,
            'theme': theme,
            'language': language,
            'now': datetime.now(),
            'branding_path': '/static/branding',
        }
