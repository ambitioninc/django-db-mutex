# flake8: noqa
from .exceptions import DBMutexError, DBMutexTimeoutError
from .version import __version__

default_app_config = 'db_mutex.apps.DBMutexConfig'
