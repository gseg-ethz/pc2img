from __future__ import annotations

from typing import TypeVar, Generic, TYPE_CHECKING, Callable, ParamSpec, Any, Generator, Protocol, cast, TypeGuard, Optional

if TYPE_CHECKING:
    from .interpolation import InterpolationStrategy
    from .projection import ProjectionStrategy


P = ParamSpec("P")
T = TypeVar("T")
S = TypeVar("S")
T_co = TypeVar("T_co", covariant=True)



class StrategyRegistry(Generic[T]):
    def __init__(self) -> None:

        self._map: dict[str, type[T]] = {}

    def register(self, identifier: str) -> Callable[[type[S]], type[S]]:
        def decorator(cls: type[S]) -> type[S]:
            if identifier in self._map:
                raise KeyError(f"Strategy {identifier!r} already registered")
            self._map[identifier] = cls
            return cls
        return decorator

    def get_strategy(self, identifier: str) -> type[T]:
        try:
            return self._map[identifier]
        except KeyError as e:
            raise KeyError(f"No strategy registered under {identifier!r}") from e

    def create(self, identifier: str, **kwargs: Any) -> T:
        cls = self.get_strategy(identifier)
        return cls(**kwargs)

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
