import pytest


@pytest.mark.parametrize("target", ["今天", "今日", "本日"])
def test_today(parser, target):
    res = parser.parse(target, basetime="2024-07-15")
    assert res[res["type"]] == "2024-07-15 00:00:00"


@pytest.mark.parametrize("target", ["明天", "明日", "次日", "隔日", "隔天"])
def test_tomorrow(parser, target):
    res = parser.parse(target, basetime="2024-07-15")
    assert res[res["type"]] == "2024-07-16 00:00:00"


@pytest.mark.parametrize(
    "target, expected",
    [
        ("前年", "2022-01-01 00:00:00"),
        ("去年", "2023-01-01 00:00:00"),
        ("今年", "2024-01-01 00:00:00"),
        ("明年", "2025-01-01 00:00:00"),
        ("後年", "2026-01-01 00:00:00"),
    ],
)
def test_relative_year(parser, target, expected):
    res = parser.parse(target, basetime="2024-07-15")
    assert res[res["type"]][:4] == expected[:4]


@pytest.mark.parametrize(
    "target, expected",
    [
        ("上週", "2024-07-08 00:00:00"),
        ("上週五", "2024-07-12 00:00:00"),
        ("上週六", "2024-07-13 00:00:00"),
        ("上禮拜天", "2024-07-14 00:00:00"),
        ("上星期日", "2024-07-14 00:00:00"),
    ],
)
def test_relative_week(parser, target, expected):
    res = parser.parse(target, basetime="2024-07-15")
    assert res[res["type"]] == expected
