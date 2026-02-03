"""
PURETEGO CRM - PDF Generator Service
Serviço de geração de orçamentos em PDF usando HTML/CSS
"""

from flask import render_template
# from xhtml2pdf import pisa # Moved to inside method
from datetime import datetime
import os
import io

class PDFGenerator:
    """Gerador de orçamentos em PDF no estilo Puretego (HTML -> PDF)"""
    
    def __init__(self, output_folder=None):
        from config.settings import config
        self.output_folder = output_folder or config.PDF_OUTPUT_FOLDER
        self.company_info = config.COMPANY_INFO
        
        # Criar pasta se não existir
        os.makedirs(self.output_folder, exist_ok=True)
    
    def generate_proposal_pdf(self, proposal_data, language='es'):
        """
        Gera um PDF de orçamento a partir de um template HTML
        """
        # Textos bilíngues
        texts = self._get_texts(language)
        
        # Nome do arquivo
        date_str = datetime.now().strftime('%Y%m%d')
        safe_name = "".join(x for x in proposal_data['client_name'] if x.isalnum() or x in (' ', '_', '-')).replace(' ', '_')
        filename = f"propuesta_{safe_name}_{date_str}.pdf"
        filepath = os.path.join(self.output_folder, filename)
        
        # Contexto para o template
        context = {
            'proposal': proposal_data,
            'company_info': self.company_info,
            'texts': texts,
            'language': language,
            'now': datetime.now(),
            'parse_date': lambda d: d if isinstance(d, datetime) else datetime.now() # Helper para segurança
        }
        
        # Renderizar HTML
        html_content = render_template('proposals/pdf_template.html', **context)
        
        try:
            from xhtml2pdf import pisa
        except ImportError:
            raise Exception("Biblioteca PDF (xhtml2pdf) não instalada no servidor. Contate o admin.")

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
        """Retorna textos no idioma especificado"""
        if language == 'pt':
            return {
                'proposal_title': 'Proposta Comercial',
                'services_subtitle': 'Presença Web • Fotos e Vídeos 360<br/>GMB • Google Search • Google Maps',
                'technical_responsible': 'Responsável Técnico',
                'client': 'Cliente',
                'client_info': 'Informações do Cliente',
                'date': 'Data',
                'proposal_date': 'Data da Proposta',
                'valid_until': 'Válido até',
                'service': 'Serviço',
                'price': 'Preço',
                'investment': 'Investimento',
                'total_investment': 'Investimento Total',
                'payment_terms': 'Forma de Pagamento',
                'additional_info': 'Informações Complementares',
                'additional_text': 'Os preços incluem fatura legal, tempo de execução e seguimento do serviço mínimo de 90 dias, devido a pautas de inclusão e mudança de informação nas ferramentas comerciais do Google.',
                'audit_title': 'Auditoria de Perfil Google',
                'audit_subtitle': 'Análise técnica da sua presença local no Google Maps e Search',
                'score_label': 'Pontuação de Saúde GMB',
                'optimization_points': 'Pontos de Otimização',
                'critical_issues': 'Problemas Críticos',
                'moderate_issues': 'Problemas Moderados',
                'positive_points': 'Pontos Positivos'
            }
        else:  # espanhol
            return {
                'proposal_title': 'Propuesta Comercial',
                'services_subtitle': 'Presencia Web • Fotos y Videos 360<br/>GMB • Google Search • Google Maps',
                'technical_responsible': 'Responsable Técnico',
                'client': 'Cliente',
                'client_info': 'Información del Cliente',
                'date': 'Fecha',
                'proposal_date': 'Fecha de la Propuesta',
                'valid_until': 'Válido hasta',
                'service': 'Servicio',
                'price': 'Precio',
                'investment': 'Inversión',
                'total_investment': 'Inversión Total',
                'payment_terms': 'Forma de Pago',
                'additional_info': 'Información Complementaria',
                'additional_text': 'Los precios anteriores incluyen factura legal, tiempo de ejecución y seguimiento del servicio mínimo es de 90 dias, debido a pautas de inclusión y cambio de información en las herramientas comerciales de Google.',
                'audit_title': 'Auditoría de Perfil Google',
                'audit_subtitle': 'Análisis técnico de su presencia local en Google Maps y Search',
                'score_label': 'Puntuación de Salud GMB',
                'optimization_points': 'Puntos de Optimización',
                'critical_issues': 'Problemas Críticos',
                'moderate_issues': 'Problemas Moderados',
                'positive_points': 'Puntos Positivos'
            }
