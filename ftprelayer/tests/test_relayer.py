import os
import tempfile
from . import TestCaseWithMox

class TestRelayer(TestCaseWithMox):
    def _makeOne(self, name='test', uploader=None, paths=None, processor=None):
        from .. import Relayer
        return Relayer(name, uploader, paths, processor)

    def test_process_without_processor(self):
        from .. import Uploader
        uploader = self.mox.CreateMock(Uploader)
        f = tempfile.NamedTemporaryFile()
        data = 'some data'
        f.write(data)
        f.flush()
        uploader.upload(os.path.basename(f.name), data)
        self.mox.ReplayAll()

        ob = self._makeOne(uploader=uploader)
        ob.process(f.name)
