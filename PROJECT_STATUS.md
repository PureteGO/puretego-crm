# 📊 PureteGO CRM - Status & Roadmap

**Data:** 24/05/2026 (Kanban Inactivity & PDF Stability Day)
**Versão:** MVP - Produção Estabilizada + Kanban Inactivity + PDF Fix
**Status do Sistema:** 🟢 Operacional (Produção & Local)

---

## 📍 1. Onde Estamos (Status Atual)

O sistema passou por uma fase crítica de estabilização em produção e agora está funcional e robusto.

### ✅ Concluído Hoje (24/05/2026 - Kanban & PDF Fix)
*   **Controle de Inatividade no Kanban**:
    *   Implementado destaque colorido sutil por inatividade nos cartões (amarelo para $\ge$ 7 dias, vermelho para $\ge$ 15 dias).
    *   Implementada rotina de auto-arquivamento após 21 dias sem movimentação.
    *   Adicionado botão de fechar (`x`) para remoção manual rápida nos cartões do Kanban.
    *   Criada a visualização **Repositório de Removidos** (`/clients/kanban/removed`) com barra de buscas JS dinâmica e ação de restauração instantânea.
*   **Estabilidade de PDF de Propostas**:
    *   Corrigido o erro crítico de dependência no servidor: `TypeError: PDF.__init__() takes 1 positional argument but 3 were given` travando `pydyf==0.10.0` no `requirements.txt`.
    *   Deploy completo realizado e serviço Gunicorn daemon (`maps2gosaas.service`) reiniciado com sucesso no VPS.

### ✅ Concluído Anteriormente
*   **Estabilidade de Produção**:
    *   Resolvidos erros de `DetachedInstanceError` em todas as rotas principais (Dashboard, Clientes, Relatórios).
    *   Implementado `joinedload` exaustivo para garantir que dados de relacionamentos subam sem falhas.
    *   Blindagem contra valores nulos em filtros de moeda e templates.
*   **Módulo Health Check (Auditoria GMB)**:
    *   Fluxo completo: Criação -> Análise Real (SerpApi) -> Gravação -> Visualização -> Deleção.
    *   **Inteligência Artificial**: Geração automática de Recomendações do Especialista e Problemas Críticos.
*   **Localização & UI**:
    *   Transição do sistema para **Espanhol (Paraguay)** como idioma primário.
    *   Adicionados Campos Detalhados no Cliente (Decisor, Recepcionista, Fatores de Decisão, etc.).
    *   Agenda do Dashboard unificada (Visitas + Interações Agendadas).
*   **Segurança & RBAC (Níveis de Acesso)**:
    - **Novo Cargo**: Implementado o "Gestor de Perfil GMB" (Gestor do Perfil GMB).
    - **Lógica Granular**: Permissão de "Ver Todos / Editar Próprios" para Localizações GMB, SEO e HealthChecks.
    - **Restrição por Plano**: O cargo só está disponível para empresas nos planos Agency Lean e Structured.
    - **Bypass Superadmin**: Garantido que o Superadmin retém acesso global irrestrito.
*   **Integração Google Business Profile**:
    - Consolidação de rotas e melhoria na segurança de vinculação de perfis.
    - Adicionado suporte a Insights GMB e Auditorias do Especialista.
*   **Infraestrutura**:
    *   Deploy contínuo via GitHub Actions operando perfeitamente.

### ✅ Concluído Hoje (Maratona de 18h)
*   **Módulo de Orçamentos (Budget Module)**: Preços e descrições agora são vinculados ao banco de dados com suporte a preenchimento automático de pacotes.
*   **Alertas & Notificações**: Sistema de alertas para tarefas atrasadas implementado (badge na Agenda e alerta pulsante no Dashboard).
*   **Segurança & RBAC (Níveis de Acesso)**: Implementado cargo "Gestor de Perfil GMB" com permissões granulares e bypass de superadmin.
*   **Dashboard Executivo**: Implementadas métricas de Conversão, Ticket Médio, Valor em Pipeline e Gráfico de Desempenho Mensal.

### 🚧 Em Andamento / Próximos Desafios
*   **Melhoria do Fluxo de Orçamentos e Propostas (Foco Imediato)**:
    *   Aprimorar o assistente e interface de criação de orçamentos/propostas.
    *   Otimizar a diagramação dos templates de PDF e visualização pública.
*   **Arquitetura Assíncrona**: Preparar ambiente para Celery/Redis para tarefas pesadas.
*   **SaaS Multi-tenant**: Refinar o fluxo de assinatura e limites de usuários por plano.

---

## 🗺️ 2. Para Onde Vamos (Próximos Passos)

### 🎯 Curto Prazo
1.  **Fluxo de Propostas & Orçamentos**: Refinar a experiência de criação e o visual dos PDFs.
2.  **Notificações**: Alertas simples para tarefas atrasadas na agenda.

### 🚀 Médio Prazo (Rumo aos 5k usuários)
1.  **Arquitetura Assíncrona**: Mover SerpApi e PDF para Celery/Redis.
2.  **Dashboard Executivo**: Gráficos de conversão de leads por etapa do Kanban.

---

## ⚠️ Pontos de Atenção
*   **Créditos de API**: Monitorar o uso da SerpApi conforme o volume de auditorias crescer.
*   **Session Timeout**: Ajustar o tempo de sessão no cPanel para evitar logouts inesperados durante o uso.

---

## 🛑 Ponto de Rollback (Pré-Refactoring)
**Data:** 06/02/2026 16:55
Criado antes do início da reestruturação de funcionalidades e níveis de acesso.

*   **Backup do Código (Zip):** `C:\ProAG\puretego-crm\FULL_BACKUP_PRE_REFACTOR_20260206_165540.zip`
*   **Backup do Banco de Dados (SQL):** `C:\ProAG\puretego-crm\FULL_DB_BACKUP_PRE_REFACTOR_20260206_165712.sql`

**Instruções para Restauração:**
1.  **Código:** Descompactar o zip na raiz do projeto, sobrescrevendo os arquivos existentes (exceto `venv` e `.env` se não necessário).
2.  **Banco de Dados:** Importar o arquivo `.sql` via linha de comando ou Workbench/HeidiSQL.
    *   Comando: `mysql -u root -p puretego_crm < FULL_DB_BACKUP_PRE_REFACTOR_20260206_165712.sql`
## ⚙️ 3. Configurações Finais & Checklist de Lançamento
1.  **Job Agendado (Sync GMB)**: Implementar script cron para rodar `service.sync_insights_to_cache` semanalmente para todos os clientes ativos.
2.  **Validação de Website**: Garantir que todos os leads tenham o campo `website` preenchido para auditorias de SEO.
3.  **Traduções Dinâmicas**: Revisar as novas labels de "Insights GMB" no arquivo `.po` para manter consistência com o Espanhol/Português.
4.  **Monitoramento de Performance**: Verificar impacto das queries de `total_sum` no Chart.js em bases com mais de 1k registros.
