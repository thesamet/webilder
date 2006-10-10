#!/usr/bin/env python
"""Add a wbz to our collection"""

import sys
import os
from webshots import wbz
from webshots import wbp
import struct

import downloader
from config import config

def handle_wbz(wbzfile):
    f = wbz.open(wbzfile, 'r')
    handle_image(f)
    
def handle_image(img):
    metadata = img.get_metadata()
    title = (metadata.get('title') or metadata.get('STR_ImageTitle'))
    album = (metadata.get('albumTitle') or metadata.get('STR_CollectionTitle'))
    if not title:
        raise ValueError, "Unable to find image's title"
    if not album:
        raise ValueError, "Unable to find image's album"
        
    downloader.save_photo(config, 
            {'name': title+'.jpg'}, 
            img.get_image_data(),
            img.get_metadata())

    print "Extracted: %s/%s" % (album, title)

def handle_wbp(wbpfile):
    f = wbp.open(wbpfile, 'r')
    res = []
    return [handle_image(picture.image) for picture in f.pictures]
        

def handle_file(filename):
    f = open(filename, 'rb')
    magic, = struct.unpack('=L', f.read(4))
    f.close()
    if magic==wbz.WBZ_ID:
        handle_wbz(filename)
    elif magic==wbp.WBP_ID:
        handle_wbp(filename)
    else:
        raise IOError, "Unrecognized file type"
        
def main():
    if len(sys.argv)!=2:
        print """wbz_handler will extract webshots archives into your collection.

Usage:

    wbz_handler filename.wbz

Where filename.wbz is a Webshots archive."""
        sys.exit(1)
    handle_file(sys.argv[1])

if __name__=='__main__':
    main()
