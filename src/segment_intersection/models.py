from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Point:
    """Punkt 2D."""
    x: float
    y: float

    def __iter__(self):
        yield self.x
        yield self.y


@dataclass(frozen=True, slots=True)
class Segment:
    """Odcinek zdefiniowany przez dwa punkty."""
    a: Point
    b: Point
