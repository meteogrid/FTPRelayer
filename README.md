FTPRelayer
==========

Redistributes files which match a specified pattern via FTP or WebDAV,
optionally archiving them locally.

`inotify` is used to watch the filesystem so this should be efficient but only
available in `Linux` systems. 

[![Build Status](https://travis-ci.org/meteogrid/FTPRelayer.svg?branch=master)](https://travis-ci.org/meteogrid/FTPRelayer)

Basic Usage
-----------

A configuration might look like this:

```ini
[main]
archive_dir = /srv/ftp/relayed_items

[logging]
filename = /var/log/ftprelayer/ftprelayer.log
level    = INFO
  [[syslog]]
  address = localhost
  facility = ftprelayer

[relayers]
    [[some_relayer_name]]
    paths = /var/foo/*, /var/zoo/*, /var/car/*

        [[[uploader]]]
        use = ftp
        host = example.com
        username = pepe
        password = pepe2
```

This will upload any file which matches the wildcard patterns in the `paths`
section using FTP to `example.com` using the specified credentials.

Actions will be logged to the specified filename and also using syslog
to `localhost` using the `ftprelayer` facility

Pre-processors
--------------

Files may also be pre-processed before relaying them using a user-supplied
function:

```ini
[[some_relayer_name]]
paths = /var/car/*,

    [[[processor]]]
    use = ftprelayer.tests.test_app:processor_func

    [[[uploader]]]
    use = ftp
    host = example.com
    username = pepe
    password = pepe2
```

The processor function receives the absolute path of the file which was just
created and should yield a 2-tuple with the file name and the file contents,
optionally modifying them. Example:

```python
def processor_func(path):
    with open(path) as f:
        yield path, f.read()
```

An object can also be used as a processor if one may want to pass extra
arguments to it. For example:

```ini
[[[processor]]]
use = ftprelayer:add_prefix
prefix = foo
```

And the associated processor:

```python
class add_prefix(object):
    def __init__(self, prefix):
        self.prefix = prefix

    def __call__(self, path):
        new_name = self.prefix + os.path.basename(path)
        with open(path) as f:
            yield new_name, f.read()
```

Relaying to several machines
----------------------------

Several uploaders may be defined under the `composite` uploader:

```ini
[[some_relayer_name]]
paths = /var/car/*,
  [[[uploader]]]
      use = composite
    [[[[ftp1]]]]
        use = ftp
        host = example.com
        username = pepe
        password = pepe2
    [[[[ftp2]]]]
        use = ftp
        host = example2.com
        username = pepe2
        password = pepe22
```

WebDAV
------

A WebDAV uploder is also implemented:


```ini
[[some_relayer_name]]
paths = /var/car/*,
  [[[uploader]]]
      use = dav
      host = example.com
      username = pepe
      password = pepe2
```
