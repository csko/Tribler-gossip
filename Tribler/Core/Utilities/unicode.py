# Written by Arno Bakker
# see LICENSE.txt for license information

import sys

def bin2unicode(bin,possible_encoding='utf_8'):
    sysenc = sys.getfilesystemencoding()
    if possible_encoding is None:
        possible_encoding = sysenc
    try:
        return bin.decode(possible_encoding)
    except:
        try:
            if possible_encoding == sysenc:
                raise
            return bin.decode(sysenc)
        except:
            try:
                return bin.decode('utf_8')
            except:
                try:
                    return bin.decode('iso-8859-1')
                except:
                    try:
                        return bin.decode(sys.getfilesystemencoding())
                    except:
                        return bin.decode(sys.getdefaultencoding(), errors = 'replace')


def str2unicode(s):
    try:
        s = unicode(s)
    except: 
        flag = 0
        for encoding in [sys.getfilesystemencoding(), 'utf_8', 'iso-8859-1', 'unicode-escape' ]:
            try:
                s = unicode(s, encoding)
                flag = 1
                break
            except: 
                pass
        if flag == 0:
            try:
                s = unicode(s,sys.getdefaultencoding(), errors = 'replace')
            except:
                pass
    return s

def dunno2unicode(dunno):
    newdunno = None
    if isinstance(dunno,unicode):
        newdunno = dunno
    else:
        try:
            newdunno = bin2unicode(dunno)
        except:
            newdunno = str2unicode(dunno)
    return newdunno


def metainfoname2unicode(metadata):
    if metadata['info'].has_key('name.utf-8'):
        namekey = 'name.utf-8'
    else:
        namekey = 'name'
    if metadata.has_key('encoding'):
        encoding = metadata['encoding']
        name = bin2unicode(metadata['info'][namekey],encoding)
    else:
        name = bin2unicode(metadata['info'][namekey])

    return (namekey,name)


def unicode2str(s):
    if not isinstance(s,unicode):
        return s
    return s.encode(sys.getfilesystemencoding())