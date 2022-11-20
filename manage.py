import sys
from collector.functools import init_logger
from collector.services import BaseSerivce

logger = init_logger(__name__)


def main():
    service = BaseSerivce.manage_services(sys.argv[1:])
    service.exicute()


if __name__ == '__main__':
    main()
