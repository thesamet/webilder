'''
File    : uitricks.py
Author  : Nadav Samet
Contact : thesamet@gmail.com
Date    : 2010 Jun 17

Description : Base class for Glade XML based controllers.
'''
import pkg_resources
import gtk
import gtk.glade
import re

import gettext
import locale
import pkg_resources

locale.setlocale(locale.LC_ALL, '')

gtk.glade.bindtextdomain(
    'webilder',
    pkg_resources.resource_filename(__name__, 'locale'))
gtk.glade.textdomain('webilder')

gettext.install('webilder')

class UITricks:
    """Base class for Glade XML based controllers."""

    def __init__(self, gladefile, toplevel, controller = None):
        """Loads a glade file and connects signal handlers to widgets."""
        if controller is None:
            controller = self
        widget_tree = gtk.glade.XML(
            pkg_resources.resource_filename(__name__,
            gladefile), toplevel)
        self.top_widget = widget_tree.get_widget(toplevel)
        widgets = dict([(widget.get_name(), widget) for widget in
            widget_tree.get_widget_prefix('')])
        for widget_name, widget in widgets.iteritems():
            setattr(self, widget_name, widget)
        for name in dir(controller):
            match = re.match('on_([a-zA-Z0-9_]+)_handle_([a-zA-Z0-9_]+)', name)
            callback = getattr(controller, name)
            if match:
                widget, signal = match.groups()
                signal = signal.replace('_', '-')
                if widget in widgets:
                    widget = widgets[widget]
                    if (signal == 'selection-changed' and
                        isinstance(widget, gtk.TreeView)):
                        widget = widget.get_selection()
                        signal = 'changed'
                    widget.connect(signal, callback)
                else:
                    raise RuntimeWarning(
                      _('Widget %s not found when trying to register '
                        'callback %s') % (widget, name))

    def run(self):
        """Calls run() of the top widget."""
        return self.top_widget.run()

    def show(self):
        """Calls show() of the top widget."""
        return self.top_widget.show()

    def destroy(self):
        """Calls top_widget() of the top widget."""
        self.top_widget.destroy()

def open_browser(url, no_browser_title, no_browser_markup):
    """Opens a webbrowser with the given URL."""
    import os
    def _iscommand(cmd):
        """Return True if cmd can be found on the executable search path."""
        path = os.environ.get("PATH")
        if not path:
            return False
        for dirname in path.split(os.pathsep):
            exe = os.path.join(dirname, cmd)
            if os.path.isfile(exe):
                return True
        return False

    if _iscommand('gnome-open'):
        os.system('gnome-open %s' % url)
    elif _iscommand('kfmclient'):
        os.system('kfmclient openURL %s' % url)
    elif _iscommand('firefox'):
        os.system('firefox %s' % url)
    elif _iscommand('mozilla-firefox'):
        os.system('mozilla-firefox %s' % url)
    else:
        mbox = gtk.MessageDialog(type=gtk.MESSAGE_INFO, buttons=gtk.BUTTONS_OK)
        mbox.set_title(no_browser_title)
        mbox.set_markup(no_browser_markup)
        mbox.run()
        mbox.destroy()
