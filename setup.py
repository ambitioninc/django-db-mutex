import re
import multiprocessing
from setuptools import setup, find_packages


# import multiprocessing to avoid this bug (http://bugs.python.org/issue15881#msg170215)
assert multiprocessing


def get_version():
    """
    Extracts the version number from the version.py file.
    """
    VERSION_FILE = 'db_mutex/version.py'
    mo = re.search(r'^__version__ = [\'"]([^\'"]*)[\'"]', open(VERSION_FILE, 'rt').read(), re.M)
    if mo:
        return mo.group(1)
    else:
        raise RuntimeError('Unable to find version string in {0}.'.format(VERSION_FILE))


setup(
    name='django-db-mutex',
    version=get_version(),
    description='Acquire a mutex via the DB in Django',
    long_description=open('README.rst').read(),
    url='http://github.com/ambitioninc/django-db-mutex/',
    author='Wes Kendall',
    author_email='opensource@ambition.com',
    packages=find_packages(),
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Framework :: Django',
        'Framework :: Django :: 1.9',
        'Framework :: Django :: 1.10',
        'Framework :: Django :: 1.11',
    ],
    license='MIT',
    install_requires=[
        'django>=1.8',
    ],
    tests_require=[
        'psycopg2',
        'django-nose>=1.4',
        'mock',
        'coverage>=3.7.1',
        'freezegun>=0.3.2',
        'django-dynamic-fixture'
    ],
    test_suite='run_tests.run_tests',
    include_package_data=True,
    zip_safe=False,
)
