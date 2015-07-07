"""initial schema

Revision ID: 70453a74993
Revises: None
Create Date: 2015-07-07 13:06:37.657719

"""

# revision identifiers, used by Alembic.
revision = '70453a74993'
down_revision = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'posts',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('user', sa.String, nullable=False),
        sa.Column('poster', sa.String, nullable=False),
        sa.Column('value', sa.String, nullable=False),
        sa.Column('text', sa.String, nullable=False),
        sa.Column('posted_at', sa.DateTime, nullable=False),
        sa.Column('slack_timestamp', sa.String, nullable=False),
        sa.Column('slack_channel', sa.String, nullable=False))

def downgrade():
    op.drop_table('posts')
