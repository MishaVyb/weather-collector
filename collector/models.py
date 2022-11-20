from __future__ import annotations

from datetime import datetime
from typing import TypeAlias

import sqlalchemy as db
from sqlalchemy import orm, sql

Base: TypeAlias = orm.declarative_base()  # type: ignore


class BaseModel(Base):
    __abstract__ = True

    id: int = db.Column(
        db.Integer, nullable=False, unique=True, primary_key=True, autoincrement=True
    )
    created_at: datetime = db.Column(
        db.DateTime(timezone=True), server_default=sql.func.now()
    )
    updated_at: datetime = db.Column(
        db.DateTime(timezone=True), onupdate=sql.func.now()
    )

    def __repr__(self):
        return f'<{self.__class__.__name__}({self.id=})>'


class CityModel(BaseModel):
    """
    City representation. Name is required, other optional.
    """

    __tablename__ = 'city'

    name: str = db.Column(db.String(50), nullable=False)
    country: str = db.Column(db.String(50))
    countryCode: str = db.Column(db.String(3))
    latitude: float = db.Column(db.Float())
    longitude: float = db.Column(db.Float())
    population: int = db.Column(db.Integer())

    measurements: list[MeasurementModel] = orm.relationship(
        'MeasurementModel',
        # back_populates='city',
        backref='city',
        cascade='all, delete-orphan',
    )

    def __str__(self) -> str:
        return self.name


class MeasurementModel(BaseModel):
    """
    Open Weather API provides a lot of information about current city weather. Depending
    on location and current weather situation some fields could appear some other could
    not. For that situation we decided to store all root fields in separate tables.

    Why `MainWeatherDataModel`?
    The basic reason for collecting weather is understanding how to cool down company's
    servers. Therefore, we parsing and store `main` field that contains current
    temperature. All other data storing as json at `ExtraMeasurementDataModel` for any
    future purposes.

    We may describe other tables to store all the data in relational (SQL) way later, if
    we will need it.
    """

    __tablename__ = 'weather_measurement'

    # city: CityModel = orm.relationship('CityModel', back='measurements')
    city_id: int = db.Column(db.Integer, db.ForeignKey("city.id"), nullable=False)

    measure_at: datetime = db.Column(db.DateTime(), nullable=False)
    "Time of data forecasted. UTC. Do not confuse with base model `created_at` field."

    main: MainWeatherDataModel = orm.relationship(
        'MainWeatherDataModel',
        uselist=False,
        backref='measurement',
        cascade='all, delete-orphan',
    )

    # [NOTE]
    # Other fields can be handled here as one-to-one relation, if the reason is appear
    # in a future.
    ...


    extra: ExtraWeatherDataModel = orm.relationship(
        'ExtraWeatherDataModel',
        uselist=False,
        backref='measurement',
        cascade='all, delete-orphan',
    )


class MainWeatherDataModel(BaseModel):
    """
    Data at `main` field from measurement response.
    """

    __tablename__ = 'main_weather_measurement'

    measurement_id = db.Column(db.Integer, db.ForeignKey('weather_measurement.id'))

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


class ExtraWeatherDataModel(BaseModel):
    """
    Additional data from weather measurement.
    """

    __tablename__ = 'extra_weather_data'

    measurement_id = db.Column(db.Integer, db.ForeignKey('weather_measurement.id'))
    data: dict = db.Column(db.JSON())
