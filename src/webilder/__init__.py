import webshots
import flickr

#Gettext Support
import gettext, gtk.glade
import locale
import pkg_resources

locale.setlocale(locale.LC_ALL, '')

for module in (gtk.glade, gettext):
    gtk.glade.bindtextdomain('webilder', pkg_resources.resource_filename(__name__, 'locale'))
    gtk.glade.textdomain('webilder')

__version__ = '0.6.5'

gettext.install('webilder')
