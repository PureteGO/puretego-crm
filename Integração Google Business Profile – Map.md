Integração Google Business Profile – Maps2GO (Design Técnico Completo)
Este documento descreve a arquitetura e fluxo para integrar a Google Business Profile API ao Maps2GO CRM, considerando o cenário de agência com múltiplas contas Google e múltiplas locations por conta.

1. Contexto – Projeto Google Cloud já criado (Passo 1)
Projeto Google Cloud
Nome: Maps2GO

ID do projeto: maps2go-486517

APIs habilitadas
✅ My Business Business Information API v1 – dados locais da empresa (locations, informações de negócio).
​

✅ My Business Account Management API v1 – gestão de contas e locations (accounts/locations).
​

Observação: Essas APIs substituem a antiga “Google My Business API v4” e dão acesso a:

Reviews (leitura e resposta, via endpoints equivalentes / compat layer).

Informações de localização (endereços, nomes, IDs).

Estrutura de contas e locations (multi‑location, multi‑conta).

OAuth 2.0 Client ID
Tipo: Web Application

Nome: Maps2GO Web Client

Client ID:
722401847261-lfoe4j55kibqtt2e1r2ruv6qucens07b.apps.googleusercontent.com

Client Secret: (armazenar em variável de ambiente, não commitar)

Redirect URI autorizada:
https://app.maps2go.online/oauth/callback

Consent Screen
Nome da aplicação: Maps2GO CRM

Email de suporte: puretegoonline@gmail.com

Tipo: Externo (usuários externos)

2. Conceito de Integração – Multi-Conta Google, Multi-Location
Cenário típico da agência:

Uma Company (tenant) no Maps2GO (ex.: PureteGo).

Várias contas Google usadas pela agência:

puretegoonline@gmail.com (principal)

puretego1@...

puretego2@...

puretego3@...

Cada conta Google administra 5–25 perfis GMB (locations) de clientes finais.

Estratégia
Maps2GO permite conectar várias contas Google por Company (tenant).

Para cada conta Google, Maps2GO lista as locations disponíveis.

Para cada location, o usuário mapeia para um Client do CRM.

Todas as operações (reviews, dados, respostas) usam:

A conta Google correta (via tokens daquela conexão).

O location_name correto daquela location.

3. Novos modelos de banco (SQLAlchemy)
3.1. Tabela GoogleConnection
Representa uma conta Google conectada via OAuth para uma Company.

class GoogleConnection(db.Model):
    __tablename__ = "google_connections"

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False)

    google_account_email = db.Column(db.String(255), nullable=True)

    access_token = db.Column(db.Text, nullable=False)
    refresh_token = db.Column(db.Text, nullable=True)
    expires_at = db.Column(db.DateTime, nullable=False)

    scopes = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    company = db.relationship("Company", backref="google_connections")

3.2. Tabela GMBLocationLink
Representa a ligação entre um Client do Maps2GO e uma location administrada por uma GoogleConnection.

class GMBLocationLink(db.Model):
    __tablename__ = "gmb_location_links"

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False)

    google_connection_id = db.Column(
        db.Integer, db.ForeignKey("google_connections.id"), nullable=False
    )

    client_id = db.Column(db.Integer, db.ForeignKey("clients.id"), nullable=False)

    # Nome completo da location na Business Profile API
    # Exemplo: "accounts/123456789/locations/987654321"
    gmb_location_name = db.Column(db.String(255), nullable=False)

    is_primary = db.Column(db.Boolean, default=True, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    company = db.relationship("Company", backref="gmb_location_links")
    google_connection = db.relationship("GoogleConnection", backref="location_links")
    client = db.relationship("Client", backref="gmb_location_links")

Observação: inicialmente você pode assumir 1 location primária por Client, mas esse design já permite múltiplas locations se necessário.

4. Fluxo de OAuth – Conectar uma conta Google
4.1. Escopo recomendado
Use o escopo moderno para Business Profile:

https://www.googleapis.com/auth/business.manage – gerenciar localizações e reviews.

4.2. URL de autorização
Quando o usuário (da Company) clica em “Conectar nova conta Google”:

Backend monta URL de autorização:

GET https://accounts.google.com/o/oauth2/v2/auth
  ?client_id=722401847261-lfoe4j55kibqtt2e1r2ruv6qucens07b.apps.googleusercontent.com
  &redirect_uri=https://app.maps2go.online/oauth/callback
  &response_type=code
  &scope=https://www.googleapis.com/auth/business.manage
  &access_type=offline
  &prompt=consent
  &state=JSON_URL_ENCODED({ "company_id": 123, "connection_type": "google_business" })

4.3. Rota /oauth/callback (Flask)
Recebe code e state.

Valida/decodifica state (inclui company_id).

Troca code por tokens no endpoint OAuth do Google.

Salva/atualiza registro em GoogleConnection:

Se a mesma conta Google já existir para a Company, atualiza tokens.

Caso contrário, cria um novo.

Opcional: chamar uma API do Google para obter o e‑mail (google_account_email) da conta autenticada, para exibir na UI.

5. Mapeando locations → Clients
5.1. Listar accounts e locations de uma conexão
Para cada GoogleConnection:

Usar My Business Account Management API para listar contas:

GET https://mybusinessaccountmanagement.googleapis.com/v1/accounts (com Authorization: Bearer <access_token>).

Escolher a account correta (na maioria dos casos o usuário terá 1; se tiver mais, mostrar lista).

Usar My Business Business Information API para listar locations:

GET https://mybusinessbusinessinformation.googleapis.com/v1/accounts/{accountId}/locations.
​

Resultado típico: lista de locations da conta Google conectada, com:

name (ex.: accounts/123456789/locations/987654321)

title

storeCode (se houver)

primaryCategory

storefrontAddress (endereço, cidade, país)

5.2. Tela “Mapear locations para Clients”
Na interface de administração da Company:

Aba: “Gerenciar Perfis Google”.

Para cada GoogleConnection (e‑mail Google):

Mostrar lista de locations daquela conta.

Para cada location:

Colunas:

Nome do local

Endereço

Campo Client (dropdown com Clients do Maps2GO dessa Company)

Flag “Primária”

Ao salvar:

Criar/atualizar registros em GMBLocationLink com:

company_id

google_connection_id

client_id

gmb_location_name

is_primary

Dessa forma, o sistema sabe qual perfil GMB corresponde a qual Client e qual conta Google deve ser usada.

6. Busca de reviews da location
Com:

GoogleConnection (tokens da conta Google).

GMBLocationLink.gmb_location_name (ID da location).

Você pode:

Determinar qual conexão usar para um Client:

Para um client_id, buscar GMBLocationLink principal (is_primary = True).

Montar a chamada para listar reviews dessa location:

Endpoint compatível (v1/v4, dependendo da lib que vocês usarem) – ex. método equivalente a:
accounts.locations.reviews.list / locations.reviews.list.

Armazenar as reviews em uma tabela gmb_reviews (opcional, mas recomendado para cache e analytics).

7. Responder reviews
Quando o usuário do Maps2GO escrever uma resposta na UI:

Para a review selecionada, buscar:

GMBLocationLink → google_connection_id + gmb_location_name

GoogleConnection → access_token

Chamar o endpoint de reply/updateReply da Google Business Profile API para aquela review específica.
​

Atualizar o registro de review em gmb_reviews com a reply enviada.

Logar uma Interaction (ex.: tipo "gmb_review_reply") para auditoria no CRM.

8. Job de refresh de tokens e sincronização
8.1. Refresh de tokens (cron / Celery)
Job periódico (ex.: a cada 30 min):

Para cada GoogleConnection:

Se expires_at < now() + 5 minutos:

Usar refresh_token para obter novo access_token.

Atualizar access_token e expires_at.

8.2. Sincronização de reviews
Outro job (ex.: a cada 1h):

Para cada GMBLocationLink:

Verificar última data de sync de reviews.

Chamar a API de reviews da Business Profile para gmb_location_name (paginando se necessário).
​

Inserir/atualizar reviews em gmb_reviews.

9. UX Resumida
9.1. Para o usuário agência (Company)
Menu Integrações → Google Business Profile:

Ver lista de contas Google conectadas.

Botão “Conectar nova conta Google” (abre OAuth).

Tela “Perfis Google Conectados”:

Para cada conta:

Lista de locations.

Dropdown para associar location → Client.

Indicar quais locations já estão ligadas.

9.2. Para o SDR/Consultor na tela do Client
Mostrar status:

“Perfil Google conectado: SIM/NÃO”.

Se SIM:

Mostrar conta Google usada (email da conexão).

Mostrar nome/location selecionada.

Aba “Reviews”:

Listar reviews, estrelas, datas.

Botão “Responder” (manual, por enquanto).

10. Resumo de Entidades Novas
GoogleConnection

Representa uma conta Google conectada via OAuth para uma Company.

GMBLocationLink

Representa o vínculo entre um Client do Maps2GO e uma location da Business Profile API.

(Opcional) GMBReview

Cache local das reviews por Client/Location para dashboard, analytics, e Health Check.

Esse design cobre:

Múltiplas contas Google por agência.

Múltiplas locations por conta.

Mapeamento explícito location → Client.

Base para, no futuro, adicionar:

IA de respostas automáticas.

Métricas de Health Check que consideram reviews (respondidas/não respondidas, notas etc.).