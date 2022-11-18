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
from collector.exeptions import ResponseError, ResponseSchemaError
from collector.models import CityModel, WeatherMeasurementModel


logger = logging.getLogger(__file__)


class BaseSerivce:
    description: str = 'Process collector services. '
    command: str = 'service'
    "Command name to run service in command line. "
    # command_arguments: tuple[str, ...] = ()

    # @staticmethod
    # def services():
    #     """
    #     Get services list
    #     """
    #     return BaseSerivce.__subclasses__()

    @staticmethod
    def get_service(*, command: str):
        """
        Get collector service by provided command name.
        """
        filtered = filter(
            lambda service: service.command == command, BaseSerivce.__subclasses__()
        )
        try:
            return next(filtered)
        except StopIteration:
            raise ValueError(f'No service with this command: {command}. ')

    @staticmethod
    def get_parser():
        parser = argparse.ArgumentParser(description=BaseSerivce.description)

        # Base argument:

        # Other servicec argemnts:
        l = BaseSerivce.__subclasses__()
        for service in BaseSerivce.__subclasses__():
            service.add_argument(parser)
        return parser

    @classmethod
    def add_argument(cls, parser: argparse.ArgumentParser):
        pass

    def exicute(self):
        logger.info(f'{self} is running. ')
        # self.exicute_subclass(self)

    def __str__(self) -> str:
        return f'<{self.__class__.__name__}>'


########################################################################################
###
########################################################################################


class InitCities(BaseSerivce):
    description = 'Init cities list from file'
    command = 'init_cities'

    #
    #  file_name = 'cities.json'
    # def __init__(self, file: str = 'cities.json') -> None:
    #     super().__init__()

    # @classmethod
    # def add_argument(cls, parser: argparse.ArgumentParser):
    #     parser.add_argument(
    #         'file_name',
    #         type=str,
    #         help='Absoulte or relative path to JSON file with cities list. ',
    #     )

    def exicute(self):
        ...


########################################################################################
### FetchCities
########################################################################################


class CitySchema(pydantic.BaseModel):
    name: str
    country: str
    countryCode: str
    latitude: float
    longitude: float
    population: int

    @pydantic.validator('name')
    def clean_name_unicode(cls, value):
        return str(
            unicodedata.normalize('NFKD', value)
            .encode('ascii', 'ignore')
            .decode("utf-8")
        )
        # return value


class CitiesListSchema(pydantic.BaseModel):
    data: list[CitySchema]


class FetchCities(BaseSerivce):
    description = 'Fetch cities list from GeoDB API'
    command = 'fetch_cities'
    url = 'http://geodb-free-service.wirefreethought.com/v1/geo/cities'
    params = {"sort": "-population", "types": "CITY"}

    def exicute(self):
        super().exicute()
        cities = self.fetch()
        self.save(cities)
        CreateCities(cities).exicute()

    def fetch(self):
        # [NOTE]
        # We are using GeoDB API Service under FREE plan provided at specified url.
        # Unfortunately, in that case limit params is restricted up to 10 and we need
        # make request 5 times to get 50 cityes.
        restricted_limit = 10
        self.params['limit'] = restricted_limit
        cities: list[CitySchema] = []

        for i in range(int(CONFIG.cities_amount / restricted_limit) + 1):
            offset = i * restricted_limit
            self.params['offset'] = offset

            logger.info(f'Fetching cities: {offset=} limit={restricted_limit}')
            response = requests.get(url=self.url, params=self.params)

            if response.status_code != HTTPStatus.OK:
                raise ResponseError(response)

            try:
                current_page_cities = CitiesListSchema.parse_raw(response.text)
                cities += current_page_cities.data
            except pydantic.ValidationError as e:
                raise ResponseSchemaError(e)

        # logger.info(
        #     '\n'.join(
        #         [
        #             str(
        #                 f'{city.name} {city.population} {city.latitude=} {city.longitude}'
        #             )
        #             for city in cities
        #         ]
        #     )
        # )
        return cities[0 : CONFIG.cities_amount]

    def save(self, cities: list[CitySchema]):
        if os.path.isfile(CONFIG.cities_file):
            pass
            # [TODO]
            # raise FileExistsError()

        with open(CONFIG.cities_file, 'w+', encoding='utf-8') as file:
            json.dump([city.dict() for city in cities], file)


########################################################################################
### Create
########################################################################################

class DBSessionMixin():
    def __init__(self) -> None:
        self.engine = db.create_engine('sqlite:///db.sqlite3', echo=True, future=True)
        self.session = orm.Session(self.engine)

class CreateCities(BaseSerivce, DBSessionMixin):
    def __init__(self, cities: list[CitySchema]) -> None:
        if not cities:
            logger.warning('No cities provided for creation. ')

        self.cities = cities
        super().__init__()

    def exicute(self):
        super().exicute()
        self.session.add_all([CityModel(**city.dict()) for city in self.cities])
        self.session.commit()
        self.session.close()


########################################################################################
### Collect
########################################################################################


class WetherMeasurementSchema(pydantic.BaseModel):
    main: dict
    dt: int
    "Time of data forecasted, Unix, UTC (timestamp)"

    @pydantic.validator('main')
    def main_field_validator(cls, value: dict):
        assert value.get('temp') is not None,  'Sub-field "temp" for "main" is required'
        return value


class CollectWeather(BaseSerivce, DBSessionMixin):
    """
    Fetch wether for cities and store data into DB.
    By default fetching wether for all cities from DB.
    """

    description = 'Fetch wether for cities and store data into DB. '
    command = 'collect_wether'
    url = 'https://api.openweathermap.org/data/2.5/weather'
    params = {
        "appid": CONFIG.open_wether_key,
        "units": "metric",
    }

    def __init__(self) -> None:
        super().__init__()
        self.cities: list[CityModel] = self.session.query(CityModel).all()

    def exicute(self):
        for city in self.cities:
            if not all([city.longitude, city.latitude]):
                self.fetch_coordinates()
                self.store_coordinates()

            measure = self.fetch_wether(city)
            self.store_measure(city, measure)
            # logger.info(f'{city}: {measure}')

        self.session.commit()
        self.session.close()

    def fetch_wether(self, city: CityModel):
        self.params['lat'] = city.latitude
        self.params['lon'] = city.longitude
        response = requests.get(self.url, self.params)

        if response.status_code != HTTPStatus.OK:
            raise ResponseError(response)

        try:
            main = WetherMeasurementSchema.parse_raw(response.text)
        except pydantic.ValidationError as e:
            raise ResponseSchemaError(e)

        return main

    def store_measure(self, city: CityModel, measure: WetherMeasurementSchema):
        self.session.add(WeatherMeasurementModel(
            city=city,
            temp=measure.main['temp'],
            measure_at=datetime.utcfromtimestamp(measure.dt)
        ))


    def fetch_coordinates(self, city: CityModel):
        ...

    def store_coordinates(self, city: CityModel):
        ...
