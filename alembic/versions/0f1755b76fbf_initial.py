"""initial

Revision ID: 0f1755b76fbf
Revises: 
Create Date: 2022-11-24 11:12:04.162960

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = '0f1755b76fbf'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('city',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('name', sa.String(length=50), nullable=False),
    sa.Column('is_tracked', sa.Boolean(), nullable=False),
    sa.Column('country', sa.String(length=50), nullable=True),
    sa.Column('countryCode', sa.String(length=3), nullable=True),
    sa.Column('latitude', sa.Float(), nullable=True),
    sa.Column('longitude', sa.Float(), nullable=True),
    sa.Column('population', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('id')
    )
    op.create_table('weather_measurement',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('city_id', sa.Integer(), nullable=False),
    sa.Column('measure_at', sa.DateTime(), nullable=False, comment='Time of data forecasted. UTC. Do not confuse with base model `created_at` field.'),
    sa.ForeignKeyConstraint(['city_id'], ['city.id'], onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('id')
    )
    op.create_table('extra_weather_data',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('measurement_id', sa.Integer(), nullable=True),
    sa.Column('data', sa.JSON(), nullable=True),
    sa.ForeignKeyConstraint(['measurement_id'], ['weather_measurement.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('id')
    )
    op.create_table('main_weather_measurement',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('measurement_id', sa.Integer(), nullable=True),
    sa.Column('temp', sa.Float(), nullable=True, comment='Temperature. Celsius.'),
    sa.Column('feels_like', sa.Float(), nullable=True, comment='This temperature parameter accounts for the human perception of weather. Celsius.'),
    sa.Column('temp_min', sa.Float(), nullable=True, comment='Minimum temperature at the moment. This is minimal currently observed temperature (within large megalopolises and urban areas). Celsius.'),
    sa.Column('temp_max', sa.Float(), nullable=True, comment='Maximum temperature at the moment. This is maximal currently observed temperature (within large megalopolises and urban areas). Celsius.'),
    sa.Column('pressure', sa.Integer(), nullable=True, comment='Atmospheric pressure (on the sea level, if there is no sea_level or grnd_level). hPa.'),
    sa.Column('humidity', sa.Integer(), nullable=True, comment='Humidity. %'),
    sa.Column('sea_level', sa.Integer(), nullable=True, comment='Atmospheric pressure on the sea level. hPa.'),
    sa.Column('grnd_level', sa.Integer(), nullable=True, comment='Atmospheric pressure on the ground level. hPa.'),
    sa.ForeignKeyConstraint(['measurement_id'], ['weather_measurement.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('main_weather_measurement')
    op.drop_table('extra_weather_data')
    op.drop_table('weather_measurement')
    op.drop_table('city')
    # ### end Alembic commands ###
