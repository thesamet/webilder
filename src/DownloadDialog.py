#!/usr/bin/env python

import os
import gtk
import gtk.glade
import webilder_globals as aglobals
import threading

from uitricks import UITricks

class DownloadProgressDialog(UITricks):

    def __init__(self, config):
        self.config = config
        UITricks.__init__(self, os.path.join(aglobals.glade_dir, 'webilder.glade'), 'DownloadProgressDialog')
        self.start_leech()
                
    def on_DownloadProgressDialog__destroy(self, *args):
        if self.leech_thread:
            self.leech_thread.terminate.set()
        return False

    def on_closebutton__clicked(self, widget):
        self._top.destroy()
        self._top = None

    def start_leech(self):
        self.leech_thread = threading.Thread(
                    target=self.do_leech)
        self.leech_thread.setDaemon(True)
        self.leech_thread.terminate = threading.Event()
        self.leech_thread.start()

    def do_leech(self):
        try:
            import downloader
            import webshots
            try:    
                downloader.download_all(self.config, notify=self.status_notify, terminate = self.leech_thread.terminate.isSet)
            except webshots.utils.LeechHighQualityForPremiumOnlyError:
                gtk.gdk.threads_enter()
                mb = gtk.MessageDialog(type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK)
                mb.set_markup("<b>Only Webshots Premium members can download "
                                "wide or highest quality photos.</b>\n\n"
                                'Go to the Preferences window, choose "Regular Quality" and try again.')
                mbval = mb.run()
                mb.destroy()
                gtk.threads_leave()
            except webshots.utils.WBZLoginException:
                gtk.threads_enter()
                mb = gtk.MessageDialog(type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK)
                mb.set_markup("<b>Incorrect Webshots Username or Password</b>\n\n"
                                'Please check your username and password in the preferences dialog.')
                mbval = mb.run()
                mb.destroy()
                gtk.gdk.threads_leave()
            except (IOError, ValueError), e:
                gtk.gdk.threads_enter()
                markup="<b>Error occured while downloading images</b>\n\n%s" % html_escape(str(e))
                mb = gtk.MessageDialog(type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK)
                mb.set_markup(markup)
                mbval = mb.run()
                mb.destroy()
                gtk.gdk.threads_leave()
        finally:
            gtk.gdk.threads_enter()
            if self._top:
                self._top.destroy()
            gtk.gdk.threads_leave()
            print "Thread done"
            

    def status_notify(self, fraction, progress_text, status_text=''):
        gtk.gdk.threads_enter()
        try:
            if self._top:
                self.progressbar.set_fraction(fraction)
                self.progressbar.set_text(progress_text)
                self.statustext.set_markup('<i>%s</i>' % status_text)                
        finally:
            gtk.gdk.threads_leave()

def html_escape(text):
    """Produce entities within text."""
    L=[]
    for c in text:
        L.append(html_escape_table.get(c,c))
    return "".join(L)

html_escape_table = {
    "&": "&amp;",
    '"': "&quot;",
    "'": "&apos;",
    ">": "&gt;",
    "<": "&lt;",
    }

