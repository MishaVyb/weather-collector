import argparse
import logging
import sys
from collector.exeptions import CollectorBaseExeption

from collector.services import BaseSerivce
from collector.functools import init_logger

logger = init_logger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Wether collector. ")
    # for service in BaseSerivce.__subclasses__():
    #     parser.add_argument(
    #         service.command,
    #         type=str
    #     )
    # aaa = BaseSerivce.__subclasses__()
    # ccc = aaa[3].__subclasses__()

    parser.add_argument(
            BaseSerivce.command,
            type=str,
            help=BaseSerivce.description,
            choices=[service.command for service in BaseSerivce.__subclasses__()],
        )

    parser.add_argument(
            '-O',
            '--override',
            action='store_true',
            help='replace cites',
        )

    args = parser.parse_args()
    logger.info(args)

    service_class = BaseSerivce.get_service(command=args.service)
    logger.info(service_class)

    aaa = args._get_kwargs()
    ddd = dict(aaa)
    service = service_class(**ddd)

    try:
        service.exicute()
    except CollectorBaseExeption as e:
        # logging all custom exeptions and continue processing
        logger.error(e)

if __name__ == '__main__':
    main()
