"""drop old user and value column

Revision ID: 49bceeb0e61d
Revises: 16c38836d489
Create Date: 2015-08-05 16:32:03.298543

"""

# revision identifiers, used by Alembic.
revision = '49bceeb0e61d'
down_revision = '16c38836d489'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.drop_column('posts', 'user')
    op.drop_column('posts', 'value')


def downgrade():
    op.add_column('posts', sa.Column('user', sa.String(64), nullable=False))
    op.add_column('posts', sa.Column('value', sa.String(64), nullable=False))
