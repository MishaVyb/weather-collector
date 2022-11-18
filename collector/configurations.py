import pydantic

import logging

logger = logging.getLogger(__file__)

CONFIG_FILE = 'configurations.json'


class CollectorConfig(pydantic.BaseModel):
    cities_amount: int = 10
    cities_file: str = 'cities.json'
    open_wether_key: str = 'deecec0236349da5eb1666916ba49e8f'


try:
    CONFIG = CollectorConfig.parse_file(CONFIG_FILE)
except Exception as e:
    # if any exeption is catched, default configuration will be used
    logger.warning(
        f'Get config from "{CONFIG_FILE}" failed: {e}. '
        'Default configurations will be used. '
    )
    CONFIG = CollectorConfig()
