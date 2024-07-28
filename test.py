from dateparser_tw import DateParser

parser = DateParser()
print(parser.parse("半個月前"))
print(parser.parse("三個半月前"))
print(parser.parse("十二個月前"))
print(parser.parse("兩年半後"))
print(parser.parse("兩年前的七月十五號"))
print(parser.parse("兩年前的七月"))
print(parser.parse("兩年前的七月十五號下午三點半"))
