# flake8: noqa
from db_mutex.exceptions import DBMutexError, DBMutexTimeoutError
from db_mutex.version import __version__

default_app_config = 'db_mutex.apps.DBMutexConfig'
