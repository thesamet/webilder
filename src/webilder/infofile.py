#!/usr/bin/env python

from webilder.webshots import wbz

def parse_info_file(filename):
    """Parses a info file, returns a dictionary representation.
    
    Returns an empty dictionary on error.
    """
    try:
        fileobj = open(info_file, 'r')
        inf = wbz.parse_metadata(fileobj.read())
    except IOError, e:
        print e
        inf = {}
    finally:
        fileobj.close()
        return inf
