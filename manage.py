import sys

from apscheduler.schedulers.blocking import BlockingScheduler

from collector.configurations import logger
from collector.services import BaseService


def hold():
    try:
        BaseService.manage_services(['--help'])
    except (KeyboardInterrupt, SystemExit):
        # --help command is raising exit exception
        # catch it to hold our program execution
        pass
    finally:
        logger.info('Processing is holding. Press Ctr-C to exit.')
        scheduler = BlockingScheduler()
        scheduler.start()


def main():
    options = sys.argv[1:]  # the first arg is a 'manage.py', skipping it
    if options:
        service = BaseService.manage_services(options)
        service.execute()
    else:
        hold()


if __name__ == '__main__':
    main()
