"""users and values joiner tables

Revision ID: 16c38836d489
Revises: 16c93656a0de
Create Date: 2015-07-21 12:24:33.077367

"""

# revision identifiers, used by Alembic.
revision = '16c38836d489'
down_revision = '16c93656a0de'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'post_users',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('user', sa.String, nullable=False),
        sa.Column('post_id', sa.Integer, nullable=False))

    op.create_table(
        'post_values',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('value', sa.String, nullable=False),
        sa.Column('post_id', sa.Integer, nullable=False))

    post_users_table = sa.sql.table('post_users',
        sa.Column('user', sa.String, nullable=False),
        sa.Column('post_id', sa.Integer, nullable=False))

    post_values_table = sa.sql.table('post_values',
        sa.Column('value', sa.String, nullable=False),
        sa.Column('post_id', sa.Integer, nullable=False))

    conn = op.get_bind()
    results = conn.execute("SELECT id, user, value FROM posts").fetchall()

    p_u = [{'post_id': r[0], 'user': r[1]} for r in results]
    p_v = [{'post_id': r[0], 'value': r[2]} for r in results]

    op.bulk_insert(post_users_table, p_u)
    op.bulk_insert(post_values_table, p_v)

def downgrade():
    op.drop_table('post_users')
    op.drop_table('post_values')
