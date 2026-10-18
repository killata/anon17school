"""make category nullable

Revision ID: 2b04f7a18e2d
Revises: 1c90c12aec8c
Create Date: 2026-10-18 23:40:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '2b04f7a18e2d'
down_revision = '1c90c12aec8c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column('posts', 'category',
               existing_type=postgresql.ENUM('Мнение', 'Учителя', 'Ищу тебя', 'Мем', 'Сплетня', name='post_category'),
               nullable=True)


def downgrade() -> None:
    op.alter_column('posts', 'category',
               existing_type=postgresql.ENUM('Мнение', 'Учителя', 'Ищу тебя', 'Мем', 'Сплетня', name='post_category'),
               nullable=False)
