from typing import Optional

from arrow import Arrow
from pydantic import BaseModel


class TimePoint(BaseModel):
    year: Optional[int] = None
    month: Optional[int] = None
    day: Optional[int] = None
    hour: Optional[int] = None
    minute: Optional[int] = None
    second: Optional[int] = None

    @property
    def is_valid(self):
        for value in self.model_fields.values():
            if value is not None:
                return True
        return False

    @property
    def is_span(self):
        for value in self.model_fields.values():
            # TODO:
            if value != -1:
                return False
        return True

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
        year = max(self.year, 1)
        month = max(self.month, 1)
        day = max(self.day, 1)
        hour = max(self.hour, 0)
        minute = max(self.minute, 0)
        second = max(self.second, 0)
        return Arrow(year, month, day, hour, minute, second)

    def gen_delta(self):
        return {
            "year": max(self.year, 0),
            "month": max(self.month, 0),
            "day": max(self.day, 0),
            "hour": max(self.hour, 0),
            "minute": max(self.minute, 0),
            "second": max(self.second, 0),
        }
