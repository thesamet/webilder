#!/usr/bin/env python

from webilder.webshots import wbz

def parse_info_file(info_file):
    """Parses a info file, returns a dictionary representation.

    Returns an empty dictionary on error.
    """
    try:
        fileobj = open(info_file, 'r')
        try:
            inf = wbz.parse_metadata(fileobj.read())
        finally:
            fileobj.close()
    except IOError, e:
        inf = {}
    return inf
