import sys
from optparse import OptionParser
from settings import configure_settings


# Configure the default settings
configure_settings()

# Django nose must be imported here since it depends on the settings being configured
from django_nose import NoseTestSuiteRunner  # noqa


def run_tests(*test_args, **kwargs):
    if not test_args:
        test_args = ['db_mutex']

    kwargs.setdefault('interactive', False)

    test_runner = NoseTestSuiteRunner(**kwargs)

    failures = test_runner.run_tests(test_args)
    sys.exit(failures)


if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option('--verbosity', dest='verbosity', action='store', default=1, type=int)
    (options, args) = parser.parse_args()

    run_tests(*args, **options.__dict__)
