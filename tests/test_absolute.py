import arrow
import pytest


@pytest.mark.parametrize(
    "target, expected",
    [
        ("2024年", arrow.get("2024-01-01")),
        ("2024年5月", arrow.get("2024-05-01")),
        ("2024年5月3日", arrow.get("2024-05-03")),
        ("2024年12月31日", arrow.get("2024-12-31")),
        ("5月", arrow.get("2024-05-01")),
        ("5月12號", arrow.get("2024-05-12")),
        ("12點半", arrow.get("2024-07-15 12:30:00")),
    ],
)
def test_absolute(parser, target, expected):
    res = parser.parse(target, basetime=arrow.get("2024-07-15 00:00:00"))
    assert res.to_arrow() == expected
