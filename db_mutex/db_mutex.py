from datetime import datetime, timedelta
import functools
import logging

from django.conf import settings
from django.db import transaction, IntegrityError
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
 
from .exceptions import DBMutexError, DBMutexTimeoutError
from .models import DBMutex


LOG = logging.getLogger(__name__)


class db_mutex(object):
    """
    An object that acts as a context manager and a function decorator for acquiring a
    DB mutex lock.
    """
    mutex_ttl_seconds_settings_key = 'DB_MUTEX_TTL_SECONDS'

    def __init__(self, lock_id, suppress_acquisition_exceptions=False):
        """
        This context manager/function decorator can be used in the following way

        .. code-block:: python

            from db_mutex import db_mutex

            # Lock a critical section of code
            try:
                with db_mutex('lock_id'):
                    # Run critical code here
                    pass
            except DBMutexError:
                print('Could not obtain lock')
            except DBMutexTimeoutError:
                print('Task completed but the lock timed out')

            # Lock a function
            @db_mutex('lock_id'):
            def critical_function():
                # Critical code goes here
                pass

            try:
                critical_function()
            except DBMutexError:
                print('Could not obtain lock')
            except DBMutexTimeoutError:
                print('Task completed but the lock timed out')

        :type lock_id: str
        :param lock_id: The ID of the lock one is trying to acquire
        :type suppress_acquisition_exceptions: bool
        :param suppress_acquisition_exceptions: Suppress exceptions when acquiring the lock and instead
            log an error message. Note that this is only applicable when using this as a decorator and
            not a context manager.

        :raises:
            * :class:`DBMutexError <db_mutex.exceptions.DBMutexError>` when the lock cannot be obtained
            * :class:`DBMutexTimeoutError <db_mutex.exceptions.DBMutexTimeoutError>` when the
              lock was deleted during execution

        """
        self.lock_id = lock_id
        self.lock = None
        self.suppress_acquisition_exceptions = suppress_acquisition_exceptions

    def get_mutex_ttl_seconds(self):
        """
        Returns a TTL for mutex locks. It defaults to 30 minutes. If the user specifies None
        as the TTL, locks never expire.

        :rtype: int
        :returns: the mutex's ttl in seconds
        """
        return getattr(settings, self.mutex_ttl_seconds_settings_key, timedelta(minutes=30).total_seconds())

    def delete_expired_locks(self):
        """
        Deletes all expired mutex locks if a ttl is provided.
        """
        ttl_seconds = self.get_mutex_ttl_seconds()
        if ttl_seconds is not None:
            DBMutex.objects.filter(creation_time__lte=datetime.utcnow() - timedelta(seconds=ttl_seconds)).delete()

    def __call__(self, func):
        return self.decorate_callable(func)

    def __enter__(self):
        self.start()

    def __exit__(self, type, value, traceback):
        return self.stop(type, value, traceback)

    def start(self):
        """
        Acquires the db mutex lock. Takes the necessary steps to delete any stale locks.
        Throws a DBMutexError if it can't acquire the lock.
        """
        # Delete any expired locks first
        self.delete_expired_locks()
        try:
            with transaction.atomic():
                self.lock = DBMutex.objects.create(lock_id=self.lock_id)
        except IntegrityError:
            raise DBMutexError('Could not acquire lock: {0}'.format(self.lock_id))

    def stop(self, type, value, traceback):
        """
        Releases the db mutex lock. Throws an error if the lock was released before the function finished.
        """
        ttl_seconds = self.get_mutex_ttl_seconds()
        
        try : 
            dbmutex = DBMutex.objects.get(id=self.lock.id)
            self.lock.delete()
        except ObjectDoesNotExist: 
            dbmutex = None
            
        if value :
            return #Any exception takes precedence over DBMutexTimeoutError
        
        if not dbmutex or (ttl_seconds and dbmutex.creation_time <= timezone.now() - timedelta(seconds=ttl_seconds)):
            raise DBMutexTimeoutError('Lock {0} expired before function completed'.format(self.lock_id))

    def decorate_callable(self, func):
        """
        Decorates a function with the db_mutex decorator by using this class as a context manager around
        it.
        """
        def wrapper(*args, **kwargs):
            try:
                with self:
                    result = func(*args, **kwargs)
                return result
            except DBMutexError as e:
                if self.suppress_acquisition_exceptions:
                    LOG.error(e)
                else:
                    raise e
        functools.update_wrapper(wrapper, func)
        return wrapper
