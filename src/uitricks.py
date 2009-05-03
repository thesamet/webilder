import gtk
import gtk.glade
import re

class UITricks:
    def __init__(self, gladefile, toplevel, controller = None):
        if controller is None:
            controller = self
        self._wTree = gtk.glade.XML(gladefile, toplevel)
        self._top = self._wTree.get_widget(toplevel)
        widgets = dict([(widget.get_name(),widget) for widget in 
            self._wTree.get_widget_prefix('')])
        for widget_name, widget in widgets.iteritems():
            setattr(self, widget_name, widget)
        for name in dir(controller):
            match = re.match('on_([a-zA-Z0-9_]+)__([a-zA-Z0-9_]+)', name)
            callback = getattr(controller, name)
            if match:
                widget, signal = match.groups()
                signal = signal.replace('_', '-')
                if widget in widgets:
                    widget = widgets[widget]
                    if signal=='selection-changed' and isinstance(widget, gtk.TreeView):
                        widget = widget.get_selection()
                        signal = 'changed'
                    widget.connect(signal, callback)
                else:
                    raise RuntimeWarning(_('Widget %s not found when trying to register callback %s') % (widget, name))

    def run(self):
        return self._top.run()

    def show(self):
        return self._top.show()

    def destroy(self):
        self._top.destroy()

def open_browser(url, no_browser_title, no_browser_markup):
    import os
    def _iscommand(cmd):
        """Return True if cmd can be found on the executable search path."""
        path = os.environ.get("PATH")
        if not path:
            return False
        for d in path.split(os.pathsep):
            exe = os.path.join(d, cmd)
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
        mb = gtk.MessageDialog(type=gtk.MESSAGE_INFO, buttons=gtk.BUTTONS_OK)
        mb.set_title(no_browser_title)
        mb.set_markup(no_browser_markup)
        mbval = mb.run()
        mb.destroy()
