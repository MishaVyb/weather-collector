from __future__ import annotations
from datetime import datetime

from http import HTTPStatus
import json
import os
from pprint import pformat
from typing import Iterable
import pydantic

import requests
import argparse
import logging
import unicodedata
import sqlalchemy as db
import sqlalchemy.orm as orm

from collector.configurations import CONFIG
from collector.exeptions import NoDataError, ResponseError, ResponseSchemaError
from collector.functools import init_logger
from collector.models import CityModel, ExtraMeasurementDataModel, MeasurementModel
from collector.services.base import BaseSerivce
from collector.services.cities import FetchCities, InitCities
from collector.session import DBSessionMixin


logger = init_logger(__name__)


########################################################################################
### Collect
########################################################################################


class MainWetherSchema(pydantic.BaseModel):
    temp: float
    feels_like: float
    temp_min: float
    temp_max: float
    pressure: int
    humidity: int
    sea_level: int | None
    grnd_level: int | None


class WetherMeasurementSchema(pydantic.BaseModel):
    main: MainWetherSchema
    "Main weather data. "
    dt: int
    "Time of data forecasted, Unix, UTC (timestamp). "


class FetchWeather(BaseSerivce, DBSessionMixin):
    """
    Fetch wether for cities and store data into DB.
    By default fetching wether for all cities from DB.

    Endpont detail information: https://openweathermap.org/current
    """

    description = 'Fetch wether for cities and store data into DB. '
    command = 'fetch_weather'
    url = 'https://api.openweathermap.org/data/2.5/weather'
    params = {
        "appid": CONFIG.open_wether_key,
        "units": "metric",
    }

    def __init__(self) -> None:
        super().__init__()
        self.cities: list[CityModel] = self.session.query(CityModel).all()

        if not self.cities:
            raise NoDataError(
                msg=(
                    'No cities at DB. '
                    f'Call for {FetchCities.command} or {InitCities.command} before. '
                )
            )

    def exicute(self):
        for city in self.cities:
            if not all([city.longitude, city.latitude]):
                self.fetch_coordinates()
                self.store_coordinates()

            measure, extra = self.fetch_wether(city)
            self.store_measure(city, measure, extra)
            # logger.info(f'{city}: {measure}')

        self.session.commit()
        self.session.close()

    def fetch_wether(self, city: CityModel):
        logger.info(f'Fetching weather for {city}. ')

        self.params['lat'] = str(city.latitude)
        self.params['lon'] = str(city.longitude)
        response = requests.get(self.url, self.params)

        if response.status_code != HTTPStatus.OK:
            raise ResponseError(response)

        try:
            measur = WetherMeasurementSchema.parse_raw(response.text)
        except pydantic.ValidationError as e:
            raise ResponseSchemaError(e)

        extra: dict = response.json()
        for field in WetherMeasurementSchema.__fields__:
            extra.pop(field)

        return measur, extra

    def store_measure(
        self, city: CityModel, measure: WetherMeasurementSchema, extra: dict
    ):
        # logger.info('Add weather measurements to DB Session. ')
        self.session.add_all(
            [
                MeasurementModel(
                    city=city,
                    measure_at=datetime.utcfromtimestamp(measure.dt),
                    **measure.main.dict(),
                ),
                ExtraMeasurementDataModel(data=extra),
            ]
        )

    def fetch_coordinates(self, city: CityModel):
        ...

    def store_coordinates(self, city: CityModel):
        ...


class CollectWetherRepeated:
    ...
