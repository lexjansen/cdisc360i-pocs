from contextvars import Token
from contextlib import contextmanager
from enum import Flag, auto
from typing import Generator

class ValidationMode(Flag):
    STRICT: int
    SKIP_REQUIRED: int
    SKIP_VALUESET: int
    SKIP_TYPE: int
    SKIP_FORMAT: int
    PERMISSIVE: int

def get_mode() -> ValidationMode: ...
def set_mode(mode: ValidationMode) -> Token: ...
def is_permissive(flag: ValidationMode) -> bool: ...

@contextmanager
def permissive(
    mode: ValidationMode = ValidationMode.PERMISSIVE,
) -> Generator[None, None, None]: ...
