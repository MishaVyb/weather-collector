"""create extra_weather_measurement_data table

Revision ID: 48971063fd73
Revises: 2670da54e0e2
Create Date: 2022-11-19 01:44:14.264297

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '48971063fd73'
down_revision = '2670da54e0e2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        'extra_weather_measurement_data',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('(CURRENT_TIMESTAMP)'),
            nullable=True,
        ),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('city_id', sa.Integer(), nullable=True),
        sa.Column('data', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(
            ['city_id'],
            ['city.id'],
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('id'),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('extra_weather_measurement_data')
    # ### end Alembic commands ###
