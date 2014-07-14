Django-db-mutex Documentation
=============================

Django-db-mutex provides the ability to acquire a mutex lock from the database
in Django.

Overview
--------

For critical pieces of code that cannot overlap with one another, it is often
necessary to acquire a mutex lock of some sort. Many solutions use a memcache
lock strategy, however, this strategy can be brittle in the case of memcache
going down or when an unconsistent hashing function is used in a distributed
memcache setup.

If your application does not need a high performance mutex lock, Django DB
Mutex does the trick. The common use case for Django DB Mutex is to provide the
abilty to lock long-running periodic tasks that should not overlap with one
another. Celery is the common backend for Django when scheduling periodic
tasks.
