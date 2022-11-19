
import pytest


@pytest.fixture
def connection():
    engine = create_engine(
    )
    return engine.connect()


def seed_database():
    users = [
        {
            "id": 1,
            "name": "John Doe",
        },
        # ...
    ]

    for user in users:
        db_user = User(**user)
        db_session.add(db_user)
    db_session.commit()


@pytest.fixture(scope="session")
def setup_database(connection):
    models.Base.metadata.bind = connection
    models.Base.metadata.create_all()

    seed_database()

    yield

    models.Base.metadata.drop_all()


@pytest.fixture
def db_session(setup_database, connection):
    transaction = connection.begin()
    yield scoped_session(
        sessionmaker(autocommit=False, autoflush=False, bind=connection)
    )
    transaction.rollback()