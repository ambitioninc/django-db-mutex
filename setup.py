import os
from setuptools import setup


setup(
    name='django-db-mutex',
    version=open(os.path.join(os.path.dirname(__file__), 'db_mutex', 'VERSION')).read().strip(),
    description='Acquire a mutex via the DB in Django',
    long_description=open('README.md').read(),
    url='http://github.com/ambitioninc/django-db-mutex/',
    author='Wes Kendall',
    author_email='wesleykendall@gmail.com',
    packages=[
        'db_mutex',
        'db_mutex.migrations',
    ],
    classifiers=[
        'Programming Language :: Python',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Framework :: Django',
    ],
    install_requires=[
        'django>=1.6',
    ],
    include_package_data=True,
)
