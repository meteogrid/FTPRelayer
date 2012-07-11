import pkg_resources
from unittest import TestCase

def fixture(s):
    return pkg_resources.resource_filename(__name__, s)

class TestApplicaton(TestCase):
    config = 'config.ini'
    def _makeOne(self):
        from .. import Application
        return Application(fixture(self.config))

    def test_relayers_are_parsed(self):
        app = self._makeOne()
        self.failUnless(len(app.relayers), 2)
