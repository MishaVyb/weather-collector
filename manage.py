import sys

from apscheduler.schedulers.blocking import BlockingScheduler

from collector.configurations import logger
from collector.services import BaseService


def main():
    options = sys.argv[1:]  # the first arg is a 'manage.py', skipping it
    try:
        service = BaseService.manage_services(options)
    except (KeyboardInterrupt, SystemExit) as e:
        if options in ['--help', '-h']:
            logger.info(BaseService.get_descriptions())
        raise e

    service.execute()


if __name__ == '__main__':
    main()
