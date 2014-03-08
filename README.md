[![Build Status](https://travis-ci.org/ambitioninc/django-db-mutex.png)](https://travis-ci.org/ambitioninc/django-db-mutex)
django-db-mutex
===============

Provides the ability to acquire a mutex lock from the database in Django.

## A Brief Overview
For critical pieces of code that cannot overlap with one another, it is often necessary to acquire a mutex lock of some sort. Many solutions use a memcache lock strategy, however, this strategy can be brittle in the case of memcache going down or when an unconsistent hashing function is used in a distributed memcache setup.

If your application does not need a high performance mutex lock, Django DB Mutex does the trick. The common use case for Django DB Mutex is to provide the abilty to lock long-running periodic tasks that should not overlap with one another. Celery is the common backend for Django when scheduling periodic tasks.

## How to Use Django DB Mutex
The Django DB Mutex app provides a context manager and function decorator for locking a critical section of code. The context manager is used in the following way:

    from db_mutex import db_mutex, DBMutexError, DBMutexTimeoutError

    # Lock a critical section of code
    try:
        with db_mutex('lock_id'):
            # Run critical code here
            pass
    except DBMutexError:
        print 'Could not obtain lock'
    except DBMutexTimeoutError:
        print 'Task completed but the lock timed out'

You'll notice that two errors were caught from this context manager. The first one, DBMutexError, is thrown if the lock cannot be acquired. The second one, DBMutexTimeoutError, is thrown if the critical code completes but the lock timed out. More about lock timeout in the next section.

The db_mutex decorator can also be used in a similar manner for locking a function.

    from db_mutex import db_mutex, DBMutexError, DBMutexTimeoutError

    @db_mutex('lock_id')
    def critical_function():
        pass

    try:
        critical_function()
    except DBMutexError:
        print 'Could not obtain lock'
    except DBMutexTimeoutError:
        print 'Task completed but the lock timed out'

## Lock Timeout
Django DB Mutex comes with lock timeout baked in. This ensures that a lock cannot be held forever. This is especially important when working with segments of code that may run out of memory or produce errors that do not raise exceptions.

In the default setup of this app, a lock is only valid for 30 minutes. As shown earlier in the example code, if the lock times out during the execution of a critical piece of code, a DBMutexTimeoutError will be thrown. This error basically says that a critical section of your code could have overlapped (but it doesn't necessarily say if a section of code overlapped or didn't).

In order to change the duration of a lock, set the DB_MUTEX_TTL_SECONDS variable in your settings.py file to a number of seconds. If you want your locks to never expire (beware!), set the setting to None.

## Usage with Celery
Django DB Mutex can be used with celery's tasks in the following manner.

    from celery import Task

    class NonOverlappingTask(Task):
        __metaclass__ = ABCMeta

        def run_worker(self, *args, **kwargs):
            """
            Run worker code here.
            """
            raise NotImplementedError()

        def run(self, *args, **kwargs):
            try:
                with db_mutex(self.__class__.__name__):
                    self.run_worker(*args, **kwargs):
            except DBMutexError:
                # Ignore this task since the same one is already running
                pass
            except DBMutexTimeoutError:
                # A task ran for a long time and another one may have overlapped with it. Report the error
                pass

## License
MIT License (see the LICENSE file included in the repository)
