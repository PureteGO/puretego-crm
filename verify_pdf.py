import os
import sys
from datetime import datetime, timedelta

# Adicionar o diretório raiz ao path para importar os módulos do app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..', '..', 'ProAG', 'puretego-crm')))

from app import create_app
from app.services import PDFGenerator

app = create_app()

def test_generate_pdf():
    with app.app_context():
        with app.test_request_context():
            # Mock de dados da proposta incluindo Health Check
            proposal_data = {
                'client_name': 'Cliente Teste Premium',
                'proposal_date': datetime.now(),
                'valid_until': datetime.now() + timedelta(days=30),
                'proposal_items': [
                    {
                        'name': 'Otimização GMB Elite',
                        'description': 'Configuração completa de perfil, fotos 360 e SEO local avançado.',
                        'price': 1500000.0
                    },
                    {
                        'name': 'Gestão de Reputação',
                        'description': 'Monitoramento e resposta estratégica a avaliações mensais.',
                        'price': 500000.0
                    }
                ],
                'total_amount': 2000000.0,
                'payment_terms': '50% entrada, 50% após conclusão',
                'health_check': {
                    'score': 45,
                    'report_data': {
                        'top_critical_issues': [
                            {'name': 'Horario de funcionamiento', 'message': 'Não configurado'},
                            {'name': 'Fotos', 'message': 'Poucas fotos encontradas'}
                        ],
                        'recommendations': [
                            'Adicionar fotos da fachada',
                            'Configurar horários especiais'
                        ]
                    }
                }
            }
            
            generator = PDFGenerator()
            print("Gerando PDF de teste...")
            filepath = generator.generate_proposal_pdf(proposal_data, language='es')
            print(f"PDF gerado com sucesso em: {filepath}")

if __name__ == "__main__":
    test_generate_pdf()
