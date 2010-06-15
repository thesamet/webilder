import threading, os
import gtk

import pkg_resources
import uitricks

class ProgressDialog(uitricks.UITricks):
    def __init__(self, text='', statustext=''):
        uitricks.UITricks.__init__(self, 'ui/webilder.glade', 'ProgressDialog')
        self.statustext.set_markup(statustext)
        self.text.set_markup(text)
        self._thread = None
        self._terminate = threading.Event()

    def should_terminate(self):
        return self._terminate.isSet()

    def on_closebutton__clicked(self, widget):
        self._terminate.set()
        self._top.destroy()
        self._top = None

    def on_ProgressDialog__destroy(self, *args):
        self._terminate.set()
        self._top = None
        return False

    def on_closebutton__clicked(self, widget):
        self._top.destroy()
        self._top = None


def progress_thread_run(func):
    def newfunc(self, *args, **kwargs):
        try:
            func(self, *args, **kwargs)
        finally:
            gtk.gdk.threads_enter()
            if self._pdialog._top:
                self._pdialog._top.destroy()
            print _("Thread done")
            gtk.gdk.threads_leave()
    return newfunc

class ProgressThread(threading.Thread):
    def __init__(self, pdialog):
        threading.Thread.__init__(self)
        self._pdialog = pdialog
        self.setDaemon(True)

    def should_terminate(self):
        return self._pdialog.should_terminate()

    def run(self):
        raise NotImplementedError

    def status_notify(self, fraction, progress_text, status_text=''):
        gtk.gdk.threads_enter()
        try:  # coupling...
            if self._pdialog._top:
                self._pdialog.progressbar.set_fraction(fraction)
                self._pdialog.progressbar.set_text(progress_text)
                self._pdialog.statustext.set_markup('<i>%s</i>' % status_text)                
        finally:
            gtk.gdk.threads_leave()

    def safe_message_dialog(self, markup, type=gtk.MESSAGE_ERROR):
        gtk.gdk.threads_enter()
        mb = gtk.MessageDialog(type=type, buttons=gtk.BUTTONS_OK)
        mb.set_markup(markup)
        mbval = mb.run()
        mb.destroy()
        gtk.gdk.threads_leave()

