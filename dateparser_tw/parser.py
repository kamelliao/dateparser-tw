from typing import Pattern

import arrow
import regex as re

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
        year_pattern = r"(?P<year>\d{4})年"
        month_pattern = r"(?P<month>10|11|12|[1-9])月"
        day_pattern = r"(?P<day>[0-3][0-9]|[1-9])[日號]?"

        RE_ABSOLUTE_DATE = re.compile(
            rf"({year_pattern})?({month_pattern}({day_pattern})?)?"
        )
        match = RE_ABSOLUTE_DATE.search(self.date_string)

        if match.group("year"):
            self.tp.year = int(match.group("year"))
        if match.group("month"):
            self.tp.month = int(match.group("month"))
        if match.group("day"):
            self.tp.day = int(match.group("day"))

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
            r"凌晨|清晨|早上|早晨|早間|晨間|今早|上午|白天|(?i)\b(?:a\.?m\.?|am)"
        )
        RE_PM = re.compile(
            r"下午|中午|午後|晚上|夜間|夜裡|夜間|今晚|(?i)\b(?:p\.?m\.?|pm)"
        )

        if match := RE_AM.search(self.date_string):
            self.tp.period_of_day = match.group()
            if self.tp.hour and 12 <= self.tp.hour <= 23:
                self.tp.hour -= 12
        elif match := RE_PM.search(self.date_string):
            self.tp.period_of_day = match.group()
            if self.tp.hour and 0 <= self.tp.hour <= 11:
                self.tp.hour += 12

    def norm_prep_related(self):
        """設定以上文時間為基準的時間偏移計算
        TODO: `半`小時、`上上上...`、`這個`、`本`
        """
        rule_base = r"(\d+){}(?:[以之]?([前後]))"

        rules = {
            "year": rule_base.format("年"),
            "month": rule_base.format("個月"),
            "day": rule_base.format("天"),
            "hour": rule_base.format("個?(?:小時|鐘頭)"),
            "minute": rule_base.format("(?:分|分鐘)"),
            "second": rule_base.format("(?:分|秒鐘)"),
            "week": rule_base.format("個?(?:周|週|星期|禮拜)"),
        }

        for key, rule in rules.items():
            pattern: Pattern = re.compile(rule)
            match = pattern.search(self.date_string)
            if match is None:
                continue

            # `前`: -1, `後`: 1
            direction = 1 if match.group(2) == "後" else -1
            value = direction * int(match.group(1))

            self.is_timedelta = True
            if key == "week":
                if self.tp.day == -1:
                    self.tp.day = 0
                self.tp.day += int(value * 7)
            else:
                # TODO: basetime + value
                setattr(self.tp, key, value)

    def norm_relative_expression(self):
        curr = self.basetime

        # whether to modify the year/month/day
        mod_flags = {
            "year": False,
            "month": False,
            "day": False,
        }

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
