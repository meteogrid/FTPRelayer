#coding=utf-8
import zipfile
import os.path
import datetime


def aemet_rename(path):
    u"""
    Renombra según reglas heredadas del Movedor de Jaime

        >>> processor = add_date_prefix('%Y_%m_')
        >>> processor.now = lambda: datetime.datetime(2007,3,1)
        >>> processor._new_name('foo')
        '2007_03_foo'
    """
    basename = os.path.basename(path)
    errors = []
    if os.path.getsize(path) == 0:
        errors.append('VACIO')
    if path.lower().endswith('.zip'):
        try:
            zf = zipfile.ZipFile(path, 'r')
            if zf.testzip():
                errors.append('ZIP_ERRONEO')
        except zipfile.BadZipfile:   
                errors.append('NO_ES_ZIP')
    if basename.startswith('10'):
        new_name = 'Algunos-SYNOPs-' + basename[4:6] + aemet_rename.now().strftime('-%Y-%m-%d-') \
                + basename[6:8] + '00.txt'
    elif basename.startswith('SYNOP'):
        new_name = 'S' + basename[5:6] + aemet_rename.now().strftime('-%Y-%m-%d-') \
            + basename[6:8] + '00.txt'
    elif basename.startswith('W'):
        new_name = basename[0:8] + aemet_rename.now().strftime('_%Y-%m-%d_%H-%M-%S') \
            + '.txt'
    elif basename.startswith('SYHOAU'):
        new_name = 'SHA' + aemet_rename.now().strftime('-%Y-%m-%d-') \
            + basename[6:8] + '00.txt'
    else:
        new_name = basename
    if errors:
        new_name += '.' + '.'.join(errors)
    with open(path) as f:
        yield new_name, f.read()

aemet_rename.now = datetime.datetime.utcnow # To mock in tests
