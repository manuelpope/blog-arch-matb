"""In-memory cache with file-modification invalidation."""
from pathlib import Path
from threading import Lock
from typing import Any, Optional


class RenderCache:
    """Thread-safe in-memory cache invalidated on file mtime change."""

    def __init__(self) -> None:
        self._cache: dict[str, tuple[float, Any]] = {}
        self._lock = Lock()
        self.hits = 0
        self.misses = 0

    def get(self, key: str, source: Optional[Path] = None) -> Optional[Any]:
        """Return cached value if fresh; None on miss or staleness."""
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                self.misses += 1
                return None

            cached_value, cached_mtime = entry
            if source is not None:
                try:
                    current_mtime = source.stat().st_mtime
                    if current_mtime != cached_mtime:
                        del self._cache[key]
                        self.misses += 1
                        return None
                except OSError:
                    del self._cache[key]
                    self.misses += 1
                    return None

            self.hits += 1
            return cached_value

    def set(self, key: str, value: Any, source: Optional[Path] = None) -> None:
        """Store value, indexed by current source mtime if provided."""
        mtime = 0.0
        if source is not None:
            try:
                mtime = source.stat().st_mtime
            except OSError:
                pass
        with self._lock:
            self._cache[key] = (value, mtime)

    def invalidate(self, key: Optional[str] = None) -> None:
        """Drop a single key or clear the whole cache."""
        with self._lock:
            if key is None:
                self._cache.clear()
            else:
                self._cache.pop(key, None)

    def stats(self) -> dict:
        """Return observability stats."""
        with self._lock:
            total = self.hits + self.misses
            hit_rate = (self.hits / total * 100) if total else 0.0
            return {
                "entries": len(self._cache),
                "hits": self.hits,
                "misses": self.misses,
                "hit_rate": f"{hit_rate:.1f}%",
            }


# Caches for each concern
md_render_cache = RenderCache()    # markdown source → HTML body
page_render_cache = RenderCache()  # full HTML pages (home, blog, post)
list_render_cache = RenderCache()  # listing endpoints
svg_memory_cache = RenderCache()   # mirror of on-disk Mermaid SVGs
