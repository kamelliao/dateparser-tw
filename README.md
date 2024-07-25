# dateparser-tw: Traditional Chinese natural language time parser

## Getting started

### Usage
```python
from dateparser_tw import DateParser

parser = DateParser()
parser.parse('昨天下午三點半', basetime='2024-07-15')  # TimePoint(year=2024, month=7, day=24, period_of_day='下午', hour=15, minute=30, second=0, granularity=<Granularity.DateTime: 'datetime'>)
```

## Roadmap
- [ ] Timespan
- [ ] Settings: prefer future/past
