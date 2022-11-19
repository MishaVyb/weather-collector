import pydantic

import logging

from collector.functools import init_logger

logger = init_logger(__name__)

# CONFIG_FILE = 'configurations.json'


class CollectorConfig(pydantic.BaseConfig):
    debug = True
    cities_amount: int = 10
    cities_file: str = 'cities.json'
    open_wether_key: str = 'deecec0236349da5eb1666916ba49e8f'

    class Config:
        env_file = ".env"

# try:
#     CONFIG = CollectorConfig.parse_file(CONFIG_FILE)
# except Exception as e:
#     # if any exeption is catched, default configuration will be used
#     logger.warning(
#         f'Get config from "{CONFIG_FILE}" failed: {e}. '
#         'Default configurations will be used. '
#     )
#     CONFIG = CollectorConfig()

CONFIG = CollectorConfig()