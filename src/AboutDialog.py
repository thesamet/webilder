import os
import gtk
import webilder_globals as aglobals

def ShowAboutDialog(name):
    about = gtk.AboutDialog()
    about.set_name(name)
    about.set_version(aglobals.version)
    about.set_copyright('Nadav Samet, 2005-2009')
    about.set_website('http://www.webilder.org')
    about.set_authors(['Nadav Samet <thesamet@gmail.com>'])
    about.set_translator_credits("French by Nicolas ELIE <chrystalyst@free.fr>\nAlessio Leonarduzzi <alessio.leonarduzzi@gmail.com>")
    icon = gtk.gdk.pixbuf_new_from_file(
        os.path.join(aglobals.glade_dir, 'camera48.png'))
    about.set_logo(icon),
    about.set_icon(icon),
    about.run()
    about.destroy()
