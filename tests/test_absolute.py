import arrow
import pytest


@pytest.mark.parametrize(
    "target, expected",
    [
        ("2024年", "2024-01-01"),
        ("2024年5月", "2024-05-01"),
        ("2024年5月3日", "2024-05-03"),
        ("2024年12月31日", "2024-12-31"),
        ("5月", "2024-05-01"),
        ("5月12號", "2024-05-12"),
        ("12點半", "2024-07-15 12:30:00"),
        ("12點12分", "2024-07-15 12:12:00"),
        ("12點12分57秒", "2024-07-15 12:12:57"),
        ("凌晨三點半", "2024-07-15 03:30:00"),
        ("下午兩點二十三分", "2024-07-15 14:23:00"),
    ],
)
def test_absolute(parser, target, expected):
    res = parser.parse(target, basetime=arrow.get("2024-07-15 00:00:00"))
    assert res.to_arrow() == arrow.get(expected)
