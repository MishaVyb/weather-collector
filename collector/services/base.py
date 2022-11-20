from __future__ import annotations

import argparse
from http import HTTPStatus
from typing import Type

import pydantic
import requests

from collector.configurations import CONFIG
from collector.exeptions import ResponseError, ResponseSchemaError
from collector.functools import init_logger

logger = init_logger(__name__)


class BaseSerivce:
    description: str = 'Process collector services. '
    command: str = 'service'
    "Command name to run service in command line. "

    def __init__(self, **kwargs) -> None:
        pass

    @staticmethod
    def manage_services():
        """
        Parsing command line args and getting service initialized with thouse args.
        """
        parser = argparse.ArgumentParser(description='Weather Collector. ')
        parser.add_argument(
            BaseSerivce.command,
            type=str,
            help='service to proceed',
            choices=[service.command for service in BaseSerivce.__subclasses__()],
        )
        for service in BaseSerivce.__subclasses__():
            service.add_argument(parser)

        args = parser.parse_args()
        service_class = BaseSerivce.get_service(command=args.service)
        return service_class(**dict(args._get_kwargs()))

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


    @classmethod
    def add_argument(cls, parser: argparse.ArgumentParser):
       pass

    def exicute(self):
        logger.info(f'{self} is running. ')

    def __str__(self) -> str:
        return f'<{self.__class__.__name__}>'


class FetchServiceMixin:
    url: str = ''
    params: dict = {
        "appid": CONFIG.open_wether_key,
        "units": "metric",
    }
    schema: Type[pydantic.BaseModel] | None = None
    "Pydantic Model to parse response JSON data."

    def exicute(self):
        self.fetch()

    def fetch(self) -> dict | list | pydantic.BaseModel:
        self.response = requests.get(self.url, self.params)

        if self.response.status_code != HTTPStatus.OK:
            raise ResponseError(self.response, self.response.json())
        if not self.schema:
            return self.response.json()

        try:
            instance = pydantic.parse_obj_as(self.schema, self.response.json())
        except pydantic.ValidationError as e:
            raise ResponseSchemaError(e)

        return instance
