# Próximos Passos do Projeto

## 🚀 Novas Funcionalidades (Prioridade Alta)

### 1. Financeiro & Fluxo de Caixa (Novo Foco)
Objetivo: Implementar controle de caixa mais ágil e preciso.
- **Contas a Pagar e Receber:** Revisão e aprimoramento dos lançamentos.
- **Pagamentos e Recebimentos Rápidos:** Criar interfaces otimizadas (modais ou ações rápidas) para registrar movimentações sem precisar navegar por muitas telas.
- **Relatórios de Fluxo de Caixa:** Visualização clara das entradas e saídas previstas x realizadas.

### 2. Emissão de Propostas
Objetivo: Simplificar e agilizar a criação de propostas comerciais.
- **Fluxo de Criação:** Revisar o passo a passo para torná-lo mais fluido.
- **Modelos de Proposta:** Garantir que os templates estejam gerando documentos profissionais e corretos.
- **Envio:** Facilitar o envio direto ou geração de PDF/Link para o cliente.

---

## 🛠️ Conclusão da Fase Atual (Traduções e UI)

### 3. Falta Apenas Compilar (Imediato - Manhã)
O trabalho de tradução está 90% pronto.
1. **Executar Script:** `python fill_google_translations.py` (Preenche chaves faltantes).
2. **Compilar:** `venv\Scripts\pybabel compile -d app/translations`.
3. **Validar:** Verificar Dashboard e Google Page em Português/Espanhol.

### 4. Responsividade Mobile
- **Dashboard:** Corrigir quebra de texto no card "Aguardando Pagamento".
- **Integração Google:** Ajustar tabela para telas pequenas (scroll horizontal ou cards).

### 5. Limpeza Técnica
- Remover scripts temporários (`fill_google_translations.py`, `_fix_template.py`, etc).
