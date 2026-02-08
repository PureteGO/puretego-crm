<?php
// Script para rodar migração SQL manualmente (Solução para Erro 500)
// Coloque este arquivo na raiz do seu site (public_html) e acesse: https://app.maps2go.online/migrate_finance.php

// CONFIGURE AS CREDENCIAIS DE PRODUÇÃO AQUI
$host = 'localhost';
$user = 'puretego_admin'; // Substitua pelo usuário do cPanel
$pass = 'SUA_SENHA_AQUI'; // Substitua pela senha
$db   = 'puretego_crm';   // Substitua pelo nome do banco

// ==========================================

$conn = new mysqli($host, $user, $pass, $db);

if ($conn->connect_error) {
    die("Falha na conexão: " . $conn->connect_error);
}

echo "<h1>Aplicando Migração Financeira...</h1>";

$sql = "
-- (Copiado de migration_finance.sql)
CREATE TABLE IF NOT EXISTS `payables` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `company_id` int(11) NOT NULL,
  `description` varchar(255) NOT NULL,
  `amount` decimal(12,2) NOT NULL,
  `due_date` date NOT NULL,
  `paid_at` datetime DEFAULT NULL,
  `status` varchar(50) DEFAULT 'open',
  `category` varchar(50) DEFAULT 'other',
  `notes` text DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `receivables` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `company_id` int(11) NOT NULL,
  `client_id` int(11) NOT NULL,
  `deal_id` int(11) DEFAULT NULL,
  `project_id` int(11) DEFAULT NULL,
  `description` varchar(255) NOT NULL,
  `amount` decimal(12,2) NOT NULL,
  `due_date` date NOT NULL,
  `paid_at` datetime DEFAULT NULL,
  `status` varchar(50) DEFAULT 'open',
  `payment_method` varchar(50) DEFAULT NULL,
  `external_id` varchar(255) DEFAULT NULL,
  `notes` text DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `commissions` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `company_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `deal_id` int(11) NOT NULL,
  `receivable_id` int(11) DEFAULT NULL,
  `amount` decimal(12,2) NOT NULL,
  `commission_type` varchar(50) DEFAULT 'closer',
  `status` varchar(50) DEFAULT 'pending',
  `paid_at` datetime DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

ALTER TABLE `roles` ADD COLUMN `can_manage_finance` tinyint(1) DEFAULT 0;
UPDATE `roles` SET `can_manage_finance` = 1 WHERE `name` IN ('owner', 'admin', 'finance', 'superadmin', 'partner');
";

// Executar múltiplos comandos
if ($conn->multi_query($sql)) {
    do {
        // Armazenar primeiro result set
        if ($result = $conn->store_result()) {
            $result->free();
        }
        // Se houver mais resultados
        if ($conn->more_results()) {
            printf("-----------------\n");
        }
    } while ($conn->next_result());
    echo "<h2 style='color:green'>Migração concluída com sucesso!</h2>";
    echo "<p>Agora tente acessar o sistema novamente.</p>";
} else {
    echo "<h2 style='color:red'>Erro na migração: " . $conn->error . "</h2>";
}

$conn->close();
?>
