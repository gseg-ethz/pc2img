from __future__ import annotations

import inspect
import logging
from collections.abc import Callable, Generator
from typing import (
    TYPE_CHECKING,
    Any,
    Generic,
    ParamSpec,
    Protocol,
    TypeVar,
    cast,
)

if TYPE_CHECKING:
    from .interpolation import InterpolationStrategy
    from .projection import ProjectionStrategy


P = ParamSpec("P")
T = TypeVar("T")
S = TypeVar("S")
T_co = TypeVar("T_co", covariant=True)

logger = logging.getLogger(__name__)

# class StrategyRegistry(Generic[T]):
class StrategyRegistry(Generic[T]):
    def __init__(self) -> None:
        self._map: dict[str, type[T]] = {}
        self._ctor_meta: dict[type[T], tuple[set[str], bool]] = {}
        self._cls_to_key: dict[type[T], str] = {}

    def register[S](self, identifier: str) -> Callable[[type[S]], type[S]]:
        def decorator(cls: type[S]) -> type[S]:
            if identifier in self._map:
                raise KeyError(f"Strategy {identifier!r} already registered")
            self._map[identifier] = cast(type[T], cls)

            self._cls_to_key.setdefault(cast(type[T], cls), identifier)

            sig = inspect.signature(cls.__init__)
            valid_kw: set[str] = set()
            accepts_var_kw = False
            for p in sig.parameters.values():
                if p.name == "self":
                    continue

                if p.kind in (p.POSITIONAL_OR_KEYWORD, p.KEYWORD_ONLY):
                    valid_kw.add(p.name)
                elif p.kind == p.VAR_KEYWORD:
                    accepts_var_kw = True
            self._ctor_meta[cast(type[T], cls)] = (valid_kw, accepts_var_kw)
            return cls
        return decorator

    def get_strategy(self, identifier: str) -> type[T]:
        try:
            return self._map[identifier]
        except KeyError as e:
            raise KeyError(f"No strategy registered under {identifier!r}") from e

    def create(self, identifier: str, **kwargs: Any) -> T:
        cls = self.get_strategy(identifier)
        valid_kw, accepts_var_kw = self._ctor_meta[cls]
        if not accepts_var_kw:
            return cls(**kwargs)

        filtered = {k: v for k, v in kwargs.items() if k in valid_kw}
        unexpected = set(kwargs) - set(filtered)
        if unexpected:
            # choose warn or raise; warning by default
            logger.warning(
                f"Ignoring unexpected kwargs for {cls.__name__}: {sorted(unexpected)}",
                stacklevel=2,
            )
        return cls(**filtered)

    # NEW: reverse lookup from instance or class to its registered key
    def key_of(self, obj: T | type[T]) -> str:
        cls: type[T] = cast(type[T], obj if inspect.isclass(obj) else type(obj))
        key = self._cls_to_key.get(cls)
        if key is not None:
            return key
        # Optional: walk MRO in case you register a base class
        for base in cls.__mro__[1:]:
            key = self._cls_to_key.get(cast(type[T], base))
            if key is not None:
                return key
        raise KeyError(f"Class {cls.__module__}.{cls.__qualname__} is not registered")


PROJECTIONS: StrategyRegistry[ProjectionStrategy] = StrategyRegistry()
INTERPOLATIONS: StrategyRegistry[InterpolationStrategy] = StrategyRegistry()

class StrategyFactory(Protocol[P, T_co]):
    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> T_co: ...

class _StrategyClass(Generic[T]):
    """
    Subclass this, setting `registry` to your StrategyRegistry
    and `base_type` to the ABC class for that family.
    """
    registry: StrategyRegistry[T]
    base_type: type[T]


    @classmethod
    def __get_validators__(cls) -> Generator[Callable[..., type[T]], None, None]:
        yield cls._validate

    @classmethod
    def _validate(cls, v: Any, *_, **__) -> type[T]:
        # 1) already the correct subclass?
        if isinstance(v, type) and issubclass(v, cls.base_type):
            return cast(type[T], v)

        # 2) a key?
        if isinstance(v, str):
            try:
                return cls.registry.get_strategy(v)
            except KeyError:
                raise ValueError(f"Unknown {cls.base_type.__name__!r} key: {v!r}")

        raise TypeError(f"Cannot interpret {v!r} as a {cls.base_type.__name__} class/key")
