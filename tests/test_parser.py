def test_case1(parser):
    res = parser.parse(text="本月三日", basetime="2021-07-01")
    assert res["type"] == "timestamp"
    assert res[res["type"]] == "2021-07-03 00:00:00"


def test_case1(parser):
    res = parser.parse(text="我需要大概33天2分鐘四秒")
    assert res["type"] == "timedelta"
    assert res[res["type"]]["year"] == 0
    assert res[res["type"]]["month"] == 0
    assert res[res["type"]]["day"] == 33
    assert res[res["type"]]["hour"] == 0
    assert res[res["type"]]["minute"] == 2
    assert res[res["type"]]["second"] == 4


def test_case2(parser):
    res = parser.parse(text="2013年二月二十八日下午四點三十分二十九秒")
    assert res["type"] == "timestamp"
    assert res[res["type"]] == "2013-02-28 16:30:29"


def test_case4(parser):
    res = parser.parse(text="本月三日", basetime="2021-07-01")
    assert res["type"] == "timestamp"
    assert res[res["type"]] == "2021-07-03 00:00:00"


def test_case5(parser):
    res = parser.parse(text="7點4分", basetime="2021-07-01")
    assert res["type"] == "timestamp"
    assert res[res["type"]] == "2021-07-01 07:04:00"
