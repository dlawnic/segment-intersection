from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Union

from .models import Point, Segment


# Epsilon dla porównań na liczbach zmiennoprzecinkowych.
EPS = 1e-9


def _cross(ax: float, ay: float, bx: float, by: float) -> float:
    return ax * by - ay * bx


def _sub(p: Point, q: Point) -> tuple[float, float]:
    return p.x - q.x, p.y - q.y


def _dot(ax: float, ay: float, bx: float, by: float) -> float:
    return ax * bx + ay * by


def _almost_zero(v: float, eps: float = EPS) -> bool:
    return abs(v) <= eps


def _between(a: float, b: float, c: float, eps: float = EPS) -> bool:
    """Czy b leży w przedziale [min(a,c), max(a,c)] z tolerancją."""
    lo = min(a, c) - eps
    hi = max(a, c) + eps
    return lo <= b <= hi


def point_on_segment(p: Point, s: Segment, eps: float = EPS) -> bool:
    """Sprawdza czy punkt p leży na odcinku s (łącznie z końcami)."""
    ax, ay = _sub(s.b, s.a)
    px, py = _sub(p, s.a)
    if not _almost_zero(_cross(ax, ay, px, py), eps):
        return False
    return _between(s.a.x, p.x, s.b.x, eps) and _between(s.a.y, p.y, s.b.y, eps)


@dataclass(frozen=True, slots=True)
class NoIntersection:
    """Brak przecięcia."""


@dataclass(frozen=True, slots=True)
class PointIntersection:
    """Przecięcie w jednym punkcie."""
    p: Point


@dataclass(frozen=True, slots=True)
class SegmentIntersection:
    """Przecięcie jest odcinkiem (wspólna część współliniowych odcinków)."""
    s: Segment


Intersection = Union[NoIntersection, PointIntersection, SegmentIntersection]


def segment_intersection(s1: Segment, s2: Segment, eps: float = EPS) -> Intersection:
    """Zwraca przecięcie dwóch odcinków.

    Wynik:
    - NoIntersection: brak części wspólnej,
    - PointIntersection: dokładnie jeden punkt,
    - SegmentIntersection: część wspólna jest odcinkiem (współliniowość i nakładanie).

    Implementacja jest odporna na typowe błędy numeryczne (epsilon).
    """
    p = s1.a
    r = Point(s1.b.x - s1.a.x, s1.b.y - s1.a.y)
    q = s2.a
    s = Point(s2.b.x - s2.a.x, s2.b.y - s2.a.y)

    rxs = _cross(r.x, r.y, s.x, s.y)
    q_p = Point(q.x - p.x, q.y - p.y)
    qpxr = _cross(q_p.x, q_p.y, r.x, r.y)

    # Przypadek: równoległe (rxs == 0)
    if _almost_zero(rxs, eps):
        # Równoległe, ale nie współliniowe
        if not _almost_zero(qpxr, eps):
            return NoIntersection()

        # Współliniowe - sprawdzamy nakładanie poprzez rzut na oś
        # Wybieramy oś o większym rozrzucie, aby uniknąć dzielenia przez 0.
        use_x = abs(r.x) >= abs(r.y)

        def coord(pt: Point) -> float:
            return pt.x if use_x else pt.y

        p0 = coord(s1.a)
        p1 = coord(s1.b)
        q0 = coord(s2.a)
        q1 = coord(s2.b)

        # Przedziały 1D
        a0, a1 = (p0, p1) if p0 <= p1 else (p1, p0)
        b0, b1 = (q0, q1) if q0 <= q1 else (q1, q0)

        lo = max(a0, b0)
        hi = min(a1, b1)

        if hi < lo - eps:
            return NoIntersection()

        # Gdy wspólna część degeneruje do punktu
        if abs(hi - lo) <= eps:
            # Wyznaczamy punkt na podstawie parametru t względem s1
            t = 0.0
            denom = (r.x if use_x else r.y)
            if not _almost_zero(denom, eps):
                t = (lo - (p.x if use_x else p.y)) / denom
            ip = Point(p.x + t * r.x, p.y + t * r.y)
            return PointIntersection(ip)

        # Wspólny odcinek: dwa końce odpowiadają lo i hi
        denom = (r.x if use_x else r.y)
        if _almost_zero(denom, eps):
            # s1 jest punktem (teoretycznie), ale wtedy hi-lo też byłoby ~0
            return NoIntersection()

        t0 = (lo - (p.x if use_x else p.y)) / denom
        t1 = (hi - (p.x if use_x else p.y)) / denom
        a_pt = Point(p.x + t0 * r.x, p.y + t0 * r.y)
        b_pt = Point(p.x + t1 * r.x, p.y + t1 * r.y)
        return SegmentIntersection(Segment(a_pt, b_pt))

    # Przypadek: nie równoległe - jednoznaczne przecięcie prostych w punkcie
    t = _cross(q_p.x, q_p.y, s.x, s.y) / rxs
    u = _cross(q_p.x, q_p.y, r.x, r.y) / rxs

    # Czy punkt przecięcia leży na obu odcinkach?
    if -eps <= t <= 1 + eps and -eps <= u <= 1 + eps:
        ip = Point(p.x + t * r.x, p.y + t * r.y)
        return PointIntersection(ip)

    return NoIntersection()


def intersection_to_human(result: Intersection, ndigits: int = 6) -> str:
    """Tekstowa reprezentacja wyniku do GUI/CLI."""
    def fmt(v: float) -> str:
        # Usuwamy -0.0 i ograniczamy liczbę cyfr
        v = 0.0 if abs(v) < EPS else v
        return f"{v:.{ndigits}f}".rstrip('0').rstrip('.') if ndigits > 0 else str(v)

    if isinstance(result, NoIntersection):
        return "NIE - brak części wspólnej"

    if isinstance(result, PointIntersection):
        return f"TAK - punkt: ({fmt(result.p.x)}, {fmt(result.p.y)})"

    if isinstance(result, SegmentIntersection):
        a, b = result.s.a, result.s.b
        return (
            "TAK - odcinek: "
            f"A=({fmt(a.x)}, {fmt(a.y)}), "
            f"B=({fmt(b.x)}, {fmt(b.y)})"
        )

    return "(nieznany wynik)"
