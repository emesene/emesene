import os
import unittest

import e3

logger = e3.Logger.LoggerProcess("test")
logger.start()
full_path = os.path.join("test", "base.db")


class LoggerTestCase(unittest.TestCase):

    def test_db_created(self):
        self.assertTrue(os.path.exists(full_path))

    def __del__(self):
        logger.quit()
        logger.join()

        if os.path.exists(full_path):
                os.remove(full_path)
