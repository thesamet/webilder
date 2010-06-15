"""Handy tool for reading binary data from files into objects"""

__all__ = ['unpack']

import struct

def from_c_string(str):
    return str[:str.find('\x00')]

def unpack(self, fmt, fp):
    """unpack binary data from the file fp, formatted by fmt. fmt is a sequence
    of tuples of the form:
        attrname, datafmt

    for each tuple, a new attr in self will be created, containing data
    formatted according to datafmt. datafmt can contain exactly one format
    characted according to struct module documentation."""
    s_fmt = '=' + ''.join(data_fmt for name, data_fmt in fmt)
    size = struct.calcsize(s_fmt)
    values = struct.unpack(s_fmt, fp.read(size))
    for (name, data_fmt), value in zip(fmt, values):
        if name:
            if isinstance(value, str):
                value = from_c_string(value)
            setattr(self, name, value)
    return size
