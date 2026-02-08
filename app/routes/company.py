"""
PURETEGO CRM - Company Routes
Rotas de perfil e configurações da empresa (multi-tenant)
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from werkzeug.utils import secure_filename
from app.routes.auth import login_required
from app.utils.decorators import permission_required
from app.models import Company
from config.database import get_db
import os
import uuid

bp = Blueprint('company', __name__, url_prefix='/company')

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@bp.route('/profile')
@login_required
@permission_required('can_manage_company')
def profile():
    """Perfil da empresa atual"""
    with get_db() as db:
        company_id = session.get('company_id')
        company = db.query(Company).filter(Company.id == company_id).first()
        
        if not company:
            flash('Empresa não encontrada.', 'error')
            return redirect(url_for('dashboard.index'))
        
        # Serialize para template
        company_data = {
            'id': company.id,
            'name': company.name,
            'slug': company.slug,
            'email': company.email,
            'phone': company.phone,
            'address': company.address,
            'logo_url': company.logo_url,
            'is_active': company.is_active,
            'created_at': company.created_at,
            'users_count': len(company.users) if company.users else 0,
            'clients_count': len(company.clients) if company.clients else 0
        }
    
    return render_template('company/profile.html', company=company_data)


@bp.route('/settings')
@login_required
@permission_required('can_manage_company')
def settings():
    """Configurações da empresa (Interface tabulada)"""
    with get_db() as db:
        company_id = session.get('company_id')
        company = db.query(Company).filter(Company.id == company_id).first()
        
        if not company:
            flash('Empresa não encontrada.', 'error')
            return redirect(url_for('dashboard.index'))
        
        # Dados SMTP para o template
        smtp_data = {
            'smtp_server': company.smtp_server or '',
            'smtp_port': company.smtp_port or 587,
            'smtp_use_tls': company.smtp_use_tls if company.smtp_use_tls is not None else True,
            'smtp_username': company.smtp_username or '',
            'smtp_from_email': company.smtp_from_email or '',
            'smtp_from_name': company.smtp_from_name or '',
            'has_password': bool(company.smtp_password)
        }
    
    return render_template('company/settings.html', 
                           company=company, 
                           smtp=smtp_data,
                           theme_choices=Company.THEME_CHOICES)


@bp.route('/settings/branding', methods=['POST'])
@login_required
@permission_required('can_manage_company')
def update_branding():
    """Atualizar Branding (Logo e Cores)"""
    with get_db() as db:
        company_id = session.get('company_id')
        company = db.query(Company).filter(Company.id == company_id).first()
        
        if not company:
            return redirect(url_for('dashboard.index'))
        
        company.name = request.form.get('name')
        company.theme_style = request.form.get('theme_style', 'tech-teal')
        company.currency_symbol = request.form.get('currency_symbol', 'Gs')
        
        # Processar upload de logo
        if 'logo' in request.files:
            file = request.files['logo']
            if file and file.filename and allowed_file(file.filename):
                # Gerar nome único
                ext = file.filename.rsplit('.', 1)[1].lower()
                filename = f"logo_{company.slug}_{uuid.uuid4().hex[:8]}.{ext}"
                
                # Salvar
                upload_folder = os.path.join(current_app.root_path, 'static', 'uploads')
                os.makedirs(upload_folder, exist_ok=True)
                filepath = os.path.join(upload_folder, filename)
                file.save(filepath)
                
                # Atualizar URL
                company.logo_url = f"/static/uploads/{filename}"
        
        db.commit()
        
        # Atualizar dados na sessão
        session['company_name'] = company.name
        session['company_logo'] = company.logo_url
        session['company_theme'] = company.theme_style
        session['company_currency'] = company.currency_symbol
        
        flash('Configurações de branding atualizadas!', 'success')
    
    return redirect(url_for('company.settings', _anchor='branding'))


@bp.route('/settings/smtp', methods=['POST'])
@login_required
@permission_required('can_manage_company')
def update_smtp():
    """Atualizar configurações SMTP"""
    with get_db() as db:
        company_id = session.get('company_id')
        company = db.query(Company).filter(Company.id == company_id).first()
        
        if not company:
            return redirect(url_for('dashboard.index'))
            
        company.smtp_server = request.form.get('smtp_server') or None
        company.smtp_port = int(request.form.get('smtp_port') or 587)
        company.smtp_use_tls = request.form.get('smtp_use_tls') == 'on'
        company.smtp_username = request.form.get('smtp_username') or None
        
        new_password = request.form.get('smtp_password')
        if new_password:
            company.smtp_password = new_password
            
        company.smtp_from_email = request.form.get('smtp_from_email') or None
        company.smtp_from_name = request.form.get('smtp_from_name') or None
        
        db.commit()
        flash('Configurações SMTP salvas!', 'success')
        
    return redirect(url_for('company.settings', _anchor='email'))


@bp.route('/settings/workflow', methods=['POST'])
@login_required
@permission_required('can_manage_company')
def update_workflow_mode():
    """Atualizar modo de trabalho (workflow_mode)"""
    with get_db() as db:
        company_id = session.get('company_id')
        company = db.query(Company).filter(Company.id == company_id).first()
        
        if not company:
            return redirect(url_for('dashboard.index'))
        
        new_mode = request.form.get('workflow_mode')
        if new_mode in [Company.WORKFLOW_SOLO, Company.WORKFLOW_LEAN, Company.WORKFLOW_STRUCTURED]:
            company.workflow_mode = new_mode
            
            # Atualizar taxas de comissão se fornecidas
            try:
                company.commission_closer_rate = float(request.form.get('commission_closer_rate', 10.0))
                company.commission_sdr_rate = float(request.form.get('commission_sdr_rate', 2.0))
            except (ValueError, TypeError):
                pass # Manter padrão em caso de erro no input
                
            db.commit()
            flash(f'Modo de trabalho e taxas atualizados!', 'success')
        else:
            flash('Modo de trabalho inválido.', 'error')
            
    return redirect(url_for('company.settings', _anchor='workflow'))


@bp.route('/remove-logo', methods=['POST'])
@login_required
@permission_required('can_manage_company')
def remove_logo():
    """Remover logo da empresa"""
    with get_db() as db:
        company_id = session.get('company_id')
        company = db.query(Company).filter(Company.id == company_id).first()
        
        if not company:
            flash('Empresa não encontrada.', 'error')
            return redirect(url_for('dashboard.index'))
        
        # Tentar deletar arquivo físico
        if company.logo_url:
            try:
                filepath = os.path.join(current_app.root_path, company.logo_url.lstrip('/'))
                if os.path.exists(filepath):
                    os.remove(filepath)
            except Exception:
                pass  # Ignorar erros de deleção
        
        company.logo_url = None
        db.commit()
        
        flash('Logo removido con éxito.', 'success')
    
    return redirect(url_for('company.profile'))


@bp.route('/email-templates')
@login_required
@permission_required('can_manage_company')
def email_templates():
    """Lista de templates de e-mail da empresa"""
    from app.models import EmailTemplate
    with get_db() as db:
        company_id = session.get('company_id')
        
        # Buscar templates da empresa + templates globais 
        templates = db.query(EmailTemplate).filter(
            (EmailTemplate.company_id == company_id) | (EmailTemplate.company_id == None)
        ).all()
        
        # Agrupar por área para o template
        grouped = {
            'sales': [t for t in templates if t.area == 'sales'],
            'finance': [t for t in templates if t.area == 'finance'],
            'general': [t for t in templates if t.area == 'general']
        }
        
    return render_template('company/email_templates.html', templates=grouped)


@bp.route('/email-templates/edit/<code>', methods=['GET', 'POST'])
@login_required
@permission_required('can_manage_company')
def edit_email_template(code):
    """Editar ou criar versão personalizada de um template"""
    from app.models import EmailTemplate
    with get_db() as db:
        company_id = session.get('company_id')
        
        # Buscar template da empresa
        template = db.query(EmailTemplate).filter(
            EmailTemplate.company_id == company_id,
            EmailTemplate.code == code
        ).first()
        
        # Se não existir, buscar o global para servir de base
        if not template:
            global_template = db.query(EmailTemplate).filter(
                EmailTemplate.company_id == None,
                EmailTemplate.code == code
            ).first()
            
            if not global_template:
                flash('Template não encontrado.', 'error')
                return redirect(url_for('company.email_templates'))
            
            template = global_template # Usar como base no GET
            
        if request.method == 'POST':
            # Se era o global, precisamos criar uma cópia para a empresa
            if template.company_id is None:
                new_template = EmailTemplate(
                    code=code,
                    name=template.name,
                    subject=request.form.get('subject'),
                    body=request.form.get('body'),
                    company_id=company_id,
                    area=template.area,
                    locale=template.locale
                )
                db.add(new_template)
            else:
                # Apenas atualizar o existente da empresa
                template.subject = request.form.get('subject')
                template.body = request.form.get('body')
            
            db.commit()
            flash('Template de e-mail atualizado!', 'success')
            return redirect(url_for('company.email_templates'))
            
    return render_template('company/edit_email_template.html', template=template)


@bp.route('/email-templates/restore/<code>', methods=['POST'])
@login_required
@permission_required('can_manage_company')
def restore_email_template(code):
    """Apagar a versão da empresa e voltar ao padrão global"""
    from app.models import EmailTemplate
    with get_db() as db:
        company_id = session.get('company_id')
        
        template = db.query(EmailTemplate).filter(
            EmailTemplate.company_id == company_id,
            EmailTemplate.code == code
        ).first()
        
        if template:
            db.delete(template)
            db.commit()
            flash('Template restaurado para o padrão global.', 'success')
            
    return redirect(url_for('company.email_templates'))
@login_required
@permission_required('can_manage_company')
def test_email():
    """Enviar email de teste usando configuração SMTP da empresa"""
    with get_db() as db:
        company_id = session.get('company_id')
        company = db.query(Company).filter(Company.id == company_id).first()
        
        if not company or not company.has_smtp_configured():
            flash('Configure o SMTP antes de enviar um e-mail de teste.', 'error')
            return redirect(url_for('company.settings', _anchor='email'))
        
        from app.services.email_service import send_email_with_company_smtp
        
        test_email = request.form.get('test_email') or session.get('user_email')
        
        success = send_email_with_company_smtp(
            company=company,
            to_email=test_email,
            subject=f"Email de Prueba - {company.name}",
            html_content=f"""
            <html>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <h2>🎉 Email de Prueba Exitoso!</h2>
                <p>Este es un email de prueba enviado desde <strong>{company.name}</strong>.</p>
                <p>Tu configuración SMTP está funcionando correctamente.</p>
                <hr>
                <small>Enviado desde PureteGO CRM</small>
            </body>
            </html>
            """
        )
        
        if success:
            flash(f'Email de prueba enviado a {test_email}!', 'success')
        else:
            flash('Error al enviar el email. Verifica la configuración SMTP.', 'error')
    
    return redirect(url_for('company.settings', _anchor='email'))
