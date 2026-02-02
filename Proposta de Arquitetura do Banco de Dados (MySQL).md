# Proposta de Arquitetura do Banco de Dados (MySQL)

A seguir, apresento uma proposta para a estrutura do banco de dados do sistema CRM. Este esquema foi projetado para ser relacional, eficiente e escalável, atendendo a todos os requisitos levantados para a implantação em um servidor cPanel.

## Diagrama de Entidade e Relacionamento (Conceitual)

-   Um `client` pode ter múltiplas `visits`, `proposals`, e `health_checks`.
-   Uma `visit` está sempre associada a um único `client` e a um `user` (o vendedor que realizou a visita).
-   Uma `proposal` (orçamento) é criada para um `client` específico por um `user`.
-   Cada `proposal` é composta por um ou mais `proposal_items`, onde cada item corresponde a um `service` oferecido.
-   Um `health_check` é o resultado da análise de um `client` e é armazenado para referência futura.
-   A tabela `clients` possui uma referência (`kanban_stage_id`) para a tabela `kanban_stages`, indicando sua posição no pipeline de vendas.

## Estrutura Detalhada das Tabelas

Abaixo está a definição de cada tabela, suas colunas e os relacionamentos.

### Tabela: `users`
Armazena as credenciais e informações dos usuários do sistema (vendedores).

| Coluna | Tipo | Descrição |
| --- | --- | --- |
| `id` | INT, PK, AUTO_INCREMENT | Identificador único do usuário. |
| `name` | VARCHAR(255) | Nome completo do usuário. |
| `email` | VARCHAR(255), UNIQUE | Endereço de e-mail para login. |
| `password` | VARCHAR(255) | Senha criptografada. |
| `created_at` | TIMESTAMP | Data e hora de criação do registro. |

### Tabela: `kanban_stages`
Define as etapas editáveis do pipeline de vendas (formato Kanban).

| Coluna | Tipo | Descrição |
| --- | --- | --- |
| `id` | INT, PK, AUTO_INCREMENT | Identificador único da etapa. |
| `name` | VARCHAR(255) | Nome da etapa (ex: "Primeiro Contato", "Proposta Enviada"). |
| `order` | INT | Ordem de exibição da etapa no Kanban. |
| `created_at` | TIMESTAMP | Data e hora de criação do registro. |

### Tabela: `clients`
Armazena os dados dos clientes prospectados e ativos.

| Coluna | Tipo | Descrição |
| --- | --- | --- |
| `id` | INT, PK, AUTO_INCREMENT | Identificador único do cliente. |
| `name` | VARCHAR(255) | Nome da empresa/cliente. |
| `gmb_profile_name` | VARCHAR(255) | Nome do perfil no Google Meu Negócio para a busca na SerpApi. |
| `contact_name` | VARCHAR(255) | Nome do contato principal na empresa. |
| `phone` | VARCHAR(50) | Telefone de contato. |
| `email` | VARCHAR(255) | E-mail de contato. |
| `address` | TEXT | Endereço do cliente. |
| `kanban_stage_id` | INT, FK (`kanban_stages.id`) | Identificador da etapa atual do cliente no pipeline. |
| `created_at` | TIMESTAMP | Data e hora de criação do registro. |

### Tabela: `visits`
Registra todas as interações e visitas realizadas a um cliente.

| Coluna | Tipo | Descrição |
| --- | --- | --- |
| `id` | INT, PK, AUTO_INCREMENT | Identificador único da visita. |
| `client_id` | INT, FK (`clients.id`) | Cliente que foi visitado. |
| `user_id` | INT, FK (`users.id`) | Usuário que realizou a visita. |
| `notes` | TEXT | Anotações sobre a visita, pontos de fechamento, etc. |
| `next_step` | TEXT | Próxima ação a ser tomada com este cliente. |
| `visit_date` | DATETIME | Data e hora da visita. |
| `created_at` | TIMESTAMP | Data e hora de criação do registro. |

### Tabela: `health_checks`
Armazena os resultados da análise do perfil Google Meu Negócio (Health Check).

| Coluna | Tipo | Descrição |
| --- | --- | --- |
| `id` | INT, PK, AUTO_INCREMENT | Identificador único do Health Check. |
| `client_id` | INT, FK (`clients.id`) | Cliente analisado. |
| `score` | INT | Pontuação final (0-100). |
| `report_data` | JSON | Dados completos do relatório em formato JSON para flexibilidade. |
| `created_at` | TIMESTAMP | Data e hora de criação do registro. |

### Tabela: `services`
Catálogo de serviços oferecidos pela Puretego, base para os orçamentos.

| Coluna | Tipo | Descrição |
| --- | --- | --- |
| `id` | INT, PK, AUTO_INCREMENT | Identificador único do serviço. |
| `name` | VARCHAR(255) | Nome do serviço (ex: "Otimização PREMIUM GMB"). |
| `description` | TEXT | Descrição detalhada do serviço. |
| `base_price` | DECIMAL(10, 2) | Preço base do serviço (pode ser ajustado no orçamento). |
| `created_at` | TIMESTAMP | Data e hora de criação do registro. |

### Tabela: `proposals`
Armazena os orçamentos gerados para os clientes.

| Coluna | Tipo | Descrição |
| --- | --- | --- |
| `id` | INT, PK, AUTO_INCREMENT | Identificador único do orçamento. |
| `client_id` | INT, FK (`clients.id`) | Cliente para o qual o orçamento foi gerado. |
| `user_id` | INT, FK (`users.id`) | Usuário que gerou o orçamento. |
| `total_amount` | DECIMAL(10, 2) | Valor total do orçamento. |
| `payment_terms` | TEXT | Condições de pagamento negociadas. |
| `status` | VARCHAR(50) | Status do orçamento (ex: "Enviado", "Aprovado", "Recusado"). |
| `pdf_file_path` | VARCHAR(255) | Caminho para o arquivo PDF do orçamento no servidor. |
| `created_at` | TIMESTAMP | Data e hora de criação do registro. |

### Tabela: `proposal_items`
Associa os serviços específicos a um orçamento, permitindo a flexibilidade de preços.

| Coluna | Tipo | Descrição |
| --- | --- | --- |
| `id` | INT, PK, AUTO_INCREMENT | Identificador único do item. |
| `proposal_id` | INT, FK (`proposals.id`) | Orçamento ao qual este item pertence. |
| `service_id` | INT, FK (`services.id`) | Serviço do catálogo que está sendo ofertado. |
| `price` | DECIMAL(10, 2) | Preço final do serviço para este orçamento específico. |
| `description` | TEXT | Descrição customizada do serviço para este orçamento, se necessário. |
