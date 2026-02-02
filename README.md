# PURETEGO CRM - Sistema de Gestão de Prospecção

Sistema CRM bilíngue (Português/Espanhol) desenvolvido em Python com Flask e MySQL para gestão de prospecção, visitas, orçamentos em PDF e análise automatizada de perfis do Google Meu Negócio.

## Tecnologias Utilizadas

- **Backend**: Python 3.11+ com Flask
- **Banco de Dados**: MySQL 5.7+
- **Frontend**: HTML5, CSS3, JavaScript
- **APIs**: SerpApi para análise do Google Meu Negócio
- **Geração de PDF**: ReportLab
- **Deploy**: Compatível com cPanel

## Estrutura do Projeto

```
puretego-crm/
├── app/
│   ├── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── client.py
│   │   ├── visit.py
│   │   ├── proposal.py
│   │   └── health_check.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── clients.py
│   │   ├── visits.py
│   │   ├── proposals.py
│   │   └── health_checks.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── serpapi_service.py
│   │   └── pdf_generator.py
│   ├── static/
│   │   ├── css/
│   │   ├── js/
│   │   └── images/
│   └── templates/
│       ├── base.html
│       ├── login.html
│       ├── dashboard.html
│       ├── clients/
│       ├── visits/
│       └── proposals/
├── config/
│   ├── __init__.py
│   ├── database.py
│   └── settings.py
├── database.sql
├── requirements.txt
├── run.py
└── README.md
```

## Funcionalidades Principais

### 1. Gestão de Clientes
- Cadastro de clientes prospectados
- Pipeline Kanban editável
- Histórico de interações

### 2. Registro de Visitas
- Anotações detalhadas de visitas
- Registro de interlocutores
- Próximos passos e ações

### 3. Health Check do Google Meu Negócio
- Análise automatizada via SerpApi
- Pontuação de 0-100
- Relatório com principais problemas
- Histórico de análises

### 4. Geração de Orçamentos
- Orçamentos flexíveis baseados em pacotes
- Geração de PDF profissional
- Condições de pagamento personalizadas
- Design baseado nos modelos Puretego

### 5. Sistema Bilíngue
- Interface em Português e Espanhol
- Orçamentos em ambos os idiomas

## Instalação

### Requisitos
- Python 3.11+
- MySQL 5.7+
- pip

### Passos

1. Clone o repositório ou faça upload para o servidor cPanel

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Configure o banco de dados no arquivo `config/settings.py`

4. Execute o script SQL para criar as tabelas:
```bash
mysql -u usuario -p < database.sql
```

5. Execute a aplicação:
```bash
python run.py
```

## Configuração no cPanel

1. Acesse o cPanel e vá em "Setup Python App"
2. Crie uma nova aplicação Python
3. Selecione Python 3.11+
4. Configure o diretório da aplicação
5. Instale as dependências do requirements.txt
6. Configure as variáveis de ambiente

## Credenciais Padrão

- **Usuário**: admin@puretego.online
- **Senha**: admin123

**IMPORTANTE**: Altere a senha padrão após o primeiro login!

## API Keys Necessárias

- **SerpApi**: Obtenha em https://serpapi.com/

Configure as chaves no arquivo `config/settings.py`

## Suporte

Para dúvidas ou suporte, entre em contato com a equipe Puretego.

---

**Desenvolvido para Puretego Online**  
www.puretego.online
