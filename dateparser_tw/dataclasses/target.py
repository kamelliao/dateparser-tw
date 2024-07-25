from typing import Optional

from arrow import Arrow
from pydantic import BaseModel, ConfigDict, Field
from typing_extensions import TypedDict


class DeltaType(TypedDict):
    year: int
    month: int
    day: int
    hour: int
    minute: int
    second: int


class Target(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    text: str = Field(frozen=True)
    basetime: Arrow = Field(default_factory=Arrow.now)
    is_timedelta: bool = False
    timedelta: Optional[DeltaType] = None
