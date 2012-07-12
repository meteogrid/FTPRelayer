import Queue
import os
import logging
from cStringIO import StringIO
from threading import Thread, Event

from configobj import ConfigObj
from ftputil import FTPHost
import pyinotify

from .util import import_string

log = logging.getLogger(__name__)

class Application(object):
    _watch_mask = (pyinotify.IN_CLOSE_WRITE | pyinotify.IN_MOVED_TO)

    def __init__(self):
        self._relayers = []
        self._wm = pyinotify.WatchManager()
        self._notifier = pyinotify.ThreadedNotifier(self._wm)
        self._queue_processor = Thread(target=self._process_queue)
        self._queue = Queue.Queue()
        self._stopping = Event()

    @classmethod
    def from_config(cls, configfile):
        config = ConfigObj(configfile)
        self = cls()
        for r in self._relayers_from_config(config['relayers']):
            self.add_relayer(r)
        return self

    def _relayers_from_config(self, section):
        for name in section.sections:
            yield Relayer.from_config(name, section[name])

    def start(self):
        self._notifier.start()
        self._queue_processor.start()


    def stop(self):
        self._stopping.set()
        self._notifier.stop()
        
    def add_relayer(self, relayer):
        self._relayers.append(relayer)
        for p in relayer.paths:
            proc_fun = _EventProcessor(self._queue, relayer)
            self._wm.add_watch(p, self._watch_mask, proc_fun=proc_fun)

    def _process_queue(self):
        while not self._stopping.isSet():
            try:
                relayer, path = self._queue.get(True, .5)
            except Queue.Empty:
                pass
            else:
                try:
                    relayer.process(path)
                except:
                    log.exception("In Relayer.process %r", relayer)

class _EventProcessor(pyinotify.ProcessEvent):
    def __init__(self, queue, relayer):
        self.queue = queue
        self.relayer = relayer
        super(_EventProcessor, self).__init__()

    def _process(self, event):
        log.debug("got event: %r", event)
        self.queue.put((self.relayer, event.pathname))

    process_IN_CLOSE_WRITE = _process
    process_IN_MOVED_TO = _process


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
        
        
    def process(self, path):
        #TODO
        pass
                    
                   
        
        
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
    

