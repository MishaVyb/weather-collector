from __future__ import annotations

import argparse
import json
import os
import unicodedata

import pydantic

from collector.configurations import CONFIG
from collector.exeptions import NoDataError
from collector.functools import init_logger
from collector.models import CityModel
from collector.services.base import BaseSerivce, FetchServiceMixin
from collector.session import DBSessionMixin

logger = init_logger(__name__)


########################################################################################
# Cities Schemas
########################################################################################


class CitySchema(pydantic.BaseModel):
    name: str
    country: str | None
    countryCode: str | None
    latitude: float | None
    longitude: float | None
    population: int | None

    @pydantic.validator('name')
    def clean_name_unicode(cls, value):
        return str(
            unicodedata.normalize('NFKD', value)
            .encode('ascii', 'ignore')
            .decode("utf-8")
        )


class CitiesListSchema(pydantic.BaseModel):
    data: list[CitySchema]


class CityCoordinatesSchema(pydantic.BaseModel):
    name: str
    lat: float
    lon: float
    country: str | None
    state: str | None

    # [FIXME] parsing response falls down because of unicode symbols
    # local_names: list[str] | None


########################################################################################
# Init Cities Service
########################################################################################


class InitCities(BaseSerivce, DBSessionMixin):
    """
    Load cities list from JSON file and appended them to database.
    If `predefined` is provided, that list will be used instead.
    """

    command = 'init_cities'

    def __init__(
        self, *, override: bool = False, predefined: list[CitySchema] = [], **kwargs
    ) -> None:
        self.predefined = predefined
        self.override = override
        BaseSerivce.__init__(self, **kwargs)
        DBSessionMixin.__init__(self)

    @classmethod
    def add_argument(cls, parser: argparse.ArgumentParser):
        parser.add_argument(
            '-O',
            '--override',
            action='store_true',
            help='set all other cities at DB not to be tracking for weather collecting',
        )

    def exicute(self):
        super().exicute()
        cities = self.predefined or self.load_from_file()
        if self.override:
            previous: list[CityModel] = self.query(CityModel).all()
            for city in previous:
                city.is_tracked = False
            logger.info(f'{len(previous)} cities are not tracked anymore. ')

        self.create_from_schema(CityModel, *cities)
        self.save()

        logger.info(f'Add new {len(cities)} records to {CityModel}. ')

    def load_from_file(self):
        try:
            return pydantic.parse_file_as(list[CitySchema], CONFIG.cities_file)
        except FileNotFoundError as e:
            raise NoDataError(e, msg='Init cities from file failed. ')


########################################################################################
# Fetch Cities Service
########################################################################################


class FetchCities(BaseSerivce, FetchServiceMixin[CitiesListSchema]):
    """
    Fetch cities list from GeoDB API, save them to JSON file for future custom
    configuration and call for `InitCities` service to store all new cities at database.

    Endpoint detail information: http://geodb-cities-api.wirefreethought.com/
    """

    command = 'fetch_cities'
    url = 'http://geodb-free-service.wirefreethought.com/v1/geo/cities'

    # [NOTE]
    # We are using GeoDB API Service under FREE plan provided at specified url.
    # Unfortunately, in that case limit params is restricted up to 10.
    # And for insntace we need make request 5 times to get 50 cityes.
    restricted_limit = 10
    params = {
        'sort': '-population',
        'types': 'CITY',
        'limit': restricted_limit,
    }
    schema = CitiesListSchema

    def exicute(self):
        super().exicute()
        cities = self.fetch()
        self.append_to_file(cities)
        logger.info(
            f'Sucessfully fethed {CONFIG.cities_amount} cities and stored them at json'
            'file. Go there to confirm results. You can make any changes and commit '
            'them by calling for `init_cities` with -O flag. '
        )

        InitCities(predefined=cities).exicute()

    def fetch(self):
        cities: list[CitySchema] = []
        repeats = CONFIG.cities_amount // self.restricted_limit
        remains = CONFIG.cities_amount % self.restricted_limit

        for i in range(repeats + int(bool(remains))):
            if i == repeats:
                self.params['limit'] = remains # for final fetching

            offset = i * self.restricted_limit
            self.params['offset'] = offset

            logger.info(f'Fetching cities: {offset}/{CONFIG.cities_amount}')

            # `data` is a core field at response json with list of cities
            cities += super().fetch().data


        self.params['limit'] = self.restricted_limit
        return cities

    def append_to_file(self, cities: list[CitySchema]):
        if os.path.isfile(CONFIG.cities_file):
            logger.warning(
                f'{CONFIG.cities_file} already exists. All data will be overriden. '
            )

        with open(CONFIG.cities_file, 'w+', encoding='utf-8') as file:
            json.dump([city.dict() for city in cities], file)


########################################################################################
# Fetch Coordinates Service
########################################################################################


class FetchCoordinates(
    BaseSerivce,
    DBSessionMixin,
    FetchServiceMixin[list[CityCoordinatesSchema]],
):
    """
    If city object doesn't have coordinates, we should get them by calling for
    Open Weather Geocoding API. The API documantation says:

    `Please use Geocoder API if you need automatic convert city names and zip-codes to
    geo coordinates and the other way around. Please note that API requests by city
    name, zip-codes and city id have been deprecated.`

    Endpont detail information: https://openweathermap.org/api/geocoding-api
    """

    command = 'fetch_coordinates'
    url = 'http://api.openweathermap.org/geo/1.0/direct'
    schema = list[CityCoordinatesSchema]
    params = {
        "appid": CONFIG.open_wether_key,
        "limit": 10,
    }

    def __init__(self, city: CityModel | str, **kwargs) -> None:

        BaseSerivce.__init__(self, **kwargs)
        DBSessionMixin.__init__(self)

        if isinstance(city, str):
            self.city: CityModel = (
                self.query(CityModel).filter(CityModel.name == city).one()
            )
        else:
            self.city = city

        self.params['q'] = f'{self.city.name},{self.city.countryCode}'

    def exicute(self):
        super().exicute()

        geo_list = self.fetch()
        if not geo_list:
            raise NoDataError(
                'Getting coordinates failed. '
                f'Geocoding has no information about {self.city}. '
            )
        if len(geo_list) > 1:
            logger.warning(
                f'Geocoding has many records for {self.city}. Taking the first.'
            )

        coordinates = geo_list[0]
        self.city.latitude = coordinates.lat
        self.city.longitude = coordinates.lon
        self.save()

    def fetch(self):
        logger.info(f'Fetching coordinates for {self.city}. ')
        return super().fetch()
