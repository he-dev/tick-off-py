import json
from datetime import datetime, date, time, timedelta
from dateutil.relativedelta import relativedelta
from functools import cache
from pathlib import Path
from typing import Any, Dict, Protocol


class CalcExpiresOn(Protocol):

    def __call__(self) -> datetime:
        return datetime.now()


class Tick:
    def __init__(self, file_name: Path, calc_expires_on: CalcExpiresOn):
        self.file_name = file_name
        self.calc_expires_on = calc_expires_on

    @property
    def is_created(self) -> bool:
        return self.file_name.is_file()

    @property
    def elapsed(self) -> timedelta:
        return datetime.now() - self.created_on

    @property
    def is_valid(self) -> bool:
        return self.expires_on > datetime.now()

    @property
    def is_expired(self) -> bool:
        return not self.is_valid

    @property
    def created_on(self) -> datetime:
        return self._read_token()["created_on"]

    @property
    def expires_on(self) -> datetime:
        return self._read_token()["expires_on"]

    def _create_token(self, valid: bool = True) -> Dict:
        return {
            "created_on": datetime.now(),
            "expires_on": self.calc_expires_on() if valid else datetime.now()
        }

    @cache  # Avoid reading token more than once until updated.
    def _read_token(self) -> Dict:
        if self.file_name.is_file():
            with self.file_name.open() as f:
                return json.load(f, cls=_JsonDateTimeDecoder)
        else:
            return self._create_token(valid=False)

    def _write_token(self, data: Dict) -> None:
        self.file_name.parent.mkdir(parents=True, exist_ok=True)
        with self.file_name.open("w") as f:
            json.dump(data, f, cls=_JsonDateTimeEncoder)
        self._read_token.cache_clear()

    def __enter__(self):
        self._read_token()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not exc_type:
            self._write_token(self._create_token())


class ValidFor(CalcExpiresOn):
    def __init__(self, period: str | timedelta):
        self.period = period

    def __call__(self) -> datetime:
        if isinstance(self.period, timedelta):
            return datetime.now() + self.period

        match self.period.casefold():
            case "today":
                return datetime.combine(datetime.now(), time.min) + relativedelta(days=1) - relativedelta(seconds=1)

            case "this-week":
                return datetime.combine(datetime.now(), time.min) + relativedelta(days=7 - datetime.now().weekday()) - relativedelta(seconds=1)

            case "this-month":
                return datetime.combine(datetime.now(), time.min).replace(day=1) + relativedelta(months=1) - relativedelta(seconds=1)

        raise ValueError("Period out of range. Must be one of [today, this-week, this-month]")


class _JsonDateTimeEncoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        if isinstance(o, (date, datetime)):
            return o.isoformat()


class _JsonDateTimeDecoder(json.JSONDecoder):
    def __init__(self):
        super().__init__(object_hook=self.parse_datetime_or_default)

    @staticmethod
    def parse_datetime_or_default(d: Dict):
        r = dict()
        for k in d.keys():
            r[k] = d[k]
            if isinstance(d[k], str):
                try:
                    r[k] = datetime.fromisoformat(d[k])  # try parse date-time
                except ValueError:
                    pass  # default value is already set
        return r
