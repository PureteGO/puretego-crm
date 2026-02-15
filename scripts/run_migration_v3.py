"""
PURETEGO CRM - Execute Migration v3 via Python/SQLAlchemy
Kanban Sales Funnel + Tasks + Notifications
"""
import sys
sys.path.insert(0, '.')

from config.database import get_db
from sqlalchemy import text

migration_statements = [
    # 1. KanbanStage new columns
    "ALTER TABLE kanban_stages ADD COLUMN stage_type VARCHAR(20) DEFAULT 'open'",
    "ALTER TABLE kanban_stages ADD COLUMN color VARCHAR(7) DEFAULT '#6c757d'",
    "ALTER TABLE kanban_stages ADD COLUMN is_active TINYINT(1) DEFAULT 1",
    "ALTER TABLE kanban_stages ADD INDEX idx_stage_type (stage_type)",
    # Heuristic stage type assignment
    "UPDATE kanban_stages SET stage_type = 'won' WHERE LOWER(name) LIKE '%ganho%' OR LOWER(name) LIKE '%won%' OR LOWER(name) LIKE '%ganado%'",
    "UPDATE kanban_stages SET stage_type = 'lost' WHERE LOWER(name) LIKE '%perdido%' OR LOWER(name) LIKE '%lost%'",
    # 2. Tasks evolution
    "ALTER TABLE tasks CHANGE user_id assigned_to_id INT NULL",
    "ALTER TABLE tasks ADD COLUMN assigned_by_id INT NULL",
    "ALTER TABLE tasks ADD COLUMN priority VARCHAR(20) DEFAULT 'medium'",
    "ALTER TABLE tasks ADD COLUMN completed_at DATETIME NULL",
    "ALTER TABLE tasks ADD INDEX idx_assigned_by (assigned_by_id)",
    "ALTER TABLE tasks ADD INDEX idx_priority (priority)",
    "UPDATE tasks SET status = 'open' WHERE status = 'pending'",
    # 3. Notifications table
    """CREATE TABLE IF NOT EXISTS notifications (
        id INT AUTO_INCREMENT PRIMARY KEY,
        company_id INT NOT NULL,
        user_id INT NOT NULL,
        title VARCHAR(255) NOT NULL,
        message TEXT,
        notification_type VARCHAR(50) DEFAULT 'info',
        reference_type VARCHAR(50),
        reference_id INT,
        is_read TINYINT(1) DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        INDEX idx_user_read (user_id, is_read),
        INDEX idx_company (company_id),
        INDEX idx_notification_type (notification_type),
        FOREIGN KEY (company_id) REFERENCES companies(id),
        FOREIGN KEY (user_id) REFERENCES users(id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
]

print("=" * 50)
print("PURETEGO CRM - Migration v3")
print("=" * 50)

with get_db() as db:
    for i, stmt in enumerate(migration_statements):
        label = stmt.strip().split('\n')[0][:60]
        try:
            db.execute(text(stmt))
            db.commit()
            print(f"  [{i+1:02d}/{len(migration_statements)}] OK - {label}")
        except Exception as e:
            err = str(e)
            if 'Duplicate column' in err or 'Duplicate key' in err or 'already exists' in err:
                print(f"  [{i+1:02d}/{len(migration_statements)}] SKIP (already exists) - {label}")
                db.rollback()
            else:
                print(f"  [{i+1:02d}/{len(migration_statements)}] ERROR: {err}")
                db.rollback()

print("=" * 50)
print("Migration complete!")
