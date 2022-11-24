import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from time import sleep
from src.tickoff import FileTick
from src.tickoff.lifetime import Constant


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
    tick = FileTick(Path("does-not-exist"), Constant(lifetime))
    assert not tick.token.is_valid
    assert tick.token.is_expired


def test_tick_when_token_exists() -> None:
    lifetime = timedelta(seconds=1)
    with TemporaryFileName(suffix="_token_test.json") as temp_name:
        with FileTick(Path(temp_name), Constant(lifetime)) as tick:
            assert tick.token.is_expired

        with FileTick(Path(temp_name), Constant(lifetime)) as tick:
            assert tick.token.is_valid
            assert not tick.token.is_expired

            sleep(1.5)
            assert not tick.token.is_valid
            assert tick.token.is_expired


def test_tick_decorator():
    lifetime = timedelta(seconds=3)
    with TemporaryFileName(suffix="_token_test.json") as temp_name:
        @Tick(Path(temp_name), Constant(lifetime))
        def foo() -> bool:
            return True

        assert foo()

        sleep(1.5)
        assert not foo()

        sleep(1.5)
        assert foo()
