import logging
import google.generativeai as genai
from flask import current_app
import os

logger = logging.getLogger(__name__)

class GeminiService:
    def __init__(self):
        self.api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash') # Using Flash as requested
        else:
            self.model = None
            logger.warning("GOOGLE_API_KEY not found. Gemini features disabled.")

    def generate_content(self, prompt):
        if not self.model:
            return "Erro: API Key do Google Gemini não configurada."
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            current_app.logger.error(f"Gemini API Error: {str(e)}")
            return "Desculpe, não consegui gerar o conteúdo no momento. Tente novamente mais tarde."

    def generate_post_suggestion(self, client_name, address, segment=None):
        prompt = f"""
        Você é um especialista em marketing digital para pequenos negócios locais.
        Crie uma sugestão de post para redes sociais (Instagram/Facebook) para o cliente: {client_name}.
        Endereço: {address}.
        Segmento: {segment or 'Geral'}.
        
        O post deve ser engajador, usar emojis, e incluir uma 'Chamada para Ação' (CTA) clara.
        Foque em uma oferta ou novidade semanal.
        """
        return self.generate_content(prompt)

    def generate_faq_suggestion(self, client_name, segment=None):
        prompt = f"""
        Crie uma lista de 5 Perguntas Frequentes (Q&A) relevantes para o perfil do Google Business Profile de: {client_name}.
        Segmento: {segment or 'Comércio Local'}.
        
        Formato:
        1. **Pergunta:** ...
           **Resposta:** ...
        
        As respostas devem ser profissionais e convidar o cliente a visitar ou entrar em contato.
        """
        return self.generate_content(prompt)
