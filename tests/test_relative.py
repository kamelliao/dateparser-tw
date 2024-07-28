import arrow
import pytest


@pytest.mark.parametrize(
    "basetime, expected",
    [
        ("2024-07-15", "2024-07-15"),
    ],
)
@pytest.mark.parametrize("target", ["今天", "今日", "本日"])
def test_today(parser, basetime, expected, target):
    res = parser.parse(target, basetime=arrow.get(basetime))
    assert res.to_arrow() == arrow.get(expected)


@pytest.mark.parametrize(
    "basetime, expected",
    [
        ("2024-07-15", "2024-07-14"),
        ("2024-07-01", "2024-06-30"),
    ],
)
@pytest.mark.parametrize("target", ["昨天", "昨日"])
def test_yesterday(parser, basetime, expected, target):
    res = parser.parse(target, basetime=arrow.get(basetime))
    assert res.to_arrow() == arrow.get(expected)


@pytest.mark.parametrize(
    "basetime, expected",
    [
        ("2024-07-15", "2024-07-16"),
        ("2024-07-31", "2024-08-01"),
    ],
)
@pytest.mark.parametrize("target", ["明天", "明日", "次日", "隔日", "隔天"])
def test_tomorrow(parser, basetime, expected, target):
    res = parser.parse(target, basetime=arrow.get(basetime))
    assert res.to_arrow() == arrow.get(expected)


@pytest.mark.parametrize(
    "target, expected",
    [
        ("前年", 2022),
        ("去年", 2023),
        ("今年", 2024),
        ("明年", 2025),
        ("後年", 2026),
    ],
)
def test_relative_year(parser, target, expected):
    res = parser.parse(target, basetime="2024-07-15")
    assert res.year == expected


@pytest.mark.parametrize(
    "target, expected",
    [
        ("上週", "2024-07-08"),
        ("上週五", "2024-07-12"),
        ("上週六", "2024-07-13"),
        ("上禮拜天", "2024-07-14"),
        ("上星期日", "2024-07-14"),
        ('星期三', '2024-07-17'),
        ('這週三', '2024-07-17'),
    ],
)
def test_relative_week(parser, target, expected):
    res = parser.parse(target, basetime="2024-07-15")
    assert res.to_arrow() == arrow.get(expected)
