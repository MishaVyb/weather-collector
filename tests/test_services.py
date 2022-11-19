import pytest
import sqlalchemy as db
import sqlalchemy.orm as orm
from collector import configurations
from collector.configurations import CONFIG

from collector.functools import init_logger
from collector.models import CityModel
from collector.services.cities import FetchCities
from collector.services.wether import ReportWeather

from collector import session as session_module

logger = init_logger(__name__)

# def test_services(opened_session):
#     city = CityModel(name='Moscow')
#     opened_session.add(city)
#     opened_session.commit()
#     logger.info(opened_session.query(CityModel).all())


# def test_service2(opened_session):
#     city = CityModel(name='Piter')
#     opened_session.add(city)
#     opened_session.commit()
#     logger.info(opened_session.query(CityModel).all())

# #def test_service3(monkeypatch, session):
# def test_service3(mock_session):
# #    monkeypatch.setattr(session_module, 'Session', session)

#     ReportWeather().exicute()


@pytest.mark.usefixtures('mock_session')
class TestServices:

    def test_afetch_cities_service(self, session: orm.Session, monkeypatch):

        monkeypatch.setattr(CONFIG, 'cities_amount', 0)
        FetchCities().exicute()
        assert session.query(CityModel).count() == CONFIG.cities_amount

        monkeypatch.setattr(CONFIG, 'cities_amount', 10)
        FetchCities().exicute()
        assert session.query(CityModel).count() == CONFIG.cities_amount
        session.query(CityModel).delete()

        monkeypatch.setattr(CONFIG, 'cities_amount', 100)
        FetchCities().exicute()
        assert session.query(CityModel).count() == CONFIG.cities_amount

    def test_report_service(self):
        logger.info(CONFIG.cities_amount)
        
        ReportWeather().exicute()
