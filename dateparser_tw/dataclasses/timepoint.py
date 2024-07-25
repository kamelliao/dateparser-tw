from enum import Enum
from typing import Optional

from arrow import Arrow
from pydantic import BaseModel


class Granularity(str, Enum):
    Year = "year"
    YearMonth = "year_month"
    DateWithPeriod = "date_with_period"

    Date = "date"
    DateHour = "date_hour"
    DateTime = "datetime"


class TimePoint(BaseModel):
    year: Optional[int] = None
    month: Optional[int] = None
    day: Optional[int] = None
    period_of_day: Optional[str] = None

    hour: Optional[int] = None
    minute: Optional[int] = None
    second: Optional[int] = None

    granularity: Optional[Granularity] = None

    def __str__(self):
        if self.granularity == Granularity.Year:
            return f"{self.year}年"
        if self.granularity == Granularity.YearMonth:
            return f"{self.year}年{self.month}月"

        date_obj = self.to_arrow()

        if self.granularity == Granularity.Date:
            return date_obj.format("YYYY年MM月DD日")
        if self.granularity == Granularity.DateWithPeriod:
            return date_obj.format("YYYY年MM月DD日") + self.period_of_day
        if self.granularity == Granularity.DateHour:
            return date_obj.format("YYYY年MM月DD日HH點")
        if self.granularity == Granularity.DateTime:
            if self.second is None:
                return date_obj.format("YYYY年MM月DD日HH點mm分")
            return date_obj.format("YYYY年MM月DD日HH點mm分ss秒")

    @property
    def is_valid(self):
        for value in self.model_fields.values():
            if value is not None:
                return True
        return False

    @classmethod
    def from_arrow(cls, arrow: Arrow):
        return cls(
            year=arrow.year,
            month=arrow.month,
            day=arrow.day,
            hour=arrow.hour,
            minute=arrow.minute,
            second=arrow.second,
        )

    def to_arrow(self) -> Arrow:
        return Arrow(
            self.year,
            self.month,
            self.day,
            self.hour,
            self.minute,
            self.second,
        )


def get_granularity(tp: TimePoint) -> Granularity:
    if tp.second or tp.minute:
        return Granularity.DateTime

    if tp.hour:
        return Granularity.DateHour

    if tp.period_of_day:
        return Granularity.DateWithPeriod

    if tp.day:
        return Granularity.Date

    if tp.month:
        return Granularity.YearMonth

    if tp.year:
        return Granularity.Year

    raise ValueError("year is required")
