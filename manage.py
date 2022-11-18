import argparse
import logging
import sys

from collector.services import BaseSerivce

logging.basicConfig(format='%(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__file__)


def main():
    parser = argparse.ArgumentParser(description=BaseSerivce.description)
    parser.add_argument(
            BaseSerivce.command,
            type=str,
            help=BaseSerivce.description,
            choices=[service.command for service in BaseSerivce.__subclasses__()],
        )
    args = parser.parse_args()

    service_class = BaseSerivce.get_service(command=args.service)
    logger.info(args)
    logger.info(service_class)

    service = service_class()
    service.exicute()

if __name__ == '__main__':
    main()
