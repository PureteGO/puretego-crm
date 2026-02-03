# 📊 PureteGO CRM - Status & Roadmap

**Data:** 03/02/2026
**Versão:** MVP - Fase de Desenvolvimento Local
**Status do Sistema:** 🟢 Operacional (Local)

---

## 📍 1. Onde Estamos (Status Atual)

O sistema básico está funcional e rodando localmente com configurações de produção simuladas.

### ✅ Concluído
*   **CI/CD & Deploy**:
    *   Pipeline GitHub Actions configurado e SUCCEEDING (Deploy via FTP).
    *   Segredos de repositório configurados automaticamente.
    *   Deploy em Staging (cPanel) realizado com sucesso.
*   **Infraestrutura Local**:
    *   Ambiente Python configurado (`venv`).
    *   Banco de dados MySQL (XAMPP) configurado e populado (`puretego_crm`).
*   **Funcionalidades Principais**:
    *   **Health Check**: Relatório visual 100% corrigido e populando dados corretamente.
    *   **Autenticação**: Login de admin implementado.
    *   **Propostas**: Geração de PDF via `xhtml2pdf` com layout profissional.

### 🚧 Em Andamento / Para Validar
*   **Configuração Final Produção**: Criar arquivo `.env` manualmente no cPanel.
*   **Validação Visual Remota**: Acessar a URL de staging para garantir que tudo carrega como no local.

---

## 🗺️ 2. Para Onde Vamos (Próximos Passos)

### 🎯 Curto Prazo (Hoje/Amanhã)
1.  **Validação Visual**: Navegar pelo sistema rodando localmente para garantir que não há erros de template (Jinja2) ou rotas quebradas.
2.  **Refinamento de UI**: Ajustar detalhes visuais nos novos módulos (CSS/Layout).
3.  **Deploy em Staging**: Colocar essa versão no cPanel para teste real remoto.

### 🚀 Médio Prazo (Rumo aos 5k usuários)
1.  **Fila de PDFs Assíncrona**: Mover a geração de PDF para background (Celery) para não travar o servidor quando múltiplos usuários gerarem propostas.
2.  **Frontend Dinâmico**: Migrar partes interativas para Vue.js ou React conforme a complexidade aumentar.
3.  **Infraestrutura**: Migrar do cPanel para um ambiente containerizado (Docker/Cloud SQL) quando a base de usuários crescer.

---

## ⚠️ Pontos de Atenção (Arquitetura)
*   **Performance**: A geração de PDF atual bloqueia a thread do servidor. Para poucos usuários é OK, mas é o primeiro gargalo a ser resolvido para escala.
*   **Segurança**: Garantir que `SECRET_KEY` e senhas de banco de produção sejam fortes e gerenciadas via variáveis de ambiente (já implementado via `.env`).
