"""
MAPS2GO CRM - Flask Application Factory
"""

from flask import Flask, session, g, request, redirect, url_for
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_babel import Babel, gettext as _, lazy_gettext as _l
from flask_wtf.csrf import CSRFProtect
from config import config, init_db, close_db
import os


# Initialize extensions
babel = Babel()
csrf = CSRFProtect()


def get_locale():
    """Select best language from user preferences"""
    # Check if user has a language preference in session
    if 'language' in session:
        return session['language']
    # Otherwise try to detect from browser
    return request.accept_languages.best_match(['pt_BR', 'es', 'en'], default='es')


def create_app(config_object=None):
    """Factory para criar a aplicação Flask"""
    
    app = Flask(__name__, 
                template_folder='templates',
                static_folder='static',
                static_url_path='/static')
    
    # Carregar configurações
    if config_object is None:
        app.config.from_object(config)
    else:
        app.config.from_object(config_object)
    
    # Configure ProxyFix for production (correct proto/host behind proxy)
    if app.config.get('FLASK_ENV') == 'production':
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
    
    # Babel configuration
    app.config['BABEL_DEFAULT_LOCALE'] = 'es'
    app.config['BABEL_SUPPORTED_LOCALES'] = ['pt_BR', 'es', 'en']
    # Use absolute path to ensure translations are found in production
    app.config['BABEL_TRANSLATION_DIRECTORIES'] = os.path.join(app.root_path, 'translations')
    
    # Initialize Babel
    babel.init_app(app, locale_selector=get_locale)
    
    # Initialize CSRF protection
    csrf.init_app(app)
    
    # Security headers
    @app.after_request
    def add_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        return response
    
    # Criar diretórios necessários
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['PDF_OUTPUT_FOLDER'], exist_ok=True)
    
    # Inicializar banco de dados
    with app.app_context():
        from app import models
        init_db()
    
    # Registrar blueprints (rotas)
    from app.routes import auth, dashboard, users, clients, interactions, visits, health_checks, proposals, google_oauth, saas, calendar, prospecting, company, projects, tasks, finance, services, notifications
    
    app.register_blueprint(auth.bp)
    app.register_blueprint(dashboard.bp)
    app.register_blueprint(users.bp)
    app.register_blueprint(clients.bp)
    app.register_blueprint(clients.api_bp)  # API for clients
    app.register_blueprint(interactions.bp)
    app.register_blueprint(visits.bp)
    app.register_blueprint(health_checks.bp)
    app.register_blueprint(proposals.bp)
    app.register_blueprint(google_oauth.bp)
    app.register_blueprint(saas.bp)
    app.register_blueprint(calendar.bp)
    app.register_blueprint(prospecting.bp)
    app.register_blueprint(company.bp)
    app.register_blueprint(projects.bp)
    app.register_blueprint(tasks.bp)
    app.register_blueprint(tasks.api_bp)
    app.register_blueprint(finance.bp)
    app.register_blueprint(services.bp)
    app.register_blueprint(notifications.bp)
    
    # Language switching route
    @app.route('/set-language/<lang>')
    def set_language(lang):
        """Set user's preferred language"""
        if lang in ['pt_BR', 'es', 'en']:
            session['language'] = lang
        return redirect(request.referrer or url_for('dashboard.index'))
    
    # Registrar função de limpeza
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        close_db()
    
    # Filtros de template personalizados
    @app.template_filter('format_currency')
    def format_currency_filter(value):
        """Formata valores monetários usando a moeda da sessão"""
        currency = session.get('company_currency', 'Gs')
        
        if value is None:
            value = 0
            
        try:
            val_float = float(value)
        except (ValueError, TypeError):
            return f"{currency} 0"

        # Formatação básica: inteiros para valores altos (ex: Guaranis), decimais para outros
        if val_float.is_integer():
            formatted_val = f"{val_float:,.0f}".replace(',', '.')
        else:
            formatted_val = f"{val_float:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            
        return f"{currency} {formatted_val}"
    
    @app.template_filter('format_date')
    def format_date_filter(value, format='%d/%m/%Y'):
        """Formata datas"""
        if value:
            # Check for %p and convert to lowercase if needed (for 'am/pm' vs 'AM/PM')
            formatted = value.strftime(format)
            if '%p' in format:
                # Some users want lowercase AM/PM
                return formatted.replace('AM', 'am').replace('PM', 'pm')
            return formatted
        return ''
    
    # Context processor para variáveis globais
    @app.context_processor
    def inject_globals():
        """Injeta variáveis globais nos templates"""
        current_lang = get_locale()
        lang_info = {
            'pt_BR': {'name': 'Português', 'flag': '🇧🇷'},
            'es': {'name': 'Español', 'flag': '🇪🇸'},
            'en': {'name': 'English', 'flag': '🇺🇸'}
        }
        from app.utils.decorators import get_current_user
        from app.models import Interaction, Visit, Task
        from sqlalchemy import func
        from datetime import datetime
        
        user = None
        overdue_count = 0
        unread_notifications = 0
        
        try:
            user = get_current_user()
            if user:
                from config.database import db_session
                from sqlalchemy import or_
                # Count overdue scheduled interactions
                overdue_count = db_session.query(func.count(Interaction.id)).filter(
                    Interaction.user_id == session.get('user_id'),
                    Interaction.status == 'scheduled',
                    Interaction.date < datetime.now()
                ).scalar() or 0
                
                # Add overdue Tasks for this user/role
                task_overdue = db_session.query(func.count(Task.id)).filter(
                    Task.company_id == session.get('company_id'),
                    Task.status.in_(['open', 'in_progress']),
                    Task.due_date < datetime.now(),
                    or_(Task.assigned_to_id == user.id, (Task.assigned_to_id.is_(None)) & (Task.role_target == (user.role.name if user.role else 'sales')))
                ).scalar() or 0
                
                overdue_count += task_overdue
                
                # Count unread notifications
                from app.models import Notification
                unread_notifications = db_session.query(func.count(Notification.id)).filter(
                    Notification.user_id == user.id,
                    Notification.company_id == session.get('company_id'),
                    Notification.is_read == False
                ).scalar() or 0
        except Exception as e:
            # Log error - in production it goes to stderr/logs
            import logging
            logging.error(f"Error in inject_globals: {e}")
            overdue_count = 0

            # Optionally add visits too if they have a status
            # For now, let's stick to Interactions which are the main "Tasks"
            
        return {
            'company_info': app.config['COMPANY_INFO'],
            'current_language': current_lang,
            'language_info': lang_info.get(current_lang, lang_info['es']),
            'available_languages': lang_info,
            'current_user': user,
            'overdue_count': overdue_count,
            'unread_notifications': unread_notifications if user else 0,
            'datetime': datetime
        }
    
    return app
