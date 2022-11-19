import logging


def init_logger(name: str, level: int = logging.INFO):
    """
    Cinfigurate and get logger by provided name.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
    logger.addHandler(handler)
    return logger