# Guia de Atualização Manual (Sem Terminal)

Como você não tem acesso ao Terminal SSH, siga estes passos para atualizar o sistema pelo painel visual do cPanel.

## Passo 1: Atualizar o Banco de Dados (phpMyAdmin)
1. Acesse o **cPanel**.
2. Abra a ferramenta **phpMyAdmin**.
3. No menu lateral esquerdo, clique no seu banco de dados (ex: `..._puretego_crm`).
4. Clique na aba **SQL** (topo da tela).
5. Copie TODO o conteúdo do arquivo `PRODUCTION_UPDATE.sql` (que está no projeto) e cole na caixa de texto.
6. Clique em **Executar** (Go).
   - *Se aparecer mensagem de sucesso (verde), deu certo.*
   - *Se der erro dizendo "Duplicate column", é porque a coluna já existe. Tudo bem.*

## Passo 2: Atualizar os Arquivos (File Manager)
**Opção A: Se você configurou o Git no cPanel (Git Version Control)**
1. Vá em **Git™ Version Control** no cPanel.
2. Encontre o repositório `puretego-crm`.
3. Clique em **Manage**.
4. Clique na aba **Pull or Deploy**.
5. Clique no botão **Update from Remote**.
   - *Isso vai baixar as mudanças do GitHub automaticamente.*

**Opção B: Se você fez upload manual (Zip)**
1. No seu computador, gere um novo zip (se tiver o script, rode `python pack_for_deploy.py`, senão zipe a pasta `app`, `config` e arquivos raiz).
2. Vá no **File Manager** do cPanel.
3. Navegue até a pasta do CRM.
4. Faça upload do novo Zip e extraia (sobrescrevendo os arquivos antigos).

## Passo 3: Reiniciar a Aplicação
Sempre que o código ou banco muda, é bom reiniciar.
1. Vá em **Setup Python App** no cPanel.
2. Encontre sua aplicação.
3. Clique no botão **Restart**.

## Passo 4: Testar
Acesse https://puretego.online/crm e verifique se o login funciona e se os novos pacotes aparecem na criação de cliente.
