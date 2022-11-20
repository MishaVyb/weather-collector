import pydantic
import pytest
import sqlalchemy.orm as orm
from collector.configurations import CONFIG, CollectorConfig
from collector.exeptions import NoDataError

from collector.functools import init_logger
from collector.models import CityModel, MeasurementModel
from collector.services.cities import (
    CitySchema,
    FetchCities,
    FetchCoordinates,
    InitCities,
)
from collector.services.weather import CollectWether, FetchWeather, ReportWeather


logger = init_logger(__name__)


@pytest.mark.usefixtures('mock_session', 'mock_config')
class TestServices:

    ####################################################################################
    # Init Cities Service
    ####################################################################################

    def test_init_cities_no_file_rises(self):
        with pytest.raises(NoDataError):
            InitCities().exicute()

    def test_init_cities_broken_file_rises(self, broken_cities_file):
        with pytest.raises(pydantic.ValidationError):
            InitCities().exicute()

    def test_init_cities(self, session: orm.Session, cities_file: list):
        InitCities().exicute()
        assert session.query(CityModel).count() == len(cities_file)

    ####################################################################################
    # Fetch Cities Service
    ####################################################################################

    @pytest.mark.parametrize(
        'cities_names',
        [
            pytest.param(['Moscow', 'Tokyo', 'Shanghai', 'Istanbul']),
        ],
    )
    def test_fetch_cities_assert_cities_list(
        self,
        session: orm.Session,
        cities_names: list[str],
    ):
        """
        Test that biggest world cities apper in DB.
        """
        FetchCities().exicute()
        for city in cities_names:
            assert session.query(CityModel).filter(CityModel.name == city).all()

    @pytest.mark.parametrize(
        'amount',
        [
            pytest.param(0),
            pytest.param(10),
            pytest.param(17),
            pytest.param(100, marks=pytest.mark.slow),
        ],
    )
    def test_fetch_cities_assert_amounts(
        self,
        session: orm.Session,
        monkeypatch: pytest.MonkeyPatch,
        config: CollectorConfig,
        amount: int,
    ):
        monkeypatch.setattr(CONFIG, 'cities_amount', amount)

        FetchCities().exicute()

        assert session.query(CityModel).count() == amount
        cities_from_file = pydantic.parse_file_as(list[CitySchema], config.cities_file)
        assert len(cities_from_file) == amount

    ####################################################################################
    # Fetch Coordinates Service
    ####################################################################################

    def test_fetch_coordinates(self, seed_cities_to_database, session: orm.Session):
        cites: list[CityModel] = session.query(CityModel).all()
        for city in cites:
            FetchCoordinates(city).exicute()
            assert city.latitude and city.longitude

    ####################################################################################
    # Fetch Weather Service
    ####################################################################################

    def test_fetch_weathe_rises(self):
        with pytest.raises(NoDataError):
            FetchWeather()

    def test_fetch_weather(self, seed_cities_to_database, session: orm.Session):
        FetchWeather().exicute()
        measures: list[MeasurementModel] = session.query(MeasurementModel).all()
        for measure in measures:
            assert measure.main
            assert measure.main.temp
            assert measure.extra
            assert measure.extra.data

    ####################################################################################
    # Collect Weather Service
    ####################################################################################

    def test_collect_weather_initial(
        self,
        session: orm.Session,
        monkeypatch: pytest.MonkeyPatch,
    ):
        repeats = 2
        cities_amount = 3
        monkeypatch.setattr(CONFIG, 'cities_amount', cities_amount)

        CollectWether(repeats=repeats, initial=True).exicute()
        assert session.query(MeasurementModel).count() == cities_amount * repeats

    def test_collect_weather_initial_many_cities(
        self,
        session: orm.Session,
        monkeypatch: pytest.MonkeyPatch,
    ):
        repeats = 1
        cities_amount = 50
        monkeypatch.setattr(CONFIG, 'cities_amount', cities_amount)

        CollectWether(repeats=repeats, initial=True).exicute()
        assert session.query(MeasurementModel).count() == cities_amount * repeats

    def test_collect_weather_with_cities_at_db(
        self,
        config: CollectorConfig,
        cities_list: list,
        seed_cities_to_database,
        session: orm.Session,
        monkeypatch: pytest.MonkeyPatch,
    ):
        repeats = 2
        CollectWether(repeats=repeats).exicute()
        assert session.query(MeasurementModel).count() == len(cities_list) * repeats

    ####################################################################################
    # Report Weather Service
    ####################################################################################

    def test_repost_weather(self, seed_cities_to_database, session: orm.Session):
        CollectWether(repeats=2).exicute()
        ReportWeather(average=True, latest=True).exicute()
        ...
