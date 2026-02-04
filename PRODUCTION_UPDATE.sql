-- ATUALIZAÇÃO SCRIPT PARA PRODUÇÃO (RODAR NO PHPMYADMIN)

-- 1. Criar Tabela de Pacotes (se não existir)
CREATE TABLE IF NOT EXISTS service_packages (
    id INTEGER NOT NULL AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    price NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    description TEXT,
    features TEXT,
    PRIMARY KEY (id),
    UNIQUE (name)
);

-- 2. Adicionar Colunas na Tabela de Clientes
-- Se estas linhas derem erro dizendo que a coluna já existe, pode ignorar
ALTER TABLE clients ADD COLUMN interested_package_id INTEGER;
ALTER TABLE clients ADD COLUMN receptionist_name VARCHAR(255);
ALTER TABLE clients ADD COLUMN decision_maker_name VARCHAR(255);
ALTER TABLE clients ADD COLUMN decision_factors TEXT;
ALTER TABLE clients ADD COLUMN best_contact_time VARCHAR(100);
ALTER TABLE clients ADD COLUMN preferred_contact_method VARCHAR(100);
ALTER TABLE clients ADD COLUMN observations TEXT;

-- 3. Criar Vínculo (Foreign Key)
-- Se der erro de que a constraint já existe, pode ignorar
ALTER TABLE clients ADD CONSTRAINT fk_clients_package 
FOREIGN KEY (interested_package_id) REFERENCES service_packages(id) ON DELETE SET NULL;

-- 4. Inserir os Pacotes (Dados Iniciais)
INSERT INTO service_packages (name, price, description, features) VALUES
('Start2GO', 1500000.00, 'Ideal para empreendedores e pequenos comércios.', 'Perfil Google, Dados essenciais, Carga de serviços, Link de reseñas, Até 3 fotos 360'),
('Biz2GO', 2900000.00, 'Para negócios locais que querem atrair mais tráfego.', 'Otimização padrão, Landing Page, Integração Maps/WhatsApp, Vídeo Institucional, Até 5 fotos 360'),
('Pro2GO', 3900000.00, 'Para empresas que buscam imagem premium.', 'Otimização Avançada, Site Institucional (5 seções), SEO Básico, Vídeo Institucional, Até 8 fotos 360'),
('Market2GO', 5900000.00, 'Para negócios que querem começar a vender online.', 'Site + Catálogo (20 prod), SEO Catálogo, SSL Dedicado, Até 10 fotos 360'),
('e-commerce2GO', 7900000.00, 'Para empresas que desejam uma loja virtual completa.', 'Loja Virtual (50 prod), Otimização Premium, SEO Completo, Consultoria Domínio, Até 12 fotos 360')
ON DUPLICATE KEY UPDATE 
price=VALUES(price), 
description=VALUES(description), 
features=VALUES(features);

-- 5. Tabelas de Interações (Agenda/Kanban)
CREATE TABLE IF NOT EXISTS interaction_types (
    id INTEGER NOT NULL AUTO_INCREMENT,
    name VARCHAR(50) NOT NULL,
    icon VARCHAR(50) DEFAULT 'fas fa-circle',
    is_call BOOLEAN DEFAULT FALSE,
    PRIMARY KEY (id),
    UNIQUE (name)
);

CREATE TABLE IF NOT EXISTS cadence_rules (
    id INTEGER NOT NULL AUTO_INCREMENT,
    trigger_type_id INTEGER NOT NULL,
    suggested_next_type_id INTEGER NOT NULL,
    delay_days INTEGER DEFAULT 2,
    PRIMARY KEY (id),
    FOREIGN KEY (trigger_type_id) REFERENCES interaction_types(id),
    FOREIGN KEY (suggested_next_type_id) REFERENCES interaction_types(id)
);

CREATE TABLE IF NOT EXISTS interactions (
    id INTEGER NOT NULL AUTO_INCREMENT,
    client_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    type_id INTEGER NOT NULL,
    date DATETIME,
    status ENUM('done', 'scheduled', 'skipped', 'missed'),
    notes TEXT,
    created_at DATETIME,
    updated_at DATETIME,
    PRIMARY KEY (id),
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (type_id) REFERENCES interaction_types(id)
);

-- 6. Inserir Tipos de Interação Iniciais
INSERT IGNORE INTO interaction_types (name, icon, is_call) VALUES
('Cold Visit', 'fas fa-walking', FALSE),
('Follow-up Call', 'fas fa-phone-volume', TRUE),
('Presentation Visit', 'fas fa-laptop', FALSE),
('Negotiation Call', 'fas fa-hand-holding-usd', TRUE),
('Exploratory Call', 'fas fa-phone', TRUE),
('Closing Visit', 'fas fa-signature', FALSE),
('Technical Visit', 'fas fa-tools', FALSE),
('Closing Call', 'fas fa-check-circle', TRUE);

-- 7. Inserir Regras de Cadência Iniciais
INSERT IGNORE INTO cadence_rules (trigger_type_id, suggested_next_type_id, delay_days)
SELECT t1.id, t2.id, 2 FROM interaction_types t1, interaction_types t2 WHERE t1.name = 'Cold Visit' AND t2.name = 'Follow-up Call'
UNION ALL
SELECT t1.id, t2.id, 3 FROM interaction_types t1, interaction_types t2 WHERE t1.name = 'Presentation Visit' AND t2.name = 'Negotiation Call'
UNION ALL
SELECT t1.id, t2.id, 5 FROM interaction_types t1, interaction_types t2 WHERE t1.name = 'Exploratory Call' AND t2.name = 'Presentation Visit'
UNION ALL
SELECT t1.id, t2.id, 2 FROM interaction_types t1, interaction_types t2 WHERE t1.name = 'Negotiation Call' AND t2.name = 'Closing Call';

