"""Logging module, for Airport."""

from django.conf import settings
from datetime import datetime
import logging


logging.basicConfig(filename=settings.LOGGING_PATH,
                    level=logging.DEBUG,)


def log_warning(*args, **kwargs):
    logging.warning(*args, **kwargs)


def log_debug(*args, **kwargs):
    logging.debug(*args, **kwargs)


def log_info(*args, **kwargs):
    logging.info(*args, **kwargs)


def log_error(*args, **kwargs):
    logging.error(*args, **kwargs)


def log_critical(*args, **kwargs):
    logging.critical(*args, **kwargs)
