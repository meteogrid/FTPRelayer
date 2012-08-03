import sys
import Queue
import datetime
import os
import logging
import shutil
from cStringIO import StringIO
from threading import Thread, Event
from fnmatch import fnmatchcase

import validate
from configobj import ConfigObj
from ftputil import FTPHost
from pkg_resources import resource_filename
import pyinotify

from .util import import_string

log = logging.getLogger(__name__)

LOG_FORMAT = "%(asctime)s %(process)d %(levelname)-5.5s [%(name)s] %(message)s"

class Application(object):
    _watch_mask = (pyinotify.IN_CLOSE_WRITE | pyinotify.IN_MOVED_TO)
    configspec_filename = resource_filename(__name__, 'configspec.ini')

    now = datetime.datetime.now # To mock in tests

    def __init__(self, archive_dir=None):
        self._relayers = []
        self._wm = pyinotify.WatchManager()
        self._notifier = pyinotify.ThreadedNotifier(self._wm)
        self._queue_processor = Thread(target=self._process_queue)
        self._queue = Queue.Queue()
        self._stopping = Event()
        self._archive_dir = archive_dir

    @classmethod
    def from_config(cls, configfile):
        spec = ConfigObj(cls.configspec_filename, list_values=False,
                         _inspec=True)
        config = ConfigObj(configfile, configspec=spec)
        if config.validate(validate.Validator()) is not True:
            raise AssertionError("Config is not valid")
        cls._setup_logging(config['logging'])
        self = cls(**dict(config['main']))
        for r in self._relayers_from_config(config['relayers']):
            self.add_relayer(r)
        return self
    
    @classmethod
    def _setup_logging(cls, config):
        logging.basicConfig(
            level = getattr(logging, config['level']),
            filename = config['filename'],
            mode = 'a+',
            stream = sys.stderr if not config['filename'] else None,
            format = LOG_FORMAT,
            )


    def _relayers_from_config(self, section):
        for name in section.sections:
            yield Relayer.from_config(name, section[name])

    def start(self, block=False):
        self._notifier.start()
        self._queue_processor.start()
        if block:
            while True:
                self._stopping.wait(1)


    def stop(self):
        self._stopping.set()
        self._notifier.stop()
        self._queue_processor.join()
        
    def add_relayer(self, relayer):
        self._relayers.append(relayer)
        for p in relayer.paths:
            self._add_watch(relayer, p)

    def _add_watch(self, relayer, path):
        proc_fun = _EventProcessor(self._queue, relayer)
        self._wm.add_watch(os.path.dirname(path), self._watch_mask,
                           proc_fun=proc_fun)

    def _process_queue(self):
        while not self._stopping.isSet():
            try:
                relayer, path = self._queue.get(True, .5)
            except Queue.Empty:
                pass
            else:
                try:
                    relayer.process(path)
                    if self._archive_dir is not None:
                        self._archive(relayer, path)
                except:
                    log.exception("When processing %r, %r", relayer.name, path)

    def _archive(self, relayer, path):
        dest = self._archive_path(relayer, path)
        destdir = os.path.dirname(dest)
        if not os.path.exists(destdir):
            os.makedirs(destdir)
        destpath = self._archive_path(relayer, path)
        log.info("Archiving %s -> %s", path, destpath)
        shutil.move(path, destpath)

    def _archive_path(self, relayer, path):
        subdir = os.path.join(self._archive_dir, relayer.name,
                              self.now().strftime('%Y/%m/%d'))
        return os.path.join(subdir, relayer.relpathto(path))
        
        

class _EventProcessor(pyinotify.ProcessEvent):
    def __init__(self, queue, relayer):
        self.queue = queue
        self.relayer = relayer
        super(_EventProcessor, self).__init__()

    def _process(self, event):
        log.debug("got event: %r", event)
        if self.relayer.path_matches(event.pathname):
            self.queue.put((self.relayer, event.pathname))

    process_IN_CLOSE_WRITE = _process
    process_IN_MOVED_TO = _process


class Relayer(object):
    uploaders = {}

    def __init__(self, name, uploader, paths, processor=None):
        self.name = name
        self.uploader = uploader
        self.paths = paths
        self.processor = processor

    @classmethod
    def from_config(cls, name, section):
        uploader = cls._make_uploader(section['uploader'])
        processor = cls._make_processor(section['processor'])
        return cls(name=name,
                   paths=section['paths'],
                   uploader=uploader,
                   processor=processor)


    @classmethod
    def _make_uploader(cls, section):
        cls = cls.uploaders[section['use']]
        return cls.from_config(_extra_values(section))

    @classmethod
    def _make_processor(cls, section):
        cls_or_func = import_string(section['use'])
        if section.extra_values:
            return cls_or_func(**_extra_values(section))
        else:
            return cls_or_func
        
        
    def path_matches(self, path):
        return any(fnmatchcase(path, p) for p in self.paths)

    def relpathto(self, path):
        base = os.path.commonprefix(self.paths+[path])
        return os.path.relpath(path, base)
        
    def process(self, path):
        log.info("Relayer '%s' processing '%s'", self.name, path)
        if self.processor is not None:
            self._process_with_processor(path)
        else:
            self._process_without_processor(path)
                    
    def _process_with_processor(self, path):
        for filename, data in self.processor(path):
            self.uploader.upload(filename, data)
                   
    def _process_without_processor(self, path):
        with open(path) as f:
            self.uploader.upload(os.path.basename(path), f.read())
                   
def _extra_values(section):
    return dict((k, section[k]) for k in section.extra_values)
        
        
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
            destname = dir + filename
            dest = ftp.file(destname, 'wb')
            log.info("FTPUploader.upload: %s -> %s", filename, destname)
            ftp.copyfileobj(StringIO(data), dest)
            dest.close()
Relayer.uploaders['ftp'] = FTPUploader

    
class SCPUploader(Uploader):
    pass
Relayer.uploaders['scp'] = SCPUploader


class add_prefix(object):
    def __init__(self, prefix):
        self.prefix = prefix

    def __call__(self, path):
        new_name = self.prefix + os.path.basename(path)
        with open(path) as f:
            yield new_name, f.read()

def main():
    if len(sys.argv)<2:
        print>>sys.stderr, "Usage %s <configfile>"%sys.argv[0]
        sys.exit(-1)
    app = Application.from_config(sys.argv[1])
    try:
        log.info("Starting app")
        app.start(True)
    except (KeyboardInterrupt, SystemExit):
        log.info("Stopping app")
        app.stop()
    else:
        app.stop()
