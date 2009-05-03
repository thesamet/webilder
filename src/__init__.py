import webilder_globals as aglobals
import webshots
import flickr

#Gettext Support
import gettext, gtk.glade
import locale
 
locale.setlocale(locale.LC_ALL, '')

for module in (gtk.glade, gettext):
    gtk.glade.bindtextdomain('webilder', aglobals.locale_dir)
    gtk.glade.textdomain('webilder')


gettext.install('webilder')

