#!/usr/bin/env python
"""Library to parse WBZ and WBC files.

Usage:

Reading WBZ files:
    f = wbz.open(file, 'r')
where file is either the name of a file or a file-like object which must 
implement read() and seek()

This returns an instance of a class with the following public methods:
    get_metadata()     -- returns a dictionary containing image's metadata
    get_image_data()    -- returns a string with the image data
"""

__all__ = ["open", "WBZError"]

JPEG_START = "\xff\xd8\xff\xe0"
JPEG_END = "\xff\xd9"
META_WBX = "info.wbx"

WBZ_PIC_ID = 0x1082CDE1L
WBZ_ID     = 0x6791AB43L;

import fileutil

class WBZError(Exception):
    pass

WBZ_PicHeader_format = [
    ('id', 'L'),
    ('header_size', 'L'),
    ('', 'L'),
    ('filename', '256s'),
    ('data_size', 'L'),
    ('', 'L'),
    ('data_size2', 'L'),
    ('', '256s')]
    
WBZ_Header_format = [
    ('id', 'L'),
    ('first_pic', 'L'),
    ('', 'L'),
    ('file_count', 'L'),
    ('entry_size', 'L'),
    ('_maybe_count_of_picheader', 'L'),
    ('', '128s')]


class WBZ_Header(object):
    def unpack(fp):
        obj = WBZ_Header()
        fileutil.unpack(obj, WBZ_Header_format, fp)
        if obj.id != WBZ_ID:
            raise WBZError, "Corrupted WBZ header"
        return obj
    unpack = staticmethod(unpack)

class WBZ_PicHeader(object):
    def unpack(fp):
        obj = WBZ_PicHeader()
        fileutil.unpack(obj, WBZ_PicHeader_format, fp)
        if obj.id != WBZ_PIC_ID:
            raise WBZError, "Corrupted WBZ header"
        return obj
    unpack = staticmethod(unpack)
        
class WBZ_read:
    def __init__(self, f):
        i_opened_the_file = None
        if isinstance(f, basestring):
            f = file(f, 'rb')
            i_opened_the_file = f
        # else, assume it is an open file object already
        self.header = WBZ_Header.unpack(f)
        if self.header.file_count != 1:
            raise WBZError, """I don't know yet how to handle WBZ with more than 
one file. please sent this file to me."""
        f.seek(self.header.first_pic)
        self.pic_header = WBZ_PicHeader.unpack(f)
        self._data = f.read(self.pic_header.data_size)
        self._data = decrypt(self._data)
        info_header = WBZ_PicHeader.unpack(f)
        info_file = f.read(info_header.data_size)
        self._info = parse_metadata(info_file)

        if i_opened_the_file:
            f.close()

    def get_metadata(self):
        return self._info
            
    def get_image_data(self):
        return self._data
                
def open(f, mode=None):
    if mode is None:
        if hasattr(f, 'mode'):
            mode = f.mode
        else:
            mode = 'rb'
    if mode in ('r', 'rb'):
        return WBZ_read(f)
    elif mode in ('w', 'wb'):
        raise NotImplementedError, "Writing wbz is not yet implemented"
    else:
        raise WBZError, "mode must be 'r', 'rb', 'w', or 'wb'"

# "decryption" methods:

def XOR_decrypt(key, data):            
    m_a, m_b = map(ord, data[:100]), map(ord, data[100:200])
    data = (''.join([chr(a^b^key^0xff) for a,b in zip(m_a,m_b)]) + 
            data[100:])
    return data

def NOT_decrypt(data):
    return ''.join([chr(255-ord(c)) for c in data[:100]])+data[100:]


def decrypt(data):
    """Decrypts wbz data."""
    dec_type = data[:8]
    if dec_type == 'WWBB0000':
        data = XOR_decrypt(0xa4, data[8:])
    elif dec_type == 'WWBB1111':
        data = XOR_decrypt(0xf2, data[8:])
    elif dec_type == 'SSPPVV00':
        data = NOT_decrypt(data[8:])
    else:
        pass # probably (i hope) raw file
    return data


def parse_metadata(metastr):
    import re
    metastr=metastr.replace('\r\n', '\n')
    return dict(re.findall('^(.*)=(.*)\n', metastr, 
        flags=re.MULTILINE))

def test():
    import sys
    f = open(sys.argv[1])
    print f.get_metadata()
    assert f.get_image_data()[-2:]=='\xff\xd9'
    
if __name__ == "__main__":
    test()
    
