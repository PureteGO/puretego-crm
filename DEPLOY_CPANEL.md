# Guia de Deploy no cPanel (V2.0)

Este guia explica como fazer o deploy seguro do PURETEGO CRM em um servidor cPanel, seguindo as melhores práticas de segurança e deploy.

## ✅ Pré-requisitos

- Acesso ao cPanel
- **Python 3.11+** habilitado no servidor (Setup Python App)
- **MySQL 5.7+** disponível
- **Acesso SSH** (Altamente recomendado para instalar dependências)

---

## 🚀 Passo 1: Preparar o Pacote de Deploy (Localmente)

Antes de enviar, vamos criar um pacote limpo, sem arquivos desnecessários.

1. No seu computador local, execute o script de empacotamento:
   ```bash
   python pack_for_deploy.py
   ```
   Isso criará um arquivo `deploy.zip` na raiz do projeto.

---

## 📤 Passo 2: Upload e Extração

1. Acesse o **File Manager** no cPanel.
2. Navegue até a pasta onde o sistema ficará (ex: `public_html/crm` ou apenas `public_html` se for raiz).
3. Faça upload do arquivo `deploy.zip`.
4. Clique com o botão direito em `deploy.zip` e selecione **Extract**.
5. (Opcional) Delete o arquivo `deploy.zip` após extrair.

---

## 🗄️ Passo 3: Configurar o Banco de Dados MySQL

1. No cPanel, vá em **MySQL Databases**.
2. **Crie o Banco:** Nomeie algo como `seuUser_puretego_crm`.
3. **Crie o Usuário:** Nomeie algo como `seuUser_crm_user` e **gere uma senha forte**.
4. **Associe:** Adicione o usuário ao banco e marque **ALL PRIVILEGES**.
5. **Importe a Estrutura:**
   - Abra o **phpMyAdmin**.
   - Selecione o banco criado.
   - Vá na aba **Import**.
   - Escolha o arquivo `database.sql` (que veio no deploy).
   - Execute.

---

## 🐍 Passo 4: Configurar Python App no cPanel

1. No cPanel, vá em **Setup Python App**.
2. **Create Application**:
   - **Python Version**: 3.11 (ou a mais recente recomendada).
   - **Application Root**: O caminho para onde você extraiu (ex: `public_html/crm`).
   - **Application URL**: A URL de acesso (ex: `puretego.online/crm`).
   - **Application Startup File**: `run.py` (ou `passenger_wsgi.py` se o servidor exigir).
   - **Application Entry Point**: `app`
3. Clique em **Create**.

---

## 📦 Passo 5: Instalar Dependências

1. No topo da página do Python App criada, copie o "Command for entering virtual environment" (ex: `source .../bin/activate`).
2. Abra o **Terminal** no cPanel (ou acesse via SSH).
3. Cole o comando para ativar o ambiente virtual.
4. Navegue até a pasta do projeto:
   ```bash
   cd public_html/crm  # Ajuste o caminho conforme necessário
   ```
5. Instale as dependências com o cache limpo (importante para evitar erros de compilação):
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
   *Nota: Se houver erros com `weasyprint` ou `xhtml2pdf` devido a bibliotecas do sistema ausentes, contate o suporte da hospedagem, mas geralmente xhtml2pdf funciona bem.*

---

## 🔒 Passo 6: Segurança e Variáveis de Ambiente (CRÍTICO)

Esta é a etapa mais importante para a segurança. **NUNCA** edite os arquivos Python para colocar senhas. Use o `.env`.

1. Dentro da pasta do projeto (via Terminal ou File Manager), copie o exemplo:
   ```bash
   cp .env.example .env
   ```
2. Edite o arquivo `.env`:
   ```bash
   nano .env
   ```
3. Preencha com os dados REAIS de produção:

   ```env
   # Gere uma chave aleatória longa para produção
   SECRET_KEY=yoursecretkey_gerada_aleatoriamente_super_segura_123

   FLASK_ENV=production

   # Credenciais do Banco criadas no Passo 3
   DB_HOST=localhost
   DB_PORT=3306
   DB_NAME=seuUser_puretego_crm
   DB_USER=seuUser_crm_user
   DB_PASS=SuaSenhaForteAqui

   SERPAPI_KEY=sua_chave_aqui
   ```

4. **Bloqueie o acesso ao arquivo .env**:
   Execute no terminal:
   ```bash
   chmod 600 .env
   ```
   Isso garante que apenas o dono do arquivo possa lê-lo.

---

## 📂 Passo 7: Pastas e Permissões

O sistema precisa escrever PDFs e uploads.

1. Crie as pastas se não existirem:
   ```bash
   mkdir -p uploads generated_pdfs
   ```
2. Dê permissão de escrita (apenas se necessário, 755 geralmente basta, tente evitar 777 se não for estritamente necessário):
   ```bash
   chmod 755 uploads generated_pdfs
   ```

---

## 🔄 Passo 8: Reiniciar

1. Volte ao **Setup Python App** no cPanel.
2. Clique no botão **Restart** da sua aplicação.

---

## ✅ Passo 9: Verificação (Smoke Test)

1. Acesse a URL do sistema.
2. Tente fazer login.
3. **Teste Crítico**: Gere um PDF de um orçamento existente. Se o PDF for gerado e baixado corretamente, o deploy foi um sucesso total!

---

## 🆘 Troubleshooting Comum

- **PDF não gera**: Verifique se a pasta `generated_pdfs` existe e tem permissão de escrita. Verifique os logs se faltam dependências de sistema para o `xhtml2pdf`.
- **Erro 500**: Verifique o log de erro no cPanel (`stderr.log` ou link de logs na interface Python App). Geralmente é falta de dependência ou erro no `.env`.
- **Conexão Recusada DB**: Verifique Usuário, Senha e se o Host é `localhost` (algumas hospedagens usam `127.0.0.1` ou outro host).

---
**PURETEGO CRM - Deploy Guide v2**
