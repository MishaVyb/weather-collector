
from __future__ import annotations

import sqlalchemy as db
import sqlalchemy.orm as orm



class DBSessionMixin:
    def __init__(self) -> None:
        self.engine = db.create_engine('sqlite:///db.sqlite3', future=True)
        self.session = orm.Session(self.engine)
