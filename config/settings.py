"""
PURETEGO CRM - Application Settings
Configurações gerais da aplicação
"""

import os
from dotenv import load_dotenv
from datetime import timedelta

load_dotenv()

# Diretório base do projeto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Configurações Flask
class Config:
    """Configurações base da aplicação"""
    
    # Secret key para sessões (ALTERAR EM PRODUÇÃO!)
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Configurações de sessão
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    SESSION_COOKIE_SECURE = False  # Mudar para True em produção com HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Configurações de upload
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max
    ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif'}
    
    # Configurações de PDF
    PDF_OUTPUT_FOLDER = os.path.join(BASE_DIR, 'generated_pdfs')
    
    # Configurações de idioma
    LANGUAGES = {
        'pt': 'Português',
        'es': 'Español'
    }
    DEFAULT_LANGUAGE = 'es'
    
    # API Keys
    SERPAPI_KEY = os.environ.get('SERPAPI_KEY') or ''
    
    # Configurações de email (para futuras implementações)
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'localhost'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    
    # Informações da empresa
    COMPANY_INFO = {
        'name': 'PureteGO Online',
        'website': 'www.puretego.online',
        'email': 'contacto@puretego.online',
        'phone': '+595 983 500 802',
        'address': 'Nepal, cerca de Valencia • Barrio San Luis • San Lorenzo',
        'technical_responsible': 'Janaê Pereira',
        'technical_email': 'janae@puretego.online'
    }
    
    # Critérios do Health Check (17 pontos)
    HEALTH_CHECK_CRITERIA = [
        {
            'id': 1,
            'name_pt': 'Horário de Funcionamento',
            'name_es': 'Horario de Funcionamiento',
            'weight': 6,
            'type': 'critical'
        },
        {
            'id': 2,
            'name_pt': 'Fotos dos Produtos/Serviços',
            'name_es': 'Fotos de Productos/Servicios',
            'weight': 6,
            'type': 'critical'
        },
        {
            'id': 3,
            'name_pt': 'Vídeos',
            'name_es': 'Videos',
            'weight': 6,
            'type': 'critical'
        },
        {
            'id': 4,
            'name_pt': 'Perfil Verificado',
            'name_es': 'Perfil Verificado',
            'weight': 8,
            'type': 'critical'
        },
        {
            'id': 5,
            'name_pt': 'Possui Site',
            'name_es': 'Posee Sitio Web',
            'weight': 7,
            'type': 'critical'
        },
        {
            'id': 6,
            'name_pt': 'Perguntas e Respostas',
            'name_es': 'Preguntas y Respuestas',
            'weight': 5,
            'type': 'critical'
        },
        {
            'id': 7,
            'name_pt': 'Posts/Publicações',
            'name_es': 'Posts/Publicaciones',
            'weight': 6,
            'type': 'critical'
        },
        {
            'id': 8,
            'name_pt': 'Descrição do Negócio',
            'name_es': 'Descripción del Negocio',
            'weight': 7,
            'type': 'critical'
        },
        {
            'id': 9,
            'name_pt': 'Presença nas Redes Sociais',
            'name_es': 'Presencia en Redes Sociales',
            'weight': 5,
            'type': 'moderate'
        },
        {
            'id': 10,
            'name_pt': 'Presença no Google Maps',
            'name_es': 'Presencia en Google Maps',
            'weight': 8,
            'type': 'moderate'
        },
        {
            'id': 11,
            'name_pt': 'Fotos do Exterior',
            'name_es': 'Fotos del Exterior',
            'weight': 4,
            'type': 'moderate'
        },
        {
            'id': 12,
            'name_pt': 'Fotos do Interior',
            'name_es': 'Fotos del Interior',
            'weight': 4,
            'type': 'moderate'
        },
        {
            'id': 13,
            'name_pt': 'Informações de Produtos e Serviços',
            'name_es': 'Información de Productos y Servicios',
            'weight': 6,
            'type': 'moderate'
        },
        {
            'id': 14,
            'name_pt': 'Possui Avaliações',
            'name_es': 'Posee Evaluaciones',
            'weight': 7,
            'type': 'positive'
        },
        {
            'id': 15,
            'name_pt': 'Endereço Configurado',
            'name_es': 'Dirección Configurada',
            'weight': 6,
            'type': 'positive'
        },
        {
            'id': 16,
            'name_pt': 'Possui Logotipo',
            'name_es': 'Posee Logotipo',
            'weight': 5,
            'type': 'positive'
        },
        {
            'id': 17,
            'name_pt': 'Resposta a Avaliações',
            'name_es': 'Respuesta a Evaluaciones',
            'weight': 4,
            'type': 'positive'
        }
    ]


class DevelopmentConfig(Config):
    """Configurações para ambiente de desenvolvimento"""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Configurações para ambiente de produção"""
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True


# Configuração ativa (alterar para ProductionConfig em produção)
config = DevelopmentConfig()
