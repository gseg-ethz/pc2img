from __future__ import annotations

from typing import TypeVar, Generic, TYPE_CHECKING, Callable, ParamSpec, Any, Generator, Protocol

if TYPE_CHECKING:
    from .interpolation import InterpolationStrategy
    from .projection import ProjectionStrategy


P = ParamSpec("P")
T = TypeVar("T")

class StrategyRegistry(Generic[P, T]):
    def __init__(self) -> None:
        self._map: dict[str, Callable[P, T]] = {}

    def register(self, identifier: str) -> Callable[[Callable[P, T]], Callable[P, T]]:
        def decorator(cls: Callable[P, T]) -> Callable[P, T]:
            self._map[identifier] = cls
            return cls
        return decorator

    def get_strategy(self, identifier: str) -> Callable[P, T]:
        try:
            return self._map[identifier]
        except KeyError as e:
            raise KeyError(f"No strategy registered under {identifier!r}") from e

    def create(self, identifier: str, **kwargs: P.kwargs) -> T:  # Only allow for named arguments
        cls = self.get_strategy(identifier)
        return cls(**kwargs)

PROJECTIONS: StrategyRegistry[str, "ProjectionStrategy"] = StrategyRegistry()
INTERPOLATIONS: StrategyRegistry[str, "InterpolationStrategy"] = StrategyRegistry()

class StrategyFactory(Protocol[P, T]):
    def __call__(self, **kwargs: P.kwargs) -> T: ...

class _StrategyClass:
    """
    Subclass this, setting `registry` to your StrategyRegistry
    and `base_type` to the ABC class for that family.
    """
    registry: StrategyRegistry[Any, Any]
    base_type: type


    @classmethod
    def __get_validators__(cls) -> Generator[Callable[[Any], Any], None, None]:
        yield cls._validate

    @classmethod
    def _validate(cls, v: Any, _) -> type:
        # 1) already the correct subclass?
        if isinstance(v, type) and issubclass(v, cls.base_type):
            return v

        # 2) a key?
        if isinstance(v, str):
            try:
                return cls.registry.get_strategy(v)
            except KeyError:
                raise ValueError(f"Unknown {cls.base_type.__name__!r} key: {v!r}")

        raise TypeError(f"Cannot interpret {v!r} as a {cls.base_type.__name__} class/key")
