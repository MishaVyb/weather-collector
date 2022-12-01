import sys

from apscheduler.schedulers.blocking import BlockingScheduler

from collector.configurations import logger
from collector.services import BaseSerivce


def hold():
    try:
        BaseSerivce.manage_services(['--help'])
    except (KeyboardInterrupt, SystemExit):
        # --help command is raising exit exeption
        # catch it to hold our program exicution
        pass
    finally:
        logger.info('Processing is holding. Press Ctr-C to exit.')
        scheduler = BlockingScheduler()
        scheduler.start()


def main():
    options = sys.argv[1:]  # the first arg is a 'manage.py', skipping it
    if options:
        service = BaseSerivce.manage_services(options)
        service.exicute()
    else:
        hold()


if __name__ == '__main__':
    main()
