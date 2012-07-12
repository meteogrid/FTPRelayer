import time
import Queue
import os.path
import shutil
import tempfile
import pkg_resources
from unittest2 import TestCase

def fixture(s):
    return pkg_resources.resource_filename(__name__, s)

class TestApplication(TestCase):
    config = 'config.ini'

    def _makeOneFromConfig(self):
        from .. import Application
        return Application.from_config(fixture(self.config))

    def _makeOne(self):
        from .. import Application
        return Application()

    def _makeRelayer(self, name='test', uploader=None, paths=None,
                     processor=None):
        from .. import Relayer
        return Relayer(name, uploader, paths, processor)


    def _makeTempDir(self):
        dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, dir)
        return dir

    def test_all_relayers_are_parsed(self):
        app = self._makeOneFromConfig()
        self.failUnlessEqual(2, len(app._relayers))

    def test_uploaders_are_properly_configured(self):
        from .. import SCPUploader, FTPUploader
        app = self._makeOneFromConfig()
        self.failUnless(isinstance(app._relayers[0].uploader, FTPUploader))
        self.failUnless(isinstance(app._relayers[1].uploader, SCPUploader))

    def test_paths_are_properly_configured(self):
        from .. import SCPUploader, FTPUploader
        app = self._makeOneFromConfig()
        self.failUnlessEqual(3, len(app._relayers[0].paths))
        self.failUnlessEqual(2, len(app._relayers[1].paths))

    def test_watch_new_file_creation(self):
        app = self._makeOne()
        dir = self._makeTempDir()
        relayer = self._makeRelayer(paths=[dir])
        app.add_relayer(relayer)
        self.addCleanup(app.stop)
        app.start()
        with open(os.path.join(dir, 'foo.txt'), 'w') as f:
            self.failUnless(app._queue.empty())
            f.write('foo')
            self.failUnless(app._queue.empty())
        try:
            item = app._queue.get(True, 1)
        except Queue.Empty:
            self.fail("No item was queued when file was closed")

    def test_watch_moved_file(self):
        app = self._makeOne()
        dir = self._makeTempDir()
        dir2 = self._makeTempDir()
        relayer = self._makeRelayer(paths=[dir])
        app.add_relayer(relayer)
        self.addCleanup(app.stop)
        app.start()
        path = os.path.join(dir2, 'foo.txt')
        with open(path, 'w') as f:
            f.write('foo')
        self.failUnless(app._queue.empty())
        os.rename(path, os.path.join(dir, 'foo.txt'))
        try:
            item = app._queue.get(True, 1)
        except Queue.Empty:
            self.fail("No item was queued when file was moved")
