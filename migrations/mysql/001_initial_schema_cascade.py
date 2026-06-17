"""
MySQL 迁移脚本：级联删除 CASCADE 约束 + ENUM 列定义

在迁移前，可直接执行：
  alembic -c migrations/mysql/alembic.ini upgrade head
或直接执行此脚本：
  mysql -u root -p your_db < <(python3 migrations/mysql/001_initial_schema_cascade.py)

注意：MySQL 需使用 InnoDB 引擎（默认），外键约束才生效。
"""

from datetime import datetime

REVISION = "001_initial_schema_cascade"
DOWN_REVISION = None

PRIORITY_VALUES = "'low','medium','high','urgent'"
STATUS_VALUES = "'pending','evaluated','scheduled','developing','completed','rejected'"

UPGRADE_SQL = f"""
-- ============================================================
-- MySQL 8.x: Feature Request Pool Initial Schema (with CASCADE)
-- ============================================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- 1. customers
CREATE TABLE IF NOT EXISTS customers (
    id          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    name        VARCHAR(128) NOT NULL,
    company     VARCHAR(128) NOT NULL DEFAULT '',
    contact     VARCHAR(128) NOT NULL DEFAULT '',
    created_at  DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    PRIMARY KEY (id),
    KEY idx_customers_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. topics
CREATE TABLE IF NOT EXISTS topics (
    id          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    name        VARCHAR(128) NOT NULL UNIQUE,
    description TEXT NULL,
    created_at  DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    PRIMARY KEY (id),
    UNIQUE KEY uk_topics_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. feedbacks
CREATE TABLE IF NOT EXISTS feedbacks (
    id           BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    description  TEXT NOT NULL,
    impact_scope VARCHAR(64) NOT NULL DEFAULT '',
    priority     ENUM({PRIORITY_VALUES}) NOT NULL DEFAULT 'medium',
    status       ENUM({STATUS_VALUES}) NOT NULL DEFAULT 'pending',
    source       VARCHAR(32) NOT NULL DEFAULT '',
    topic_id     BIGINT UNSIGNED NULL,
    created_at   DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    updated_at   DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
    PRIMARY KEY (id),
    KEY idx_feedbacks_topic (topic_id),
    KEY idx_feedbacks_status (status),
    KEY idx_feedbacks_priority (priority),
    KEY idx_feedbacks_created_at (created_at DESC),
    CONSTRAINT fk_feedbacks_topic
        FOREIGN KEY (topic_id) REFERENCES topics(id)
        ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. feedback_customer (多对多 + CASCADE，不留孤儿)
CREATE TABLE IF NOT EXISTS feedback_customer (
    feedback_id BIGINT UNSIGNED NOT NULL,
    customer_id BIGINT UNSIGNED NOT NULL,
    PRIMARY KEY (feedback_id, customer_id),
    KEY idx_fc_customer (customer_id),
    CONSTRAINT fk_fc_feedback
        FOREIGN KEY (feedback_id) REFERENCES feedbacks(id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_fc_customer
        FOREIGN KEY (customer_id) REFERENCES customers(id)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5. status_changes (CASCADE ON feedback_id)
CREATE TABLE IF NOT EXISTS status_changes (
    id          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    feedback_id BIGINT UNSIGNED NOT NULL,
    old_status  ENUM({STATUS_VALUES}) NULL,
    new_status  ENUM({STATUS_VALUES}) NOT NULL,
    changed_by  VARCHAR(64) NOT NULL DEFAULT '',
    remark      TEXT NULL,
    changed_at  DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    PRIMARY KEY (id),
    KEY idx_status_changes_feedback (feedback_id),
    KEY idx_status_changes_changedat (changed_at DESC),
    CONSTRAINT fk_sc_feedback
        FOREIGN KEY (feedback_id) REFERENCES feedbacks(id)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

SET FOREIGN_KEY_CHECKS = 1;
"""

DOWNGRADE_SQL = """
SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS status_changes;
DROP TABLE IF EXISTS feedback_customer;
DROP TABLE IF EXISTS feedbacks;
DROP TABLE IF EXISTS topics;
DROP TABLE IF EXISTS customers;
SET FOREIGN_KEY_CHECKS = 1;
"""


def upgrade_sql() -> str:
    return UPGRADE_SQL


def downgrade_sql() -> str:
    return DOWNGRADE_SQL


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "down":
        print(downgrade_sql())
    else:
        print(upgrade_sql())
