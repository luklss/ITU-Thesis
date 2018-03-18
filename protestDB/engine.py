from sqlalchemy import create_engine
from sqlite3 import dbapi2 as sqlite

import os
import configparser
config = configparser.ConfigParser()
self_path = os.path.dirname(os.path.abspath(__file__))
config.read(os.path.join(self_path, "alembic.ini"))
db_name=config['alembic']['db_name']

class Connection:

    # Defined static, to persist engine across instances
    engine = None

    def __init__(self, db_name_and_path=db_name):
        if Connection.engine is None:
            Connection.setupEngine(db_name_and_path)
        self.conn   = self.engine.connect()

    @staticmethod
    def setupEngine(db_name_and_path=db_name):
        if not Connection.engine is None:
            return Connection.engine
        if db_name_and_path == db_name:
            db_name_and_path = os.path.join(self_path, db_name)
        Connection.engine = create_engine('sqlite+pysqlite:///%s' % db_name_and_path, module=sqlite)
        return Connection.engine
