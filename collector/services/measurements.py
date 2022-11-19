from __future__ import annotations
from datetime import datetime

from http import HTTPStatus
import json
import os
from pprint import pformat
from time import sleep
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
from collector.models import (
    BaseModel,
    CityModel,
    ExtraMeasurementDataModel,
    MeasurementModel,
)
from collector.services.base import BaseSerivce, FetchServiceMixin
from collector.services.cities import FetchCities, FetchCoordinates, InitCities
from collector.session import DBSessionMixin


logger = init_logger(__name__)


########################################################################################
### Fetch Weather
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


class FetchWeather(BaseSerivce, DBSessionMixin, FetchServiceMixin):
    """
    Fetch wether for cities and store data into DB.
    By default fetching wether for all cities from DB.

    Endpont detail information: https://openweathermap.org/current
    """

    description = 'Fetch wether for cities and store data into DB. '
    command = 'fetch_weather'
    url = 'https://api.openweathermap.org/data/2.5/weather'
    # params = {
    #     "appid": CONFIG.open_wether_key,
    #     "units": "metric",
    # }
    schema = WetherMeasurementSchema

    def __init__(self, **kwargs) -> None:

        BaseSerivce.__init__(self, **kwargs)
        DBSessionMixin.__init__(self)

        self.cities: list[CityModel] = self.query(CityModel).all()

        if not self.cities:
            raise NoDataError(
                'No cities at DB. '
                f'Call for {FetchCities.command} or {InitCities.command} before. '
            )

    def exicute(self):
        for city in self.cities:
            if not all([city.longitude, city.latitude]):
                FetchCoordinates(city).exicute()

            measure, extra = self.fetch(city)
            self.store(city, measure, extra)

        self.save()

    def fetch(self, city: CityModel):  # type: ignore
        logger.info(f'Fetching weather for {city}. ')

        self.params['lat'] = str(city.latitude)
        self.params['lon'] = str(city.longitude)

        measur = super().fetch()
        # response = requests.get(self.url, self.params)

        # if response.status_code != HTTPStatus.OK:
        #     raise ResponseError(response)

        # try:
        #     measur = WetherMeasurementSchema.parse_raw(response.text)
        # except pydantic.ValidationError as e:
        #     raise ResponseSchemaError(e)

        extra: dict = self.response.json()
        for field in self.schema.__fields__:
            extra.pop(field)

        return measur, extra

    def store(self, city: CityModel, measure: WetherMeasurementSchema, extra: dict):
        # logger.info('Add weather measurements to DB Session. ')u
        self.create(
            MeasurementModel(
                city=city,
                measure_at=datetime.utcfromtimestamp(measure.dt),
                **measure.main.dict(),
            ),
            ExtraMeasurementDataModel(data=extra),
        )


########################################################################################
### Collect Weather
########################################################################################


class CollectWether(BaseSerivce):
    command = 'collect_weather'
    delay = CONFIG.collect_weather_delay

    def __init__(self, **kwargs) -> None:
        self.counter = 0
        super().__init__(**kwargs)

    def exicute(self):
        while True:
            logger.info(f'\nStarting collecting wether ({self.counter}). ')

            FetchWeather().exicute()

            logger.info(
                f'Collecting successfuly. Next collection runs in {self.delay} seconds.'
                ' Sleeping...'
            )
            self.counter += 1
            sleep(self.delay)
