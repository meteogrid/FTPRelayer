from unittest2 import TestCase
import mox


class TestCaseWithMox(TestCase):
    def setUp(self):
        self.mox = mox.Mox()

    def tearDown(self):
        self.mox.UnsetStubs()
