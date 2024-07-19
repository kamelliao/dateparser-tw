import pytest
from dateparser_tw import TimeNormalizer


@pytest.fixture(scope='session', autouse=True)
def parser():
    return TimeNormalizer()