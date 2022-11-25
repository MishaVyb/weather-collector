import logging
from pprint import pformat
import pydantic

from collector.functools import init_logger

logger = init_logger(__name__, level=logging.INFO)


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
    path: str = 'db.sqlite3'

    @property
    def url(self):
        return f'sqlite:///{self.path}'


class CollectorConfig(pydantic.BaseSettings):
    """
    cities_amount: int = 50
        Amount for auto-inital cities list by fetching them from GeoDB.
    cities_file: str = 'cities.json'
        File to descibe which cities weather collector fetching data for.
    collect_weather_delay: float = 1 * 60 * 60
        Delay between every weather measurement. Seconds. Dafault: 1 hour.
    open_weather_key: str
        Open Weather API key.
        [NOTE]
        Default key is getting access for Open Weather under FREE plan and should be used
        only for demonstration porpuses. Restrictions:
        - 60 calls/minute
        - 1,000,000 calls/month
    """

    debug: bool

    cities_amount: int = 50
    cities_file: str = 'cities.json'
    collect_weather_delay: float = 1 * 60 * 60
    retry_collect_delay: float = 3
    open_weather_key: str

    POSTGRES_USER: str | None = None
    POSTGRES_PASSWORD: str | None = None
    POSTGRES_DB: str | None = None

    db: DatabaseConfig | SQLiteDatabaseConfig = SQLiteDatabaseConfig()

    @pydantic.validator('db', pre=True)
    def debug_mode_database_sqlite(cls, db: dict, values: dict):
        if not isinstance(db, dict):
            return values

        # at this point we can not check is posgress variables was loaded
        # because the could be uploaded from 'prod.env' bu we are using 'debug.env'.
        # therefore for debug mode sqlite is alwase used.
        if values.get('debug'):
            for field in DatabaseConfig.__fields__:
                db.pop(field, None)
        return db

    @pydantic.root_validator(pre=True)
    def make_alias_to_posrgess_variables(cls, values: dict):
        db: dict = values.get('db', {})
        if not isinstance(db, dict):
            return values

        if values.get('POSTGRES_USER'):
            db.setdefault('user', values.get('POSTGRES_USER'))
        if values.get('POSTGRES_PASSWORD'):
            db.setdefault('password', values.get('POSTGRES_PASSWORD'))

        values['db'] = db
        return values

    def __str__(self) -> str:
        return '\n' + pformat(self.dict())

    class Config:
        # production build envirement variables described at 'prod.env'
        # 'debug.env' has the highest priority and addet to .dockerignore
        env_file = (
            'prod.env',
            # 'debug.env',
        )
        env_nested_delimiter = '__'


try:
    CONFIG = CollectorConfig()
    logger.debug(f'Running collector under this configurations: {CONFIG}')
except Exception as e:
    raise RuntimeError(
        f'Init configurations falls down. Ensure to have ".env" file. Details: {e}'
    )


