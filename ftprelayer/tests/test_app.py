import os
import time
import datetime
import shutil
import tempfile
import pkg_resources
from unittest2 import TestCase

from . import TestCaseWithMox

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
        self.failUnlessEqual(7, len(app._relayers))

    def test_uploaders_are_properly_loaded_and_configured(self):
        from .. import (CompositeUploader, SCPUploader, FTPUploader,
                         _NullUploader, Uploader)
        app = self._makeOneFromConfig()
        self.assertIsInstance(app._relayers[0].uploader, FTPUploader)
        self.failUnlessEqual(app._relayers[0].uploader.host, 'example.com')
        self.failUnlessEqual(app._relayers[0].uploader.username, 'pepe')
        self.failUnlessEqual(app._relayers[0].uploader.password, 'pepe2')

        self.assertIsInstance(app._relayers[1].uploader, SCPUploader)
        self.failUnlessEqual(app._relayers[1].uploader.host, 'example.org')
        self.failUnlessEqual(app._relayers[1].uploader.username, 'pepe2')
        self.failUnlessEqual(app._relayers[1].uploader.password, 'pepe22')

        self.assertIsInstance(app._relayers[4].uploader, _NullUploader)

        self.assertIsInstance(app._relayers[5].uploader, CompositeUploader)
        sub_uploaders = app._relayers[5].uploader.uploaders
        self.failUnlessEqual(len(sub_uploaders), 2)
        for v in sub_uploaders:
            self.assertIsInstance(v, Uploader)

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
        app.add_relayer(relayer)
        self.addCleanup(app.stop)
        app.start()
        fname = os.path.join(dir, 'foo.txt')
        with open(fname, 'w') as f:
            f.write('foo')
        time.sleep(.1)
        self.failUnless(not os.path.exists(fname))
        archive_path = app._archive_path(relayer, fname, no_clobber=False)
        self.assertIn(relayer.name, archive_path)
        self.assertIn(cur_date.strftime('%Y/%m/%d'), archive_path)
        self.assertIn(subdir, archive_path)
        self.assertIn(os.path.basename(fname), archive_path)
        self.failUnless(os.path.exists(archive_path))

    def test_archive_path_does_not_clobber(self):
        archive_dir = self._makeTempDir()
        app = self._makeOne(archive_dir=archive_dir)
        relayer = self._makeRelayer(paths=['/tmp/*'])
        fname = '/tmp/foo'
        archive_path = app._archive_path(relayer, fname)
        touch(archive_path)
        archive_path2 = app._archive_path(relayer, fname)
        self.assertNotEqual(archive_path, archive_path2)
        self.failUnless(archive_path2.endswith('.1'))

        touch(archive_path2)
        archive_path3 = app._archive_path(relayer, fname)
        self.assertNotEqual(archive_path2, archive_path3)
        self.failUnless('.1' not in archive_path3)
        self.failUnless(archive_path3.endswith('.2'))

    def test_file_archival_with_error(self):
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
        def raise_error(*args, **kw): raise RuntimeError
        relayer.process = raise_error
        app.add_relayer(relayer)
        self.addCleanup(app.stop)
        app.start()
        fname = os.path.join(dir, 'foo.txt')
        with open(fname, 'w') as f:
            f.write('foo')
        time.sleep(.1)
        self.failUnless(not os.path.exists(fname))
        archive_path = app._archive_path(relayer, fname, no_clobber=False,
                                         has_error=True)
        self.assertIn(relayer.name, archive_path)
        self.assertIn(cur_date.strftime('%Y/%m/%d'), archive_path)
        self.assertIn(subdir, archive_path)
        self.assertIn(os.path.basename(fname), archive_path)
        self.failUnless(os.path.exists(archive_path))

    def test_two_relayers_can_watch_the_same_dir(self):
        app = self._makeOne()
        dir = self._makeTempDir()
        state  = {'called1':False, 'called2':False}
        relayer1 = self._makeRelayer(paths=[dir+'/*.1'])
        def process1(self):
            state['called1'] = True
        relayer1.process = process1
        app.add_relayer(relayer1)

        relayer2 = self._makeRelayer(paths=[dir+'/*.2'])
        def process2(self):
            state['called2'] = True
        relayer2.process = process2
        app.add_relayer(relayer2)

        self.addCleanup(app.stop)
        app.start()

        with open(os.path.join(dir, 'foo.1'), 'w') as f:
            self.failUnless(not state['called1'])
            f.write('foo')
            self.failUnless(not state['called1'])
        time.sleep(.1)
        self.failUnless(state['called1'])

        with open(os.path.join(dir, 'foo.2'), 'w') as f:
            self.failUnless(not state['called2'])
            f.write('foo')
            self.failUnless(not state['called2'])
        time.sleep(.1)
        self.failUnless(state['called2'])

def touch(path):
    dirname = os.path.dirname(path)
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    with open(path, 'a+'):
        pass

def processor_func(path):
    with open(path) as f:
        yield path, f.read()


class TestMain(TestCaseWithMox):
    def test_too_few_args(self):
        import ftprelayer
        self.assertEqual(-1, ftprelayer.main(['./ftprelayer']))

    def test_good_run(self):
        import ftprelayer
        self.mox.StubOutClassWithMocks(ftprelayer, 'Application')
        self.mox.StubOutWithMock(ftprelayer, 'log')
        app = ftprelayer.Application

        args = ['./ftprelayer', 'som_config']
        app.from_config(args[1]).AndReturn(app)
        ftprelayer.log.info("Starting app")
        app.start(True)
        app.stop()

        self.mox.ReplayAll()
        ftprelayer.main(args)

    def test_app_stops(self):
        import ftprelayer
        self.mox.StubOutClassWithMocks(ftprelayer, 'Application')
        self.mox.StubOutWithMock(ftprelayer, 'log')
        app = ftprelayer.Application

        args = ['./ftprelayer', 'som_config']
        app.from_config(args[1]).AndReturn(app)
        ftprelayer.log.info("Starting app")
        app.start(True).AndRaise(KeyboardInterrupt)
        ftprelayer.log.info("Stopping app")
        app.stop()

        self.mox.ReplayAll()
        ftprelayer.main(args)
