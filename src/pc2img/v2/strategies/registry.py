from __future__ import annotations

from typing import TypeVar, Generic, TYPE_CHECKING, Any, Callable, ParamSpec

if TYPE_CHECKING:
    from .interpolation import InterpolationStrategy
    from .projection import ProjectionStrategy


P = ParamSpec("P")
T = TypeVar("T")

class StrategyRegistry(Generic[P, T]):
    def __init__(self) -> None:
        self._map: dict[str, Callable[P, T]] = {}

    def register(self, name: str) -> Callable[[Callable[P, T]], Callable[P, T]]:
        def decorator(cls: Callable[P, T]) -> Callable[P, T]:
            self._map[name] = cls
            return cls
        return decorator

    def create(self, name: str, *args: P.args, **kwargs: P.kwargs) ->  T:
        cls = self._map[name]
        return cls(*args, **kwargs)

PROJECTIONS: StrategyRegistry[Any, "ProjectionStrategy"] = StrategyRegistry()
INTERPOLATIONS: StrategyRegistry[Any, "InterpolationStrategy"] = StrategyRegistry()
