import sys

from loguru import logger

from .helpers import int_common, str_common
from .helpers.LunarSolarConverter import LunarSolarConverter
from .normalizer import DateParser
from .resource.pattern import pattern, r

logger_format = "<level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
logger.remove()
default_logger = logger.add(sys.stdout, format=logger_format, level="INFO")


__all__ = [
    "DateParser",
    "int_common",
    "str_common",
    "LunarSolarConverter",
    "default_logger",
    "logger_format",
    "pattern",
    "r",
]
