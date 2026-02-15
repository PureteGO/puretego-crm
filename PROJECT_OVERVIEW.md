# Visão Geral do Projeto: PureteGO CRM

Este documento consolida as definições de infraestrutura, arquitetura de dados e fluxos de uso do PureteGO CRM para fins de documentação, planejamento e integração com ferramentas de IA (ex: Perplexity).

---

## 1. Visão Geral do Sistema

**Nome do Projeto:** PureteGO CRM
**Objetivo:** Plataforma de gestão integrada para agências digitais focadas em SEO Local e Google Business Profile (GBP). O sistema gerencia todo o ciclo de vida do cliente, desde a prospecção (SDR), vendas, gestão de projetos/serviços, até o financeiro e relatórios de performance.

**Arquitetura:** Aplicação Monolítica Modular (MVC) em Python/Flask.
**Modelo de Negócio:** Multi-tenant (SaaS para agências gerenciarem seus clientes).

---

## 2. Stack Tecnológico

### Backend
*   **Linguagem:** Python 3.11+
*   **Framework Web:** Flask 3.0.0
*   **ORM:** SQLAlchemy 2.0+ (com Flask-SQLAlchemy)
*   **Autenticação:** Flask-Login + Flask-WTF + Bcrypt
*   **Internacionalização (i18n):** Flask-Babel (Suporte a pt_BR, en, es)
*   **Geração de PDF:** xhtml2pdf / WeasyPrint (para propostas e relatórios)

### Frontend
*   **Template Engine:** Jinja2 (Renderização Server-Side)
*   **CSS Framework:** Bootstrap 5 (Customizado via CSS variáveis)
*   **JS:** Vanilla JS + Chart.js (Dashboards) + Reactive Dashboard (Polling)
*   **Ícones:** Bootstrap Icons

### Banco de Dados
*   **Motor:** MySQL 5.7+ (Produção) / SQLite (Desenvolvimento opcional)
*   **Driver:** PyMySQL

### Infraestrutura & Deploy
*   **Servidor:** cPanel (Hospedagem Compartilhada ou VPS Gerenciado)
*   **WSGI Server:** Passenger WSGI
*   **Gerenciamento de Processos:** Setup Python App (cPanel)
*   **Versionamento:** Git (GitHub)

### Integrações Externas
*   **Google Business Profile API:** Gestão de fichas, reviews e insights.
*   **Google Auth:** Login social e conexão de contas.
*   **SERP API:** Rastreamento de ranking local.

---

## 3. Arquitetura do Banco de Dados

O banco de dados é relacional e normalizado. Abaixo estão os principais modelos agrupados por módulo.

### A. Core & Acesso (RBAC)
*   **users**: Usuários do sistema (SDR, Vendas, Admin, Financeiro, Produção). Relaciona-se com `roles`.
*   **roles**: Definição de perfis de acesso e permissões.
*   **companies**: Tenants (Agências que usam o CRM).
*   **audit_logs**: Registro de atividades críticas para segurança e compliance.

### B. CRM & Vendas (Funil)
*   **clients**: Entidade central. Leads e Clientes ativos. Possui `status`, `lead_temperature` e dados detalhados de contato.
*   **kanban_stages**: Etapas do funil de vendas (ex: Novo, Qualificado, Proposta, Negociação, Fechado).
*   **interactions**: Histórico de chamadas, emails e reuniões com o cliente.
*   **deals**: Oportunidades de negócio específicas.
*   **proposals**: Propostas comerciais geradas (PDF). Linkadas a `clients` e `users`.
*   **service_packages**: Pacotes de serviços pré-definidos (SaaS ou Avulso) para venda.

### C. Gestão de Projetos & Serviços (Pós-Venda)
*   **projects**: Contratos ativos. Gerencia a execução do serviço vendido.
*   **tasks / project_tickets**: Tarefas operacionais vinculadas a um projeto.
*   **services**: Catálogo de serviços individuais.
*   **visits**: Agendamento e registro de visitas presenciais (Field Sales).

### D. Módulo Google Business Profile (GBP)
*   **gmb_location_links**: Vínculo entre um `client` interno e uma `Location ID` do Google.
*   **gmb_reviews**: Avaliações importadas do Google para gestão de reputação.
*   **health_checks**: Auditoria automatizada da ficha do cliente (Score 0-100).
*   **local_search / rankings**: Monitoramento de posição em palavras-chave locais.

### E. Financeiro
*   **receivables**: Contas a receber (faturas geradas para clientes).
*   **payables**: Contas a pagar (despesas da agência).
*   **payable_categories**: Categorização de despesas (Plano de Contas).
*   **commissions**: Cálculo de comissões para vendedores (SDR/Closer).

---

## 4. Fluxos de Uso (Jornada do Usuário)

O sistema adapta a interface (Dashboard) baseada no papel do usuário (`role`).

### 1. SDR (Sales Development Rep)
*   **Objetivo:** Prospecção e Qualificação.
*   **Fluxo:**
    1.  Cadastra novos Leads (`clients`).
    2.  Registra atividades (`interactions`).
    3.  Move cards no Kanban até a etapa de "Agendamento".
    4.  Dashboard focado em **Novos Leads/Dia** e **Atividades Realizadas**.

### 2. Executivo de Vendas (Closer)
*   **Objetivo:** Fechamento e Contratos.
*   **Fluxo:**
    1.  Recebe Leads qualificados.
    2.  Realiza visitas/reuniões (`visits`).
    3.  Gera e envia Propostas (`proposals`) em PDF.
    4.  Converte Lead em Cliente (Gera `Project` e `Receivable` inicial).
    5.  Dashboard focado em **Pipeline**, **Propostas Abertas** e **Vendas Fechadas**.

### 3. Gestor de Projetos / Operações (Production)
*   **Objetivo:** Entrega do Serviço (Setup + Recorrência).
*   **Fluxo:**
    1.  Visualiza novos Projetos (`projects`) com status "Onboarding".
    2.  Gerencia tarefas técnicas (`project_tickets`) como "Otimizar Ficha", "Responder Reviews".
    3.  Monitora o `HealthCheck` dos clientes.
    4.  Dashboard focado em **Tarefas Pendentes** e **Status dos Projetos**.

### 4. Financeiro
*   **Objetivo:** Fluxo de Caixa e Cobrança.
*   **Fluxo:**
    1.  Monitora `receivables` (mensalidades de clientes).
    2.  Registra pagamentos e inadimplência.
    3.  Gerencia contas a pagar (`payables`).
    4.  Dashboard focado em **Faturamento**, **Inadimplência** e **Fluxo de Caixa**.

### 5. Admin / Owner
*   **Objetivo:** Visão Estratégica.
*   **Fluxo:**
    1.  Acesso irrestrito a todos os módulos.
    2.  Relatórios gerenciais de performance (CAC, LTV, Churn).
    3.  Configuração de metas e usuários.

---

## 5. Estrutura de Pastas (Código Fonte)

```text
/
├── app/
│   ├── models/       # Definição das tabelas do banco (SQLAlchemy)
│   ├── routes/       # Controladores e Endpoints (Blueprints)
│   ├── services/     # Lógica de negócio complexa (ex: GMB API, PDF Gen)
│   ├── templates/    # Arquivos HTML (Jinja2)
│   ├── static/       # Assets (CSS, JS, Imagens)
│   └── translations/ # Arquivos .po/.mo para i18n
├── config/           # Configurações de ambiente (Dev/Prod)
├── migrations/       # Versões do banco de dados (Alembic)
├── scripts/          # Utilitários de manutenção e correção de dados
└── requirements.txt  # Dependências Python
```

## 6. Próximos Passos (Feature Roadmap)

1.  **Refatoração de Layout (UI/UX Premium):** Modernização visual dos Dashboards.
2.  **Módulo de Inteligência Artificial:** Integração mais profunda para análise de sentimento em reviews e sugestão de respostas.
3.  **App Mobile (Futuro):** API RESTful para suporte a aplicativo nativo.
