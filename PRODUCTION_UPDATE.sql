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

-- 2. Adicionar Coluna na Tabela de Clientes
-- Se esta linha der erro dizendo que a coluna já existe, pode ignorar
ALTER TABLE clients ADD COLUMN interested_package_id INTEGER;

-- 3. Criar Vínculo (Foreign Key)
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
