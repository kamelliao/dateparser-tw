from typing import List, Optional, Union

import arrow
from arrow.arrow import Arrow
from loguru import logger

from .helpers.str_common import (del_keyword, filter_irregular_expression,
                                 number_translator)
from .point import TimePoint
from .resource.pattern import pattern
from .result import DeltaType, Result
from .unit import TimeUnit


def sanitize_date(date_string: str) -> str:
    date_string = filter_irregular_expression(date_string)
    date_string = del_keyword(date_string, r"\s+")  # clear spaces
    date_string = del_keyword(date_string, "[的]+")  # clear language particles
    date_string = number_translator(date_string)

    return date_string


def merge_matches(matches: List[str]) -> List[str]:
    start_position = -1
    end_position = -1
    match_index = 0
    extracted_strings = []

    logger.debug("Extracting keywords using regex:")

    for match in matches:
        logger.debug(match)
        start_position = match.start()

        if start_position == end_position:
            # If the start position is the same as the end position of the previous match, merge with the previous entry
            match_index -= 1
            extracted_strings[match_index] += match.group()
        else:
            # Otherwise, append the new match
            extracted_strings.append(match.group())

        logger.debug(f"Extracted strings: {extracted_strings}")
        end_position = match.end()
        match_index += 1

    return extracted_strings


def process_matches(self, extrated_strings: List[str]) -> List[TimeUnit]:
    res = []
    context_tp = TimePoint()

    logger.debug(f"基础时间： {self.basetime}")
    logger.debug(f"待处理的字段: {extrated_strings}")
    logger.debug(f"待处理字段长度: {len(extrated_strings)}")

    for item in extrated_strings:
        time_unit = TimeUnit(item, self, context_tp)
        res.append(time_unit)
        context_tp = time_unit.tp

    logger.debug(f"全部字段处理后的结果： {res}")
    return self.filter(res)


class DateParser:
    def __init__(self, isPreferFuture=True, tz="Asia/Taipei"):
        self.isPreferFuture = isPreferFuture

        self.tz = tz
        self.pattern = pattern

    def parse(self, text: str, basetime: Union[arrow.Arrow, str] = None) -> dict:
        if basetime is None:
            basetime = arrow.now(self.tz)

        self.isTimeDelta = False
        self.timeDelta = None  # type: Optional[DeltaType]
        self.target = text
        self.basetime: Arrow = arrow.get(basetime)
        self._basetime = self.basetime

        parsed_date = self.extract(text)

        return parsed_date

    def extract(self, date_string: str) -> dict:
        date_string = sanitize_date(date_string)

        matches = list(self.pattern.finditer(date_string))
        extracted_strings = merge_matches(matches)

        try:
            res: List[TimeUnit] = []
            # 时间上下文： 前一个识别出来的时间会是下一个时间的上下文，用于处理：周六3点到5点这样的多个时间的识别，第二个5点应识别到是周六的。
            contextTp = TimePoint()

            logger.debug(f"基础时间： {self.basetime}")
            logger.debug(f"待处理的字段: {extracted_strings}")
            logger.debug(f"待处理字段长度: {len(extracted_strings)}")
            for i in range(0, len(extracted_strings)):
                res.append(TimeUnit(extracted_strings[i], self, contextTp))
                contextTp = res[i].tp

            logger.debug(f"全部字段处理后的结果： {res}")
            res = self.filter(res)

            if self.isTimeDelta and self.timeDelta:
                return Result.from_timedelta(self.timeDelta)
            if len(res) == 1:
                return Result.from_timestamp(res)
            if len(res) == 2:
                return Result.from_timespan(res)
            return Result.from_invalid()
        except Exception as e:
            logger.opt(exception=e).debug("解析时发生错误")
            return Result.from_exception(e)

    def filter(self, tu_arr: List[TimeUnit]):
        """
        过滤掉无效识别。
        """
        res = []
        for tu in tu_arr:
            if not tu:
                continue

            if tu.time.int_timestamp != 0:
                res.append(tu)
        logger.debug(f"过滤无效识别后： {res}")
        return res
