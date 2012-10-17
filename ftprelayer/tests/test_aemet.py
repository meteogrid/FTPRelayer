#coding=utf-8
import os
import tempfile
from . import TestCaseWithMox
import zipfile
import datetime
from tempfile import tempdir
import shutil

class TestRelayer(TestCaseWithMox):
    def _makeOne(self, name='test', uploader=None, paths=None, processor=None):
        from ..aemet import aemet_rename
        return aemet_rename

    def test_zip_ok(self):
        f = tempfile.NamedTemporaryFile(suffix='.zip')
        zf = zipfile.ZipFile(f.name, 'w')
        files = [
            ('a', 'data'),
            ('b', 'datab'),
        ]
        for fname, data in files:
            zf.writestr(fname, data)
        zf.close()
        sut = self._makeOne()

        ret_files = list(sut(f.name))
        self.failUnlessEqual(1, len(ret_files))
        self.failUnlessEqual(os.path.basename(f.name), ret_files[0][0])

    def test_zip_not_ok(self):
        f = tempfile.NamedTemporaryFile(suffix='.zip')
        zf = zipfile.ZipFile(f.name, 'w')
        files = [
            ('a', 'data'),
            ('b', 'datab'),
        ]
        for fname, data in files:
            zf.writestr(fname, data)
            zf.fp.seek(-3, os.SEEK_END) # Provoca corrupción
        zf.close()
        sut = self._makeOne()

        ret_files = list(sut(f.name))
        self.failUnlessEqual(1, len(ret_files))
        self.failUnlessEqual(os.path.basename(f.name) + '.ZIP_ERRONEO',
                             ret_files[0][0])

    def test_zip_not_zip(self):
        sut = self._makeOne()
        f = tempfile.NamedTemporaryFile(suffix='.zip')
        f.write('not a zip file')
        f.seek(0)
        ret_files = list(sut(f.name))
        self.failUnlessEqual(1, len(ret_files))
        self.failUnlessEqual(os.path.basename(f.name) + '.NO_ES_ZIP', ret_files[0][0])

    def test_algunos_synop(self):
        f = tempfile.NamedTemporaryFile(prefix='10123456')
        f.write('algo')
        f.seek(0)
        sut = self._makeOne()
        sut.now = lambda: datetime.datetime(2010,11,12,13,14)
        ret_files = list(sut(f.name))
        self.failUnlessEqual(1, len(ret_files))
        self.failUnlessEqual('Algunos-SYNOPs-34-2010-11-12-5600.txt', ret_files[0][0])

    def test_synop(self):
        f = tempfile.NamedTemporaryFile(prefix='SYNOP1234567')
        f.write('algo')
        f.seek(0)
        sut = self._makeOne()
        sut.now = lambda: datetime.datetime(2010,11,12,13,14)
        ret_files = list(sut(f.name))
        self.failUnlessEqual(1, len(ret_files))
        self.failUnlessEqual('S1-2010-11-12-2300.txt', ret_files[0][0])

    def test_syhoau(self):
        f = tempfile.NamedTemporaryFile(prefix='SYHOAU1234567')
        f.write('algo')
        f.seek(0)
        sut = self._makeOne()
        sut.now = lambda: datetime.datetime(2010,11,12,13,14)
        ret_files = list(sut(f.name))
        self.failUnlessEqual(1, len(ret_files))
        self.failUnlessEqual('SHA-2010-11-12-1200.txt', ret_files[0][0])

    def test_w(self):
        f = tempfile.NamedTemporaryFile(prefix='W12345678')
        f.write('algo')
        f.seek(0)
        sut = self._makeOne()
        sut.now = lambda: datetime.datetime(2010,11,12,13,14)
        ret_files = list(sut(f.name))
        self.failUnlessEqual(1, len(ret_files))
        self.failUnlessEqual('W1234567_2010-11-12_13-14-00.txt', ret_files[0][0])

class TestEosUploader(TestCaseWithMox):
    def _makeOne(self, destinations):
        from .. import EosUploader
        sut = EosUploader(destinations)
        sut.now = lambda: datetime.datetime(2010,11,12,13,14)
        return sut

    def test_upload(self):
        dtemp = tempfile.mkdtemp()
        try:
            dest1 = os.path.join(dtemp, 'aa')
            os.makedirs(dest1)
            open(os.path.join(dest1,'xx',), 'wb').write('data')
            
            dest2 = os.path.join(dtemp, 'bb')
            os.makedirs(dest2)
            open(os.path.join(dest2,'xx'), 'wb').write('otro')
            
            dest3 = os.path.join(dtemp, 'cc')

            destinations = [dest1, dest2, dest3]
            uploader = self._makeOne(destinations)
            uploader.upload('xx', 'data')
            for dest in destinations:
                self.failUnlessEqual(open(os.path.join(dest,'xx')).read(), 'data')
            self.failUnlessEqual(open(os.path.join(dest2,'xx.OTRO_POSTERIOR 2010-11-12_13-14-00')).read(), 'otro')
        finally:
            shutil.rmtree(dtemp)