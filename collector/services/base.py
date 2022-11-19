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


logger = init_logger(__name__)


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