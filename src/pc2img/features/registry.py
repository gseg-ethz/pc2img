import re

from .core import BaseFeatureStrategy, DerivativeFeatureStrategy


class FeatureSpec:
    """
    Represents a parsed feature name and its parameters.
    """

    def __init__(self, name: str, pattern: re.Pattern):
        m = pattern.fullmatch(name)
        if not m:
            raise ValueError(f"Name '{name}' does not match pattern {pattern.pattern}")
        self.name = name
        self.params = m.groupdict()
        # dependencies recognized from params or fixed list
        self.dependencies = []
        if "base_feature" in self.params:
            self.dependencies.append(self.params["base_feature"])
        self.cls = None


class FeatureRegistry:
    def __init__(self):
        self._map: dict[
            re.Pattern[str], type[BaseFeatureStrategy | DerivativeFeatureStrategy]
        ] = {}
        self._default_cls: type[BaseFeatureStrategy] = None

    def register(self, cls=None, *, default: bool = False):
        # support both @reg and @reg(default=True)
        def decorator(c: type[BaseFeatureStrategy | DerivativeFeatureStrategy]):
            pat = c.regex_pattern
            if pat in self._map:
                raise RuntimeError(f"Pattern {pat.pattern} already registered")
            self._map[pat] = c
            if default and self._default_cls is None:
                self._default_cls = c
            elif default and self._default_cls != c:
                raise RuntimeError(
                    f"strategy {c.__name__} already registered as default"
                )

            return c

        return decorator(cls) if cls else decorator

    def match(self, name: str) -> FeatureSpec:
        matches = [(p, c) for p, c in self._map.items() if p.fullmatch(name)]
        if len(matches) > 1:
            raise RuntimeError(f"Multiple patterns match '{name}'")
        if len(matches) == 1:
            pat, cls = matches[0]
            spec = FeatureSpec(name, pat)
            inst = cls(**spec.params)
            spec.cls = cls
            spec.dependencies = inst.dependencies
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
        raise RuntimeError(f"No pattern for '{name}' and no default registered")


FEATURES = FeatureRegistry()
