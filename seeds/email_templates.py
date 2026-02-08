"""
PURETEGO CRM - Email Template Seeding
Popula templates de e-mail globais (fallback)
"""

from config.database import get_db
from app.models import EmailTemplate

def seed_email_templates():
    templates = [
        # COMERCIAL
        {
            'code': 'proposal_send',
            'name': 'Envio de Proposta',
            'area': 'sales',
            'subject': 'Proposta Comercial - {{tenant_name}}',
            'body': """Olá {{client_name}},

É um prazer apresentar nossa proposta para o projeto {{deal_title}}.

Você pode visualizar os detalhes e aceitar a proposta através do link abaixo:
{{proposal_link}}

Qualquer dúvida, estou à disposição.

Atenciosamente,
{{sender_name}}
{{tenant_name}}"""
        },
        
        # FINANCEIRO
        {
            'code': 'invoice_send',
            'name': 'Nova Cobrança',
            'area': 'finance',
            'subject': 'Fatura Disponível - {{tenant_name}}',
            'body': """Olá {{client_name}},

Informamos que uma nova fatura referente a {{invoice_description}} está disponível para pagamento.

Valor: {{amount}}
Vencimento: {{due_date}}

Por favor, realize o pagamento para evitar interrupções no serviço.

Atenciosamente,
Financeiro - {{tenant_name}}"""
        },
        {
            'code': 'payment_confirmation',
            'name': 'Confirmação de Pagamento',
            'area': 'finance',
            'subject': 'Pagamento Confirmado - {{tenant_name}}',
            'body': """Olá {{client_name}},

Confirmamos o recebimento do pagamento referente a {{invoice_description}} no valor de {{amount}}.

Obrigado pela parceria!

Atenciosamente,
Financeiro - {{tenant_name}}"""
        }
    ]

    with get_db() as db:
        for t_data in templates:
            # Verificar se já existe (padrão global tem company_id=None)
            exists = db.query(EmailTemplate).filter(
                EmailTemplate.code == t_data['code'],
                EmailTemplate.company_id == None
            ).first()
            
            if not exists:
                print(f"Semeando template global: {t_data['code']}")
                template = EmailTemplate(
                    code=t_data['code'],
                    name=t_data['name'],
                    subject=t_data['subject'],
                    body=t_data['body'],
                    area=t_data['area'],
                    company_id=None
                )
                db.add(template)
        
        db.commit()

if __name__ == "__main__":
    seed_email_templates()
