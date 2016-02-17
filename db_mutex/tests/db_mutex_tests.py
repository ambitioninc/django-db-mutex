from datetime import datetime

from db_mutex.exceptions import DBMutexError, DBMutexTimeoutError
from db_mutex.models import DBMutex
from db_mutex.db_mutex import db_mutex

from django.test import TestCase
from django.test.utils import override_settings
from freezegun import freeze_time


class ContextManagerTestCase(TestCase):
    """
    Tests db_mutex as a context manager.
    """
    @freeze_time('2014-02-01')
    def test_no_lock_before(self):
        """
        Tests that a lock is succesfully acquired.
        """
        # There should be no locks before and after the context manager
        self.assertEqual(DBMutex.objects.count(), 0)
        with db_mutex('lock_id'):
            self.assertEqual(DBMutex.objects.count(), 1)
            m = DBMutex.objects.get(lock_id='lock_id')
            self.assertEqual(m.creation_time, datetime(2014, 2, 1))
        self.assertEqual(DBMutex.objects.count(), 0)

    @freeze_time('2014-02-01')
    def test_lock_before(self):
        """
        Tests when a lock already exists.
        """
        # Create a lock
        m = DBMutex.objects.create(lock_id='lock_id')
        # Try to acquire the lock. It should raise an exception
        with self.assertRaises(DBMutexError):
            with db_mutex('lock_id'):
                raise NotImplementedError
        # The lock should still exist
        self.assertTrue(DBMutex.objects.filter(id=m.id).exists())

    @freeze_time('2014-02-01')
    def test_lock_before_suppress_acquisition_errors(self):
        """
        Tests when a lock already exists. Verifies that an exception is thrown when
        suppress_acquisition_errors is True. The exception is still thrown because
        we are using it as a context manager
        """
        # Create a lock
        m = DBMutex.objects.create(lock_id='lock_id')
        # Try to acquire the lock. It should neither acquire nor release it
        with self.assertRaises(DBMutexError):
            with db_mutex('lock_id', suppress_acquisition_exceptions=True):
                raise NotImplementedError
        # The lock should still exist
        self.assertTrue(DBMutex.objects.filter(id=m.id).exists())

    @freeze_time('2014-02-01')
    def test_lock_different_id(self):
        """
        Tests that the lock still works even when another lock with a different id exists.
        """
        # Create a lock
        m = DBMutex.objects.create(lock_id='lock_id')
        # Try to acquire the lock with a different ID
        with db_mutex('lock_id2'):
            self.assertEqual(DBMutex.objects.count(), 2)
            m2 = DBMutex.objects.get(lock_id='lock_id2')
            self.assertEqual(m2.creation_time, datetime(2014, 2, 1))
        # The original lock should still exist but the other one should be gone
        self.assertTrue(DBMutex.objects.filter(id=m.id).exists())
        self.assertEqual(DBMutex.objects.count(), 1)

    def test_lock_timeout_default(self):
        """
        Tests that the lock timeout works with the default value of 30 minutes.
        """
        with freeze_time('2014-02-01'):
            # Create a lock
            orig_lock = DBMutex.objects.create(lock_id='lock_id')

        # Try to acquire the lock one minute in the future. It should fail
        with freeze_time('2014-02-01 00:01:00'):
            with self.assertRaises(DBMutexError):
                with db_mutex('lock_id'):
                    raise NotImplementedError

        # Try to acquire the lock 9 minutes in the future. It should fail
        with freeze_time('2014-02-01 00:09:00'):
            with self.assertRaises(DBMutexError):
                with db_mutex('lock_id'):
                    raise NotImplementedError

        # Try to acquire the lock 30 minutes in the future. It should pass since the lock timed out
        with freeze_time('2014-02-01 00:30:00'):
            with db_mutex('lock_id'):
                self.assertFalse(DBMutex.objects.filter(id=orig_lock.id).exists())
                self.assertEqual(DBMutex.objects.count(), 1)
                m = DBMutex.objects.get(lock_id='lock_id')
                self.assertEqual(m.creation_time, datetime(2014, 2, 1, 0, 30))

    @override_settings(DB_MUTEX_TTL_SECONDS=None)
    def test_no_lock_timeout(self):
        """
        Tests that the lock timeout works when None is configured as the timeout.
        """
        with freeze_time('2014-02-01'):
            # Create a lock
            DBMutex.objects.create(lock_id='lock_id')

        # Try to acquire the lock one minute in the future. It should fail
        with freeze_time('2014-02-01 00:01:00'):
            with self.assertRaises(DBMutexError):
                with db_mutex('lock_id'):
                    raise NotImplementedError

        # Try to acquire the lock 9 minutes in the future. It should fail
        with freeze_time('2014-02-01 00:09:00'):
            with self.assertRaises(DBMutexError):
                with db_mutex('lock_id'):
                    raise NotImplementedError

        # Try to acquire the lock 30 minutes in the future. It should fail
        with freeze_time('2014-02-01 00:30:00'):
            with self.assertRaises(DBMutexError):
                with db_mutex('lock_id'):
                    raise NotImplementedError

        # Try to acquire the lock years in the future. It should fail
        with freeze_time('2016-02-01 00:30:00'):
            with self.assertRaises(DBMutexError):
                with db_mutex('lock_id'):
                    raise NotImplementedError

    @override_settings(DB_MUTEX_TTL_SECONDS=60 * 60)
    def test_custom_lock_timeout(self):
        """
        Tests that the custom lock timeout works when an hour is configured as the timeout.
        """
        with freeze_time('2014-02-01'):
            # Create a lock
            orig_lock = DBMutex.objects.create(lock_id='lock_id')

        # Try to acquire the lock one minute in the future. It should fail
        with freeze_time('2014-02-01 00:01:00'):
            with self.assertRaises(DBMutexError):
                with db_mutex('lock_id'):
                    raise NotImplementedError

        # Try to acquire the lock 31 minutes in the future. It should fail
        with freeze_time('2014-02-01 00:31:00'):
            with self.assertRaises(DBMutexError):
                with db_mutex('lock_id'):
                    raise NotImplementedError

        # Try to acquire the lock 60 minutes in the future. It should pass
        with freeze_time('2014-02-01 01:00:00'):
            with db_mutex('lock_id'):
                self.assertFalse(DBMutex.objects.filter(id=orig_lock.id).exists())
                self.assertEqual(DBMutex.objects.count(), 1)
                m = DBMutex.objects.get(lock_id='lock_id')
                self.assertEqual(m.creation_time, datetime(2014, 2, 1, 1))

    def test_lock_timeout_error(self):
        """
        Tests the case when a lock expires while the context manager is executing.
        """
        with freeze_time('2014-02-01'):
            # Acquire a lock at the given time and release it before it is finished. It
            # should result in an error
            with self.assertRaises(DBMutexTimeoutError):
                with db_mutex('lock_id'):
                    self.assertEqual(DBMutex.objects.count(), 1)
                    m = DBMutex.objects.get(lock_id='lock_id')
                    self.assertEqual(m.creation_time, datetime(2014, 2, 1))

                    # Release the lock before the context manager finishes
                    m.delete()


class FunctionDecoratorTestCase(TestCase):
    """
    Tests db_mutex as a function decorator.
    """
    @freeze_time('2014-02-01')
    def test_no_lock_before(self):
        """
        Tests that a lock is succesfully acquired.
        """
        # There should be no locks before and after the context manager
        self.assertEqual(DBMutex.objects.count(), 0)

        @db_mutex('lock_id')
        def run_get_lock():
            self.assertEqual(DBMutex.objects.count(), 1)
            m = DBMutex.objects.get(lock_id='lock_id')
            self.assertEqual(m.creation_time, datetime(2014, 2, 1))

        run_get_lock()
        self.assertEqual(DBMutex.objects.count(), 0)

    @freeze_time('2014-02-01')
    def test_lock_before(self):
        """
        Tests when a lock already exists.
        """
        # Create a lock
        m = DBMutex.objects.create(lock_id='lock_id')

        @db_mutex('lock_id')
        def run_get_lock():
            raise NotImplementedError

        # Try to acquire the lock. It should raise an exception
        with self.assertRaises(DBMutexError):
            run_get_lock()

        # The lock should still exist
        self.assertTrue(DBMutex.objects.filter(id=m.id).exists())

    @freeze_time('2014-02-01')
    def test_lock_before_suppress_acquisition_exceptions(self):
        """
        Tests when a lock already exists. Note that it should not raise an exception since
        suppress_acquisition_exceptions is True.
        """
        # Create a lock
        m = DBMutex.objects.create(lock_id='lock_id')

        @db_mutex('lock_id', suppress_acquisition_exceptions=True)
        def run_get_lock():
            raise NotImplementedError

        # Try to acquire the lock. It should not raise an exception nor acquire the lock
        run_get_lock()

        # The lock should still exist
        self.assertTrue(DBMutex.objects.filter(id=m.id).exists())

    @freeze_time('2014-02-01')
    def test_lock_different_id(self):
        """
        Tests that the lock still works even when another lock with a different id exists.
        """
        # Create a lock
        m = DBMutex.objects.create(lock_id='lock_id')

        @db_mutex('lock_id2')
        def run_get_lock2():
            self.assertEqual(DBMutex.objects.count(), 2)
            m2 = DBMutex.objects.get(lock_id='lock_id2')
            self.assertEqual(m2.creation_time, datetime(2014, 2, 1))

        # Try to acquire the lock with a different ID
        run_get_lock2()
        # The original lock should still exist but the other one should be gone
        self.assertTrue(DBMutex.objects.filter(id=m.id).exists())
        self.assertEqual(DBMutex.objects.count(), 1)

    def test_lock_timeout_default(self):
        """
        Tests that the lock timeout works with the default value of 30 minutes.
        """
        with freeze_time('2014-02-01'):
            # Create a lock
            orig_lock = DBMutex.objects.create(lock_id='lock_id')

        # Try to acquire the lock one minute in the future. It should fail
        @freeze_time('2014-02-01 00:01:00')
        @db_mutex('lock_id')
        def run_get_lock1():
            raise NotImplementedError

        with self.assertRaises(DBMutexError):
            run_get_lock1()

        # Try to acquire the lock 9 minutes in the future. It should fail
        @freeze_time('2014-02-01 00:09:00')
        @db_mutex('lock_id')
        def run_get_lock2():
            raise NotImplementedError

        with self.assertRaises(DBMutexError):
            run_get_lock2()

        @freeze_time('2014-02-01 00:30:00')
        @db_mutex('lock_id')
        def run_get_lock3():
            self.assertFalse(DBMutex.objects.filter(id=orig_lock.id).exists())
            self.assertEqual(DBMutex.objects.count(), 1)
            m = DBMutex.objects.get(lock_id='lock_id')
            self.assertEqual(m.creation_time, datetime(2014, 2, 1, 0, 30))

        # Try to acquire the lock 30 minutes in the future. It should pass since the lock timed out
        run_get_lock3()

    @override_settings(DB_MUTEX_TTL_SECONDS=None)
    def test_no_lock_timeout(self):
        """
        Tests that the lock timeout works when None is configured as the timeout.
        """
        with freeze_time('2014-02-01'):
            # Create a lock
            DBMutex.objects.create(lock_id='lock_id')

        # Try to acquire the lock one minute in the future. It should fail
        @freeze_time('2014-02-01 00:01:00')
        @db_mutex('lock_id')
        def run_get_lock1():
            raise NotImplementedError

        with self.assertRaises(DBMutexError):
            run_get_lock1()

        # Try to acquire the lock 9 minutes in the future. It should fail
        @freeze_time('2014-02-01 00:09:00')
        @db_mutex('lock_id')
        def run_get_lock2():
            raise NotImplementedError

        with self.assertRaises(DBMutexError):
            run_get_lock2()

        # Try to acquire the lock 30 minutes in the future. It should fail
        @freeze_time('2014-02-01 00:30:00')
        @db_mutex('lock_id')
        def run_get_lock3():
            raise NotImplementedError

        with self.assertRaises(DBMutexError):
            run_get_lock3()

        # Try to acquire the lock years in the future. It should fail
        @freeze_time('2016-02-01 00:30:00')
        @db_mutex('lock_id')
        def run_get_lock4():
            raise NotImplementedError

        with self.assertRaises(DBMutexError):
            run_get_lock4()

    @override_settings(DB_MUTEX_TTL_SECONDS=60 * 60)
    def test_custom_lock_timeout(self):
        """
        Tests that the custom lock timeout works when an hour is configured as the timeout.
        """
        with freeze_time('2014-02-01'):
            # Create a lock
            orig_lock = DBMutex.objects.create(lock_id='lock_id')

        # Try to acquire the lock one minute in the future. It should fail
        @freeze_time('2014-02-01 00:01:00')
        @db_mutex('lock_id')
        def run_get_lock1():
            raise NotImplementedError

        with self.assertRaises(DBMutexError):
            run_get_lock1()

        # Try to acquire the lock 31 minutes in the future. It should fail
        @freeze_time('2014-02-01 00:31:00')
        @db_mutex('lock_id')
        def run_get_lock2():
            raise NotImplementedError

        with self.assertRaises(DBMutexError):
            run_get_lock2()

        # Try to acquire the lock 60 minutes in the future. It should pass
        @freeze_time('2014-02-01 01:00:00')
        @db_mutex('lock_id')
        def run_get_lock3():
            self.assertFalse(DBMutex.objects.filter(id=orig_lock.id).exists())
            self.assertEqual(DBMutex.objects.count(), 1)
            m = DBMutex.objects.get(lock_id='lock_id')
            self.assertEqual(m.creation_time, datetime(2014, 2, 1, 1))

        run_get_lock3()

    def test_lock_timeout_error(self):
        """
        Tests the case when a lock expires while the context manager is executing.
        """
        @freeze_time('2014-02-01')
        @db_mutex('lock_id')
        def run_get_lock1():
            # Acquire a lock at the given time and release it before it is finished. It
            # should result in an error
            self.assertEqual(DBMutex.objects.count(), 1)
            m = DBMutex.objects.get(lock_id='lock_id')
            self.assertEqual(m.creation_time, datetime(2014, 2, 1))

            # Release the lock before the context manager finishes
            m.delete()

        with self.assertRaises(DBMutexTimeoutError):
            run_get_lock1()
