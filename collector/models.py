





from typing import TypeAlias

import sqlalchemy as db
import sqlalchemy.orm as orm
import sqlalchemy.dialects.sqlite as sqlite

Base: TypeAlias = orm.declarative_base()  # type: ignore
# ENGENE = db.create_engine('sqlite:///db.sqlite3', echo=True, future=True)
# SESSION = orm.Session(# ENGENE)
# class DBSession(orm.Session):


class BaseModel(Base):
    __abstract__ = True

    id = db.Column(
        db.Integer, nullable=False, unique=True, primary_key=True, autoincrement=True
    )
    # created_at = Column(TIMESTAMP, nullable=True)
    # updated_at = Column(TIMESTAMP, nullable=True)

    def __repr__(self):
        return f'<{self.__class__.__name__}({self.id=})>'


class CityModel(BaseModel):
    __tablename__ = 'city'

    name = db.Column(db.String(50),  nullable=False)
    country = db.Column(db.String(50))
    countryCode = db.Column(db.String(3))
    latitude = db.Column(db.Float())
    longitude = db.Column(db.Float())
    population = db.Column(db.Integer())

    def __str__(self) -> str:
        return self.name


    measurements = orm.relationship(
        "WeatherMeasurementModel", back_populates="city", cascade="all, delete-orphan"
    )

class WeatherMeasurementModel(BaseModel):
    __tablename__ = 'weather_measurement'

    city = orm.relationship('CityModel', back_populates='measurements')
    city_id = db.Column(db.Integer, db.ForeignKey("city.id"))
    temp = db.Column(db.Float())
    measure_at = db.Column(db.DateTime(timezone='UTC'))





