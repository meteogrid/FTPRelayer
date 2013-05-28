from configobj import ConfigObj

from . import TestCase
from StringIO import StringIO


class _DummyUploader(object):
    def __init__(self):
        self.files = {}

    def upload(self, filename, data):
        self.files[filename] = data

    @classmethod
    def from_config(cls, section):
        return cls()


class TestCompositeUploader(TestCase):
    def _makeOne(self, section):
        from .. import CompositeUploader
        return CompositeUploader(section)

    def test_upload(self):
        _ini = '''
        [uploaders]
            [[up1]]
                use=ftprelayer.tests.test_composite:_DummyUploader
            [[up2]]
                use=ftprelayer.tests.test_composite:_DummyUploader
        '''
        filename = 'some_file'
        data = 'some_data'
        conf = ConfigObj(StringIO(_ini))
        section = conf['uploaders']
        ob = self._makeOne(section)

        ob.upload(filename, data)
        for u in ob.uploaders.values():  # FIXME: Accede a la implementacion
            self.failUnlessEqual(u.files, {filename: data})
