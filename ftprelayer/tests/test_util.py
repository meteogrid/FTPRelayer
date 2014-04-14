import os
from unittest import TestCase
import tempfile
import zipfile
from StringIO import StringIO

class Test_add_prefix_to_zip_contents(TestCase):
    def _makeOne(self, *args):
        from .. import add_prefix_to_zip_contents
        return add_prefix_to_zip_contents(*args)

    def test_adds_prefix(self):
        f = tempfile.NamedTemporaryFile()
        zip = zipfile.ZipFile(f.name, 'w')
        files = [
            ('a', 'data'),
            ('b', 'datab'),
        ]
        for fname, data in files:
            zip.writestr(fname, data)
        zip.close()

        prefix = 'some_prefix'
        sut = self._makeOne(prefix)

        ret_files = list(sut(f.name))
        self.failUnlessEqual(1, len(ret_files))
        self.failUnlessEqual(os.path.basename(f.name), ret_files[0][0])
        zfile = zipfile.ZipFile(StringIO(ret_files[0][1]))
        self.failUnlessEqual(len(files), len(zfile.filelist))
        for f in zfile.filelist:
            self.failUnless(f.filename.startswith(prefix))

class Test_rename_predictia(TestCase):
    def _callSUT(self, *args):
        from .. import rename_predictia
        return rename_predictia(*args)

    def test_it_renames(self):
        old = 'oper_d01_2014032700_2014033000.nc'
        self.failUnlessEqual(self._callSUT(old), 'oper_d01_2014032700.nc')
