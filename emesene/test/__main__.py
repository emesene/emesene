import unittest

import gettext
gettext.install('emesene')

from test_avatar_cache import AvatarCacheTestCase
from test_cache_manager import CacheManagerTestCase
from test_emoticon_cache import EmoticonCacheTestCase
from test_ring_buffer import RingBufferTestCase
from test_logger import LoggerTestCase

unittest.main()
