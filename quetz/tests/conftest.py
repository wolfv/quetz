"""py.test fixtures

Fixtures for Quetz components
-----------------------------
- `db`

"""
# Copyright 2020 QuantStack
# Distributed under the terms of the Modified BSD License.

from pytest import fixture

from quetz.database import get_session
from quetz.config import Config
# global db session object
_db = None


@fixture
def db():
    """Get a db session"""
    global _db
    if _db is None:
        _db = get_session('sqlite:///:memory:')

    return _db

def get_test_config():

    c = {
        'github': {
            'client_id': '',
            'client_secret': ''
        },
        'sqlalchemy': {
            'database_url': ''
        },
        'session': {
            'secret': 'abcdefg',
            'https_only': False
        }
    }

    global _db
    if _db is None:
        _db = get_session('sqlite:///:memory:')

    conf = Config(config=c, db_session=_db)
    return conf