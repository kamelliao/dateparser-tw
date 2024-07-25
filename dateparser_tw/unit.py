import copy
from typing import TYPE_CHECKING, Pattern

import arrow
import regex as re
from loguru import logger

from .enums import RangeTimeEnum
from .helpers.arrow_helper import arrow2tp, tp2arrow
from .helpers.LunarSolarConverter import Lunar, LunarSolarConverter
from .point import TimePoint
from .resource import holiday

if TYPE_CHECKING:
    from .normalizer import TimeNormalizer


class TimeUnit:
    def __init__(
        self, date_string: str, normalizer: "TimeNormalizer", contextTp: TimePoint
    ):
        """时间语句分析 \n
        date_string: 时间表达式 \n
        normalizer: TimeNormalizer 类
        """
        logger.debug("TimeUnit 初始化:")
        logger.debug(f"          字段: {date_string}")
        logger.debug(f"         上下文: {contextTp}")

        self._noyear = False
        self.date_string = date_string
        self.normalizer = normalizer
        self.tp = TimePoint()
        self.tp_origin = contextTp
        self.isFirstTimeSolveContext = True
        self.isMorning = False
        self.isAllDayTime = True
        self.time = normalizer.basetime
        self._basetime = normalizer._basetime
        self.time_normalization()

    def __repr__(self):
        if self.normalizer.isTimeDelta:
            return f"<TimeUnit(Delta) {self.normalizer.timeDelta})"
        else:
            return f"<TimeUnit {self.time}"

    def time_normalization(self):
        self.norm_setyear()
        self.norm_setmonth()
        self.norm_setday()
        self.norm_setmonth_fuzzyday()
        # self.norm_setBaseRelated()
        self.norm_relative_expression()
        # self.norm_sethour()
        # self.norm_setminute()
        # self.norm_setsecond()
        # self.norm_setSpecial()
        # self.norm_setSpanRelated()  # ok
        # self.norm_setHoliday()
        # self.modifyTimeBase()

        self.tp_origin.tunit = copy.deepcopy(self.tp.tunit)
        logger.debug(f"self.tp: {self.tp}")

        # 判断是时间点还是时间区间
        spanFlag = True
        for i in range(0, 4):
            if self.tp.tunit[i] != -1:
                spanFlag = False

        if spanFlag:
            self.normalizer.isTimeDelta = True

        if self.normalizer.isTimeDelta:
            logger.debug("isTimeDelta")
        else:
            logger.debug("判断是时间点")

        if self.normalizer.isTimeDelta:
            if not self.tp.is_valid():
                logger.debug("self.tp is invalid.")
                return
            self.normalizer.timeDelta = self.tp.gen_delta()
            logger.debug(f"时间间隔: {self.normalizer.timeDelta}")
            return

        time_grid = arrow2tp(self.normalizer.basetime)
        tunitpointer = 5
        while tunitpointer >= 0 and self.tp.tunit[tunitpointer] < 0:
            tunitpointer -= 1
        for i in range(0, tunitpointer):
            if self.tp.tunit[i] < 0:
                self.tp.tunit[i] = time_grid[i]

        self.time = self.tp.get_arrow()
        logger.debug(f"时间点: {self.time}")

    def norm_setyear(self):
        """
        年-规范化方法--该方法识别时间表达式单元的年字段
        """
        # xx年後
        rule = r"([0-9]{1,})(?=年後)"
        pattern: Pattern = re.compile(rule)
        match = pattern.search(self.date_string)
        if match is not None:
            self.tp.set_unit(self.normalizer.basetime.shift(years=int(match.group())))
            return

        # 一位数表示的年份
        rule = r"(?<![0-9])[0-9]{1}(?=年)"
        pattern: Pattern = re.compile(rule)
        match = pattern.search(self.date_string)
        if match is not None:
            self.normalizer.isTimeDelta = True
            year = int(match.group())
            self.tp.year = year

        # 两位数表示的年份
        rule = r"[0-9]{2}(?=年)"
        pattern: Pattern = re.compile(rule)
        match = pattern.search(self.date_string)
        if match is not None:
            year = int(match.group())
            self.tp.year = year

        # 三位数表示的年份
        rule = r"(?<![0-9])[0-9]{3}(?=年)"
        pattern: Pattern = re.compile(rule)
        match = pattern.search(self.date_string)
        if match is not None:
            self.normalizer.isTimeDelta = True
            year = int(match.group())
            self.tp.year = year

        # 四位数表示的年份
        rule = r"[0-9]{4}(?=年)"
        pattern: Pattern = re.compile(rule)
        match = pattern.search(self.date_string)
        if match is not None:
            year = int(match.group())
            self.tp.year = year

    def norm_setmonth(self):
        """
        月-规范化方法--该方法识别时间表达式单元的月字段
        """
        rule = r"((10)|(11)|(12)|([1-9]))(?=月)"
        pattern: Pattern = re.compile(rule)
        match = pattern.search(self.date_string)
        if match is not None:
            self.tp.month = int(match.group())
            # 处理倾向于未来时间的情况
            self.preferFuture(1)

    def norm_setmonth_fuzzyday(self):
        """
        月-日 兼容模糊写法：该方法识别时间表达式单元的月、日字段
        """
        rule = r"((10)|(11)|(12)|([1-9]))(月|\.|\-)([0-3][0-9]|[1-9])"
        pattern: Pattern = re.compile(rule)
        match = pattern.search(self.date_string)
        if match is not None:
            matchStr = match.group()
            p = re.compile(r"(月|\.|\-)")
            m = p.search(matchStr)
            if m is not None:
                splitIndex = m.start()
                month = matchStr[0:splitIndex]
                day = matchStr[splitIndex + 1 :]
                self.tp.month = int(month)
                self.tp.day = int(day)
                # 处理倾向于未来时间的情况
                self.preferFuture(1)
            self._check_time(self.tp.tunit)

    def norm_setday(self):
        """
        日-规范化方法：该方法识别时间表达式单元的日字段
        """
        rule = r"((?<!\d))([0-3][0-9]|[1-9])(?=(日|號))"
        pattern: Pattern = re.compile(rule)
        match = pattern.search(self.date_string)
        if match is not None:
            self.tp.day = int(match.group())
            # 处理倾向于未来时间的情况
            self.preferFuture(2)
            self._check_time(self.tp.tunit)

        rule = r"((?<!\d))([0-3][0-9]|[1-9])(?=(日|天)後)"
        pattern: Pattern = re.compile(rule)
        match = pattern.search(self.date_string)
        if match is not None:
            self.normalizer.isTimeDelta = True
            self.tp.day = int(match.group())
            self._check_time(self.tp.tunit)

    def norm_checkKeyword(self):
        # * 对关键字：早（包含早上/早晨/早间），上午，中午,午间,下午,午後,晚上,傍晚,晚间,晚,pm,PM的正确时间计算
        # * 规约：
        # * 1.中午/午间0-10点视为12-22点
        # * 2.下午/午後0-11点视为12-23点
        # * 3.晚上/傍晚/晚间/晚1-11点视为13-23点，12点视为0点
        # * 4.0-11点pm/PM视为12-23点
        rule = r"凌晨"
        pattern: Pattern = re.compile(rule)
        match = pattern.search(self.date_string)
        if match is not None:
            if self.tp.hour == -1:  # 增加对没有明确时间点，只写了"凌晨"這种情况的处理
                self.tp.hour = RangeTimeEnum.day_break
            elif 12 <= self.tp.hour <= 23:
                self.tp.hour -= 12
            elif self.tp.hour == 0:
                self.tp.hour = 12
            # 处理倾向于未来时间的情况
            self.preferFuture(3)
            self.isAllDayTime = False

        rule = r"早上|早晨|早間|晨間|今早|明早|早|清晨"
        pattern: Pattern = re.compile(rule)
        match = pattern.search(self.date_string)
        if match is not None:
            if (
                self.tp.hour == -1
            ):  # 增加对没有明确时间点，只写了"早上/早晨/早间"這种情况的处理
                self.tp.hour = RangeTimeEnum.early_morning
                # 处理倾向于未来时间的情况
            elif 12 <= self.tp.hour <= 23:
                self.tp.hour -= 12
            elif self.tp.hour == 0:
                self.tp.hour = 12
            self.preferFuture(3)
            self.isAllDayTime = False

        rule = r"上午"
        pattern: Pattern = re.compile(rule)
        match = pattern.search(self.date_string)
        if match is not None:
            if self.tp.hour == -1:  # 增加对没有明确时间点，只写了"上午"這种情况的处理
                self.tp.hour = RangeTimeEnum.morning
            elif 12 <= self.tp.hour <= 23:
                self.tp.hour -= 12
            elif self.tp.hour == 0:
                self.tp.hour = 12
            # 处理倾向于未来时间的情况
            self.preferFuture(3)
            self.isAllDayTime = False

        rule = r"(中午)|(午間)|(白天)"
        pattern: Pattern = re.compile(rule)
        match = pattern.search(self.date_string)
        if match is not None:
            if 0 <= self.tp.hour <= 10:
                self.tp.hour += 12
            if (
                self.tp.hour == -1
            ):  # 增加对没有明确时间点，只写了"中午/午间"這种情况的处理
                self.tp.hour = RangeTimeEnum.noon
            # 处理倾向于未来时间的情况
            self.preferFuture(3)
            self.isAllDayTime = False

        rule = r"(下午)|(午後)|(pm)|(PM)"
        pattern: Pattern = re.compile(rule)
        match = pattern.search(self.date_string)
        if match is not None:
            if 0 <= self.tp.hour <= 11:
                self.tp.hour += 12
            if (
                self.tp.hour == -1
            ):  # 增加对没有明确时间点，只写了"下午|午後"這种情况的处理
                self.tp.hour = RangeTimeEnum.afternoon
            # 处理倾向于未来时间的情况
            self.preferFuture(3)
            self.isAllDayTime = False

        rule = r"晚上|夜間|夜裡|今晚|明晚|晚|夜裡"
        pattern: Pattern = re.compile(rule)
        match = pattern.search(self.date_string)
        if match is not None:
            if 0 <= self.tp.hour <= 11:
                self.tp.hour += 12
            elif self.tp.hour == 12:
                self.tp.hour = 0
            elif (
                self.tp.hour == -1
            ):  # 增加对没有明确时间点，只写了"下午|午後"這种情况的处理
                self.tp.hour = RangeTimeEnum.lateNight
            # 处理倾向于未来时间的情况
            self.preferFuture(3)
            self.isAllDayTime = False

    def norm_sethour(self):
        """
        时-规范化方法：该方法识别时间表达式单元的时字段
        """
        rule = r"(?<!(周|星期))([0-2]?[0-9])(?=(點|時))"
        pattern: Pattern = re.compile(rule)
        match = pattern.search(self.date_string)
        if match is not None:
            self.tp.hour = int(match.group())
            self.norm_checkKeyword()
            # 处理倾向于未来时间的情况
            self.preferFuture(3)
            self.isAllDayTime = False
        else:
            self.norm_checkKeyword()

    def norm_setminute(self):
        """
        分-规范化方法：该方法识别时间表达式单元的分字段
        """
        rule = r"([0-9]+(?=分(?!鐘)))|((?<=((?<!小)[点时]))[0-5]?[0-9](?!刻))"
        pattern: Pattern = re.compile(rule)
        match = pattern.search(self.date_string)
        if match is not None:
            if match.group() != "":
                self.tp.minute = int(match.group())
                # 处理倾向于未来时间的情况
                # self.preferFuture(4)
                self.isAllDayTime = False
        # 加对一刻，半，3刻的正确识别（1刻为15分，半为30分，3刻为45分）
        rule = r"(?<=[点时])[1一]刻(?!鐘)"
        pattern: Pattern = re.compile(rule)
        match = pattern.search(self.date_string)
        if match is not None:
            self.tp.minute = 15
            # 处理倾向于未来时间的情况
            # self.preferFuture(4)
            self.isAllDayTime = False

        rule = r"(?<=[点时])半"
        pattern: Pattern = re.compile(rule)
        match = pattern.search(self.date_string)
        if match is not None:
            self.tp.minute = 30
            # 处理倾向于未来时间的情况
            self.preferFuture(4)
            self.isAllDayTime = False

        rule = r"(?<=[点时])[3三]刻(?!鐘)"
        pattern: Pattern = re.compile(rule)
        match = pattern.search(self.date_string)
        if match is not None:
            self.tp.minute = 45
            # 处理倾向于未来时间的情况
            # self.preferFuture(4)
            self.isAllDayTime = False

    def norm_setsecond(self):
        """
        添加了省略"秒"说法的时间：如17点15分32
        """
        rule = r"([0-9]+(?=秒))|((?<=分)[0-5]?[0-9])"
        pattern: Pattern = re.compile(rule)
        match = pattern.search(self.date_string)
        if match is not None:
            self.tp.second = int(match.group())
            self.isAllDayTime = False

    def norm_setSpecial(self):
        """
        特殊形式的规范化方法-该方法识别特殊形式的时间表达式单元的各個字段
        """
        rule = r"(晚上|夜間|夜裡|今晚|明晚|晚|夜裡|下午|午後)(?<!(周|星期))([0-2]?[0-9]):[0-5]?[0-9]:[0-5]?[0-9]"
        pattern: Pattern = re.compile(rule)
        match = pattern.search(self.date_string)
        if match is not None:
            rule = r"([0-2]?[0-9]):[0-5]?[0-9]:[0-5]?[0-9]"
            pattern: Pattern = re.compile(rule)
            match = pattern.search(self.date_string)
            if match is not None:
                tmp_target = match.group()
                tmp_parser = tmp_target.split(":")
                if 0 <= int(tmp_parser[0]) <= 11:
                    self.tp.hour = int(tmp_parser[0]) + 12
                else:
                    self.tp.hour = int(tmp_parser[0])

                self.tp.minute = int(tmp_parser[1])
                self.tp.second = int(tmp_parser[2])
                # 处理倾向于未来时间的情况
                self.preferFuture(3)
                self.isAllDayTime = False

        else:
            rule = r"(晚上|夜間|夜裡|今晚|明晚|晚|夜裡|下午|午後)(?<!(周|星期))([0-2]?[0-9]):[0-5]?[0-9]"
            pattern: Pattern = re.compile(rule)
            match = pattern.search(self.date_string)
            if match is not None:
                rule = r"([0-2]?[0-9]):[0-5]?[0-9]"
                pattern: Pattern = re.compile(rule)
                match = pattern.search(self.date_string)
                if match is not None:
                    tmp_target = match.group()
                    tmp_parser = tmp_target.split(":")
                    if 0 <= int(tmp_parser[0]) <= 11:
                        self.tp.hour = int(tmp_parser[0]) + 12
                    else:
                        self.tp.hour = int(tmp_parser[0])
                    self.tp.minute = int(tmp_parser[1])
                    # 处理倾向于未来时间的情况
                    self.preferFuture(3)
                    self.isAllDayTime = False

        if match is None:
            rule = r"(?<!(周|星期))([0-2]?[0-9]):[0-5]?[0-9]:[0-5]?[0-9](PM|pm|p\.m)"
            pattern: Pattern = re.compile(rule, re.I)
            match = pattern.search(self.date_string)
            if match is not None:
                rule = r"([0-2]?[0-9]):[0-5]?[0-9]:[0-5]?[0-9]"
                pattern: Pattern = re.compile(rule)
                match = pattern.search(self.date_string)
                if match is not None:
                    tmp_target = match.group()
                    tmp_parser = tmp_target.split(":")
                    if 0 <= int(tmp_parser[0]) <= 11:
                        self.tp.hour = int(tmp_parser[0]) + 12
                    else:
                        self.tp.hour = int(tmp_parser[0])

                    self.tp.minute = int(tmp_parser[1])
                    self.tp.second = int(tmp_parser[2])
                    # 处理倾向于未来时间的情况
                    self.preferFuture(3)
                    self.isAllDayTime = False

            else:
                rule = r"(?<!(周|星期))([0-2]?[0-9]):[0-5]?[0-9](PM|pm|p.m)"
                pattern: Pattern = re.compile(rule, re.I)
                match = pattern.search(self.date_string)
                if match is not None:
                    rule = r"([0-2]?[0-9]):[0-5]?[0-9]"
                    pattern: Pattern = re.compile(rule)
                    match = pattern.search(self.date_string)
                    if match is not None:
                        tmp_target = match.group()
                        tmp_parser = tmp_target.split(":")
                        if 0 <= int(tmp_parser[0]) <= 11:
                            self.tp.hour = int(tmp_parser[0]) + 12
                        else:
                            self.tp.hour = int(tmp_parser[0])
                        self.tp.minute = int(tmp_parser[1])
                        # 处理倾向于未来时间的情况
                        self.preferFuture(3)
                        self.isAllDayTime = False

        if match is None:
            rule = r"(?<!(周|星期|晚上|夜間|夜裡|今晚|明晚|晚|夜裡|下午|午後))([0-2]?[0-9]):[0-5]?[0-9]:[0-5]?[0-9]"
            pattern: Pattern = re.compile(rule)
            match = pattern.search(self.date_string)
            if match is not None:
                tmp_target = match.group()
                tmp_parser = tmp_target.split(":")
                self.tp.hour = int(tmp_parser[0])
                self.tp.minute = int(tmp_parser[1])
                self.tp.second = int(tmp_parser[2])
                # 处理倾向于未来时间的情况
                self.preferFuture(3)
                self.isAllDayTime = False
            else:
                rule = r"(?<!(周|星期|晚上|夜間|夜裡|今晚|明晚|晚|夜裡|下午|午後))([0-2]?[0-9]):[0-5]?[0-9]"
                pattern: Pattern = re.compile(rule)
                match = pattern.search(self.date_string)
                if match is not None:
                    tmp_target = match.group()
                    tmp_parser = tmp_target.split(":")
                    self.tp.hour = int(tmp_parser[0])
                    self.tp.minute = int(tmp_parser[1])
                    # 处理倾向于未来时间的情况
                    self.preferFuture(3)
                    self.isAllDayTime = False
        # 這里是对年份表达的极好方式
        rule = (
            r"[0-9]?[0-9]?[0-9]{2}-((10)|(11)|(12)|([1-9]))-((?<!\d))([0-3][0-9]|[1-9])"
        )
        pattern: Pattern = re.compile(rule)
        match = pattern.search(self.date_string)
        if match is not None:
            tmp_target = match.group()
            tmp_parser = tmp_target.split("-")
            self.tp.year = int(tmp_parser[0])
            self.tp.month = int(tmp_parser[1])
            self.tp.day = int(tmp_parser[2])

        rule = (
            r"[0-9]?[0-9]?[0-9]{2}/((10)|(11)|(12)|([1-9]))/((?<!\d))([0-3][0-9]|[1-9])"
        )
        pattern: Pattern = re.compile(rule)
        match = pattern.search(self.date_string)
        if match is not None:
            tmp_target = match.group()
            tmp_parser = tmp_target.split("/")
            self.tp.year = int(tmp_parser[0])
            self.tp.month = int(tmp_parser[1])
            self.tp.day = int(tmp_parser[2])

        rule = (
            r"((10)|(11)|(12)|([1-9]))/((?<!\d))([0-3][0-9]|[1-9])/[0-9]?[0-9]?[0-9]{2}"
        )
        pattern: Pattern = re.compile(rule)
        match = pattern.search(self.date_string)
        if match is not None:
            tmp_target = match.group()
            tmp_parser = tmp_target.split("/")
            self.tp.month = int(tmp_parser[0])
            self.tp.day = int(tmp_parser[1])
            self.tp.year = int(tmp_parser[2])

        rule = r"[0-9]?[0-9]?[0-9]{2}\.((10)|(11)|(12)|([1-9]))\.((?<!\d))([0-3][0-9]|[1-9])"
        pattern: Pattern = re.compile(rule)
        match = pattern.search(self.date_string)
        if match is not None:
            tmp_target = match.group()
            tmp_parser = tmp_target.split(".")
            self.tp.year = int(tmp_parser[0])
            self.tp.month = int(tmp_parser[1])
            self.tp.day = int(tmp_parser[2])

    def norm_setBaseRelated(self):
        """
        设置以上文时间为基准的时间偏移计算
        """
        logger.debug(f"设置以上文时间为基准的时间偏移计算: {self.date_string}")
        cur = self.normalizer.basetime
        flag = [False, False, False]

        rule = r"\d+(?=天[以之]?前)"
        pattern: Pattern = re.compile(rule)
        match = pattern.search(self.date_string)
        if match is not None:
            flag[2] = True
            day = int(match.group())
            cur = cur.shift(days=-day)

        rule = r"\d+(?=天[以之]?後)"
        pattern: Pattern = re.compile(rule)
        match = pattern.search(self.date_string)
        if match is not None:
            flag[2] = True
            day = int(match.group())
            cur = cur.shift(days=day)

        rule = r"\d+(?=(個)?月[以之]?前)"
        pattern: Pattern = re.compile(rule)
        match = pattern.search(self.date_string)
        if match is not None:
            flag[1] = True
            month = int(match.group())
            cur = cur.shift(months=-month)

        rule = r"\d+(?=(個)?月[以之]?後)"
        pattern: Pattern = re.compile(rule)
        match = pattern.search(self.date_string)
        if match is not None:
            flag[1] = True
            month = int(match.group())
            cur = cur.shift(months=month)

        rule = r"\d+(?=年[以之]?前)"
        pattern: Pattern = re.compile(rule)
        match = pattern.search(self.date_string)
        if match is not None:
            flag[0] = True
            year = int(match.group())
            cur = cur.shift(years=-year)

        rule = r"\d+(?=年[以之]?後)"
        pattern: Pattern = re.compile(rule)
        match = pattern.search(self.date_string)
        if match is not None:
            flag[0] = True
            year = int(match.group())
            cur = cur.shift(years=year)

        if flag[0] or flag[1] or flag[2]:
            self.tp.year = int(cur.year)
        if flag[1] or flag[2]:
            self.tp.month = int(cur.month)
        if flag[2]:
            self.tp.day = int(cur.day)

    # todo 时间长度相关
    def norm_setSpanRelated(self):
        """和時間長度相關的表達式
        # TODO: `半`小時、`上上上...`、`這個`、`本`
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
                setattr(self.tp, key, value)

    # 節假日相关
    def norm_setHoliday(self):
        rule = (
            r"(情人節)|(母親節)|(青年節)|(教師節)|(中元節)|(端午)|(勞動節)|(7夕)|(初13)|(初14)|(初15)|"
            r"(初12)|(初11)|(初9)|(初8)|(初7)|(初6)|(初5)|(初4)|(初3)|(初2)|(初1)|(中和節)|(聖誕)|(中秋)|(春節)|(元宵)|"
            r"(航海日)|(兒童節)|(國慶)|(植樹節)|(元旦)|(重陽節)|(婦女節)|(記者節)|(立春)|(雨水)|(驚蟄)| (春分)|(清明)|(穀雨)|"
            r"(立夏)|(小滿)|(芒種)|(夏至)|(小暑)|(大暑)|(立秋)|(處暑)|(白露)|(秋分)|(寒露)|(霜降)|(立冬)|(小雪)|(大雪)|"
            r"(冬至)|(小寒)|(大寒)"
        )
        pattern: Pattern = re.compile(rule)
        match = pattern.search(self.date_string)
        if match is not None:
            month = 0
            day = 0
            if self.tp.year == -1:
                year = self.normalizer.basetime.year
                self.tp.year = int(year)
            holi = match.group()
            if "節" not in holi:
                holi += "節"
            if holi in holiday.solar:
                month, day = holiday.solar[holi].split("-")
            elif holi in holiday.lunar:
                date = holiday.lunar[holi].split("-")
                lsConverter = LunarSolarConverter()
                lunar = Lunar(self.tp.year, int(date[0]), int(date[1]), False)
                solar = lsConverter.LunarToSolar(lunar)
                self.tp.year = solar.solarYear
                month = solar.solarMonth
                day = solar.solarDay
            else:
                holi = holi.strip("節")
                if holi in ["小寒", "大寒"]:
                    self.tp.year += 1
                month, day = self.china_24_st(self.tp.year, holi)
            self.tp.month = int(month)
            self.tp.day = int(day)

    def china_24_st(self, year: int, china_st: str):
        """
        二十世纪和二十一世纪，24節气计算
        :param year: 年份
        :param china_st: 節气
        :return: 節气日期（月, 日）
        """
        if (19 == year // 100) or (2000 == year):
            # 20世纪 key值
            st_key = [
                6.11,
                20.84,
                4.6295,
                19.4599,
                6.3826,
                21.4155,
                5.59,
                20.888,
                6.318,
                21.86,
                6.5,
                22.2,
                7.928,
                23.65,
                8.35,
                23.95,
                8.44,
                23.822,
                9.098,
                24.218,
                8.218,
                23.08,
                7.9,
                22.6,
            ]
        else:
            # 21世纪 key值
            st_key = [
                5.4055,
                20.12,
                3.87,
                18.73,
                5.63,
                20.646,
                4.81,
                20.1,
                5.52,
                21.04,
                5.678,
                21.37,
                7.108,
                22.83,
                7.5,
                23.13,
                7.646,
                23.042,
                8.318,
                23.438,
                7.438,
                22.36,
                7.18,
                21.94,
            ]
        # 二十四節气字典-- key值, 月份，(特殊年份，相差天数)...
        solar_terms = {
            "小寒": [st_key[0], "1", (2019, -1), (1982, 1)],
            "大寒": [st_key[1], "1", (2082, 1)],
            "立春": [st_key[2], "2", (None, 0)],
            "雨水": [st_key[3], "2", (2026, -1)],
            "惊蛰": [st_key[4], "3", (None, 0)],
            "春分": [st_key[5], "3", (2084, 1)],
            "清明": [st_key[6], "4", (None, 0)],
            "谷雨": [st_key[7], "4", (None, 0)],
            "立夏": [st_key[8], "5", (1911, 1)],
            "小满": [st_key[9], "5", (2008, 1)],
            "芒种": [st_key[10], "6", (1902, 1)],
            "夏至": [st_key[11], "6", (None, 0)],
            "小暑": [st_key[12], "7", (2016, 1), (1925, 1)],
            "大暑": [st_key[13], "7", (1922, 1)],
            "立秋": [st_key[14], "8", (2002, 1)],
            "处暑": [st_key[15], "8", (None, 0)],
            "白露": [st_key[16], "9", (1927, 1)],
            "秋分": [st_key[17], "9", (None, 0)],
            "寒露": [st_key[18], "10", (2088, 0)],
            "霜降": [st_key[19], "10", (2089, 1)],
            "立冬": [st_key[20], "11", (2089, 1)],
            "小雪": [st_key[21], "11", (1978, 0)],
            "大雪": [st_key[22], "12", (1954, 1)],
            "冬至": [st_key[23], "12", (2021, -1), (1918, -1)],
        }
        if china_st in ["小寒", "大寒", "立春", "雨水"]:
            flag_day = int((year % 100) * 0.2422 + solar_terms[china_st][0]) - int(
                (year % 100 - 1) / 4
            )
        else:
            flag_day = int((year % 100) * 0.2422 + solar_terms[china_st][0]) - int(
                (year % 100) / 4
            )
        # 特殊年份处理
        for special in solar_terms[china_st][2:]:
            if year == special[0]:
                flag_day += special[1]
                break
        return (solar_terms[china_st][1]), str(flag_day)

    def norm_relative_expression(self):
        """
        设置当前时间相关的时间表达式
        """
        curr = self.normalizer.basetime

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
        # RE_YEAR_RELATIVE = re.compile(r"([前去今本明後])年")
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

    def modifyTimeBase(self):
        """
        该方法用于更新basetime使之具有上下文关联性
        """
        if not self.normalizer.isTimeDelta:
            if 30 <= self.tp.year < 100:
                self.tp.year = 1900 + self.tp.year
            if 0 < self.tp.year < 30:
                self.tp.year = 2000 + self.tp.year
            time_grid = arrow2tp(self.normalizer.basetime)
            arr = []
            for i in range(0, 6):
                if self.tp.tunit[i] == -1:
                    arr.append(time_grid[i])
                else:
                    arr.append(self.tp.tunit[i])
            self.normalizer.basetime = tp2arrow(arr)
            logger.debug(
                f"更新basetime使之具有上下文关联性: {self.normalizer.basetime}"
            )

    def preferFutureWeek(self, weekday, cur):
        # 1. 确认用户选项
        if not self.normalizer.isPreferFuture:
            return cur
        # 2. 检查被检查的时间级别之前，是否没有更高级的已经确定的时间，如果有，则不进行处理.
        for i in range(0, 2):
            if self.tp.tunit[i] != -1:
                return cur
        # 获取当前是在周几，如果识别到的时间小于当前时间，则识别时间为下一周
        tmp = self.normalizer.basetime
        curWeekday = tmp.weekday()
        if curWeekday > weekday:
            cur = cur.shift(days=7)
        return cur

    def preferFuture(self, checkTimeIndex):
        """
        如果用户选项是倾向于未来时间，检查checkTimeIndex所指的时间是否是过去的时间，如果是的话，将大一级的时间设为当前时间的+1。
        如在晚上说"早上8点看书"，则识别为明天早上;
        12月31日说"3号买菜"，则识别为明年1月的3号。
        :param checkTimeIndex: _tp.tunit时间数组的下标
        """
        # 1. 检查被检查的时间级别之前，是否没有更高级的已经确定的时间，如果有，则不进行处理.
        for i in range(0, checkTimeIndex):
            if self.tp.tunit[i] != -1:
                return
        # 2. 根据上下文补充时间
        self.checkContextTime(checkTimeIndex)
        # 3. 根据上下文补充时间後再次检查被检查的时间级别之前，是否没有更高级的已经确定的时间，如果有，则不进行倾向处理
        # TODO 确认是否可以删除掉.
        # for i in range(0, checkTimeIndex):
        #     if self.tp.tunit[i] != -1:
        #         return

        # 4. 确认用户选项
        if not self.normalizer.isPreferFuture:
            return
        # 5. 获取当前时间，如果识别到的时间小于当前时间，则将其上的所有级别时间设置为当前时间，并且其上一级的时间步长+1
        time_arr = arrow2tp(self.normalizer.basetime)
        cur = self.normalizer.basetime
        cur_unit = time_arr[checkTimeIndex]
        logger.debug(time_arr)
        logger.debug(self.tp.tunit)
        if self.tp.year == -1:
            self._noyear = True
        else:
            self._noyear = False
        if cur_unit < self.tp.tunit[checkTimeIndex]:
            return
        # if cur_unit == self.tp.tunit[checkTimeIndex]:
        #     down_unit = int(time_arr[checkTimeIndex + 1])
        #     if down_unit
        # 准备增加的时间单位是被检查的时间的上一级，将上一级时间+1
        cur = self.addTime(cur, checkTimeIndex - 1)
        time_arr = arrow2tp(cur)
        for i in range(0, checkTimeIndex):
            self.tp.tunit[i] = time_arr[i]
            # if i == 1:
            #     self.tp.tunit[i] += 1

    def _check_time(self, parse):
        """
        检查未来时间点
        :param parse: 解析出来的list
        """
        time_arr = arrow2tp(self.normalizer.basetime)
        if self._noyear:
            # check the month
            logger.debug(parse)
            logger.debug(time_arr)
            if parse[1] == int(time_arr[1]):
                if parse[2] > int(time_arr[2]):
                    parse[0] = parse[0] - 1
            self._noyear = False

    def checkContextTime(self, checkTimeIndex: int):
        """
        根据上下文时间补充时间信息
        :param checkTimeIndex:
        """
        if not self.isFirstTimeSolveContext:
            return
        for i in range(0, checkTimeIndex):
            if self.tp.tunit[i] == -1 and self.tp_origin.tunit[i] != -1:
                self.tp.tunit[i] = self.tp_origin.tunit[i]
        # 在处理小时這個级别时，如果上文时间是下午的且下文没有主动声明小时级别以上的时间，则也把下文时间设为下午
        if (
            self.isFirstTimeSolveContext is True
            and checkTimeIndex == 3
            and self.tp_origin.tunit[checkTimeIndex] >= 12
            and self.tp.tunit[checkTimeIndex] < 12
        ):
            self.tp.tunit[checkTimeIndex] += 12
        self.isFirstTimeSolveContext = False

    def addTime(self, cur: arrow.Arrow, fore_unit: int) -> arrow.Arrow:
        if fore_unit == 0:
            cur = cur.shift(years=1)
        elif fore_unit == 1:
            cur = cur.shift(months=1)
        elif fore_unit == 2:
            cur = cur.shift(days=1)
        elif fore_unit == 3:
            cur = cur.shift(hours=1)
        elif fore_unit == 4:
            cur = cur.shift(minutes=1)
        elif fore_unit == 5:
            cur = cur.shift(seconds=1)
        return cur
