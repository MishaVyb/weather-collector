
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
from collector.functools import init_logger
from collector.models import CityModel, ExtraMeasurementDataModel, MeasurementModel
from collector.services.base import BaseSerivce
from collector.session import DBSessionMixin


logger = init_logger(__name__)
########################################################################################
###
########################################################################################


class InitCities(BaseSerivce):
    description = 'Init cities list from JSON file'
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
    """
    Fetch cities list from GeoDB API.
    Endpoint detail information: http://geodb-cities-api.wirefreethought.com/
    """

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
