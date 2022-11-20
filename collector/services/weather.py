from __future__ import annotations

import argparse
import sys
from datetime import datetime
from time import sleep

import pydantic

from collector.configurations import CONFIG
from collector.exeptions import CollectorBaseExeption, NoDataError
from collector.functools import init_logger
from collector.models import (
    CityModel,
    ExtraWeatherDataModel,
    MainWeatherDataModel,
    MeasurementModel,
)
from collector.services.base import BaseSerivce, FetchServiceMixin
from collector.services.cities import FetchCities, FetchCoordinates, InitCities
from collector.session import DBSessionMixin

logger = init_logger(__name__)


########################################################################################
# Weather Schemas
########################################################################################


class MainWetherSchema(pydantic.BaseModel):
    """
    Schema for parsing `main` field from Open Weather response.

    For more information see `MainWeatherDataModel` where we store all these values.
    """

    temp: float
    feels_like: float
    temp_min: float
    temp_max: float
    pressure: int
    humidity: int
    sea_level: int | None
    grnd_level: int | None


class WeatherMeasurementSchema(pydantic.BaseModel):
    """
    Schema for parsing data from Open Weather API. We only ensure to have `main` field
    and `dt` field. Other is optional and will be stored at extra data table.

    For more information see `MeasurementModel` where we store all these values.
    """

    main: MainWetherSchema
    dt: int
    "Time of data forecasted, Unix, UTC (timestamp). `measure_at` field at model."


########################################################################################
# Fetch Weather Service
########################################################################################


class FetchWeather(
    BaseSerivce, DBSessionMixin, FetchServiceMixin[WeatherMeasurementSchema]
):
    """
    Fetch weather for cities and store data into database.
    By default fetching weather for all cities from database.

    Endpont detail information: https://openweathermap.org/current
    """

    command = 'fetch_weather'
    url = 'https://api.openweathermap.org/data/2.5/weather'
    schema = WeatherMeasurementSchema

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
        super().exicute()
        for city in self.cities:
            if not all([city.longitude, city.latitude]):
                try:
                    FetchCoordinates(city).exicute()
                except NoDataError as e:
                    logger.warning(f'Can not get weather for {city}: {e}. Continue. ')
                    continue

            measure, extra = self.fetch(city)
            self.store(city, measure, extra)

        self.save()

    def fetch(self, city: CityModel):  # type: ignore
        logger.info(f'Fetching weather for {city}. ')

        self.params['lat'] = str(city.latitude)
        self.params['lon'] = str(city.longitude)

        measure = super().fetch()

        extra: dict = self.response.json()
        for field in self.schema.__fields__:
            extra.pop(field)

        return measure, extra

    def store(self, city: CityModel, measure: WeatherMeasurementSchema, extra: dict):
        self.create(
            MeasurementModel(
                city=city,
                measure_at=datetime.utcfromtimestamp(measure.dt),
                main=MainWeatherDataModel(**measure.main.dict()),
                extra=ExtraWeatherDataModel(data=extra),
            )
        )


########################################################################################
# Collect Weather Service
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
                InitCities(**kwargs).exicute()
            except NoDataError as e:
                logger.warning(f'{e}. Handling by calling for {FetchCities()}.')
                FetchCities(**kwargs).exicute()

        super().__init__(**kwargs)

    @classmethod
    def add_argument(cls, parser: argparse.ArgumentParser):
        parser.add_argument(
            '-r',
            '--repeats',
            metavar='<amount>',
            type=int,
            help='collecting repeats amount. Default: infinity',
        )
        parser.add_argument(
            '-i',
            '--initial',
            action='store_true',
            help='init cities before collecting. Usefull with -O flag',
        )

    def exicute(self):
        while True:
            logger.info(f'\n\n\t Starting collecting weather ({self.counter}). ')

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
# Report Weather Service
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
            help='report avarage temperature for all cities',
        )
        parser.add_argument(
            '--latest',
            action='store_true',
            help='report latest measured temperature for all cities',
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
            f'Collector storing {n_measure} weather measerements for {n_cites} cities.'
        )

    def get_avarage(self):
        report = ''
        cites: list[CityModel] = self.query(CityModel).all()
        for city in cites:
            measurements: list[MeasurementModel] = (
                self.query(MeasurementModel)
                .filter(MeasurementModel.city_id == city.id)
                .all()
            )
            if not measurements:
                continue

            n_measure = len(measurements)
            first = measurements[0]
            last = measurements[-1]
            avarage = sum([measure.main.temp for measure in measurements]) / n_measure
            report += (
                '\n'
                f'Average temperature at {city.name} is {avarage} C. '
                f'({n_measure} measurements {first.measure_at} ... {last.measure_at})'
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
                f'Last measured temperature at {city.name} is {measure.main.temp} C. '
                f'({measure.measure_at})'
            )
        return report