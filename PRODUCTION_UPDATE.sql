-- ATUALIZAÇÃO SCRIPT PARA PRODUÇÃO (RODAR NO PHPMYADMIN)
-- Versão 10.6.24-MariaDB suporta IF NOT EXISTS em ALTER TABLE

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

-- 2. Adicionar Colunas na Tabela de Clientes (IDEMPOTENTE)
ALTER TABLE clients ADD COLUMN IF NOT EXISTS interested_package_id INTEGER;
ALTER TABLE clients ADD COLUMN IF NOT EXISTS receptionist_name VARCHAR(255);
ALTER TABLE clients ADD COLUMN IF NOT EXISTS decision_maker_name VARCHAR(255);
ALTER TABLE clients ADD COLUMN IF NOT EXISTS decision_factors TEXT;
ALTER TABLE clients ADD COLUMN IF NOT EXISTS best_contact_time VARCHAR(100);
ALTER TABLE clients ADD COLUMN IF NOT EXISTS preferred_contact_method VARCHAR(100);
ALTER TABLE clients ADD COLUMN IF NOT EXISTS observations TEXT;

-- 3. Criar Vínculo (Foreign Key)
-- Nota: MySQL não suporta IF NOT EXISTS em CONSTRAINT, então usamos um bloco anônimo ou apenas ignoramos o erro manual
-- Mas a maioria dos servidores já tem a coluna, o importante é popular os tipos.

-- 4. Inserir os Pacotes (Dados Iniciais)
INSERT IGNORE INTO service_packages (id, name, price, description, features) VALUES
(1, 'Dominación en Google Maps - Pack 90 días', 3500000.00, 'Auditoría SEO Local avanzada, optimización técnica del Perfil de Empresa (GMB), gestión estratégica de reseñas e reputación, y posicionamiento en el Local Pack para máxima visibilidad.', NULL),
(2, 'Desarrollo Web de Alto Nivel', 3500000.00, 'Sitios enfocados en la conversión (CRO) y optimizados para Google. Diseño personalizado, velocidad extrema, adaptado a móviles y con DNS gestionado profesionalmente.', NULL),
(3, 'Tienda Virtual de Gran Escala', 7500000.00, 'E-commerce profesional con gestión de inventario, pasarela de pagos integrada y optimización para ventas masivas online. Incluye seguimiento de conversiones.', NULL),
(4, 'Propulsor de Tráfico (Google Ads)', 2500000.00, 'Gestión de campañas SEM focalizadas en intención de compra. Segmentación avanzada para atraer clientes calificados de forma inmediata y maximizar el ROI.', NULL);

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


