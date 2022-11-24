from pprint import pformat
import pydantic

from collector.functools import init_logger

logger = init_logger(__name__)


class DatabaseConfig(pydantic.BaseModel):
    dialect: str = 'postgresql'
    driver: str | None = 'psycopg2'  # if None default db driver will be used
    user: str
    password: str
    host: str = 'db'
    port: int = 5432
    database: str = 'default'

    @property
    def url(self):
        driver = f'+{self.driver}' if self.driver else ''
        return (
            f'{self.dialect}{driver}:'
            f'//{self.user}:{self.password}@{self.host}:{self.port}/{self.database}'
        )


class SQLiteDatabaseConfig(pydantic.BaseModel):
    path: str = 'db.sqlite'

    @property
    def url(self):
        return f'sqlite:///{self.path}'


class CollectorConfig(pydantic.BaseSettings):
    debug: bool

    db: DatabaseConfig | SQLiteDatabaseConfig = SQLiteDatabaseConfig()

    cities_amount: int = 50
    "Amount for auto-inital cities list by fetching them from GeoDB. "
    cities_file: str = 'cities.json'
    "File to descibe which cities weather collector fetching data for. "
    collect_weather_delay: float = 1 * 60 * 60
    "Delay between every weather measurement. Seconds. Dafault: 1 hour. "
    retry_collect_delay: float = 3
    open_weather_key: str
    """
    Open Weather API key.

    [NOTE]
    Default key is getting access for Open Weather under FREE plan and should be used
    only for demonstration porpuses. Restrictions:
    - 60 calls/minute
    - 1,000,000 calls/month
    """

    def __str__(self) -> str:
        return '\n' + pformat(self.dict())

    class Config:
        # production build envirement variables described at '.env'
        # 'debug.env' has the highest priority and addet to .dockerignore
        env_file = '.env', 'debug.env'
        env_nested_delimiter = '__'


try:
    CONFIG = CollectorConfig()
except Exception as e:
    raise RuntimeError(
        f'Init configurations falls down. Ensure to have ".env" file. Details: {e}'
    )
