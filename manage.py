#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""

import os
import sys

from dotenv import load_dotenv

settings_module = "ohmg.settings"

is_testing = "test" in sys.argv
if is_testing:
    settings_module = "tests.settings_test"

if is_testing:
    import coverage

    os.environ["TESTING"] = "True"
    cov = coverage.coverage(source=["ohmg"], omit=["*/tests/*", "*/migrations/*"])
    cov.set_option("report:show_missing", True)
    cov.set_option("report:skip_covered", True)
    cov.erase()
    cov.start()


def main():
    """Run administrative tasks."""
    load_dotenv()
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", settings_module)
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()

    if is_testing:
        cov.stop()
        cov.save()
        cov.report()
