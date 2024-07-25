from typing import List, Union

import arrow
from arrow.arrow import Arrow
from loguru import logger

from .helpers.str_common import (del_keyword, filter_irregular_expression,
                                 number_translator)
from .resource.pattern import pattern
from .parser import Parser


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
            # If the start position is the same as the end position of the
            # previous match, merge with the previous entry
            match_index -= 1
            extracted_strings[match_index] += match.group()
        else:
            # Otherwise, append the new match
            extracted_strings.append(match.group())

        logger.debug(f"Extracted strings: {extracted_strings}")
        end_position = match.end()
        match_index += 1

    return extracted_strings


def sanitize_date(date_string: str) -> str:
    date_string = filter_irregular_expression(date_string)
    date_string = del_keyword(date_string, r"\s+")  # clear spaces
    date_string = del_keyword(date_string, "[的]+")  # clear language particles
    date_string = number_translator(date_string)

    return date_string


class DateParser:
    def __init__(self, tz="Asia/Taipei"):
        self.tz = tz
        self.pattern = pattern

    def parse(self, text: str, basetime: Union[arrow.Arrow, str] = None) -> dict:
        self.target = text
        self.basetime: Arrow = (
            arrow.now(self.tz)
            if basetime is None
            else arrow.get(basetime, tzinfo=self.tz)
        )

        parsed_date = self.extract(text)

        return parsed_date

    def extract(self, date_string: str) -> dict:
        date_string = sanitize_date(date_string)

        matches = list(self.pattern.finditer(date_string))
        extrated_spans = merge_matches(matches)

        spans = []
        # TODO: 时间上下文： 前一个识别出来的时间会是下一个时间的上下文，用于处理：周六3点到5点这样的多个时间的识别，第二个5点应识别到是周六的。
        # contextTp = TimePoint()

        for span in extrated_spans:
            spans.append(Parser.parse(span, self.basetime))

        return spans[0]
