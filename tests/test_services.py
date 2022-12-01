import pydantic
import pytest
import sqlalchemy.orm as orm

from collector.configurations import CONFIG, CollectorConfig
from collector.exceptions import NoDataError
from collector.models import CityModel, MeasurementModel
from collector.services.cities import (CitySchema, FetchCities,
                                       FetchCoordinates, InitCities)
from collector.services.weather import (CollectScheduler, FetchWeather,
                                        ReportWeather)


@pytest.mark.usefixtures('mock_config', 'setup_database')
class TestServices:

    ####################################################################################
    # Init Cities Service
    ####################################################################################

    def test_init_cities_no_file_rises(self):
        with pytest.raises(NoDataError):
            InitCities().execute()

    def test_init_cities_broken_file_rises(self, broken_cities_file):
        with pytest.raises(pydantic.ValidationError):
            InitCities().execute()

    def test_init_cities_(self, session: orm.Session, cities_file: list):
        InitCities().execute()
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
        Test that biggest world cities appear in DB.
        """
        FetchCities().execute()
        for city in cities_names:
            assert session.query(CityModel).filter(CityModel.name == city).all()

    @pytest.mark.parametrize(
        'amount',
        [
            pytest.param(1),
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

        FetchCities().execute()

        assert session.query(CityModel).count() == amount
        cities_from_file = pydantic.parse_file_as(list[CitySchema], config.cities_file)
        assert len(cities_from_file) == amount

    def test_fetch_cities_zero_cities_amount_rises(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        monkeypatch.setattr(CONFIG, 'cities_amount', 0)

        # the same as InitCities - FetchCities will rise NoDataError for 0 cities amount
        with pytest.raises(NoDataError):
            FetchCities().execute()

    ####################################################################################
    # Fetch Coordinates Service
    ####################################################################################

    def test_fetch_coordinates(self, seed_cities_to_database, session: orm.Session):
        cites: list[CityModel] = session.query(CityModel).all()
        for city in cites:
            FetchCoordinates(city).execute()
            assert city.latitude and city.longitude

    ####################################################################################
    # Fetch Weather Service
    ####################################################################################

    def test_fetch_weather_rises(self):
        with pytest.raises(NoDataError):
            FetchWeather()

    def test_fetch_weather(self, seed_cities_to_database, session: orm.Session):
        FetchWeather().execute()
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

        CollectScheduler(repeats=repeats, initial=True).execute()
        assert session.query(MeasurementModel).count() == cities_amount * repeats

    def test_collect_weather_initial_many_cities(
        self,
        session: orm.Session,
        monkeypatch: pytest.MonkeyPatch,
    ):
        repeats = 1
        cities_amount = 50
        monkeypatch.setattr(CONFIG, 'cities_amount', cities_amount)

        CollectScheduler(repeats=repeats, initial=True).execute()
        assert session.query(MeasurementModel).count() == cities_amount * repeats

    def test_collect_weather_with_cities_at_db(
        self,
        cities_list: list,
        seed_cities_to_database,
        session: orm.Session,
        monkeypatch: pytest.MonkeyPatch,
    ):
        repeats = 2
        CollectScheduler(repeats=repeats).execute()
        assert session.query(MeasurementModel).count() == len(cities_list) * repeats

    ####################################################################################
    # Report Weather Service
    ####################################################################################

    def test_report_weather(self, seed_cities_to_database, session: orm.Session):
        CollectScheduler(repeats=1).execute()
        ReportWeather(average=True, latest=True).execute()
        ...
