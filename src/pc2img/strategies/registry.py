from __future__ import annotations

from typing import TypeVar, Generic, TYPE_CHECKING, Callable, ParamSpec

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

    def create(self, identifier: str, **kwargs: P.kwargs) -> T:  # Only allow for named arguments
        cls = self._map[identifier]
        return cls(**kwargs)

PROJECTIONS: StrategyRegistry[str, "ProjectionStrategy"] = StrategyRegistry()
INTERPOLATIONS: StrategyRegistry[str, "InterpolationStrategy"] = StrategyRegistry()
