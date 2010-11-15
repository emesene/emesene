import unittest

import os
import sys
import cStringIO
sys.path.append(os.path.abspath('.'))

from e3 import cache
import testutils

class CacheManagerTestCase(unittest.TestCase):
    def setUp(self):
        self.cache = cache.CacheManager('tmp')

    def test_get_avatar_cache(self):
        # once to create the instance
        avatar_cache = self.cache.get_avatar_cache('some@user.com')
        self.assertEqual(type(avatar_cache), cache.AvatarCache)
        # another to test the retrieval
        avatar_cache_1 = self.cache.get_avatar_cache('some@user.com')
        self.assertTrue(avatar_cache is avatar_cache_1)

    def test_get_emoticon_cache(self):
        # once to create the instance
        emoticon_cache = self.cache.get_emoticon_cache('some@user.com')
        self.assertEqual(type(emoticon_cache), cache.EmoticonCache)
        # once to create the instance
        emoticon_cache_1 = self.cache.get_emoticon_cache('some@user.com')
        self.assertTrue(emoticon_cache is emoticon_cache_1)

if __name__ == '__main__':
    unittest.main()

