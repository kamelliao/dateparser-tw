from typing import Literal, TypedDict


class Setting(TypedDict):
    prefer_dates_from: Literal["current", "future", "past"]
