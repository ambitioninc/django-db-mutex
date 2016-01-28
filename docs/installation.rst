Installation
============

* Install Django-db-mutex with your favorite Python package manager::
    
    # Using pip
    pip install django-db-mutex
    
    # Or, using pip (from source, in editable form)
    pip install -e git://github.com/ambitioninc/django-db-mutex.git#egg=django-db-mutex

* Add ``'db_mutex'`` to your ``INSTALLED_APPS`` setting::

    INSTALLED_APPS = (
        # other apps
        'db_mutex',
    )
