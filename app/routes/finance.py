from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from flask_babel import _
from app.routes.auth import login_required, get_current_user
from app.utils.decorators import permission_required
from app.models import Receivable, Company, User, Commission, Payable, PayableCategory
from app.services.email_service import EmailService
from app.utils.tenant import filter_by_company
from config.database import get_db
from datetime import datetime, date, timedelta
from sqlalchemy import func
from sqlalchemy.orm import joinedload

bp = Blueprint('finance', __name__, url_prefix='/finance')

@bp.route('/receivables', methods=['GET', 'POST'])
@login_required
def list_receivables():
    """Listagem de contas a receber"""
    with get_db() as db:
        if request.method == 'POST':
            # Registro manual de recebível
            try:
                company_id = session.get('company_id')
                client_id = request.form.get('client_id')
                amount_val = request.form.get('amount')
                due_date_val = request.form.get('due_date')
                installments_val = request.form.get('installments', '1')
                
                if not client_id or not amount_val or not due_date_val:
                    raise ValueError(_("Missing required fields"))
                
                total_amount = float(amount_val)
                base_due_date = datetime.strptime(due_date_val, '%Y-%m-%d').date()
                installments = int(installments_val)
                description = request.form.get('description', _('Manual entry'))
                
                if installments > 1:
                    installment_amount = total_amount / installments
                    for i in range(1, installments + 1):
                        # Calculate due date for this installment (+30 days for each)
                        due_date = base_due_date + timedelta(days=30 * (i - 1))
                        
                        new_receivable = Receivable(
                            company_id=company_id,
                            client_id=int(client_id),
                            description=f"{description} ({i}/{installments})",
                            amount=installment_amount,
                            due_date=due_date,
                            status='open'
                        )
                        db.add(new_receivable)
                else:
                    new_receivable = Receivable(
                        company_id=company_id,
                        client_id=int(client_id),
                        description=description,
                        amount=total_amount,
                        due_date=base_due_date,
                        status='open'
                    )
                    db.add(new_receivable)

                db.commit()
                flash(_('Recebível(eis) registrado(s) com sucesso!'), 'success')
                return redirect(url_for('finance.list_receivables'))
            except Exception as e:
                db.rollback()
                flash(f'Erro: {str(e)}', 'error')

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
        
        # Métricas rápidas
        stats = {
            'total_open': filter_by_company(db.query(func.sum(Receivable.amount)), Receivable).filter(Receivable.status == 'open').scalar() or 0,
            'total_paid': filter_by_company(db.query(func.sum(Receivable.amount)), Receivable).filter(Receivable.status == 'paid').scalar() or 0,
            'overdue_count': filter_by_company(db.query(func.count(Receivable.id)), Receivable).filter(Receivable.status == 'open', Receivable.due_date < datetime.utcnow().date()).scalar() or 0
        }
        
        # Lista de clientes para o formulário de cadastro
        from app.models.client import Client
        clients = filter_by_company(db.query(Client), Client).order_by(Client.name.asc()).all()
            
        return render_template('finance/receivables.html', receivables=receivables, stats=stats, clients=clients, datetime=datetime)

@bp.route('/receivables/<int:id>/pay', methods=['POST'])
@login_required
def mark_as_paid(id):
    """Marcar um recebível como pago"""
    with get_db() as db:
        receivable = filter_by_company(db.query(Receivable), Receivable).filter(Receivable.id == id).first()
        if not receivable:
            return jsonify({'success': False, 'message': 'Recebível não encontrado'}), 404
            
        try:
            amount_paid = request.form.get('amount_paid')
            if amount_paid:
                amount_paid = float(amount_paid)
            else:
                # Default to full remaining balance
                amount_paid = float(receivable.amount) - float(receivable.paid_amount or 0)
                
            payment_method = request.form.get('payment_method', 'transfer')
            
            # Update paid amount
            current_paid = float(receivable.paid_amount or 0)
            receivable.paid_amount = current_paid + amount_paid
            receivable.payment_method = payment_method
            receivable.paid_at = datetime.utcnow()
            
            # Update status
            if receivable.paid_amount >= receivable.amount:
                receivable.status = 'paid'
                # Se estiver ligado a um projeto, atualizar o status financeiro do projeto também se for o caso
                if receivable.project:
                    receivable.project.financial_status = 'paid'
                    if receivable.project.phase == 'financeiro':
                        receivable.project.phase = 'onboarding'
            else:
                receivable.status = 'partial'
                if receivable.project:
                    receivable.project.financial_status = 'partial'
               
            db.commit()
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.args.get('json'):
                return jsonify({'success': True, 'message': 'Pagamento registrado com sucesso'})
                
            flash(_('Pagamento registrado!'), 'success')
            return redirect(url_for('finance.list_receivables'))
        except Exception as e:
            db.rollback()
            return jsonify({'success': False, 'message': str(e)}), 400


@bp.route('/receivables/<int:id>/update', methods=['POST'])
@login_required
@permission_required('can_manage_finance')
def update_receivable(id):
    """Editar um lançamento de conta a receber"""
    data = request.get_json() if request.is_json else request.form
    
    with get_db() as db:
        receivable = filter_by_company(db.query(Receivable), Receivable).filter(Receivable.id == id).first()
        if not receivable:
            return jsonify({'success': False, 'message': 'Recebível não encontrado'}), 404
            
        try:
            if 'description' in data:
                receivable.description = data.get('description')
            if 'amount' in data:
                receivable.amount = float(data.get('amount'))
            if 'due_date' in data:
                receivable.due_date = datetime.strptime(data.get('due_date'), '%Y-%m-%d').date()
            
            db.commit()
            return jsonify({'success': True})
        except Exception as e:
            db.rollback()
            return jsonify({'success': False, 'message': str(e)}), 400

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
            # Criar novo pagamento
            try:
                company_id = session.get('company_id')
                if not company_id:
                    raise ValueError("Sessão inválida (Company ID missing)")

                amount_val = request.form.get('amount')
                amount = float(amount_val) if amount_val else 0.0
                
                due_date_val = request.form.get('due_date')
                if not due_date_val:
                    raise ValueError("Data de vencimento obrigatória")
                
                base_due_date = datetime.strptime(due_date_val, '%Y-%m-%d').date()
                repeat_months = int(request.form.get('repeat_months', '1'))
                description = request.form.get('description')
                category_id = request.form.get('category_id')
                category_id = int(category_id) if category_id and category_id != 'None' else None

                if repeat_months > 1:
                    for i in range(1, repeat_months + 1):
                        due_date = base_due_date + timedelta(days=30 * (i - 1))
                        
                        new_payable = Payable(
                            company_id=company_id,
                            description=f"{description} ({i}/{repeat_months})",
                            amount=amount,
                            due_date=due_date,
                            category_id=category_id,
                            notes=request.form.get('notes')
                        )
                        db.add(new_payable)
                else:
                    new_payable = Payable(
                        company_id=company_id,
                        description=description,
                        amount=amount,
                        due_date=base_due_date,
                        category_id=category_id,
                        notes=request.form.get('notes')
                    )
                    db.add(new_payable)

                db.commit()
                flash(_('Contas(s) a pagar registrada(s)!'), 'success')
                return redirect(url_for('finance.list_payables'))
            except ValueError as e:
                db.rollback()
                flash(f'Erro de validação: {str(e)}', 'error')
            except Exception as e:
                db.rollback()
                flash(f'Erro ao registrar conta: {str(e)}', 'error')

        query = filter_by_company(db.query(Payable).options(joinedload(Payable.category_obj)), Payable)
        
        # Filtros
        status = request.args.get('status')
        if status:
            query = query.filter(Payable.status == status)
            
        # Ordenação
        sort = request.args.get('sort', 'due_date')
        order = request.args.get('order', 'asc')
        
        if sort == 'amount':
            query = query.order_by(Payable.amount.asc() if order == 'asc' else Payable.amount.desc())
        else:
            query = query.order_by(Payable.due_date.asc() if order == 'asc' else Payable.due_date.desc())
            
        payables = query.all()
        
        # Categories for the form
        from app.models.payable_category import PayableCategory
        categories = filter_by_company(db.query(PayableCategory), PayableCategory).order_by(PayableCategory.name.asc()).all()
        
        # Stats de payables
        stats = {
            'total_open': filter_by_company(db.query(func.sum(Payable.amount)), Payable).filter(Payable.status == 'open').scalar() or 0,
            'total_paid': filter_by_company(db.query(func.sum(Payable.amount)), Payable).filter(Payable.status == 'paid').scalar() or 0
        }
        
        return render_template('finance/payables.html', payables=payables, stats=stats, categories=categories, datetime=datetime)

@bp.route('/categories', methods=['POST'])
@login_required
@permission_required('can_manage_finance')
def manage_categories():
    """Criar ou editar categorias de despesas"""
    with get_db() as db:
        from app.models.payable_category import PayableCategory
        company_id = session.get('company_id')
        cat_id = request.form.get('id')
        name = request.form.get('name')
        color = request.form.get('color', '#6c757d')
        
        if not name:
            return jsonify({'success': False, 'message': 'Nome obrigatório'}), 400
            
        if cat_id:
            category = filter_by_company(db.query(PayableCategory), PayableCategory).filter(PayableCategory.id == cat_id).first()
            if category:
                category.name = name
                category.color = color
        else:
            new_cat = PayableCategory(company_id=company_id, name=name, color=color)
            db.add(new_cat)
            
        db.commit()
        return jsonify({'success': True})

@bp.route('/categories/<int:id>/delete', methods=['POST'])
@login_required
@permission_required('can_manage_finance')
def delete_category(id):
    """Excluir uma categoria se não estiver em uso"""
    with get_db() as db:
        from app.models.payable_category import PayableCategory
        category = filter_by_company(db.query(PayableCategory), PayableCategory).filter(PayableCategory.id == id).first()
        if not category:
            return jsonify({'success': False, 'message': 'Categoria não encontrada'}), 404
            
        # Verificar se está em uso
        if db.query(Payable).filter(Payable.category_id == id).first():
            return jsonify({'success': False, 'message': 'Não é possível excluir: categoria em uso por lançamentos.'}), 400
            
        db.delete(category)
        db.commit()
        return jsonify({'success': True})

@bp.route('/payables/<int:id>/pay', methods=['POST'])
@login_required
@permission_required('can_manage_finance')
def pay_payable(id):
    """Marcar conta a pagar como paga"""
    with get_db() as db:
        payable = filter_by_company(db.query(Payable), Payable).filter(Payable.id == id).first()
        if not payable:
            return jsonify({'success': False, 'message': 'Conta não encontrada'}), 404
            
        try:
            amount_paid = request.form.get('amount_paid')
            if amount_paid:
                amount_paid = float(amount_paid)
            else:
                # Default to full remaining balance
                amount_paid = float(payable.amount) - float(payable.paid_amount or 0)
            
            # Update paid amount
            current_paid = float(payable.paid_amount or 0)
            payable.paid_amount = current_paid + amount_paid
            payable.paid_at = datetime.utcnow()
            
            # Update status
            if payable.paid_amount >= payable.amount:
                payable.status = 'paid'
            else:
                payable.status = 'partial'
                
            db.commit()
            return jsonify({'success': True})
        except Exception as e:
            db.rollback()
            return jsonify({'success': False, 'message': str(e)}), 400

@bp.route('/payables/<int:id>/update', methods=['POST'])
@login_required
@permission_required('can_manage_finance')
def update_payable(id):
    """Editar um lançamento de conta a pagar"""
    with get_db() as db:
        payable = filter_by_company(db.query(Payable), Payable).filter(Payable.id == id).first()
        if not payable:
            return jsonify({'success': False, 'message': 'Conta não encontrada'}), 404
            
        try:
            payable.description = request.form.get('description')
            payable.amount = float(request.form.get('amount'))
            due_date_str = request.form.get('due_date')
            if due_date_str:
                payable.due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
            
            category_id = request.form.get('category_id')
            payable.category_id = int(category_id) if category_id and category_id != 'None' else None
            
            db.commit()
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 400

@bp.route('/payables/<int:id>/delete', methods=['POST'])
@login_required
@permission_required('can_manage_finance')
def delete_payable(id):
    """Excluir um lançamento de conta a pagar"""
    with get_db() as db:
        payable = filter_by_company(db.query(Payable), Payable).filter(Payable.id == id).first()
        if not payable:
            return jsonify({'success': False, 'message': 'Conta não encontrada'}), 404
            
        db.delete(payable)
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
