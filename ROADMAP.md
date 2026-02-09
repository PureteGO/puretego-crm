# Roadmap & Próximos Afazeres (PURETEGO CRM)

## 🚀 Novas Funcionalidades Estruturais (SaaS)

### 1. Gestão de Pacotes SaaS (Maps2GO -> Clientes)
- [ ] Criar interface no painel **SaaS Admin** para que a Maps2GO possa alterar o `plan_tier` de qualquer empresa (Tenant) cadastrada.
- [ ] Implementar visualização dos limites de cada pacote (v4 de API Google, usuários, histórico de rankings) no painel do administrador Maps2GO.
- [ ] Criar log de faturamento/vencimento de pacotes dentro do registro da empresa.

### 2. Níveis de Privilégios Internos (Configuráveis pelo Tenant Owner)
- [ ] Desenvolver interface de "Gestão de Cargos" onde o dono da empresa (Tenant Owner) possa:
    - [ ] Criar cargos personalizados (ex: "Supervisor de GMB", "Vendedor Junior").
    - [ ] Ativar/Desativar permissões granulares para cada cargo (View, Edit, Delete, Manage GMB, Financeiro).
- [ ] Refatorar os decorators de `permission_required` para buscar as permissões dinamicamente no banco de dados, em vez de depender apenas de roles estáticos.

---

## 🛠️ Manutenção e Debugging (Em Andamento)

### 3. Integração Google Business Profile
- [x] Correção do link entre Conta Google e Cliente CRM.
- [x] Botão para auditoria oficial forçada.
- [ ] Automatizar o Sync de Insights (Rodar tarefa agendada para buscar dados das últimas 24h).

### 4. Gestão de SEO (Rankings)
- [x] Correção de erro 500 ao adicionar palavras-chave (Imports fixados).
- [ ] **Refatorar Lógica de Detecção de Rankings:** O sistema atual falha em identificar a posição mesmo quando a empresa está em #1. Necessário melhorar a precisão do matching (usar CID, site ou endereço) e debugar o retorno da API Serper.
- [ ] Gráfico de histórico de posições dentro da aba SEO do cliente.

### 5. Traduções e UX
- [ ] Revisão final de strings em Espanhol (ES) para consistência no painel.
- [ ] Testar modal de exclusão de colunas do Kanban (verificar conflitos de JS).

---
*Última atualização: 09/02/2026*
