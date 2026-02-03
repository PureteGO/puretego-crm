"""
PURETEGO CRM - Flask Application Factory
"""

from flask import Flask, session, g
from config import config, init_db, close_db
import os


def create_app(config_object=None):
    """Factory para criar a aplicação Flask"""
    
    app = Flask(__name__)
    
    # Carregar configurações
    if config_object is None:
        app.config.from_object(config)
    else:
        app.config.from_object(config_object)
    
    # Criar diretórios necessários
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['PDF_OUTPUT_FOLDER'], exist_ok=True)
    
    # Inicializar banco de dados
    with app.app_context():
        # Import models so SQLAlchemy knows about them before creating tables
        from app import models
        init_db()
    
    # Registrar blueprints (rotas)
    from app.routes import auth, clients, visits, proposals, health_checks, dashboard, interactions
    
    app.register_blueprint(auth.bp)
    app.register_blueprint(clients.bp)
    app.register_blueprint(visits.bp)
    app.register_blueprint(proposals.bp)
    app.register_blueprint(health_checks.bp)
    app.register_blueprint(dashboard.bp)
    app.register_blueprint(interactions.bp)
    
    # Registrar função de limpeza
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        close_db()
    
    # Filtros de template personalizados
    @app.template_filter('format_currency')
    def format_currency_filter(value, currency='GS'):
        """Formata valores monetários"""
        if currency == 'GS':
            return f"GS {value:,.0f}".replace(',', '.')
        else:
            return f"R$ {value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    
    @app.template_filter('format_date')
    def format_date_filter(value, format='%d/%m/%Y'):
        """Formata datas"""
        if value:
            return value.strftime(format)
        return ''
    
    # Context processor para variáveis globais
    @app.context_processor
    def inject_globals():
        """Injeta variáveis globais nos templates"""
        return {
            'company_info': app.config['COMPANY_INFO'],
            'current_language': session.get('language', app.config['DEFAULT_LANGUAGE'])
        }
    
    return app
