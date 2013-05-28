
from . import TestCaseWithMox

class TestCompositeUploader(TestCaseWithMox):
    def _makeOne(self, uploaders):
        from .. import CompositeUploader
        return CompositeUploader(uploaders)

    def test_delegates_to_uploaders(self):
        from .. import Uploader
        filename = 'some_filename'
        data = 'some_data'
        # Crea los mock y 'graba' las llamadas que espera que se hagan sobre
        # ellos
        up1 = self.mox.CreateMock(Uploader)
        up1.upload(filename, data)
        up2 = self.mox.CreateMock(Uploader)
        up2.upload(filename, data)
        self.mox.ReplayAll()
        ob = self._makeOne([up1, up2])
        ob.upload(filename, data)

    def test_if_one_uploader_fails_others_are_executed(self):
        from .. import Uploader
        filename = 'some_filename'
        data = 'some_data'
        # Crea los mock y 'graba' las llamadas que espera que se hagan sobre
        # ellos
        up1 = self.mox.CreateMock(Uploader)
        up1.upload(filename, data).AndRaise(RuntimeError)
        up2 = self.mox.CreateMock(Uploader)
        up2.upload(filename, data)
        self.mox.ReplayAll()
        ob = self._makeOne([up1, up2])
        ob.upload(filename, data)
