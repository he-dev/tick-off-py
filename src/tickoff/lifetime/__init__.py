from datetime import datetime, date, time, timedelta
from dateutil.relativedelta import relativedelta
from typing import Any, Dict, Protocol


class Period(Protocol):
    def expires_on(self) -> datetime:
        ...


class Constant:
    def __init__(self, value: timedelta):
        self.value = value

    def expires_on(self) -> datetime:
        return datetime.now() + self.value


# noinspection PyMethodMayBeStatic
class Today:
    def expires_on(self) -> datetime:
        return datetime.combine(datetime.now(), time.min) + relativedelta(days=1) - relativedelta(seconds=1)


# noinspection PyMethodMayBeStatic
class ThisWeek:
    def expires_on(self) -> datetime:
        return datetime.combine(datetime.now(), time.min) + relativedelta(days=7 - datetime.now().weekday()) - relativedelta(seconds=1)


# noinspection PyMethodMayBeStatic
class ThisMonth:
    def expires_on(self) -> datetime:
        return datetime.combine(datetime.now(), time.min).replace(day=1) + relativedelta(months=1) - relativedelta(seconds=1)
