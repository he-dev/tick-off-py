import json
from lifetime import Period
from abc import ABC, abstractmethod
from datetime import datetime, date, time, timedelta
from functools import cache
from pathlib import Path
from typing import Any, Dict, Callable, Protocol
from dataclasses import dataclass


@dataclass()
class Token:
    created_on: datetime = datetime.now()
    expires_on: datetime = datetime.now()

    @property
    def elapsed(self) -> timedelta:
        return datetime.now() - self.created_on

    @property
    def is_valid(self) -> bool:
        return self.expires_on > datetime.now()

    @property
    def is_expired(self) -> bool:
        return not self.is_valid


class Tick(ABC):
    def __init__(self, period: Period):
        self.period = period
        self.token = self._read_token()

    @abstractmethod
    def _read_token(self) -> Token:
        pass

    @abstractmethod
    def _write_token(self, token: Token) -> None:
        pass

    def commit(self):
        self._write_token(Token(expires_on=self.period.expires_on()))

    def __enter__(self):
        self._read_token()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not exc_type:
            self.commit()


class FileTick(Tick):
    def __init__(self, file_name: Path, period: Period):
        self.file_name = file_name
        super(FileTick, self).__init__(period)

    @cache  # Avoid reading token more than once until updated.
    def _read_token(self) -> Token:
        if self.file_name.is_file():
            with self.file_name.open() as f:
                j = json.load(f, cls=_JsonDateTimeDecoder)
                return Token(j["created_on"], j["expires_on"])
        else:
            return Token()

    def _write_token(self, token: Token) -> None:
        self.file_name.parent.mkdir(parents=True, exist_ok=True)
        with self.file_name.open("w") as f:
            json.dump({"created_on": token.created_on, "expires_on": token.expires_on}, f, cls=_JsonDateTimeEncoder)
        self._read_token.cache_clear()


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
