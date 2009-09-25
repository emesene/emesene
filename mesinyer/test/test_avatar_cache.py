import unittest

import os
import sys
import cStringIO
sys.path.append(os.path.abspath('.'))

from e3 import cache
import testutils

class TestCreate(unittest.TestCase):
    def setUp(self):
        self.cache = cache.AvatarCache('tmp', 'user@host.com')
        self.image_path = testutils.create_binary_file(self.cache.path)

    def test_insert(self):
        response = self.cache.insert(self.image_path)
        self.assertNotEqual(response, None, 'cache.insert should return a tuple')
        stamp, hash_ = response
        self.assertTrue(hash_ in self.cache, hash_ + ' should be in cache')
        items = self.cache.list()
        self.assertTrue((stamp, hash_) in items,
                str((stamp, hash_)) + ' should be in cache.list(): ' + str(items))

    def test_insert_raw(self):
        image = cStringIO.StringIO(testutils.random_binary_data(4096))
        response = self.cache.insert_raw(image)
        self.assertNotEqual(response, None, 'cache.insert_raw should return a tuple')
        stamp, hash_ = response
        self.assertTrue(hash_ in self.cache, hash_ + ' should be in cache')
        items = self.cache.list()
        self.assertTrue((stamp, hash_) in items,
                str((stamp, hash_)) + ' should be in cache.list(): ' + str(items))

    def test_last(self):
        image = cStringIO.StringIO(testutils.random_binary_data(4096))
        response = self.cache.insert_raw(image)
        self.assertNotEqual(response, None, 'cache.insert_raw should return a tuple')
        self.assertTrue('last' in self.cache, 'last should be in cache')

    def test_remove(self):
        new_image_path = testutils.create_binary_file(self.cache.path)
        stamp, hash_ = self.cache.insert(new_image_path)
        self.assertTrue(self.cache.remove(hash_), 'remove should return True')
        items = self.cache.list()
        self.assertTrue((stamp, hash_) not in items,
                str((stamp, hash_)) + ' should not be in cache.list(): ' + str(items))

if __name__ == '__main__':
    unittest.main()

