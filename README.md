# Maps2GO CRM - Sistema de Gestão de Prospecção

Sistema CRM multilíngue (Português/Espanhol/Inglês) desenvolvido em Python com Flask e MySQL para gestão de prospecção, visitas, orçamentos em PDF e análise automatizada de perfis do Google Meu Negócio.

## Tecnologias Utilizadas

- **Backend**: Python 3.11+ com Flask
- **Banco de Dados**: MySQL 5.7+ (SQLAlchemy ORM)
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5.3
- **APIs**: SerpApi para análise do Google Meu Negócio
- **Geração de PDF**: ReportLab / Pillow
- **Deploy**: Compatível com cPanel
- **Segurança**: CSRF Protection, bcrypt, Security Headers

## Domínios

- **Marketing**: www.maps2go.online
- **Aplicação**: app.maps2go.online

## Funcionalidades Principais

### 1. Multi-Tenancy (SaaS)
- Isolamento completo de dados por empresa
- Painel de administração SuperAdmin
- Gestão de pacotes de serviço
- Impersonação de tenants

### 2. Gestão de Clientes
- Cadastro de clientes prospectados
- Pipeline Kanban editável (drag & drop)
- Histórico de interações
- Soft delete

### 3. Registro de Interações
- Visitas, chamadas, emails, WhatsApp
- Tipos de interação customizáveis
- Timeline visual por cliente
- Agendamento de follow-ups

### 4. Health Check do Google Meu Negócio
- Análise automatizada via SerpApi
- Pontuação de 0-100 com 17 critérios
- Sistema de créditos por pacote
- Relatório com problemas e recomendações

### 5. Geração de Orçamentos
- Pacotes de serviços flexíveis
- Geração de PDF profissional
- Condições de pagamento personalizadas

### 6. Sistema Multilíngue
- Interface em Português, Espanhol e Inglês
- Troca de idioma em tempo real
- Flask-Babel integration
- **Diretiva de Desenvolvimento**: Toda nova funcionalidade ou correção deve obrigatoriamente contemplar os 3 idiomas utilizando `_()`.

### 7. Controle de Acesso
- Roles: Owner, Manager, Admin, Sales, SDR
- Permissões granulares por função
- SuperAdmin para suporte técnico

## Instalação

### Requisitos
- Python 3.11+
- MySQL 5.7+
- pip

### Passos

1. Clone o repositório
2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Configure o `.env`:
```env
FLASK_ENV=development
SECRET_KEY=sua-chave-secreta-aqui
DB_HOST=localhost
DB_PORT=3306
DB_NAME=maps2go_crm
DB_USER=root
DB_PASS=
SERPAPI_KEY=sua-chave-serpapi
```

4. Execute a aplicação:
```bash
python run.py
```

## Configuração no cPanel

1. Acesse o cPanel → "Setup Python App"
2. Crie aplicação Python 3.11+
3. Configure o diretório da aplicação
4. Instale requirements.txt
5. Configure variáveis de ambiente

## Segurança

- ✅ CSRF Protection (Flask-WTF)
- ✅ Security Headers (X-Frame-Options, X-XSS-Protection)
- ✅ Session HttpOnly + SameSite
- ✅ bcrypt password hashing
- ✅ Role-based access control

## Suporte

Para dúvidas ou suporte, entre em contato:
- Email: contacto@maps2go.online
- Website: www.maps2go.online

---

**Desenvolvido por Maps2GO**
