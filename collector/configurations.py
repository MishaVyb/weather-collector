from pprint import pformat

import pydantic

from collector.functools import init_logger

logger = init_logger('weather-collector', 'INFO')


class DatabaseConfig(pydantic.BaseModel):
    dialect: str = 'postgresql'
    driver: str | None = 'psycopg2'
    user: str
    password: str
    host: str = 'db'
    port: int = 5432
    database: str = 'default'
    echo: bool = False

    @property
    def url(self):
        driver = f'+{self.driver}' if self.driver else ''
        return (
            f'{self.dialect}{driver}:'
            f'//{self.user}:{self.password}@{self.host}:{self.port}/{self.database}'
        )


class SQLiteDatabaseConfig(pydantic.BaseModel):
    path: str = 'db.sqlite3'
    echo: bool = False

    @property
    def url(self):
        return f'sqlite:///{self.path}'


class CollectorConfig(pydantic.BaseSettings):
    """
    debug: `bool`
        true: force using SQLite instead of postgreSQL (even if it defined at .env)
    cities_amount: `int` = 50
        Amount for auto-initial cities list by fetching them from GeoDB.
    cities_file: `str` = 'cities.json'
        File to describe which cities weather collector fetching data for.
    collect_weather_delay: `float` = 1 * 60 * 60
        Delay between every weather measurement. Seconds. Default: 1 hour.
    open_weather_key: `str`
        Open Weather API key. Open Weather could be used under FREE plan. Restrictions:
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
    POSTGRES_HOST: str | None = None

    db: DatabaseConfig | SQLiteDatabaseConfig = SQLiteDatabaseConfig()

    @pydantic.validator('db', pre=True)
    def debug_mode_database_sqlite(cls, db: dict, values: dict):
        if not isinstance(db, dict):
            return values

        # at this point we can not check is postgres variables was loaded
        # because they could be uploaded from 'prod.env' but we are using 'debug.env'.
        # therefore for debug mode sqlite is always used.
        if values.get('debug'):
            for field in DatabaseConfig.__fields__:
                db.pop(field, None)
        return db

    @pydantic.root_validator(pre=True)
    def make_config_fields_equal_to_postgres_variables(cls, values: dict):
        db: dict = values.get('db', {})
        if not isinstance(db, dict):
            return values

        for postgres_field, config_field in zip(
            ['POSTGRES_USER', 'POSTGRES_PASSWORD', 'POSTGRES_DB', 'POSTGRES_HOST'],
            ['user', 'password', 'database', 'host'],
        ):
            if values.get(postgres_field):
                db.setdefault(config_field, values.get(postgres_field))

        values['db'] = db
        return values

    def __str__(self) -> str:
        return '\n' + pformat(self.dict())

    class Config:
        # debug.env and .env has more higher priority than prod.env
        # describe production build at prod.env or .env (debug.env in .dockerignore)
        env_file = 'prod.env', 'debug.env', '.env'
        env_nested_delimiter = '__'


try:
    CONFIG = CollectorConfig()
    logger.debug(f'Running collector under this configurations: {CONFIG}')
except Exception as e:
    raise RuntimeError(
        f'Init configurations fails. Ensure to have ".env" file. Details: {e}'
    )
