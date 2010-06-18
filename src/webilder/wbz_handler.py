#!/usr/bin/env python
"""Add a wbz to our collection"""

from webilder.config import config
from webilder import downloader
from webilder.webshots import wbz
from webilder.webshots import wbp

import sys
import struct

def handle_wbz(wbzfile):
    """Imports the given wbz filename."""
    fileobj = wbz.open(wbzfile, 'r')
    handle_image(fileobj)

def handle_image(img):
    """Handled a parsed wbz object."""
    metadata = img.get_metadata()
    title = (metadata.get('title') or metadata.get('STR_ImageTitle'))
    album = (metadata.get('albumTitle') or metadata.get('STR_CollectionTitle'))
    if not title:
        raise ValueError, _("Unable to find image's title")
    if not album:
        raise ValueError, _("Unable to find image's album")

    downloader.save_photo(config,
            {'name': title+'.jpg'},
            img.get_image_data(),
            img.get_metadata())

    print _("Extracted: %s/%s") % (album, title)

def handle_wbp(wbpfile):
    """Imports the given wbp filename."""
    wbpfile = wbp.open(wbpfile, 'r')
    return [handle_image(picture.image) for picture in wbpfile.pictures]


def handle_file(filename):
    """Handles a filename. Checks whethers it is wbz or wbp."""
    fileobj = open(filename, 'rb')
    magic, = struct.unpack('=L', fileobj.read(4))
    fileobj.close()
    if magic == wbz.WBZ_ID:
        handle_wbz(filename)
    elif magic == wbp.WBP_ID:
        handle_wbp(filename)
    else:
        raise IOError, _("Unrecognized file type")

def main():
    """Command line interface to wbz_handler."""
    if len(sys.argv)!=2:
        print _(
        """wbz_handler will extract webshots archives into your collection.

Usage:

    wbz_handler filename.wbz

Where filename.wbz is a Webshots archive.""")
        sys.exit(1)
    handle_file(sys.argv[1])

if __name__ == '__main__':
    main()
