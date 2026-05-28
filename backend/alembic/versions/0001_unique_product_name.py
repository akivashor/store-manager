"""unique product name

Revision ID: 0001
Revises:
Create Date: 2026-05-28

"""
from alembic import op

revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_unique_constraint('uq_products_name', 'products', ['name'])


def downgrade():
    op.drop_constraint('uq_products_name', 'products', type_='unique')
