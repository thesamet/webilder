import os
import gtk
import pkg_resources

from webilder import __version__

def ShowAboutDialog(name):
    about = gtk.AboutDialog()
    about.set_name(name)
    about.set_version(__version__)
    about.set_copyright('Nadav Samet, 2005-2009')
    about.set_website('http://www.webilder.org')
    about.set_authors(['Nadav Samet <thesamet@gmail.com>'])
    about.set_translator_credits("French by Nicolas ELIE <chrystalyst@free.fr>\nAlessio Leonarduzzi <alessio.leonarduzzi@gmail.com>")
    icon = gtk.gdk.pixbuf_new_from_file(
        pkg_resources.resource_filename(__name__, 'ui/camera48.png'))
    about.set_logo(icon),
    about.set_icon(icon),
    about.run()
    about.destroy()
