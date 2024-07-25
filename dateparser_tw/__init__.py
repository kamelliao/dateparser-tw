import sys

from loguru import logger

from .normalizer import DateParser

logger_format = "<level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
logger.remove()
default_logger = logger.add(sys.stdout, format=logger_format, level="INFO")


__all__ = ["DateParser"]
