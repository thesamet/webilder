"""Library to parse WBZ and WBC files.

Usage:

Reading WBP files:
    f = wbp.open(file, 'r')
where file is either the name of a file or a file-like object which must
implement read() and seek().

This returns an instance of a class which have the following attributes:
    title               -- the collection title
    pictures            -- list of picture. See below.

    Each picture has the attributes as described in WBP_PicHeader_format.
    It also has an attribute 'image' which contains an object implementing
    the same interface of wbz files:

    get_metadata()     -- returns a dictionary containing image's metadata
    get_image_data()    -- returns a string with the image data
"""

__all__ = ["open", "WBPError"]


class WBPError(Exception):
    pass

import __builtin__
import struct
import time
import fileutil
import wbz

WBP_ID = 0x95FA16ABL
WBP_PIC_ID = 0xF071CDE2L

WBP_DirEntry_format = [('start', 'L'),
                        ('length', 'L'),
                        ('', 'L'),
                        ('data', 'L'),
                        ('copyrighted', 'L'),
                        ('', '20s')]

WBP_PicHeader_format = [('id', 'L'),
                        ('header_size', 'L'),
                        ('size', 'L'),
                        ('filename', '256s'),
                        ('title', '128s'),
                        ('description', '256s'),
                        ('credit', '256s'),
                        ('kind', '8s'),
                        ('pic_size', 'L'),
                        ('thumb_size', 'L'),
                        ('', 'L'), ('', '140s'),
                        ('date_added', 'L'),
                        ('fit_to_screen', 'L'),
                        ('image_pid', '1012s'),]

WBP_Header_format = [('id', 'L'),
                    ('first_pic', 'L'),
                    ('', 'L'),
                    ('title', '2184s'),
                    ('file_count', 'L'),]

class WBP_DirEntry(object):
    def unpack(fp):
        obj = WBP_DirEntry()
        fileutil.unpack(obj, WBP_DirEntry_format, fp)
        return obj
    unpack = staticmethod(unpack)

class WBP_PicHeader(object):
    def unpack(fp):
        obj = WBP_PicHeader()
        s = fileutil.unpack(obj, WBP_PicHeader_format, fp)
        if obj.id != WBP_PIC_ID:
            raise WBPError, "Invalid header"
        return obj
    unpack = staticmethod(unpack)

class WBP_Header(object):
    def unpack(fp):
        obj = WBP_Header()
        fileutil.unpack(obj, WBP_Header_format, fp)
        if obj.id != WBP_ID:
            raise WBPError, "Invalid header"
        obj.entries = [WBP_DirEntry.unpack(fp) for dummy in xrange(obj.file_count)]
        return obj
    unpack = staticmethod(unpack)

class WBP_Image(object):
    def __init__(self, imagedata, metadata):
        self.imagedata = imagedata
        self.metadata = metadata

    def get_image_data(self):
        return self.imagedata

    def get_metadata(self):
        return self.metadata

class WBP_read(object):
    def __init__(self, f):
        i_opened_the_file = None
        if isinstance(f, basestring):
            f = __builtin__.open(f, 'rb')
            i_opened_the_file = f
        # else, assume it is an open file object already

        self.header = WBP_Header.unpack(f)
        self.pictures = []
        for entry in self.header.entries:
            f.seek(entry.start)
            pic = WBP_PicHeader.unpack(f)
            data = wbz.decrypt(f.read(pic.size))
            pic.image = WBP_Image(data,
                dict(title=pic.title,
                     credit=pic.credit,
                     albumTitle=self.header.title))
            self.pictures.append(pic)

def open(f, mode=None):
    if mode is None:
        if hasattr(f, 'mode'):
            mode = f.mode
        else:
            mode = 'rb'
    if mode in ('r', 'rb'):
        return WBP_read(f)
    elif mode in ('w', 'wb'):
        raise NotImplementedError, "Writing wbp is not yet implemented"
    else:
        raise WBZError, "mode must be 'r', 'rb', 'w', or 'wb'"

def test():
    import sys
    h = open(sys.argv[1], 'r')
    for pic in h.pictures:
        d = pic.image.get_metadata()
        print (d['title'], d['albumTitle'], d['credit'])
        data = pic.image.get_image_data()
        assert(data[-2:] == '\xff\xd9')

if __name__ == "__main__":
    test()
