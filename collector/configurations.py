import pydantic

from collector.functools import init_logger

logger = init_logger(__name__)


class CollectorConfig(pydantic.BaseSettings):
    debug: bool = False

    cities_amount: int = 50
    "Amount for auto-inital cities list by fetching them from GeoDB. "

    cities_file: str = 'cities.json'
    "File to descibe cities collector fetching weather for. "

    collect_weather_delay: float = 1 * 60 * 60
    "Delay between every weather measurement. Seconds. Dafault: 1 hour. "

    open_wether_key: str = 'deecec0236349da5eb1666916ba49e8f'
    """
    Open Weather API key.

    [NOTE]
    Default key is getting access for Open Weather under FREE plan and should be used
    only for demonstration porpuses. Restrictions:
    - 60 calls/minute
    - 1,000,000 calls/month
    """

    class Config:
        env_file = '.env'


CONFIG = CollectorConfig()
