"""initial

Revision ID: 2670da54e0e2
Revises:
Create Date: 2022-11-19 01:16:15.659888

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2670da54e0e2'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        'city',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('(CURRENT_TIMESTAMP)'),
            nullable=True,
        ),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('country', sa.String(length=50), nullable=True),
        sa.Column('countryCode', sa.String(length=3), nullable=True),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('population', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('id'),
    )
    op.create_table(
        'weather_measurement',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('(CURRENT_TIMESTAMP)'),
            nullable=True,
        ),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('city_id', sa.Integer(), nullable=True),
        sa.Column('measure_at', sa.DateTime(), nullable=True),
        sa.Column('temp', sa.Float(), nullable=True),
        sa.Column('feels_like', sa.Float(), nullable=True),
        sa.Column('temp_min', sa.Float(), nullable=True),
        sa.Column('temp_max', sa.Float(), nullable=True),
        sa.Column('pressure', sa.Integer(), nullable=True),
        sa.Column('humidity', sa.Integer(), nullable=True),
        sa.Column('sea_level', sa.Integer(), nullable=True),
        sa.Column('grnd_level', sa.Integer(), nullable=True),
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
    op.drop_table('weather_measurement')
    op.drop_table('city')
    # ### end Alembic commands ###
