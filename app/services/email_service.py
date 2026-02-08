"""
PURETEGO CRM - Email Service
Serviço para envio de e-mails transacionais com SMTP por tenant e templates personalizáveis.
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app, url_for
from app.models import Company, EmailTemplate, EmailLog
from config.database import db_session

class EmailService:
    @staticmethod
    def send_transactional_email(company_id, template_code, recipient, placeholders, reference_id=None, user_id=None):
        """
        Envia um e-mail transacional baseado em um template com fallback global.
        """
        # 1. Buscar Template (Empresa -> Global)
        template = db_session.query(EmailTemplate).filter(
            EmailTemplate.company_id == company_id,
            EmailTemplate.code == template_code,
            EmailTemplate.is_active == True
        ).first()
        
        if not template:
            template = db_session.query(EmailTemplate).filter(
                EmailTemplate.company_id == None,
                EmailTemplate.code == template_code,
                EmailTemplate.is_active == True
            ).first()
            
        if not template:
            return False, f"Template '{template_code}' no encontrado."

        # 2. Buscar Configuração da Empresa
        company = db_session.query(Company).get(company_id)
        
        # 3. Processar Placeholders (Assunto e Corpo)
        subject = EmailService._render_text(template.subject, placeholders)
        body = EmailService._render_text(template.body, placeholders)
        
        # 4. Enviar via SMTP
        success, error = EmailService._send_via_smtp(company, recipient, subject, body)
        
        # 5. Registrar Log
        EmailService._log_email(
            company_id=company_id,
            email_type=template_code,
            recipient=recipient,
            subject=subject,
            status='sent' if success else 'error',
            error_message=error,
            reference_id=reference_id,
            user_id=user_id
        )
        
        return success, error

    @staticmethod
    def _render_text(text, placeholders):
        """Substitui placeholders {{ key }} pelos valores no dicionário"""
        for key, value in placeholders.items():
            placeholder = f"{{{{{key}}}}}"
            text = text.replace(placeholder, str(value or ''))
        return text

    @staticmethod
    def _send_via_smtp(company, recipient, subject, body):
        """Envia e-mail usando SMTP da empresa ou fallback global"""
        
        # Determinar Configurações
        if company and company.has_smtp_configured():
            smtp_config = company.get_smtp_config()
        else:
            # Fallback Global
            smtp_config = {
                'server': current_app.config.get('MAIL_SERVER', 'localhost'),
                'port': current_app.config.get('MAIL_PORT', 587),
                'use_tls': current_app.config.get('MAIL_USE_TLS', True),
                'username': current_app.config.get('MAIL_USERNAME'),
                'password': current_app.config.get('MAIL_PASSWORD'),
                'from_email': current_app.config.get('MAIL_DEFAULT_SENDER', 'no-reply@maps2go.online'),
                'from_name': current_app.config.get('MAIL_FROM_NAME', 'Maps2GO')
            }

        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{smtp_config.get('from_name', 'Maps2GO')} <{smtp_config['from_email']}>"
            msg['To'] = recipient
            msg['Subject'] = subject
            
            # Versão texto puro
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            # Versão HTML (Se o corpo contiver HTML, senão envia como texto em envelope básico)
            if '<html' in body.lower() or '<body' in body.lower() or '<p>' in body.lower():
                msg.attach(MIMEText(body, 'html', 'utf-8'))
            else:
                # Converter quebras de linha para <br> para um HTML básico
                html_body = f"<html><body style='font-family: sans-serif; white-space: pre-wrap;'>{body}</body></html>"
                msg.attach(MIMEText(html_body, 'html', 'utf-8'))

            # Conectar e Enviar
            if smtp_config.get('use_tls', True):
                context = ssl.create_default_context()
                with smtplib.SMTP(smtp_config['server'], smtp_config['port'], timeout=15) as server:
                    server.starttls(context=context)
                    if smtp_config.get('password'):
                        server.login(smtp_config['username'], smtp_config['password'])
                    server.send_message(msg)
            else:
                with smtplib.SMTP(smtp_config['server'], smtp_config['port'], timeout=15) as server:
                    if smtp_config.get('password'):
                        server.login(smtp_config['username'], smtp_config['password'])
                    server.send_message(msg)
                    
            return True, None
            
        except Exception as e:
            current_app.logger.error(f"Error SMTP: {str(e)}")
            return False, str(e)

    @staticmethod
    def _log_email(company_id, email_type, recipient, subject, status, error_message=None, reference_id=None, user_id=None):
        """Salva registro do envio no banco de dados"""
        try:
            log = EmailLog(
                company_id=company_id,
                email_type=email_type,
                recipient=recipient,
                subject=subject,
                status=status,
                error_message=error_message,
                reference_id=reference_id,
                user_id=user_id
            )
            db_session.add(log)
            db_session.commit()
        except Exception as e:
            current_app.logger.error(f"Error logging email: {str(e)}")
            # No rollback here to avoid breaking context if it fails
            pass

# Wrappers para compatibilidade com código antigo
def send_email(to_email, subject, html_content, text_content=None):
    """Envia um email genérico usando SMTP global"""
    success, error = EmailService._send_via_smtp(None, to_email, subject, html_content)
    return success

def send_email_with_company_smtp(company, to_email, subject, html_content, text_content=None):
    """Envia um email usando SMTP da empresa"""
    success, error = EmailService._send_via_smtp(company, to_email, subject, html_content)
    return success

def send_password_reset_email(user, reset_url):
    """Envia email de recuperação de senha (mantido conforme original)"""
    subject = "Recuperación de Contraseña - PureteGO CRM"
    html_content = f"Hola {user.name}, usa este enlace para restablecer tu contraseña: {reset_url}"
    return send_email(user.email, subject, html_content)
