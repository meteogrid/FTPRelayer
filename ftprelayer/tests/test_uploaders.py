from mox import IgnoreArg, Func
from . import TestCaseWithMox


class TestFTPUploader(TestCaseWithMox):
    def _makeOne(self, host='host', username='foo', password=None, dir='/'):
        from .. import FTPUploader
        return FTPUploader(host, username, password, dir)
    
    def test_upload(self):
        from ftputil import FTPHost

        filename = 'some_file'
        data = 'some_data'
        host = 'host'
        username = 'uname'
        password = 'foo'
        remotedir = '/foo/bar'

        ob = self._makeOne(host, username, password, remotedir)
        ftp = ob.FTPHost = self.mox.CreateMock(FTPHost)

        # Graba acciones esperadas en el mock del FTPHost
        ftp(host, username, password).AndReturn(ftp)
        ftp.__enter__().AndReturn(ftp)
        ftp.makedirs(remotedir+'/')
        mockfile = self.mox.CreateMock(file)
        ftp.file(remotedir+'/'+filename, 'wb').AndReturn(mockfile)
        def verify_filecontent(f):
            return f.getvalue()==data
        ftp.copyfileobj(Func(verify_filecontent), mockfile)
        mockfile.close()
        ftp.__exit__(None, None, None)

        self.mox.ReplayAll()

        ob.upload(filename, data)
