import contextlib
import enum
import os
from typing import Generator
from typing import NamedTuple
from typing import Optional
from typing import Tuple
from typing import Union

from pre_commit.util import EnvironT


class _Unset(enum.Enum):
    UNSET = 1


UNSET = _Unset.UNSET


class Var(NamedTuple):
    name: str
    default: str


# python3.6.0: `typing.NamedTuple` did not support defaults
Var.__new__.__defaults__ = ('',)


SubstitutionT = Tuple[Union[str, Var], ...]
ValueT = Union[str, _Unset, SubstitutionT]
PatchesT = Tuple[Tuple[str, ValueT], ...]


def format_env(parts: SubstitutionT, env: EnvironT) -> str:
    return ''.join(
        env.get(part.name, part.default) if isinstance(part, Var) else part
        for part in parts
    )


@contextlib.contextmanager
def envcontext(
        patch: PatchesT,
        _env: Optional[EnvironT] = None,
) -> Generator[None, None, None]:
    """In this context, `os.environ` is modified according to `patch`.

    `patch` is an iterable of 2-tuples (key, value):
        `key`: string
        `value`:
            - string: `environ[key] == value` inside the context.
            - UNSET: `key not in environ` inside the context.
            - template: A template is a tuple of strings and Var which will be
              replaced with the previous environment
    """
    env = os.environ if _env is None else _env
    before = env.copy()

    for k, v in patch:
        if v is UNSET:
            env.pop(k, None)
        elif isinstance(v, tuple):
            env[k] = format_env(v, before)
        else:
            env[k] = v

    try:
        yield
    finally:
        env.clear()
        env.update(before)
