from __future__ import annotations
from datetime import datetime

from http import HTTPStatus
import json
import os
from pprint import pformat
import sys
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
from collector.exeptions import (
    CollectorBaseExeption,
    NoDataError,
    ResponseError,
    ResponseSchemaError,
)
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
    """
    Schema for `main` field from Open Weather response. For more information see
    `MeasurementModel` where we store all these values.
    """

    temp: float
    feels_like: float
    temp_min: float
    temp_max: float
    pressure: int
    humidity: int
    sea_level: int | None
    grnd_level: int | None


class WetherMeasurementSchema(pydantic.BaseModel):
    """
    Response data from Open Weather API contains several fields. We only ensure to have
    `main` field and `dt` field. Other is optional and will be stored at extra data
    table.
    """

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
                try:
                    FetchCoordinates(city).exicute()
                except NoDataError as e:
                    logger.warning(f'Can not get wether for {city}: {e}. Continue. ')
                    continue

            measure, extra = self.fetch(city)
            self.store(city, measure, extra)

        self.save()

    def fetch(self, city: CityModel):  # type: ignore
        logger.info(f'Fetching weather for {city}. ')

        self.params['lat'] = str(city.latitude)
        self.params['lon'] = str(city.longitude)

        measur = super().fetch()

        extra: dict = self.response.json()
        for field in self.schema.__fields__:
            extra.pop(field)

        return measur, extra

    def store(self, city: CityModel, measure: WetherMeasurementSchema, extra: dict):
        self.create(
            MeasurementModel(
                city=city,
                measure_at=datetime.utcfromtimestamp(measure.dt),
                **measure.main.dict(),
            ),
            ExtraMeasurementDataModel(city=city, data=extra),
        )


########################################################################################
### Collect Weather
########################################################################################


class CollectWether(BaseSerivce):
    command = 'collect'
    delay = CONFIG.collect_weather_delay

    def __init__(
        self, *, repeats: int | None = None, initial: bool = False, **kwargs
    ) -> None:
        self.counter = 0
        self.repeats = repeats

        if initial:
            try:
                InitCities().exicute()
            except NoDataError as e:
                logger.warning(f'{e}. Handling by calling for {FetchCities()}.')
                FetchCities().exicute()

        super().__init__(**kwargs)

    @classmethod
    def add_argument(cls, parser: argparse.ArgumentParser):
        parser.add_argument(
            '-R',
            '--repeats',
            type=int,
            help='Collecting repeats amount. Default: infinity. ',
        )
        parser.add_argument(
            '-I',
            '--initial',
            help='Init cities before collecting. Usefull with -O flag. ',
        )

    def exicute(self):
        while True:
            logger.info(f'\n\n\t Starting collecting wether ({self.counter}). ')

            try:
                FetchWeather().exicute()
                logger.info('Collected successfuly. ')
            except CollectorBaseExeption as e:
                # logging all custom exeptions and continue collecting
                #
                # [NOTE]
                # Custom exeptions raised when response is broken or when db has not
                # neccassery data. While this thread will be sliping, the reason of
                # error could be changed by others. Therefore, we won't stop collecting.
                logger.error(e)

            finally:
                self.counter += 1
                if self.repeats and self.counter >= self.repeats:
                    break

                logger.info(
                    f'Next collecting runs in {self.delay} seconds. Sleeping...'
                )

            sleep(self.delay)

        logger.info('End of collecting. ')


########################################################################################
### Report Weather
########################################################################################


class ReportWeather(BaseSerivce, DBSessionMixin):
    command = 'report'
    output = sys.stdout

    def __init__(self, average: bool = False, latest: bool = False, **kwargs) -> None:
        self.methods = [self.get_basic]
        if average:
            self.methods.append(self.get_avarage)
        if latest:
            self.methods.append(self.get_latest)

        BaseSerivce.__init__(self, **kwargs)
        DBSessionMixin.__init__(self)

    @classmethod
    def add_argument(cls, parser: argparse.ArgumentParser):
        parser.add_argument(
            '--average',
            action='store_true',
            help='Report avarage temperature for all cities. ',
        )
        parser.add_argument(
            '--latest',
            action='store_true',
            help='Report latest measured temperature for all cities. ',
        )

    def exicute(self):
        super().exicute()

        for method in self.methods:
            self.output.write(method())
            self.output.write('\n')

    def get_basic(self):
        n_cites = self.query(CityModel).count()
        n_measure = self.query(MeasurementModel).count()
        return (
            '\n'
            f'Collector strores {n_measure} weather measerements for {n_cites} cities.'
        )

    def get_avarage(self):
        report = ''
        cites: list[CityModel] = self.query(CityModel).all()
        for city in cites:
            measurements: list[MeasurementModel] = (
                self.query(MeasurementModel).filter(MeasurementModel.city_id == city.id)
                # .order_by(MeasurementModel.measure_at)
                .all()
            )
            if not measurements:
                continue

            n_measure = len(measurements)
            first = measurements[0]
            last = measurements[-1]
            avarage = sum([measure.temp for measure in measurements]) / n_measure
            report += (
                '\n'
                f'Average temperature at {city.name} is {avarage} C. '
                f'({n_measure} measurements {first.measure_at} -> {last.measure_at})'
            )
        return report

    def get_latest(self):
        report = ''
        cites: list[CityModel] = self.query(CityModel).all()
        for city in cites:
            measure: MeasurementModel = (
                self.query(MeasurementModel)
                .filter(MeasurementModel.city_id == city.id)
                .order_by(MeasurementModel.id.desc())
                .first()
            )
            if not measure:
                continue

            report += (
                '\n'
                f'Temparature at {city.name} is {measure.temp} C. '
                f'({measure.measure_at})'
            )
        return report
