Installation
============

* Install Django-db-mutex with your favorite Python package manager::
    
    # Using pip
    pip install django-db-mutex
    
    # Or, using pip (from the latest source code)
    pip install git+git://github.com/ambitioninc/django-db-mutex.git

* Add ``'db_mutex'`` to your ``INSTALLED_APPS`` setting::

    INSTALLED_APPS = (
        # other apps
        'db_mutex',
    )
