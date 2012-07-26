import os
import time
import datetime
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

    def test_all_relayers_are_parsed(self):
        app = self._makeOneFromConfig()
        self.failUnlessEqual(5, len(app._relayers))

    def test_uploaders_are_properly_loaded_and_configured(self):
        from .. import SCPUploader, FTPUploader
        app = self._makeOneFromConfig()
        self.assertIsInstance(app._relayers[0].uploader, FTPUploader)
        self.failUnlessEqual(app._relayers[0].uploader.host, 'example.com')
        self.failUnlessEqual(app._relayers[0].uploader.username, 'pepe')
        self.failUnlessEqual(app._relayers[0].uploader.password, 'pepe2')

        self.assertIsInstance(app._relayers[1].uploader, SCPUploader)
        self.failUnlessEqual(app._relayers[1].uploader.host, 'example.org')
        self.failUnlessEqual(app._relayers[1].uploader.username, 'pepe2')
        self.failUnlessEqual(app._relayers[1].uploader.password, 'pepe22')

    def test_paths_are_properly_configured(self):
        app = self._makeOneFromConfig()
        self.failUnlessEqual(3, len(app._relayers[0].paths))
        self.failUnlessEqual(2, len(app._relayers[1].paths))

    def test_processor_func_is_loaded(self):
        app = self._makeOneFromConfig()
        self.assertIs(app._relayers[2].processor, processor_func)

    def test_processor_class_is_loaded_and_configured(self):
        from .. import add_prefix
        app = self._makeOneFromConfig()
        self.assertIsInstance(app._relayers[3].processor, add_prefix)
        self.failUnlessEqual(app._relayers[3].processor.prefix, 'foo')

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

    def test_file_archival(self):
        archive_dir = self._makeTempDir()
        app = self._makeOne(archive_dir=archive_dir)
        cur_date = datetime.datetime(2009,6,7)
        app.now = lambda: cur_date
        common_dir = self._makeTempDir()
        subdir = 'subdir'
        dir = os.path.join(common_dir, subdir)
        os.makedirs(dir)
        relayer = self._makeRelayer(
            paths=[os.path.join(dir, '*'),
                   os.path.join(common_dir,  'other_dir', '*')])
        relayer.process = lambda s: True
        app.add_relayer(relayer)
        self.addCleanup(app.stop)
        app.start()
        fname = os.path.join(dir, 'foo.txt')
        with open(fname, 'w') as f:
            f.write('foo')
        time.sleep(.1)
        self.failUnless(not os.path.exists(fname))
        archive_path = app._archive_path(relayer, fname)
        self.assertIn(relayer.name, archive_path)
        self.assertIn(cur_date.strftime('%Y/%m/%d'), archive_path)
        self.assertIn(subdir, archive_path)
        self.assertIn(os.path.basename(fname), archive_path)
        self.failUnless(os.path.exists(archive_path))

def processor_func(path):
    with open(path) as f:
        yield path, f.read()
