'''
File    : progress_dialog.py
Author  : Nadav Samet
Contact : thesamet@gmail.com
Date    : 2010 Jun 17

Description : Download that tracks download progess.
'''

from webilder import uitricks
import threading
import gtk


class ProgressDialog(uitricks.UITricks):
    """Controller for progress dialog."""
    def __init__(self, text='', statustext=''):
        uitricks.UITricks.__init__(self, 'ui/webilder.glade', 'ProgressDialog')
        self.statustext.set_markup(statustext)
        self.text.set_markup(text)
        self._thread = None
        self._terminate = threading.Event()

    def should_terminate(self):
        """Sets a flag indicating that the dialog should be closed."""
        return self._terminate.isSet()

    # pylint: disable=C0103
    def on_closebutton_handle_clicked(self, _widget):
        """Called when the close button is called."""
        self._terminate.set()
        self.top_widget.destroy()
        self.top_widget = None

    def on_ProgressDialog_handle_destroy(self, *_args):
        """Called when the window is destroyed."""
        self._terminate.set()
        self.top_widget = None
        return False


def progress_thread_run(func):
    """Decorator for the working functions."""
    def newfunc(self, *args, **kwargs):
        """Wrapper function."""
        # pylint: disable=W0212
        try:
            func(self, *args, **kwargs)
        finally:
            gtk.gdk.threads_enter()
            if self._pdialog.top_widget:
                self._pdialog.top_widget.destroy()
            print _("Thread done")
            gtk.gdk.threads_leave()
    return newfunc

class ProgressThread(threading.Thread):
    """Represents a thread that whose progress is monitored."""
    def __init__(self, pdialog):
        threading.Thread.__init__(self)
        self._pdialog = pdialog
        self.setDaemon(True)

    def should_terminate(self):
        """Returns whether the thread should terminate."""
        return self._pdialog.should_terminate()

    def run(self):
        """Should be implemented by derived classes."""
        raise NotImplementedError

    def status_notify(self, fraction, progress_text, status_text=''):
        """Updates the GUI with the given progress."""
        gtk.gdk.threads_enter()
        try:  # coupling...
            if self._pdialog.top_widget:
                self._pdialog.progressbar.set_fraction(fraction)
                self._pdialog.progressbar.set_text(progress_text)
                self._pdialog.statustext.set_markup('<i>%s</i>' % status_text)
        finally:
            gtk.gdk.threads_leave()

    def safe_message_dialog(self, markup, msgtype=gtk.MESSAGE_ERROR):
        """Shows a popup message (avoids a threading pitfall here.)"""
        gtk.gdk.threads_enter()
        mbox = gtk.MessageDialog(type=msgtype, buttons=gtk.BUTTONS_OK)
        mbox.set_markup(markup)
        mbox.run()
        mbox.destroy()
        gtk.gdk.threads_leave()
