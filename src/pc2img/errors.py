"""Shared exception types for pc2img.

``RegistryLookupError`` is the single miss/duplicate exception raised by BOTH
``StrategyRegistry`` (strategies) and ``FeatureRegistry`` (features). It unifies
the previously divergent contracts — ``KeyError`` in the strategy registry vs
``RuntimeError`` in the feature registry.

The dual inheritance is deliberate: because ``RegistryLookupError`` subclasses
BOTH ``KeyError`` and ``RuntimeError``, every pre-existing ``except KeyError``
caller (e.g. ``_StrategyClass._validate``) AND every ``except RuntimeError``
caller keeps catching it unchanged. The unification therefore breaks ZERO
callers while giving both registries one recognizable, catchable miss type.

The MRO is well-defined: ``RegistryLookupError → KeyError → RuntimeError →
LookupError → Exception`` (``KeyError`` and ``RuntimeError`` share only
``Exception`` as a common base, so no C3 conflict arises).

Note: the *type* raised on a registry miss changed when the two registries'
exception types were unified. Because of the dual inheritance the observable
catch behavior is preserved, but code that matches on the exact class
``KeyError``/``RuntimeError`` (rather than catching a superclass) will now see
``RegistryLookupError``. No such call site exists in the codebase or tests.
"""

from __future__ import annotations


class RegistryLookupError(KeyError, RuntimeError):
    """Unified miss/duplicate lookup error for pc2img registries.

    Subclasses both :class:`KeyError` and :class:`RuntimeError` so existing
    ``except KeyError`` and ``except RuntimeError`` handlers continue to catch
    registry misses now that the registry-miss exception type is unified.
    """

    def __str__(self) -> str:
        # KeyError (first in the MRO) overrides __str__ to repr-wrap the message,
        # so a single-string arg would render with surrounding quotes
        # (``"Unknown feature 'range'"`` → ``'"Unknown feature ...'"``). Restore
        # the plain RuntimeError-style message the FeatureRegistry sites used to
        # emit before the unification; multi/no-arg cases defer to the base.
        if len(self.args) == 1 and isinstance(self.args[0], str):
            return self.args[0]
        return super().__str__()
