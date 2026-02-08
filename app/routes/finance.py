from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from app.routes.auth import login_required, get_current_user
from app.utils.decorators import permission_required
from app.models import Receivable, Company, User, Commission, Payable
from app.services.email_service import EmailService
from app.utils.tenant import filter_by_company
from config.database import get_db
from datetime import datetime, date
from sqlalchemy import func
from sqlalchemy.orm import joinedload

bp = Blueprint('finance', __name__, url_prefix='/finance')

@bp.route('/receivables')
@login_required
def list_receivables():
    """Listagem de contas a receber"""
    with get_db() as db:
        # Use eager loading to prevent DetachedInstanceError
        query = filter_by_company(db.query(Receivable).options(
            joinedload(Receivable.client), 
            joinedload(Receivable.project)
        ), Receivable)
        
        # Filtros básicos (status)
        status = request.args.get('status')
        if status:
            query = query.filter(Receivable.status == status)
            
        receivables = query.order_by(Receivable.due_date.asc()).all()
        for r in receivables:
            if r.client: db.expunge(r.client)
            if r.project: db.expunge(r.project)
            db.expunge(r)
        
        # Métricas rápidas
        stats = {
            'total_open': filter_by_company(db.query(func.sum(Receivable.amount)), Receivable).filter(Receivable.status == 'open').scalar() or 0,
            'total_paid': filter_by_company(db.query(func.sum(Receivable.amount)), Receivable).filter(Receivable.status == 'paid').scalar() or 0,
            'overdue_count': filter_by_company(db.query(func.count(Receivable.id)), Receivable).filter(Receivable.status == 'open', Receivable.due_date < datetime.utcnow().date()).scalar() or 0
        }
        
    return render_template('finance/receivables.html', receivables=receivables, stats=stats)

@bp.route('/receivables/<int:id>/pay', methods=['POST'])
@login_required
def mark_as_paid(id):
    """Marcar um recebível como pago"""
    with get_db() as db:
        receivable = filter_by_company(db.query(Receivable), Receivable).filter(Receivable.id == id).first()
        if not receivable:
            return jsonify({'success': False, 'message': 'Recebível não encontrado'}), 404
            
        payment_method = request.form.get('payment_method', 'transfer')
        
        receivable.status = 'paid'
        receivable.paid_at = datetime.utcnow()
        receivable.payment_method = payment_method
        
        # Se estiver ligado a um projeto, atualizar o status financeiro do projeto também se for o caso
        if receivable.project:
            # Lógica simples: se pagou o faturamento inicial, o projeto pode avançar
            receivable.project.financial_status = 'paid'
            if receivable.project.phase == 'financeiro':
                receivable.project.phase = 'onboarding'
        
        db.commit()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'message': 'Pagamento registrado com sucesso'})
            
        flash('Pagamento registrado!', 'success')
        return redirect(url_for('finance.list_receivables'))

@bp.route('/receivables/<int:receivable_id>/send-invoice', methods=['POST'])
@login_required
@permission_required('can_manage_finance')
def send_invoice(receivable_id):
    """Envia fatura/cobrança para o cliente via e-mail"""
    with get_db() as db:
        receivable = db.query(Receivable).options(joinedload(Receivable.client)).filter(Receivable.id == receivable_id).first()
        
        if not receivable:
            flash('Cobrança não encontrada.', 'error')
            return redirect(url_for('finance.list_receivables'))
        
        # Preparar placeholders
        # Formatar valores
        currency = session.get('company_currency', 'Gs')
        amount_str = f"{currency} {receivable.amount:,.2f}"
        due_date_str = receivable.due_date.strftime('%d/%m/%Y') if receivable.due_date else 'N/A'
        
        placeholders = {
            'client_name': receivable.client.name if receivable.client else 'Cliente',
            'client_company': receivable.client.company_name if receivable.client else '',
            'amount': amount_str,
            'due_date': due_date_str,
            'invoice_description': receivable.description or 'Serviços Prestados',
            'tenant_name': session.get('company_name', 'Maps2GO'),
            'sender_name': session.get('user_name', 'Consultor')
        }
        
        # Determinar destinatário
        recipient = receivable.client.email if receivable.client else None
        if not recipient:
            flash('Cliente não possui e-mail cadastrado.', 'error')
            return redirect(url_for('finance.list_receivables'))
            
        # Enviar e-mail
        success, error = EmailService.send_transactional_email(
            company_id=session.get('company_id'),
            template_code='invoice_send',
            recipient=recipient,
            placeholders=placeholders,
            reference_id=receivable.id,
            user_id=session.get('user_id')
        )
        
        if success:
            flash(f'Invoice enviada para {recipient}!', 'success')
        else:
            flash(f'Erro ao enviar e-mail: {error}', 'error')
            
    return redirect(url_for('finance.list_receivables'))

@bp.route('/get-summary')
@login_required
def get_finance_summary():
    """API: Resumo financeiro para o dashboard"""
    with get_db() as db:
        # A Receber (Open)
        awaiting = filter_by_company(db.query(func.sum(Receivable.amount)), Receivable).filter(Receivable.status == 'open').scalar() or 0
        
        # Recebido (Mês Atual)
        first_day = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        won_month = filter_by_company(db.query(func.sum(Receivable.amount)), Receivable).filter(
            Receivable.status == 'paid',
            Receivable.paid_at >= first_day
        ).scalar() or 0
        
        # Contratos pendentes (Projects sem contrato assinado)
        from app.models.project import Project
        pending_contracts = filter_by_company(db.query(func.count(Project.id)), Project).filter(Project.contract_file_path == None).scalar() or 0
        
        # 4. Comissões e Custos (Para cálculo de lucro no dashboard)
        commissions_pending = filter_by_company(db.query(func.sum(Commission.amount)), Commission).filter(Commission.status == 'pending').scalar() or 0
        payables_open = filter_by_company(db.query(func.sum(Payable.amount)), Payable).filter(Payable.status == 'open').scalar() or 0
        
        # 5. Folha de Pagamento (Payroll) - Somente ativos
        # Precisamos importar User aqui para evitar dependência circular se houver
        from app.models.user import User
        payroll = filter_by_company(db.query(func.sum(User.base_salary)), User).filter(User.is_active == True).scalar() or 0
        
        return jsonify({
            'success': True,
            'awaiting_payment': float(awaiting),
            'won_amount': float(won_month),
            'pending_contracts': int(pending_contracts),
            'commissions_pending': float(commissions_pending),
            'payables_open': float(payables_open),
            'payroll_monthly': float(payroll),
            'net_profit_estimate': float(awaiting) - float(commissions_pending) - float(payables_open) - float(payroll)
        })

@bp.route('/payables', methods=['GET', 'POST'])
@login_required
@permission_required('can_manage_finance')
def list_payables():
    """Gestão de Contas a Pagar"""
    with get_db() as db:
        if request.method == 'POST':
            # Criar novo pagamento
            new_payable = Payable(
                company_id=session.get('company_id'),
                description=request.form.get('description'),
                amount=float(request.form.get('amount', 0)),
                due_date=datetime.strptime(request.form.get('due_date'), '%Y-%m-%d').date(),
                category=request.form.get('category', 'other'),
                notes=request.form.get('notes')
            )
            db.add(new_payable)
            db.commit()
            flash(_('Conta a pagar registrada!'), 'success')
            return redirect(url_for('finance.list_payables'))

        query = filter_by_company(db.query(Payable), Payable)
        payables = query.order_by(Payable.due_date.asc()).all()
        for p in payables:
            db.expunge(p)
        
        # Stats de payables
        stats = {
            'total_open': filter_by_company(db.query(func.sum(Payable.amount)), Payable).filter(Payable.status == 'open').scalar() or 0,
            'total_paid': filter_by_company(db.query(func.sum(Payable.amount)), Payable).filter(Payable.status == 'paid').scalar() or 0
        }
        
    return render_template('finance/payables.html', payables=payables, stats=stats)

@bp.route('/payables/<int:id>/pay', methods=['POST'])
@login_required
@permission_required('can_manage_finance')
def pay_payable(id):
    """Marcar conta a pagar como paga"""
    with get_db() as db:
        payable = filter_by_company(db.query(Payable), Payable).filter(Payable.id == id).first()
        if not payable:
            return jsonify({'success': False, 'message': 'Conta não encontrada'}), 404
            
        payable.status = 'paid'
        payable.paid_at = datetime.utcnow()
        db.commit()
        return jsonify({'success': True})

@bp.route('/commissions')
@login_required
@permission_required('can_manage_finance')
def list_commissions():
    """Listagem de comissões calculadas"""
    with get_db() as db:
        query = filter_by_company(db.query(Commission).options(joinedload(Commission.user)), Commission)
        commissions = query.order_by(Commission.created_at.desc()).all()
        for c in commissions:
            if c.user: db.expunge(c.user)
            if c.deal: db.expunge(c.deal)
            db.expunge(c)
        
        stats = {
            'total_pending': filter_by_company(db.query(func.sum(Commission.amount)), Commission).filter(Commission.status == 'pending').scalar() or 0,
            'total_paid': filter_by_company(db.query(func.sum(Commission.amount)), Commission).filter(Commission.status == 'paid').scalar() or 0
        }
        
    return render_template('finance/commissions.html', commissions=commissions, stats=stats)

@bp.route('/commissions/<int:id>/pay', methods=['POST'])
@login_required
@permission_required('can_manage_finance')
def pay_commission(id):
    """Marcar comissão como paga"""
    with get_db() as db:
        comm = filter_by_company(db.query(Commission), Commission).filter(Commission.id == id).first()
        if not comm:
            return jsonify({'success': False, 'message': 'Comissão não encontrada'}), 404
            
        comm.status = 'paid'
        comm.paid_at = datetime.utcnow()
        db.commit()
        return jsonify({'success': True})
