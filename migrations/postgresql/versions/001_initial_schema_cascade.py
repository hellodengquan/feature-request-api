from alembic import op
import sqlalchemy as sa

revision = "001_initial_schema_cascade"
down_revision = None
branch_labels = ("postgresql",)
depends_on = None


def upgrade():
    op.execute(
        """
        CREATE TYPE priority_level AS ENUM ('low', 'medium', 'high', 'urgent');
        CREATE TYPE feedback_status AS ENUM ('pending', 'evaluated', 'scheduled', 'developing', 'completed', 'rejected');
        """
    )
    op.create_table(
        "customers",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("company", sa.String(length=128), nullable=False, server_default=""),
        sa.Column("contact", sa.String(length=128), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_customers_name", "customers", ["name"])
    op.create_table(
        "topics",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uk_topics_name"),
    )
    op.create_table(
        "feedbacks",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("impact_scope", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("priority", sa.Enum("low", "medium", "high", "urgent", name="priority_level"),
                  nullable=False, server_default="medium"),
        sa.Column("status", sa.Enum("pending", "evaluated", "scheduled", "developing", "completed", "rejected",
                                    name="feedback_status"),
                  nullable=False, server_default="pending"),
        sa.Column("source", sa.String(length=32), nullable=False, server_default=""),
        sa.Column("topic_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["topic_id"], ["topics.id"], name="fk_feedbacks_topic",
                                ondelete="SET NULL", onupdate="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_feedbacks_topic", "feedbacks", ["topic_id"])
    op.create_index("idx_feedbacks_status", "feedbacks", ["status"])
    op.create_index("idx_feedbacks_priority", "feedbacks", ["priority"])
    op.create_index("idx_feedbacks_created_at", "feedbacks", ["created_at"])
    op.create_table(
        "feedback_customer",
        sa.Column("feedback_id", sa.Integer(), nullable=False),
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["feedback_id"], ["feedbacks.id"], name="fk_fc_feedback",
                                ondelete="CASCADE", onupdate="CASCADE"),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], name="fk_fc_customer",
                                ondelete="CASCADE", onupdate="CASCADE"),
        sa.PrimaryKeyConstraint("feedback_id", "customer_id"),
    )
    op.create_index("idx_fc_customer", "feedback_customer", ["customer_id"])
    op.create_table(
        "status_changes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("feedback_id", sa.Integer(), nullable=False),
        sa.Column("old_status", sa.Enum("pending", "evaluated", "scheduled", "developing", "completed", "rejected",
                                         name="feedback_status"),
                  nullable=True),
        sa.Column("new_status", sa.Enum("pending", "evaluated", "scheduled", "developing", "completed", "rejected",
                                         name="feedback_status"),
                  nullable=False),
        sa.Column("changed_by", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("remark", sa.Text(), nullable=False, server_default=""),
        sa.Column("changed_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["feedback_id"], ["feedbacks.id"], name="fk_sc_feedback",
                                ondelete="CASCADE", onupdate="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_status_changes_feedback", "status_changes", ["feedback_id"])
    op.create_index("idx_status_changes_changedat", "status_changes", ["changed_at"])


def downgrade():
    op.drop_index("idx_status_changes_changedat", table_name="status_changes")
    op.drop_index("idx_status_changes_feedback", table_name="status_changes")
    op.drop_table("status_changes")
    op.drop_index("idx_fc_customer", table_name="feedback_customer")
    op.drop_table("feedback_customer")
    op.drop_index("idx_feedbacks_created_at", table_name="feedbacks")
    op.drop_index("idx_feedbacks_priority", table_name="feedbacks")
    op.drop_index("idx_feedbacks_status", table_name="feedbacks")
    op.drop_index("idx_feedbacks_topic", table_name="feedbacks")
    op.drop_table("feedbacks")
    op.drop_table("topics")
    op.drop_index("idx_customers_name", table_name="customers")
    op.drop_table("customers")
    op.execute("DROP TYPE IF EXISTS feedback_status; DROP TYPE IF EXISTS priority_level;")
