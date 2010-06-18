'''
File    : AboutDialog.py
Author  : Nadav Samet
Contact : thesamet@gmail.com
Date    : 2010 Jun 17

Description : Controller for the about dialog.
'''

from webilder import __version__

import gtk
import pkg_resources


def show_about_dialog(name):
    """Shows the about dialog."""
    about = gtk.AboutDialog()
    about.set_name(name)
    about.set_version(__version__)
    about.set_copyright('Nadav Samet, 2005-2010')
    about.set_website('http://www.webilder.org')
    about.set_authors(['Nadav Samet <thesamet@gmail.com>'])
    about.set_translator_credits(
        'French by Nicolas ELIE <chrystalyst@free.fr>\n'
        'Alessio Leonarduzzi <alessio.leonarduzzi@gmail.com>')
    icon = gtk.gdk.pixbuf_new_from_file(
        pkg_resources.resource_filename(__name__, 'ui/camera48.png'))
    about.set_logo(icon),
    about.set_icon(icon),
    about.run()
    about.destroy()
