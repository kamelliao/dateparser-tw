import re
from typing import List, Pattern, Union

import arrow
from arrow.arrow import Arrow
from loguru import logger

from .dataclasses import TimePoint
from .helpers.str_common import convert_chinese_numeral
from .parser import Parser
from .resource.pattern import PATTERN

RE_SPACES = re.compile(r"\s+")
RE_LANGUAGE_PARTICLES = re.compile(r"[的]+")


def extract_spans(date_string: str, pattern: Pattern) -> List[str]:
    matches = pattern.finditer(date_string)

    start_position = -1
    end_position = -1
    match_index = 0
    extracted_strings = []

    for match in matches:
        start_position = match.start()

        if start_position == end_position:
            # If the start position is the same as the end position of the
            # previous match, merge with the previous entry
            match_index -= 1
            extracted_strings[match_index] += match.group()
        else:
            # Otherwise, append the new match
            extracted_strings.append(match.group())

        end_position = match.end()
        match_index += 1

    return extracted_strings


def sanitize_date(date_string: str) -> str:
    date_string = RE_SPACES.sub("", date_string)  # clear spaces
    date_string = RE_LANGUAGE_PARTICLES.sub("", date_string)  # clear language particles
    date_string = convert_chinese_numeral(date_string)

    return date_string


class DateParser:
    def __init__(self, tz="Asia/Taipei"):
        self.tz = tz
        self.pattern = PATTERN

    def parse(self, text: str, basetime: Union[arrow.Arrow, str] = None):
        self.target = text
        self.basetime: Arrow = (
            arrow.now(self.tz)
            if basetime is None
            else arrow.get(basetime, tzinfo=self.tz)
        )

        parsed_date = self.extract(text)

        return parsed_date

    def extract(self, date_string: str) -> TimePoint:
        logger.debug(f"Original date string: {date_string}")
        date_string = sanitize_date(date_string)
        extracted_spans = extract_spans(date_string, self.pattern)

        logger.debug(f"Santized date string: {date_string}")
        logger.debug(f"Extracted spans: {extracted_spans}")

        # TODO: 时间上下文： 前一个识别出来的时间会是下一个时间的上下文，用于处理：周六3点到5点这样的多个时间的识别，第二个5点应识别到是周六的。
        # contextTp = TimePoint()

        spans = []
        for span in extracted_spans:
            spans.append(Parser.parse(span, self.basetime))

        return spans[0]
