import time
import datetime
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

    def _makeOne(self, **kw):
        from .. import Application
        return Application(**kw)

    def _makeRelayer(self, name='test', uploader=None, paths=None,
                     processor=None):
        from .. import Relayer
        return Relayer(name, uploader, paths, processor)


    def _makeTempDir(self):
        dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, dir)
        return dir

    def test_app_is_properly_configured(self):
        app = self._makeOneFromConfig()
        self.assertIsInstance(app._cleanup, bool)
        
    def test_all_relayers_are_parsed(self):
        app = self._makeOneFromConfig()
        self.failUnlessEqual(2, len(app._relayers))

    def test_uploaders_are_properly_configured(self):
        from .. import SCPUploader, FTPUploader
        app = self._makeOneFromConfig()
        self.failUnless(isinstance(app._relayers[0].uploader, FTPUploader))
        self.failUnless(isinstance(app._relayers[1].uploader, SCPUploader))

    def test_paths_are_properly_configured(self):
        app = self._makeOneFromConfig()
        self.failUnlessEqual(3, len(app._relayers[0].paths))
        self.failUnlessEqual(2, len(app._relayers[1].paths))

    def test_watch_new_file_creation(self):
        app = self._makeOne()
        dir = self._makeTempDir()
        relayer = self._makeRelayer(paths=[dir+'/*'])
        state  = {'called':False}
        def process(self):
            state['called'] = True
        relayer.process = process
        app.add_relayer(relayer)
        self.addCleanup(app.stop)
        app.start()
        with open(os.path.join(dir, 'foo.txt'), 'w') as f:
            self.failUnless(not state['called'])
            f.write('foo')
            self.failUnless(not state['called'])
        time.sleep(.1)
        self.failUnless(state['called'])

    def test_watch_moved_file(self):
        app = self._makeOne()
        dir = self._makeTempDir()
        dir2 = self._makeTempDir()
        relayer = self._makeRelayer(paths=[dir+'/*'])
        state  = {'called':False}
        def process(self):
            state['called'] = True
        relayer.process = process
        app.add_relayer(relayer)
        self.addCleanup(app.stop)
        app.start()
        path = os.path.join(dir2, 'foo.txt')
        with open(path, 'w') as f:
            f.write('foo')
        self.failUnless(not state['called'])
        os.rename(path, os.path.join(dir, 'foo.txt'))
        time.sleep(.1)
        self.failUnless(state['called'])

    def test_file_cleanup(self):
        app = self._makeOne(cleanup=True)
        dir = self._makeTempDir()
        relayer = self._makeRelayer(paths=[dir+'/*'])
        relayer.process = lambda s: True
        app.add_relayer(relayer)
        self.addCleanup(app.stop)
        app.start()
        fname = os.path.join(dir, 'foo.txt')
        with open(fname, 'w') as f:
            f.write('foo')
        time.sleep(.1)
        self.failUnless(not os.path.exists(fname))

    def test_file_archival(self):
        archive_dir = self._makeTempDir()
        app = self._makeOne(archive_dir=archive_dir)
        app.now = lambda: datetime.datetime(2009,6,7)
        dir = self._makeTempDir()
        relayer = self._makeRelayer(paths=[dir+'/*'])
        relayer.process = lambda s: True
        app.add_relayer(relayer)
        self.addCleanup(app.stop)
        app.start()
        fname = os.path.join(dir, 'foo.txt')
        with open(fname, 'w') as f:
            f.write('foo')
        time.sleep(.1)
        self.failUnless(not os.path.exists(fname))
        self.failUnless(os.path.exists(app._archive_path(fname)))
