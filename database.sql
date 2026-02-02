-- ============================================
-- PURETEGO CRM - Database Schema
-- Sistema de CRM para gestão de prospecção
-- Compatível com MySQL 5.7+ e cPanel
-- ============================================

CREATE DATABASE IF NOT EXISTS puretego_crm CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE puretego_crm;

-- Tabela: users
-- Armazena usuários do sistema (vendedores)
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabela: kanban_stages
-- Define as etapas do pipeline de vendas
CREATE TABLE IF NOT EXISTS kanban_stages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    `order` INT NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_order (`order`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabela: clients
-- Armazena dados dos clientes prospectados
CREATE TABLE IF NOT EXISTS clients (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    gmb_profile_name VARCHAR(255),
    contact_name VARCHAR(255),
    phone VARCHAR(50),
    email VARCHAR(255),
    address TEXT,
    kanban_stage_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (kanban_stage_id) REFERENCES kanban_stages(id) ON DELETE SET NULL,
    INDEX idx_kanban_stage (kanban_stage_id),
    INDEX idx_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabela: visits
-- Registra visitas realizadas aos clientes
CREATE TABLE IF NOT EXISTS visits (
    id INT AUTO_INCREMENT PRIMARY KEY,
    client_id INT NOT NULL,
    user_id INT NOT NULL,
    notes TEXT,
    next_step TEXT,
    visit_date DATETIME NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_client (client_id),
    INDEX idx_visit_date (visit_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabela: health_checks
-- Armazena resultados da análise do Google Meu Negócio
CREATE TABLE IF NOT EXISTS health_checks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    client_id INT NOT NULL,
    score INT NOT NULL,
    report_data JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE,
    INDEX idx_client (client_id),
    INDEX idx_score (score)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabela: services
-- Catálogo de serviços oferecidos
CREATE TABLE IF NOT EXISTS services (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    base_price DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabela: proposals
-- Armazena orçamentos gerados
CREATE TABLE IF NOT EXISTS proposals (
    id INT AUTO_INCREMENT PRIMARY KEY,
    client_id INT NOT NULL,
    user_id INT NOT NULL,
    total_amount DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    payment_terms TEXT,
    status VARCHAR(50) NOT NULL DEFAULT 'draft',
    pdf_file_path VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_client (client_id),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabela: proposal_items
-- Itens individuais de cada orçamento
CREATE TABLE IF NOT EXISTS proposal_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    proposal_id INT NOT NULL,
    service_id INT NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    description TEXT,
    FOREIGN KEY (proposal_id) REFERENCES proposals(id) ON DELETE CASCADE,
    FOREIGN KEY (service_id) REFERENCES services(id) ON DELETE CASCADE,
    INDEX idx_proposal (proposal_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- DADOS INICIAIS
-- ============================================

-- Inserir etapas padrão do Kanban
INSERT INTO kanban_stages (name, `order`) VALUES
('Primeiro Contato', 1),
('Visita Agendada', 2),
('Proposta Enviada', 3),
('Negociação', 4),
('Fechado - Ganho', 5),
('Fechado - Perdido', 6);

-- Inserir serviços padrão da Puretego
INSERT INTO services (name, description, base_price) VALUES
('Otimização PREMIUM GMB - 90 dias', 'Atualização de perfil completo, Otimização para SEO, Fotos 360 com Tour Virtual, Registro de produtos/serviços, 90 dias de seguimento, Publicações semanais, Resposta a reseñas, Capacitação, Integração WhatsApp Business', 3500000.00),
('Otimização PREMIUM GMB - 120 dias', 'Atualização de perfil completo, Otimização para SEO, Fotos 360 com Tour Virtual, Registro de produtos/serviços, 120 dias de seguimento, Publicações semanais, Resposta a reseñas, Capacitação, Integração WhatsApp Business', 4500000.00),
('Desenvolvimento Site Institucional', 'Registro e Gestão de Domínios, Hospedagem web incluída, Desenvolvimento de Site Web, Certificação SSL 128-bit, Conteúdo institucional, 50 contas de email profissionais, Manutenção mensal', 3500000.00),
('Desenvolvimento Tienda Virtual', 'Todos os itens do Site Institucional, Lançamento dos primeiros 50 produtos, Funcionalidades para venda online, Carrinho de compra, Promoções e descontos, Registro de clientes, Integração PagoPar/Bancard', 6500000.00),
('Vídeo Institucional', 'Criação de vídeo institucional até 1 minuto formato 16:9', 500000.00),
('Consultoria Google Ads', 'Consultoria inicial para tráfico pago Google ADS (investimento mínimo 80us mensual)', 800000.00);

-- Inserir usuário padrão (senha: admin123 - ALTERAR EM PRODUÇÃO)
-- Senha criptografada com password_hash() do PHP
INSERT INTO users (name, email, password) VALUES
('Administrador', 'admin@puretego.online', '$2y$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi');

-- ============================================
-- FIM DO SCRIPT
-- ============================================
