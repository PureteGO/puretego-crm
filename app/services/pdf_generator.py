"""
PURETEGO CRM - PDF Generator Service
Serviço de geração de orçamentos em PDF usando HTML/CSS (xhtml2pdf)
"""

from flask import render_template
from datetime import datetime
import os
import io


# Theme color map — maps company.theme_style to hex colors for PDF
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
    """Gerador de orçamentos em PDF no estilo PureteGO/Maps2GO (HTML -> PDF)"""
    
    def __init__(self, output_folder=None):
        from config.settings import config
        self.output_folder = output_folder or config.PDF_OUTPUT_FOLDER
        self.company_info = config.COMPANY_INFO
        
        # Criar pasta se não existir
        os.makedirs(self.output_folder, exist_ok=True)
    
    def preview_html(self, proposal_data, language='es', company=None):
        """Gera HTML para visualização (sem PDF)"""
        texts = self._get_texts(language)
        
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
        
        context = {
            'proposal': proposal_data,
            'company_info': merged_company,
            'theme': theme,
            'texts': texts,
            'language': language,
            'language': language,
            'now': datetime.now(),
            'branding_path': '/static/branding',  # Web path for preview
        }
        return render_template('proposals/pdf_template.html', **context)

    def generate_proposal_pdf(self, proposal_data, language='es', company=None):
        """
        Gera um PDF de orçamento a partir de um template HTML.
        proposal_data deve conter:
          - client_name, title, proposal_date, valid_until
          - total_amount, currency, payment_terms
          - options: lista de opções com items (v2)
          - payment_schedule: lista de parcelas (opcional)
          - health_check: dict do health check (opcional)
        company: dict com dados da empresa (name, email, phone, etc.)
        """
        texts = self._get_texts(language)
        
        # Resolve theme colors
        theme_style = 'maps2go-official'
        if company and company.get('theme_style'):
            theme_style = company['theme_style']
        theme = THEME_COLORS.get(theme_style, THEME_COLORS['maps2go-official'])
        
        # Merge company data with default COMPANY_INFO
        merged_company = dict(self.company_info)
        if company:
            for key in ['name', 'email', 'phone', 'address', 'logo_url', 'slug']:
                if company.get(key):
                    merged_company[key] = company[key]
        
        # Nome do arquivo
        date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_name = "".join(
            x for x in proposal_data.get('client_name', 'proposta')
            if x.isalnum() or x in (' ', '_', '-')
        ).replace(' ', '_')
        filename = f"propuesta_{safe_name}_{date_str}.pdf"
        filepath = os.path.join(self.output_folder, filename)
        
        # Absolute path for PDF generation
        base_dir = os.getcwd()
        branding_absolute_path = os.path.join(base_dir, 'app', 'static', 'branding').replace('\\', '/')
        
        # Contexto para o template
        context = {
            'proposal': proposal_data,
            'company_info': merged_company,
            'theme': theme,
            'texts': texts,
            'language': language,
            'now': datetime.now(),
            'branding_path': branding_absolute_path,  # Absolute path for xhtml2pdf
        }
        
        # Renderizar HTML
        html_content = render_template('proposals/pdf_template.html', **context)
        
        try:
            from xhtml2pdf import pisa
        except ImportError:
            raise Exception(
                "Biblioteca PDF (xhtml2pdf) não instalada no servidor. "
                "Instale com: pip install xhtml2pdf"
            )

        # Converter para PDF
        with open(filepath, "w+b") as result_file:
            pisa_status = pisa.CreatePDF(
                io.BytesIO(html_content.encode('utf-8')),
                dest=result_file,
                encoding='utf-8'
            )
            
        if pisa_status.err:
            raise Exception(f"Erro ao gerar PDF: {pisa_status.err}")
        
        return filepath
    
    def _get_texts(self, language):
        """Retorna textos no idioma especificado (es, pt, en)"""
        
        texts = {
            'es': {
                # Cover & headers
                'proposal_title': 'Propuesta Comercial',
                'services_subtitle': 'Presencia Web · Fotos y Videos 360 · GMB · SEO Local',
                'technical_responsible': 'Responsable Técnico',
                'proposal_date': 'Fecha de la Propuesta',
                'valid_until': 'Válido hasta',
                'prepared_for': 'Preparado para',
                'doc_number': 'Nro. Documento',

                # About section
                'section_01': '01',
                'about_label': 'NUESTRO ENFOQUE',
                'about_title': 'Sobre Nosotros',
                'authority_quote': (
                    'Acompañamos la evolución de Google desde sus inicios. Con raíces en Brasil desde 2001, '
                    'nacimos de la necesidad de conectar negocios locales con clientes reales a través de '
                    'datos y resultados auditables.'
                ),
                'about_description': (
                    'Somos especialistas en Geomarketing de Élite. Mientras otros se enfocan en métricas de vanidad, '
                    'nosotros nos obsesionamos con el ROI y la intención de compra directa en Google Search y Google Maps.'
                ),
                'pillar_1_title': 'Transparencia Radical',
                'pillar_1_desc': 'Resultados 100% auditables a través de herramientas oficiales de Google.',
                'pillar_2_title': 'Enfoque en Ventas',
                'pillar_2_desc': 'Optimizamos para el momento exacto en que el cliente busca lo que usted ofrece.',
                'pillar_3_title': 'Datos Reales',
                'pillar_3_desc': 'Sin métricas falsas. Solo datos que impactan directo en su facturación.',
                'pillar_4_title': 'Acompañamiento',
                'pillar_4_desc': 'Seguimiento continuo con reportes mensuales y ajustes estratégicos.',

                # Audit section
                'section_02': '02',
                'audit_label': 'DIAGNÓSTICO',
                'audit_title': 'Auditoría de Perfil Google',
                'audit_subtitle': 'Análisis técnico de su presencia local en Google Maps y Search',
                'score_label': 'Puntuación de Salud GMB',
                'criteria_name': 'Criterio',
                'criteria_status': 'Estado',
                'criteria_type': 'Tipo',
                'detected': 'Detectado',
                'not_detected': 'No detectado',

                # Services section
                'section_03': '03',
                'proposal_label': 'INVERSIÓN',
                'proposal_intro_text': 'Preparamos un plan de acción personalizado para fortalecer la presencia digital de {client_name}:',
                'default_badge': 'Recomendada',
                'service': 'Servicio / Paquete',
                'qty': 'Cant.',
                'unit_price': 'Precio Unit.',
                'discount': 'Desc.',
                'billing': 'Cobro',
                'total': 'Total',
                'recurring': 'Mensual',
                'one_time': 'Único',
                'total_investment': 'Inversión Total',

                # Payment
                'payment_schedule': 'Cronograma de Pagos',
                'due_date': 'Fecha de Vencimiento',
                'description': 'Descripción',
                'amount': 'Monto',
                'payment_terms': 'Forma de Pago',
                'installment': 'Cuota',

                # Notes
                'note_label': 'Nota',
                'additional_text': (
                    'Los precios anteriores incluyen factura legal. Tiempo de ejecución y seguimiento del servicio '
                    'mínimo es de 90 días, debido a pautas de inclusión y cambio de información en las herramientas '
                    'comerciales de Google.'
                ),
                'page_word': 'Página',
                'of_word': 'de',
            },
            'pt': {
                # Cover & headers
                'proposal_title': 'Proposta Comercial',
                'services_subtitle': 'Presença Web · Fotos e Vídeos 360 · GMB · SEO Local',
                'technical_responsible': 'Responsável Técnico',
                'proposal_date': 'Data da Proposta',
                'valid_until': 'Válido até',
                'prepared_for': 'Preparado para',
                'doc_number': 'Nro. Documento',

                # About section
                'section_01': '01',
                'about_label': 'NOSSA ABORDAGEM',
                'about_title': 'Sobre Nós',
                'authority_quote': (
                    'Acompanhamos a evolução do Google desde seus primórdios. Com raízes no Brasil desde 2001, '
                    'nascemos da necessidade de conectar negócios locais com clientes reais através de '
                    'dados e resultados auditáveis.'
                ),
                'about_description': (
                    'Somos especialistas em Geomarketing de Elite. Enquanto outros focam em métricas de vaidade, '
                    'nós nos concentramos no ROI e na intenção de compra direta no Google Search e Google Maps.'
                ),
                'pillar_1_title': 'Transparência Radical',
                'pillar_1_desc': 'Resultados 100% auditáveis através de ferramentas oficiais do Google.',
                'pillar_2_title': 'Foco em Vendas',
                'pillar_2_desc': 'Otimizamos para o momento exato em que o cliente busca o que você oferece.',
                'pillar_3_title': 'Dados Reais',
                'pillar_3_desc': 'Sem métricas falsas. Apenas dados que impactam direto no seu faturamento.',
                'pillar_4_title': 'Acompanhamento',
                'pillar_4_desc': 'Seguimento contínuo com relatórios mensais e ajustes estratégicos.',

                # Audit section
                'section_02': '02',
                'audit_label': 'DIAGNÓSTICO',
                'audit_title': 'Auditoria de Perfil Google',
                'audit_subtitle': 'Análise técnica da sua presença local no Google Maps e Search',
                'score_label': 'Pontuação de Saúde GMB',
                'criteria_name': 'Critério',
                'criteria_status': 'Status',
                'criteria_type': 'Tipo',
                'detected': 'Detectado',
                'not_detected': 'Não detectado',

                # Services section
                'section_03': '03',
                'proposal_label': 'INVESTIMENTO',
                'proposal_intro_text': 'Preparamos um plano de ação personalizado para fortalecer a presença digital de {client_name}:',
                'default_badge': 'Recomendada',
                'service': 'Serviço / Pacote',
                'qty': 'Qtd.',
                'unit_price': 'Preço Unit.',
                'discount': 'Desc.',
                'billing': 'Cobrança',
                'total': 'Total',
                'recurring': 'Mensal',
                'one_time': 'Único',
                'total_investment': 'Investimento Total',

                # Payment
                'payment_schedule': 'Cronograma de Pagamentos',
                'due_date': 'Data de Vencimento',
                'description': 'Descrição',
                'amount': 'Valor',
                'payment_terms': 'Forma de Pagamento',
                'installment': 'Parcela',

                # Notes
                'note_label': 'Nota',
                'additional_text': (
                    'Os preços incluem fatura legal. Tempo de execução e seguimento do serviço '
                    'mínimo é de 90 dias, devido a pautas de inclusão e mudança de informação nas ferramentas '
                    'comerciais do Google.'
                ),
                'page_word': 'Página',
                'of_word': 'de',
            },
            'en': {
                # Cover & headers
                'proposal_title': 'Commercial Proposal',
                'services_subtitle': 'Web Presence · 360 Photos & Videos · GMB · Local SEO',
                'technical_responsible': 'Technical Lead',
                'proposal_date': 'Proposal Date',
                'valid_until': 'Valid Until',
                'prepared_for': 'Prepared for',
                'doc_number': 'Doc. Number',

                # About section
                'section_01': '01',
                'about_label': 'OUR APPROACH',
                'about_title': 'About Us',
                'authority_quote': (
                    'We have been following Google\'s evolution since its early days. With roots in Brazil since 2001, '
                    'we were born from the need to connect local businesses with real customers through '
                    'data and auditable results.'
                ),
                'about_description': (
                    'We are specialists in Elite Geomarketing. While others focus on vanity metrics, '
                    'we obsess over ROI and direct purchase intent on Google Search and Google Maps.'
                ),
                'pillar_1_title': 'Radical Transparency',
                'pillar_1_desc': '100% auditable results through official Google tools.',
                'pillar_2_title': 'Sales Focus',
                'pillar_2_desc': 'We optimize for the exact moment when customers search for what you offer.',
                'pillar_3_title': 'Real Data',
                'pillar_3_desc': 'No fake metrics. Only data that directly impacts your revenue.',
                'pillar_4_title': 'Ongoing Support',
                'pillar_4_desc': 'Continuous monitoring with monthly reports and strategic adjustments.',

                # Audit section
                'section_02': '02',
                'audit_label': 'DIAGNOSIS',
                'audit_title': 'Google Profile Audit',
                'audit_subtitle': 'Technical analysis of your local presence on Google Maps and Search',
                'score_label': 'GMB Health Score',
                'criteria_name': 'Criteria',
                'criteria_status': 'Status',
                'criteria_type': 'Type',
                'detected': 'Detected',
                'not_detected': 'Not detected',

                # Services section
                'section_03': '03',
                'proposal_label': 'INVESTMENT',
                'proposal_intro_text': 'We prepared a customized action plan to strengthen the digital presence of {client_name}:',
                'default_badge': 'Recommended',
                'service': 'Service / Package',
                'qty': 'Qty',
                'unit_price': 'Unit Price',
                'discount': 'Disc.',
                'billing': 'Billing',
                'total': 'Total',
                'recurring': 'Monthly',
                'one_time': 'One-time',
                'total_investment': 'Total Investment',

                # Payment
                'payment_schedule': 'Payment Schedule',
                'due_date': 'Due Date',
                'description': 'Description',
                'amount': 'Amount',
                'payment_terms': 'Payment Terms',
                'installment': 'Installment',

                # Notes
                'note_label': 'Note',
                'additional_text': (
                    'Prices include legal invoice. Minimum execution time and service follow-up is 90 days, '
                    'due to inclusion guidelines and information changes in Google\'s commercial tools.'
                ),
                'page_word': 'Page',
                'of_word': 'of',
            }
        }
        
        return texts.get(language, texts['es'])
