"""
PostgreSQL 迁移脚本：级联删除 CASCADE 约束 + 枚举类型升级

在迁移前，可直接执行：
  alembic -c migrations/postgresql/alembic.ini upgrade head
或直接执行此脚本：
  psql -d your_db -U your_user -f migrations/postgresql/001_initial_schema_cascade.sql
"""

from datetime import datetime
from enum import Enum as PyEnum


REVISION = "001_initial_schema_cascade"
DOWN_REVISION = None
DEPENDS_ON = None

PRIORITY_ENUM = ["low", "medium", "high", "urgent"]
STATUS_ENUM = ["pending", "evaluated", "scheduled", "developing", "completed", "rejected"]

UPGRADE_SQL = f"""
-- ============================================================
-- PostgreSQL: Feature Request Pool Initial Schema (with CASCADE)
-- ============================================================

BEGIN;

-- 1. 枚举类型
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'priority_level') THEN
        CREATE TYPE priority_level AS ENUM ({', '.join(repr(v) for v in PRIORITY_ENUM)});
    END IF;
END$$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'feedback_status') THEN
        CREATE TYPE feedback_status AS ENUM ({', '.join(repr(v) for v in STATUS_ENUM)});
    END IF;
END$$;

-- 2. customers
CREATE TABLE IF NOT EXISTS customers (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(128) NOT NULL,
    company     VARCHAR(128) NOT NULL DEFAULT '',
    contact     VARCHAR(128) NOT NULL DEFAULT '',
    created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_customers_name ON customers(name);

-- 3. topics
CREATE TABLE IF NOT EXISTS topics (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(128) NOT NULL UNIQUE,
    description TEXT NOT NULL DEFAULT '',
    created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_topics_name ON topics(name);

-- 4. feedbacks
CREATE TABLE IF NOT EXISTS feedbacks (
    id            SERIAL PRIMARY KEY,
    description   TEXT NOT NULL,
    impact_scope  VARCHAR(64) NOT NULL DEFAULT '',
    priority      priority_level NOT NULL DEFAULT 'medium',
    status        feedback_status NOT NULL DEFAULT 'pending',
    source        VARCHAR(32) NOT NULL DEFAULT '',
    topic_id      INTEGER NULL,
    created_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_feedbacks_topic
        FOREIGN KEY (topic_id) REFERENCES topics(id)
        ON DELETE SET NULL ON UPDATE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_feedbacks_topic  ON feedbacks(topic_id);
CREATE INDEX IF NOT EXISTS idx_feedbacks_status ON feedbacks(status);
CREATE INDEX IF NOT EXISTS idx_feedbacks_priority ON feedbacks(priority);
CREATE INDEX IF NOT EXISTS idx_feedbacks_created_at ON feedbacks(created_at DESC);

-- 5. feedback_customer (多对多 + CASCADE，不留孤儿)
CREATE TABLE IF NOT EXISTS feedback_customer (
    feedback_id INTEGER NOT NULL,
    customer_id INTEGER NOT NULL,
    PRIMARY KEY (feedback_id, customer_id),
    CONSTRAINT fk_fc_feedback
        FOREIGN KEY (feedback_id) REFERENCES feedbacks(id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_fc_customer
        FOREIGN KEY (customer_id) REFERENCES customers(id)
        ON DELETE CASCADE ON UPDATE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_fc_customer ON feedback_customer(customer_id);

-- 6. status_changes (CASCADE ON feedback_id)
CREATE TABLE IF NOT EXISTS status_changes (
    id          SERIAL PRIMARY KEY,
    feedback_id INTEGER NOT NULL,
    old_status  feedback_status NULL,
    new_status  feedback_status NOT NULL,
    changed_by  VARCHAR(64) NOT NULL DEFAULT '',
    remark      TEXT NOT NULL DEFAULT '',
    changed_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_sc_feedback
        FOREIGN KEY (feedback_id) REFERENCES feedbacks(id)
        ON DELETE CASCADE ON UPDATE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_status_changes_feedback  ON status_changes(feedback_id);
CREATE INDEX IF NOT EXISTS idx_status_changes_changedat ON status_changes(changed_at DESC);

-- 7. updated_at 自动维护（PostgreSQL 需要触发器）
CREATE OR REPLACE FUNCTION maintain_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at := CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_feedbacks_updated_at ON feedbacks;
CREATE TRIGGER trg_feedbacks_updated_at
BEFORE UPDATE ON feedbacks
FOR EACH ROW
EXECUTE FUNCTION maintain_updated_at();

COMMIT;
"""

DOWNGRADE_SQL = """
BEGIN;
DROP TRIGGER IF EXISTS trg_feedbacks_updated_at ON feedbacks;
DROP FUNCTION IF EXISTS maintain_updated_at();
DROP INDEX IF EXISTS idx_status_changes_changedat;
DROP INDEX IF EXISTS idx_status_changes_feedback;
ALTER TABLE status_changes DROP CONSTRAINT IF EXISTS fk_sc_feedback;
DROP TABLE IF EXISTS status_changes;
DROP INDEX IF EXISTS idx_fc_customer;
ALTER TABLE feedback_customer DROP CONSTRAINT IF EXISTS fk_fc_customer;
ALTER TABLE feedback_customer DROP CONSTRAINT IF EXISTS fk_fc_feedback;
DROP TABLE IF EXISTS feedback_customer;
DROP INDEX IF EXISTS idx_feedbacks_created_at;
DROP INDEX IF EXISTS idx_feedbacks_priority;
DROP INDEX IF EXISTS idx_feedbacks_status;
DROP INDEX IF EXISTS idx_feedbacks_topic;
ALTER TABLE feedbacks DROP CONSTRAINT IF EXISTS fk_feedbacks_topic;
DROP TABLE IF EXISTS feedbacks;
DROP TABLE IF EXISTS topics;
DROP INDEX IF EXISTS idx_customers_name;
DROP TABLE IF EXISTS customers;
DROP TYPE IF EXISTS feedback_status;
DROP TYPE IF EXISTS priority_level;
COMMIT;
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
