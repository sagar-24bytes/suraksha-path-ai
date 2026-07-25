"""
SurakshaPath AI — Lightweight Route Cache.

Caches computed RouteResult objects to accelerate repeated routing queries.
Automatically invalidates cache entries when hazard snapshots, blocked edges, or
graph topology changes to guarantee zero stale route returns.

Design Principles:
  - Cache lookup key includes source_node, exit list hash, and hazard snapshot hash.
  - Automatic cache flush / invalidation upon hazard signature modification.
  - Low memory footprint.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple, Any, TYPE_CHECKING
from routing.hazard_model import HazardSnapshot

if TYPE_CHECKING:
    from routing.path_manager import RouteResult


class RouteCache:
    """Lightweight, self-invalidating route cache."""

    def __init__(self, max_size: int = 256) -> None:
        self.max_size = max_size
        self._cache: Dict[Tuple[str, str, str], Any] = {}
        self._last_hazard_hash: str = ""

    def _make_key(
        self,
        source_node: str,
        target_exits: List[str],
        hazard_hash: str,
    ) -> Tuple[str, str, str]:
        """Construct tuple cache key."""
        exits_key = ",".join(sorted(target_exits))
        return (source_node, exits_key, hazard_hash)

    def get(
        self,
        source_node: str,
        target_exits: List[str],
        snapshot: Optional[HazardSnapshot] = None,
    ) -> Optional[Any]:
        """Look up cached RouteResult.

        Args:
            source_node: Starting zone ID.
            target_exits: List of allowed exit IDs.
            snapshot: Current HazardSnapshot.

        Returns:
            Cached RouteResult if valid match, None otherwise.
        """
        hazard_hash = snapshot.compute_hash() if snapshot else "STATIC"
        
        # Automatic invalidation if global hazard hash has changed
        if hazard_hash != self._last_hazard_hash:
            self.clear()
            self._last_hazard_hash = hazard_hash
            return None

        key = self._make_key(source_node, target_exits, hazard_hash)
        return self._cache.get(key)

    def put(
        self,
        source_node: str,
        target_exits: List[str],
        result: Any,
        snapshot: Optional[HazardSnapshot] = None,
    ) -> None:
        """Store computed RouteResult in cache.

        Args:
            source_node: Starting zone ID.
            target_exits: List of allowed exit IDs.
            result: Computed RouteResult instance.
            snapshot: Current HazardSnapshot.
        """
        hazard_hash = snapshot.compute_hash() if snapshot else "STATIC"
        
        if len(self._cache) >= self.max_size:
            self.clear()

        self._last_hazard_hash = hazard_hash
        key = self._make_key(source_node, target_exits, hazard_hash)
        self._cache[key] = result

    def clear(self) -> None:
        """Flush all cache entries."""
        self._cache.clear()

    @property
    def size(self) -> int:
        """Return current cached entry count."""
        return len(self._cache)
