import argparse
import logging
import sys
from collector.exeptions import CollectorBaseExeption

from collector.services import BaseSerivce
from collector.functools import init_logger

logger = init_logger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Wether collector. ")
    for service in BaseSerivce.__subclasses__():
        service.add_argument(parser)

    parser.add_argument(
            BaseSerivce.command,
            type=str,
            help=BaseSerivce.description,
            choices=[service.command for service in BaseSerivce.__subclasses__()],
        )

    args = parser.parse_args()
    service_class = BaseSerivce.get_service(command=args.service)
    logger.debug(args)
    logger.debug(service_class)

    service = service_class(**dict(args._get_kwargs()))
    # try:
    service.exicute()
    # except CollectorBaseExeption as e:
    #     # logging all custom exeptions and continue processing
    #     logger.error(e)

if __name__ == '__main__':
    main()
