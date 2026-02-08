-- PURETEGO CRM - Finance Module Schema (Manual Fix)
-- Run this in your production database via phpMyAdmin or MySQL client to fix the 500 error

SET FOREIGN_KEY_CHECKS=0;

-- 1. Create Payables Table
CREATE TABLE IF NOT EXISTS `payables` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `company_id` int(11) NOT NULL,
  `description` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `amount` decimal(12,2) NOT NULL,
  `due_date` date NOT NULL,
  `paid_at` datetime DEFAULT NULL,
  `status` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT 'open',
  `category` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT 'other',
  `notes` text COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `ix_payables_company_id` (`company_id`),
  KEY `ix_payables_due_date` (`due_date`),
  KEY `ix_payables_status` (`status`),
  KEY `ix_payables_category` (`category`),
  CONSTRAINT `fk_payables_company` FOREIGN KEY (`company_id`) REFERENCES `companies` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. Create Receivables Table
CREATE TABLE IF NOT EXISTS `receivables` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `company_id` int(11) NOT NULL,
  `client_id` int(11) NOT NULL,
  `deal_id` int(11) DEFAULT NULL,
  `project_id` int(11) DEFAULT NULL,
  `description` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `amount` decimal(12,2) NOT NULL,
  `due_date` date NOT NULL,
  `paid_at` datetime DEFAULT NULL,
  `status` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT 'open',
  `payment_method` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `external_id` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `notes` text COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `ix_receivables_company_id` (`company_id`),
  KEY `ix_receivables_client_id` (`client_id`),
  KEY `ix_receivables_deal_id` (`deal_id`),
  KEY `ix_receivables_project_id` (`project_id`),
  KEY `ix_receivables_due_date` (`due_date`),
  KEY `ix_receivables_status` (`status`),
  CONSTRAINT `fk_receivables_company` FOREIGN KEY (`company_id`) REFERENCES `companies` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_receivables_client` FOREIGN KEY (`client_id`) REFERENCES `clients` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_receivables_deal` FOREIGN KEY (`deal_id`) REFERENCES `deals` (`id`) ON DELETE SET NULL,
  CONSTRAINT `fk_receivables_project` FOREIGN KEY (`project_id`) REFERENCES `projects` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. Create Commissions Table (Updated Schema per Code)
CREATE TABLE IF NOT EXISTS `commissions` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `company_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `deal_id` int(11) NOT NULL,
  `receivable_id` int(11) DEFAULT NULL,
  `amount` decimal(12,2) NOT NULL,
  `commission_type` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT 'closer',
  `status` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT 'pending',
  `paid_at` datetime DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `ix_commissions_company_id` (`company_id`),
  KEY `ix_commissions_user_id` (`user_id`),
  KEY `ix_commissions_deal_id` (`deal_id`),
  KEY `ix_commissions_receivable_id` (`receivable_id`),
  KEY `ix_commissions_status` (`status`),
  CONSTRAINT `fk_commissions_company` FOREIGN KEY (`company_id`) REFERENCES `companies` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_commissions_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_commissions_deal` FOREIGN KEY (`deal_id`) REFERENCES `deals` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_commissions_receivable` FOREIGN KEY (`receivable_id`) REFERENCES `receivables` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- 4. Update Roles table to include permissions
-- If error occurs saying column exists, ignore
ALTER TABLE `roles` ADD COLUMN `can_manage_finance` tinyint(1) DEFAULT 0;
UPDATE `roles` SET `can_manage_finance` = 1 WHERE `name` IN ('owner', 'admin', 'finance', 'superadmin', 'partner');

SET FOREIGN_KEY_CHECKS=1;
