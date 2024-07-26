import re

import arrow
from loguru import logger

from .dataclasses import Setting, TimePoint, get_granularity


class Parser:
    def __init__(
        self, date_string: str, basetime: arrow.Arrow, settings: Setting = None
    ):
        self.date_string = date_string
        self.basetime = basetime
        self.settings = settings or {}
        self.tp = TimePoint()

        self._parse()

    @classmethod
    def parse(cls, date_string: str, basetime: arrow.Arrow, settings: Setting = None):
        obj = cls(date_string, basetime, settings)
        return obj.tp

    def _parse(self):
        self.norm_absolute_date()
        self.norm_absolute_time()
        self.norm_hour_notation()
        self.norm_relative_expression()
        self.norm_prep_related()

        self.fill_basetime()
        self.tp.granularity = get_granularity(self.tp)
        self.fill_empty_fields()

    def norm_absolute_date(self):
        RE_YEAR = re.compile(r"(?P<year>\d{4})年")
        RE_MONTH = re.compile(r"(?P<month>10|11|12|[1-9])月")
        RE_DAY = re.compile(r"(?P<day>[0-3][0-9]|[1-9])[日號]")

        if match := RE_YEAR.search(self.date_string):
            self.tp.year = int(match.group("year"))
            logger.debug(f"Matched: (year, {self.tp.year})")
        if match := RE_MONTH.search(self.date_string):
            self.tp.month = int(match.group("month"))
            logger.debug(f"Matched: (month, {self.tp.month})")
        if match := RE_DAY.search(self.date_string):
            self.tp.day = int(match.group("day"))
            logger.debug(f"Matched: (day, {self.tp.day})")

    def norm_absolute_time(self):
        hour_pattern = r"(?P<hour>[0-2]?[0-9])[點時](?P<hour_half>半)?"
        minute_pattern = r"(?P<minute>[0-5]?[0-9])[分鐘](?P<minute_half>半)?"
        second_pattern = r"(?P<second>[0-5]?[0-9])[秒]?"

        RE_ABSOLUTE_TIME = re.compile(
            rf"{hour_pattern}(?:{minute_pattern}(?:{second_pattern})?)?"
        )
        match = RE_ABSOLUTE_TIME.search(self.date_string)

        if not match:
            return

        if match.group("hour"):
            self.tp.hour = int(match.group("hour"))
            if match.group("hour_half"):
                self.tp.minute = 30

        if match.group("minute"):
            self.tp.minute = int(match.group("minute"))
            if match.group("minute_half"):
                self.tp.second = 30

        if match.group("second"):
            self.tp.second = int(match.group("second"))

    def norm_hour_notation(self):
        """Must be called after norm_absolute_time."""
        RE_AM = re.compile(
            r"(凌晨|清晨|早上|早晨|早間|晨間|今早|上午|白天|am|AM|a\.m\.|a\.m|A\.M\.|A\.M)"
        )
        RE_PM = re.compile(
            r"(下午|中午|午後|晚上|夜間|夜裡|夜間|今晚|pm|PM|p\.m\.|p\.m|P\.M\.|P\.M)"
        )

        if match := RE_AM.search(self.date_string):
            self.tp.period_of_day = match.group()
            if self.tp.hour and 12 <= self.tp.hour <= 23:
                self.tp.hour -= 12
        elif match := RE_PM.search(self.date_string):
            self.tp.period_of_day = match.group()
            if self.tp.hour and 0 <= self.tp.hour <= 11:
                self.tp.hour += 12

    def norm_relative_expression(self):
        SHIFTS = {
            "前": -2,
            "去": -1,
            "昨": -1,
            "今": 0,
            "本": 0,
            "明": 1,
            "次": 1,
            "隔": 1,
            "後": 2,
        }

        # whether to modify the year/month/day
        curr = self.basetime
        mod_flags = {
            "year": False,
            "month": False,
            "day": False,
        }

        # year
        RE_YEAR_RELATIVE = re.compile(r"(大*前|[去今本明隔次]|大*後)年")
        match = RE_YEAR_RELATIVE.search(self.date_string)
        if match is not None:
            mod_flags["year"] = True

            extra_shift = match.group(1).count("大")
            if SHIFTS[match.group(1)] < 0:
                curr = curr.shift(years=SHIFTS[match.group(1)] - extra_shift)
            else:
                curr = curr.shift(years=SHIFTS[match.group(1)] + extra_shift)

        # month
        RE_MONTH_RELATIVE = re.compile(r"(上+個|下+個|這個|本)月")
        match = RE_MONTH_RELATIVE.search(self.date_string)
        if match is not None:
            mod_flags["month"] = True

            if "上" in match.group(1):
                curr = curr.shift(months=-match.group(1).count("上"))
            elif "下" in match.group(1):
                curr = curr.shift(months=match.group(1).count("下"))
            else:
                curr = curr.shift(months=0)

        # day
        RE_DAY_RELATIVE = re.compile(r"(大*前|[昨今本明隔次]|大*後)[天日]")
        match = RE_DAY_RELATIVE.search(self.date_string)
        if match is not None:
            mod_flags["day"] = True

            extra_shift = match.group(1).count("大")
            if SHIFTS[match.group(1)] < 0:
                curr = curr.shift(days=SHIFTS[match.group(1)] - extra_shift)
            else:
                curr = curr.shift(days=SHIFTS[match.group(1)] + extra_shift)

        # week
        RE_WEEK_RELATIVE = re.compile(
            r"(上+個?|下+個?|這個?|本)?(?:周|週|星期|禮拜)([1-7]?)"
        )
        match = RE_WEEK_RELATIVE.search(self.date_string)
        if match is not None:
            mod_flags["day"] = True

            # set week
            if "上" in match.group(1):
                curr = curr.shift(weeks=-match.group(1).count("上"))
            elif "下" in match.group(1):
                curr = curr.shift(weeks=match.group(1).count("下"))
            else:
                curr = curr.shift(weeks=0)

            # set day (eg. `這週3`)
            if match.group(2):
                offset = (int(match.group(2)) - 1) - curr.weekday()
                curr = curr.shift(days=offset)

            # when demonstrative pronouns like `上個` are not used, eg., `周5`
            # in this case, should consider whether user prefer future time
            if not match.group(1):
                curr = self.preferFutureWeek(int(match.group(2)), curr)

        if any(mod_flags.values()):
            self.tp.year = int(curr.year)
        if mod_flags["month"] or mod_flags["day"]:
            self.tp.month = int(curr.month)
        if mod_flags["day"]:
            self.tp.day = int(curr.day)

    def norm_prep_related(self):
        """設定以上文時間為基準的時間偏移計算"""
        PREPOSITIONS = {
            "前": -1,
            "後": 1,
        }

        HALF_NUMBERS = {
            "year": {"value": 6, "unit": "個月"},  # 6 months
            "month": {"value": 15, "unit": "天"},  # 15 days
            "day": {"value": 12, "unit": "小時"},  # 12 hours
            "hour": {"value": 30, "unit": "分鐘"},  # 30 minutes
            "minute": {"value": 30, "unit": "秒"},  # 30 seconds
        }

        # `2個月前`, `2個半月前`, `半個月前`, `半月前`, TODO: `2月前` is `before February` or `2 months ago`?
        rule_base = r"(?P<value>(?P<int_part>\d+)?(?P<half_exp>個?半)?)(?P<unit>{})(?P<half_exp_after>半)?(?:[以之]?(?P<prep>[前後]))"

        rules = {
            "year": rule_base.format("年"),
            "month": rule_base.format("個?月"),
            "day": rule_base.format("天"),
            "week": rule_base.format("個?(?:周|週|星期|禮拜)"),
            "hour": rule_base.format("個?(?:小時|鐘頭)"),
            "minute": rule_base.format("(?:分|分鐘)"),
            "second": rule_base.format("(?:分|秒鐘)"),
        }

        rules = {key: re.compile(value) for key, value in rules.items()}

        # normalize `半` expression. eg. `半年前` -> `6個月前`
        # this is because `arrow` does not support 0.5 as a time unit
        for key, pattern in rules.items():
            match = pattern.search(self.date_string)
            if match is None:
                continue
            # note: `half_exp_after` is for years, eg. `3年半前`
            if not match.group("half_exp") and not match.group("half_exp_after"):
                continue

            match_dict = match.groupdict()
            match_dict.update(HALF_NUMBERS.get(key))

            # eg. `3個半月前` -> `105天前` (15 + 3*30)
            if match_dict["int_part"]:
                match_dict["value"] += int(match_dict["int_part"]) * (
                    HALF_NUMBERS.get(key)["value"] * 2
                )

            # reconstruct the date_string
            self.date_string = (
                f"{match_dict['value']}{match_dict['unit']}{match_dict['prep']}"
            )
            logger.debug(f"Normalized `半` expression: {self.date_string}")

        # parse timepoint
        curr = self.basetime
        mod_flags = {key: False for key in rules.keys() if key != "week"}

        for key, pattern in rules.items():
            match = pattern.search(self.date_string)
            if match is None:
                continue

            direction = PREPOSITIONS.get(match.group("prep"))
            value = direction * int(match.group("value"))
            curr = curr.shift(**{key + "s": value})

            if key == "week":
                mod_flags["day"] = True
            else:
                mod_flags[key] = True

            logger.debug(f"Matched: ({key}, {value})")

        # update flags: if a unit is mentioned, all units above it should be updated
        running_flag = False
        for unit in reversed(mod_flags.keys()):
            if mod_flags[unit]:
                running_flag = True
            mod_flags[unit] = running_flag

        # update the timepoint, granularity to only that mentioned in the date_string
        for key, value in mod_flags.items():
            if value:
                setattr(self.tp, key, getattr(curr, key))

    def fill_basetime(self):
        if self.tp.second and not self.tp.minute:
            self.tp.minute = self.basetime.minute

        if self.tp.minute and not self.tp.hour:
            self.tp.hour = self.basetime.hour

        if self.tp.hour and not self.tp.day:
            self.tp.day = self.basetime.day

        if self.tp.day and not self.tp.month:
            self.tp.month = self.basetime.month

        if self.tp.month and not self.tp.year:
            self.tp.year = self.basetime.year

    def fill_empty_fields(self):
        for field in ["month", "day"]:
            if getattr(self.tp, field) is None:
                setattr(self.tp, field, 1)

        for field in ["hour", "minute", "second"]:
            if getattr(self.tp, field) is None:
                setattr(self.tp, field, 0)
