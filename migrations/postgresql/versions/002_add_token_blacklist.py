from alembic import op
import sqlalchemy as sa

revision = "002_add_token_blacklist"
down_revision = "001_initial_schema_cascade"
branch_labels = ("postgresql",)
depends_on = None


def upgrade():
    op.create_table(
        "token_blacklist",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("jti", sa.String(length=64), nullable=False),
        sa.Column("reason", sa.String(length=32), nullable=False, server_default="manual"),
        sa.Column("revoked_by", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("jti", name="uk_token_blacklist_jti"),
    )
    op.create_index("idx_token_blacklist_jti", "token_blacklist", ["jti"], unique=True)
    op.create_index("idx_token_blacklist_expires", "token_blacklist", ["expires_at"])

    op.create_table(
        "revoked_accounts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("reason", sa.String(length=128), nullable=False, server_default=""),
        sa.Column("revoked_by", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="uk_revoked_accounts_user_id"),
    )
    op.create_index("idx_revoked_accounts_user_id", "revoked_accounts", ["user_id"], unique=True)

    op.create_table(
        "jwt_rotation_log",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("old_version", sa.Integer(), nullable=False),
        sa.Column("new_version", sa.Integer(), nullable=False),
        sa.Column("rotated_by", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade():
    op.drop_table("jwt_rotation_log")
    op.drop_index("idx_revoked_accounts_user_id", table_name="revoked_accounts")
    op.drop_constraint("uk_revoked_accounts_user_id", "revoked_accounts", type_="unique")
    op.drop_table("revoked_accounts")
    op.drop_index("idx_token_blacklist_expires", table_name="token_blacklist")
    op.drop_index("idx_token_blacklist_jti", table_name="token_blacklist")
    op.drop_constraint("uk_token_blacklist_jti", "token_blacklist", type_="unique")
    op.drop_table("token_blacklist")
