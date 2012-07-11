import pkg_resources
def import_string(s):
    if isinstance(s, basestring):
        return pkg_resources.EntryPoint.parse('x='+s).load(False)
    return s
