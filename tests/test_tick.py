import json
import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from tempfile import NamedTemporaryFile
from time import sleep
from src.tick_off import Tick, ValidFor


class TemporaryFileName:
    def __init__(self, suffix: str, create=False, delete=True):
        self.suffix = suffix
        self.create = create
        self.delete = delete

    def __enter__(self):
        self._temp_name = os.path.join(tempfile.gettempdir(), f"{os.urandom(4).hex()}_{self.suffix}")
        try:
            return self._temp_name
        finally:
            if self.create:
                open(self._temp_name, "x").close()

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.delete:
            os.remove(self._temp_name)


def test_tick_when_token_does_not_exist():
    lifetime = timedelta(seconds=1)
    tick = Tick(Path("does-not-exist"), ValidFor(lifetime))
    assert not tick.is_created
    assert not tick.is_valid
    assert tick.is_expired


def test_tick_when_token_exists() -> None:
    lifetime = timedelta(seconds=1)
    with TemporaryFileName(suffix="_token_test.json") as temp_name:
        with Tick(Path(temp_name), ValidFor(lifetime)) as tick:
            assert not tick.is_created
            assert tick.is_expired

        with Tick(Path(temp_name), ValidFor(lifetime)) as tick:
            assert tick.is_created
            assert tick.is_valid
            assert not tick.is_expired

            sleep(1.5)
            assert tick.is_created
            assert not tick.is_valid
            assert tick.is_expired


def test_tick_decorator():
    lifetime = timedelta(seconds=3)
    with TemporaryFileName(suffix="_token_test.json") as temp_name:
        @Tick(Path(temp_name), lifetime)
        def foo() -> bool:
            return True

        assert foo()

        sleep(1.5)
        assert not foo()

        sleep(1.5)
        assert foo()
