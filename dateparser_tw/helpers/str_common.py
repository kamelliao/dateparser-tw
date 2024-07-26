import re
from loguru import logger

from .utils import replace_spans

DIGIT_MAP = {
    "零": 0,
    "一": 1,
    "二": 2,
    "兩": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
}

PLACE_MAP = {"十": 10, "百": 100, "千": 1000, "萬": 10000, "億": 100000000}

RE_NUMERAL = re.compile(r"([零一二兩三四五六七八九十百千萬億]+)")


def cn2an(target: str) -> int:
    """Convert Chinese numerals to Arabic numerals."""
    # Initialize result and variables for processing
    result = 0
    temp_value = 0

    # Process each character in the Chinese numeral string
    for char in target:
        if char in DIGIT_MAP:
            temp_value = DIGIT_MAP[char]
        elif char in PLACE_MAP:
            if temp_value == 0:
                temp_value = 1
            result += temp_value * PLACE_MAP[char]
            temp_value = 0
        else:
            raise ValueError(f"Invalid character found: {char}")

    # Add the last processed value
    result += temp_value

    return result


def convert_chinese_numeral(target: str):
    spans = {
        match.span(): str(cn2an(match.group())) for match in RE_NUMERAL.finditer(target)
    }

    target = replace_spans(target, spans)

    # `星期天` -> `星期7`
    pattern = re.compile(r"(周|週|星期|禮拜)([天日])")
    if pattern.search(target):
        target = target.replace("天", "7").replace("日", "7")

    return target


def word2number(s: str):
    if s.isdigit():
        return int(s)
    return DIGIT_MAP.get(s, -1)
