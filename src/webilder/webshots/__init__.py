'''
File    : __init__.py
Author  : Nadav Samet
Contact : thesamet@gmail.com
Date    : 2010 Jun 17

Description : Webilder webshots plugin package.
'''

from webilder.webshots.utils import get_download_list
from webilder.webshots.utils import get_photo_stream
from webilder.webshots.utils import process_photo

def fetch_photo_info(_config, _photo):
    """The photo info for webshots is embedded in the wbz arhchive. So this is
    a no op."""
