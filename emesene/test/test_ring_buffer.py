import os
import sys
import unittest
sys.path.append(os.path.abspath('.'))

from e3.common import RingBuffer

class TestCreate(unittest.TestCase):

    ITEMS = [1, 2.4, False, None, "foo", [], (1,2,3)]

    def test_create(self):
        ring = RingBuffer()

        self.assertEquals(len(ring), 0)
        self.assertRaises(IndexError, ring.pop)

    def test_push(self):
        ring = RingBuffer()
        ring.push(1)

        self.assertEquals(ring.pop(), 1)

        ring.push("foo")
        ring.push(False)

        self.assertEquals(ring.pop(), False)
        self.assertEquals(ring.pop(), "foo")
        self.assertRaises(IndexError, ring.pop)

        for item in TestCreate.ITEMS:
            ring.push(item)

        for item in TestCreate.ITEMS[-5::][::-1]:
            self.assertEquals(ring.pop(), item)

        self.assertRaises(IndexError, ring.pop)

        r1 = RingBuffer(1)

        r1.push("foo")
        self.assertEquals(r1.pop(), "foo")
        self.assertRaises(IndexError, r1.pop)

        r1.push("foo")
        r1.push(False)

        self.assertEquals(r1.pop(), False)
        self.assertRaises(IndexError, r1.pop)

    def test_peak(self):
        ring = RingBuffer()
        self.assertRaises(IndexError, ring.peak)

        for i in range(5):
            ring.push(i)

        self.assertEquals(ring.peak(), 4)
        self.assertEquals(ring.peak(1), 0)
        self.assertEquals(ring.peak(2), 1)
        self.assertEquals(ring.peak(3), 2)
        self.assertEquals(ring.peak(4), 3)
        self.assertEquals(ring.peak(5), 4)
        self.assertEquals(ring.peak(6), 0)
        self.assertEquals(ring.peak(7), 1)
        self.assertEquals(ring.peak(-1), 3)
        self.assertEquals(ring.peak(-2), 2)
        self.assertEquals(ring.peak(-3), 1)
        self.assertEquals(ring.peak(-4), 0)
        self.assertEquals(ring.peak(-5), 4)
        self.assertEquals(ring.peak(-6), 3)
        self.assertEquals(ring.peak(-7), 2)

if __name__ == '__main__':
    unittest.main()
