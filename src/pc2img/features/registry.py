import re
from typing import cast

from ..errors import RegistryLookupError
from .core import BaseFeatureStrategy, DerivativeFeatureStrategy


class FeatureSpec:
    """
    Represents a parsed feature name and its parameters.
    """

    name: str
    params: dict[str, str | None]
    dependencies: list[str]
    # Resolved by ``FeatureRegistry.match`` after construction; ``None`` until set.
    cls: type[BaseFeatureStrategy | DerivativeFeatureStrategy] | None

    def __init__(self, name: str, pattern: re.Pattern):
        m = pattern.fullmatch(name)
        if not m:
            raise ValueError(f"Name '{name}' does not match pattern {pattern.pattern}")
        self.name = name
        self.params = m.groupdict()
        # FeatureSpec does NOT derive its own dependencies. ``FeatureRegistry.match``
        # is the single writer of ``spec.dependencies`` (via ``cls.dependencies_for``
        # on the matched path, or ``[]`` on the default-fallback path); deriving them
        # here was dead code that ``match`` overwrote on every path.
        self.dependencies = []
        self.cls = None


class FeatureRegistry:
    def __init__(self):
        self._map: dict[re.Pattern[str], type[BaseFeatureStrategy | DerivativeFeatureStrategy]] = {}
        # The default class is genuinely optional until a `default=True`
        # feature registers, so type it `type[...] | None`.
        self._default_cls: type[BaseFeatureStrategy] | None = None

    def register(self, cls=None, *, default: bool = False):
        # support both @reg and @reg(default=True)
        def decorator(c: type[BaseFeatureStrategy | DerivativeFeatureStrategy]):
            pat = c.regex_pattern
            if pat in self._map:
                raise RegistryLookupError(f"Pattern {pat.pattern} already registered")
            self._map[pat] = c
            if default and self._default_cls is None:
                # The default feature is by construction a per-point BaseFeatureStrategy
                # (a derivative raster cannot stand in as the unknown-name fallback);
                # narrow the broader decorator param to the annotated default type.
                self._default_cls = cast("type[BaseFeatureStrategy]", c)
            elif default and self._default_cls != c:
                raise RegistryLookupError(f"strategy {c.__name__} already registered as default")

            return c

        return decorator(cls) if cls else decorator

    def match(self, name: str) -> FeatureSpec:
        matches = [(p, c) for p, c in self._map.items() if p.fullmatch(name)]
        if len(matches) > 1:
            raise RegistryLookupError(f"Multiple patterns match '{name}'")
        if len(matches) == 1:
            pat, cls = matches[0]
            spec = FeatureSpec(name, pat)
            spec.cls = cls
            # Derive dependencies from the parsed groupdict WITHOUT
            # constructing the feature (no more double `__init__`). Each family
            # overrides `dependencies_for` to mirror its own derivation, so
            # match() and construction always agree.
            spec.dependencies = cls.dependencies_for(spec.params)
            return spec
        # no regex match → fallback to default base-feature
        if self._default_cls:
            # create a pseudo-spec for default class
            spec = FeatureSpec.__new__(FeatureSpec)
            spec.name = name
            spec.params = {"feature": name}
            spec.dependencies = []
            spec.cls = self._default_cls
            return spec
        raise RegistryLookupError(f"No pattern for '{name}' and no default registered")


FEATURES = FeatureRegistry()
