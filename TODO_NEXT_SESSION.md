# Próximos Passos - Retomada

## 1. Correção do Botão "Eliminar" (Kanban)
- **Status Atual**: O código foi refatorado para usar `data-confirm` e listeners globais para evitar conflitos de sintaxe.
- **Problema**: O usuário relata que ainda não funciona.
- **Ação**: 
    - Verificar se o arquivo JS está carregando cache antigo.
    - Testar se o listener `document.addEventListener('submit'...)` está capturando o evento corretamente.
    - Inspecionar console do navegador para erros silenciosos.

## 2. Consistência nas Traduções
- **Status Atual**: Vários templates traduzidos, mas há inconsistências relatadas (partes em PT, partes em ES/EN misturadas).
- **Ação**:
    - Revisar templates do Kanban e Clientes.
    - Verificar arquivos `.po` (traduções compiladas).
    - Garantir que `_('Texto')` está sendo usado em todo lugar visível.

## 3. Integração Google API
- **Status Atual**: Quotas identificadas como "0" no Google Console.
- **Ação**: Confirmar se o usuário ajustou as quotas para > 0 para permitir listar as empresas.

## 4. Preparação para Deploy (Novo Servidor)
- **Status**: Servidor disponível amanhã.
- **Ações Críticas**:
    - [ ] Atualizar `requirements.txt` (garantir todas libs).
    - [ ] Adicionar novo domínio nas **Authorized Redirect URIs** do Google Cloud Console.
    - [ ] Configurar variáveis de ambiente (`.env`) de produção.
    - [ ] Validar conexão MySQL no novo servidor.
