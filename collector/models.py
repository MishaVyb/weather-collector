





from datetime import datetime
from typing import TypeAlias

import sqlalchemy as db
from sqlalchemy import orm, sql
import sqlalchemy.dialects.sqlite as sqlite

Base: TypeAlias = orm.declarative_base()  # type: ignore
# ENGENE = db.create_engine('sqlite:///db.sqlite3', echo=True, future=True)
# SESSION = orm.Session(# ENGENE)
# class DBSession(orm.Session):


class BaseModel(Base):
    __abstract__ = True

    id: int = db.Column(
        db.Integer, nullable=False, unique=True, primary_key=True, autoincrement=True
    )
    created_at: datetime = db.Column(db.DateTime(timezone=True), server_default=sql.func.now())
    updated_at: datetime = db.Column(db.DateTime(timezone=True), onupdate=sql.func.now())

    def __repr__(self):
        return f'<{self.__class__.__name__}({self.id=})>'


class CityModel(BaseModel):
    """
    City representation. Name is required, other optional.
    """
    __tablename__ = 'city'

    name: str = db.Column(db.String(50),  nullable=False)
    country: str = db.Column(db.String(50))
    countryCode: str = db.Column(db.String(3))
    latitude: float = db.Column(db.Float())
    longitude: float = db.Column(db.Float())
    population: int = db.Column(db.Integer())

    def __str__(self) -> str:
        return self.name


    measurements = orm.relationship(
        "MeasurementModel", back_populates="city", cascade="all, delete-orphan"
    )

class MeasurementModel(BaseModel):
    """
    Main data from wether measurement.

    Open Weather API provides a lot of information about current weather at the city.
    We parsing and store in seperated fields only data from `main` field and storing
    `dt` (`measure_at`) value as it is important data also.
    """
    __tablename__ = 'weather_measurement'

    city: str = orm.relationship('CityModel', back_populates='measurements')
    city_id: int = db.Column(db.Integer, db.ForeignKey("city.id"))
    measure_at: datetime = db.Column(db.DateTime())
    "Time of data forecasted. UTC. "

    temp: float = db.Column(db.Float())
    "Temperature. Celsius."
    feels_like: float = db.Column(db.Float())
    """
    This temperature parameter accounts for the human perception of weather. Celsius.
    """
    temp_min: float = db.Column(db.Float())
    """
    Minimum temperature at the moment. This is minimal currently observed temperature
    (within large megalopolises and urban areas). Celsius.
    """
    temp_max: float = db.Column(db.Float())
    """
    Maximum temperature at the moment. This is maximal currently observed temperature
    (within large megalopolises and urban areas). Celsius.
    """
    pressure: int = db.Column(db.Integer())
    """
    Atmospheric pressure (on the sea level, if there is no sea_level or grnd_level).
    hPa.
    """
    humidity: int = db.Column(db.Integer())
    "Humidity. %"
    sea_level: int = db.Column(db.Integer())
    "Atmospheric pressure on the sea level. hPa."
    grnd_level: int = db.Column(db.Integer())
    "Atmospheric pressure on the ground level. hPa."


class ExtraMeasurementDataModel(BaseModel):
    """
    Additional data from wether measurement.
    """
    __tablename__ = 'extra_weather_measurement_data'

    data: dict = db.Column(db.JSON())









