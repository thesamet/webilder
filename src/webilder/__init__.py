'''
File    : __init__.py
Author  : Nadav Samet
Contact : thesamet@gmail.com
Date    : 2010 Jun 17

Description : Webilder package entrypoint. Exports the software version.
'''
import webilder.webshots
import webilder.flickr

#Gettext Support
import gettext, gtk.glade
import locale
import pkg_resources

locale.setlocale(locale.LC_ALL, '')

gtk.glade.bindtextdomain(
    'webilder',
    pkg_resources.resource_filename(__name__, 'locale'))
gtk.glade.textdomain('webilder')

__version__ = '0.6.8'

gettext.install('webilder')
