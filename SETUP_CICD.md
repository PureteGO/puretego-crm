# Guia de Configuração CI/CD (GitHub Actions + cPanel)

Para que o deploy automático funcione, precisamos configurar o acesso entre o GitHub e o seu cPanel.

## 1. No cPanel (Preparação)

1.  Acesse **Git™ Version Control**.
2.  Crie um repositório (se ainda não existir) clonando o seu repo do GitHub.
    *   *Dica:* Desmarque "Clone repository" se quiser criar um vazio, ou cole a URL do seu GitHub.
    *   Anote o **Repository Path** (ex: `/home/seusuario/repositories/puretego-crm`).

3.  Acesse **SSH Access** (Acesso SSH).
    *   Gere um novo par de chaves (Key Pair) ou use um existente.
    *   **Importante:** Você precisa da **Chave Privada (Private Key)**.
    *   Autorize a chave pública no mesmo menu ("Manage" -> "Authorize").
    *   Baixe e abra a Chave Privada no seu bloco de notas. Copie todo o conteúdo.

## 2. No GitHub (Secrets)

Para não expor suas senhas no código, usamos "Secrets".

1.  Vá no seu repositório no GitHub -> **Settings** -> **Secrets and variables** -> **Actions**.
2.  Clique em **New repository secret**.
3.  Adicione as seguintes chaves:

    | Nome da Secret | Valor |
    | :--- | :--- |
    | `CPANEL_HOST` | O endereço do seu site (ex: `puretego.online` ou o IP do servidor). |
    | `CPANEL_USERNAME` | Seu usuário de login do cPanel. |
    | `CPANEL_SSH_KEY` | O conteúdo da **Chave Privada** SSH que eu gerei para você. |
    | `CPANEL_SSH_PASSPHRASE` | A senha da chave SSH: `PureTego_Deploy_2026_@_Secure_SSH_Access!` |

## 3. Ajuste o Script de Deploy (`.github/workflows/deploy.yml`)

1.  Abra o arquivo `.github/workflows/deploy.yml`.
2.  Verifique a linha que começa com `cd /home/...`.
3.  Certifique-se que o caminho aponta para onde o repositório está no seu cPanel (o **Repository Path** do passo 1).

## 4. Testar

Faça um commit e push para a branch `main`.
Vá na aba **Actions** do GitHub e veja o deploy acontecendo em tempo real!
