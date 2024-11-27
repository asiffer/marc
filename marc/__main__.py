#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""

import os
import sys
from importlib._bootstrap import ModuleSpec

# in the zipapp case __main__.py is put out of the module
# so __spec__ is None and django crashes. Here it links
# back to this file. This file must be copied to the root
# of the zippapp project (keeping the  __main__.py name )
if __spec__ is None:
    __spec__ = ModuleSpec("marc.__main__", None)


def main():
    # Ensure the zipapp path is added to sys.path
    """Run administrative tasks."""
    # Add the directory containing the app to sys.path

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "marc.settings")
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
