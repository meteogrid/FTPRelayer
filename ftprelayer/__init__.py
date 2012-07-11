from cStringIO import StringIO

from configobj import ConfigObj
from ftputil import FTPHost

from .util import import_string

class Application(object):
    def __init__(self, configfile):
        config = ConfigObj(configfile)
        self.relayers = list(self._iter_relayers(config['relayers']))

    def _iter_relayers(self, section):
        for name in section.sections:
            yield Relayer.from_config(name, section[name])

        

class Relayer(object):
    uploaders = {}
    default_uploader = "ftp"

    def __init__(self, name, uploader, paths, processor=None):
        self.name = name
        self.uploader = uploader
        self.paths = paths
        self.processor = processor

    @classmethod
    def from_config(cls, name, section):
        uploader = cls._make_uploader(section)
        return cls(name=name,
                   uploader=uploader,
                   paths=section.get('paths', []),
                   processor=import_string(section.get('processor')))


    @classmethod
    def _make_uploader(cls, section):
        cls = cls.uploaders[section.get('uploader', cls.default_uploader)]
        return cls.from_config(section)
        
        
                    
                   
        
        
class Uploader(object):
    def __init__(self, host, username, password=None, dir='/'):
        self.host = host
        self.username = username
        self.password = password
        self.dir = dir

    @classmethod
    def from_config(cls, section):
        return cls(section['host'], section['username'],
                   section.get('password'), section.get('dir','/'))
        
    def upload(self, filename, data):
        raise NotImplementedError("Abstract method must be overriden")

class FTPUploader(Uploader):
    FTPHost = FTPHost  # for mock inyection in tests

    def upload(self, filename, data):
        with self.FTPHost(self.host, self.username, self.password) as ftp:
            dir = self.dir.rstrip('/') + '/'
            ftp.makedirs(dir)
            dest = ftp.file(dir+filename, 'w')
            ftp.copyfileobj(StringIO(data), dest)
            dest.close()
Relayer.uploaders['ftp'] = FTPUploader

    
class SCPUploader(Uploader):
    pass
Relayer.uploaders['scp'] = SCPUploader
    

