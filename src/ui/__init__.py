"""UI package for FluidSim Linux."""


class _LazyIcons:
    """Lazily-loaded icon cache. Builds icons on first access so that a
    QApplication must already exist (prevents QPixmap crash at import time)."""

    def __init__(self):
        self._icons = None
        self._built = False

    def _build(self):
        if not self._built:
            from src.ui.icons import make_all_icons
            self._icons = make_all_icons()
            self._built = True

    def __getitem__(self, key):
        self._build()
        return self._icons[key]

    def __contains__(self, key):
        self._build()
        return key in self._icons

    def get(self, key, default=None):
        self._build()
        return self._icons.get(key, default)

    def __len__(self):
        self._build()
        return len(self._icons)

    def keys(self):
        self._build()
        return self._icons.keys()

    def items(self):
        self._build()
        return self._icons.items()

    def values(self):
        self._build()
        return self._icons.values()


# Module-level singleton — no icons built until something accesses ICONS
ICONS = _LazyIcons()
