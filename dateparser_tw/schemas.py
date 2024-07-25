from dataclasses import dataclass
from typing import Optional, Union

import arrow

from .result import DeltaType


@dataclass
class Target:
    text: str
    basetime: Union[arrow.Arrow]
    is_timedelta: bool = False
    timedelta: Optional[DeltaType] = None
