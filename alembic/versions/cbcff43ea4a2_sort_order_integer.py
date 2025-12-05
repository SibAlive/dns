"""sort_order - Integer

Revision ID: cbcff43ea4a2
Revises: 5121cdb36b43
Create Date: 2025-12-05 14:51:08.223813

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cbcff43ea4a2'
down_revision: Union[str, Sequence[str], None] = '5121cdb36b43'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # 1. Добавляем временный столбец INTEGER
    op.add_column('product_images', sa.Column(
        'sort_order_temp', sa.Integer(), nullable=True))

    # 2. Копируем данные: true=1, false=0, NULL остается NULL
    op.execute('''
        UPDATE product_images 
        SET sort_order_temp = CASE 
            WHEN sort_order IS TRUE THEN 1 
            WHEN sort_order IS FALSE THEN 0 
            ELSE NULL 
        END
    ''')

    # 3. Удаляем старый столбец
    op.drop_column('product_images', 'sort_order')

    # 4. Переименовываем временный в основной
    op.alter_column('product_images', 'sort_order_temp',
                    new_column_name='sort_order')


def downgrade():
    # Обратное преобразование: 0/NULL=false, остальные=true
    op.add_column('product_images', sa.Column(
        'sort_order_temp', sa.BOOLEAN(), nullable=True))

    op.execute('''
        UPDATE product_images 
        SET sort_order_temp = CASE 
            WHEN sort_order IS NULL OR sort_order = 0 THEN false 
            ELSE true 
        END
    ''')

    op.drop_column('product_images', 'sort_order')
    op.alter_column('product_images', 'sort_order_temp',
                    new_column_name='sort_order')