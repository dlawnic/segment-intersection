import unittest

from segment_intersection.geometry import (
    NoIntersection,
    PointIntersection,
    SegmentIntersection,
    segment_intersection,
)
from segment_intersection.models import Point, Segment


class SegmentIntersectionTests(unittest.TestCase):
    def test_proper_intersection(self):
        s1 = Segment(Point(0, 0), Point(4, 4))
        s2 = Segment(Point(0, 4), Point(4, 0))
        res = segment_intersection(s1, s2)
        self.assertIsInstance(res, PointIntersection)
        self.assertAlmostEqual(res.p.x, 2.0, places=7)
        self.assertAlmostEqual(res.p.y, 2.0, places=7)

    def test_touching_at_endpoint(self):
        s1 = Segment(Point(0, 0), Point(2, 0))
        s2 = Segment(Point(2, 0), Point(2, 2))
        res = segment_intersection(s1, s2)
        self.assertIsInstance(res, PointIntersection)
        self.assertAlmostEqual(res.p.x, 2.0, places=7)
        self.assertAlmostEqual(res.p.y, 0.0, places=7)

    def test_parallel_disjoint(self):
        s1 = Segment(Point(0, 0), Point(2, 0))
        s2 = Segment(Point(0, 1), Point(2, 1))
        res = segment_intersection(s1, s2)
        self.assertIsInstance(res, NoIntersection)

    def test_collinear_overlap_segment(self):
        s1 = Segment(Point(0, 0), Point(5, 0))
        s2 = Segment(Point(2, 0), Point(7, 0))
        res = segment_intersection(s1, s2)
        self.assertIsInstance(res, SegmentIntersection)
        self.assertAlmostEqual(res.s.a.x, 2.0, places=7)
        self.assertAlmostEqual(res.s.b.x, 5.0, places=7)

    def test_collinear_touch_point(self):
        s1 = Segment(Point(0, 0), Point(2, 0))
        s2 = Segment(Point(2, 0), Point(5, 0))
        res = segment_intersection(s1, s2)
        self.assertIsInstance(res, PointIntersection)
        self.assertAlmostEqual(res.p.x, 2.0, places=7)
        self.assertAlmostEqual(res.p.y, 0.0, places=7)

    def test_no_intersection_skew(self):
        s1 = Segment(Point(0, 0), Point(1, 1))
        s2 = Segment(Point(2, 0), Point(3, 1))
        res = segment_intersection(s1, s2)
        self.assertIsInstance(res, NoIntersection)


if __name__ == "__main__":
    unittest.main(verbosity=2)
