from __future__ import annotations

import argparse
from http import HTTPStatus
from typing import Generic, Iterable, Type, TypeVar

import requests
from pydantic import BaseModel, ValidationError, parse_obj_as

from collector.configurations import CONFIG, logger
from collector.exceptions import ResponseError, ResponseSchemaError

_SchemaType = TypeVar('_SchemaType', bound=BaseModel | Iterable[BaseModel])
"""
Bounded TypeVar for Generic classes that takes any subtype of BaseModel class.
Also bound to Iterable, because JSON response could be a `list[BaseModel]`.
"""


class BaseService:
    command: str = 'service_name'
    "Command name to run service in command line. "

    def __init__(self, **kwargs) -> None:
        self.init_kwargs = kwargs

    @classmethod
    def manage_services(cls, argv: list[str]):
        """
        Parsing command line args and getting service initialized with thouse args.
        """
        parser = argparse.ArgumentParser(description='Weather Collector. ')
        parser.add_argument(
            'service',
            type=str,
            help='service to proceed',
            choices=[service.command for service in cls.__subclasses__()],
        )
        for service in cls.__subclasses__():
            service.add_argument(parser)

        args = parser.parse_args(argv)
        service_class = cls.get_service(command=args.service)
        return service_class(**dict(args._get_kwargs()))

    @classmethod
    def get_service(cls, *, command: str):
        """
        Get collector service by provided command name.
        """
        filtered = filter(
            lambda service: service.command == command, cls.__subclasses__()
        )
        try:
            return next(filtered)
        except StopIteration:
            raise ValueError(f'No service with this command: {command}. ')

    @classmethod
    def get_descriptions(cls):
        return 'Collect Weather services description: \n' + '\n'.join(
            [
                f'{service.command}:\t{service.__doc__}'
                for service in cls.__subclasses__()
            ]
        )

    @classmethod
    def add_argument(cls, parser: argparse.ArgumentParser):
        pass

    def execute(self):
        logger.info(f'{self} is running. ')

    def __str__(self) -> str:
        return f'<{self.__class__.__name__}>'


class FetchServiceMixin(Generic[_SchemaType]):
    url: str = ''
    params: dict = {
        "appid": CONFIG.open_weather_key,
        "units": "metric",
    }
    schema: Type[_SchemaType]
    "Pydantic Model to parse response JSON data. Must be defined at inhereted classes. "

    def fetch(self) -> _SchemaType:
        self.response = requests.get(self.url, self.params)

        if self.response.status_code != HTTPStatus.OK:
            raise ResponseError(self.response, self.response.json())
        if not getattr(self, 'schema', None):
            return self.response.json()

        try:
            instance = parse_obj_as(self.schema, self.response.json())
        except ValidationError as e:
            raise ResponseSchemaError(e)

        return instance
