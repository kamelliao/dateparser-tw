import pytest

from dateparser_tw import DateParser


@pytest.fixture(scope="session", autouse=True)
def parser():
    return DateParser()
