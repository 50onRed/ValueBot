"""Initial Schema

Revision ID: 16c93656a0de
Revises: 
Create Date: 2015-07-17 14:00:37.565422

"""

# revision identifiers, used by Alembic.
revision = '16c93656a0de'
down_revision = None
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'posts',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('user', sa.String(64), nullable=False),
        sa.Column('poster', sa.String(64), nullable=False),
        sa.Column('value', sa.String(64), nullable=False),
        sa.Column('text', sa.String(500), nullable=False),
        sa.Column('posted_at', sa.DateTime, nullable=False),
        sa.Column('slack_timestamp', sa.String(64), nullable=False),
        sa.Column('slack_channel', sa.String(64), nullable=False))

def downgrade():
    op.drop_table('posts')
