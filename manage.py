import sys
from collector.functools import init_logger
from collector.services import BaseSerivce

logger = init_logger(__name__)

from datetime import datetime
from time import sleep
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.blocking import BlockingScheduler

def hold():
    try:
        BaseSerivce.manage_services(['--help'])
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        logger.info('Processing is holding. Press Ctr-C to exit.')
        scheduler = BlockingScheduler()
        scheduler.start()

def main():
    argv = sys.argv[1:]
    if argv:
        service = BaseSerivce.manage_services(argv)
        service.exicute()
    else:
        hold()



if __name__ == '__main__':
    # # if len(sys.argv) > 1 and sys.argv[1] == 'hellow':
    # logger.info('hellow world docker')

    # # else:
    logger.info(sys.argv)
    main()

