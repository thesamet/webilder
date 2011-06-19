#!/usr/bin/env python
'''
File    : webilder_gnome_applet.py
Author  : Nadav Samet
Contact : thesamet@gmail.com
Date    : 2011 May 7

Description : Webilder panel indicator for Ubuntu Unity.
'''
import pygtk
pygtk.require('2.0')
import pkg_resources

from webilder.base_applet import BaseApplet
from webilder.config import config
from webilder import AboutDialog
from webilder import config_dialog
from webilder import DownloadDialog
from webilder import __version__
from webilder import WebilderDesktop

import appindicator
import gio
import gobject
import gtk
import os
import sys


class WebilderUnityIndicator(BaseApplet):
    """Implementation for Webilder Unity panel indicator."""
    def __init__(self):
        BaseApplet.__init__(self)
        self.ind = appindicator.Indicator(
                "Webilder Indicator",
                os.path.abspath(
                    pkg_resources.resource_filename(__name__,
                                                    'ui/camera48.png')),
                appindicator.CATEGORY_APPLICATION_STATUS)
        self.ind.set_status(appindicator.STATUS_ACTIVE)
        propxml = """
    <popup name="button3">
        <menuitem name="Item 1" action="Browse"/>
        <menuitem name="Item 2" action="NextPhoto"/>
        <menuitem name="Item 3" action="Leech"/>
        <menuitem name="Item 6" action="DeleteCurrent"/>
        <menuitem name="Item 4" action="Pref"/>
        <menuitem name="Item 5" action="About"/>
        <menuitem name="Item 5" action="Quit"/>
    </popup>
    """
        uimanager = gtk.UIManager()
        uimanager.add_ui_from_string(propxml)
        action_group = gtk.ActionGroup("WebilderActions")
        action_group.add_actions([
             ("Pref", "gtk-preferences",  _("_Preferences"), "<control>P", 
              _("Open the preferences dialog"), self.preferences ),
             ("About", "gtk-about", _("_About"),  "<control>A", 
              _("About Webilder"), self.about),
             ("Browse", "gtk-directory", _("_Browse Photos"), "<control>B", 
              _("Browse your photo colleciton"), self.browse),
             ("NextPhoto", "gtk-go-forward", _("_Next Photo"), "<control>N",
              _("Switch wallpaper to the next photo"), self.next_photo),
             ("Leech", None, _("_Download Photos"), "<control>D",
              _("Download new photos"), self.leech),
             ("DeleteCurrent", "gtk-delete", _("Delete Current"), None,
              _("Delete the current photo from your collection"),
               self.delete_current),
             ("Quit", "gtk-quit", _("Quit"), None,
              _("Quit Webilder Desktop Indicator"),
               self.quit),
             ])
        leech_action = action_group.get_action("Leech")
        leech_action.set_gicon(gio.FileIcon(gio.File(
            pkg_resources.resource_filename(__name__,
                                            'ui/camera48.png'))))

        uimanager.insert_action_group(action_group, 0)

        menu = uimanager.get_widget('/button3')
        self.ind.set_menu(menu)

        gobject.timeout_add(60*1000, self.timer_event)
        self.photo_browser = None
        self.download_dlg = None

    def set_tooltip(self, text):
        """Sets the tooltip. Unimplemented for unity, see
        https://bugs.launchpad.net/indicator-application/+bug/527458"""

    def preferences(self, _action):
        """Opens the preferences dialog."""
        config_dialog.ConfigDialog().run_dialog(config)

    def about(self, _action):
        """Opens the about dialog."""
        AboutDialog.show_about_dialog(_('Webilder Applet'))

    def leech(self, _action):
        """Starts downloading photos."""
        def remove_reference(*_args):
            """Removes reference to the download dialog so we will not it is
            not running."""
            self.download_dlg = None

        if self.download_dlg:
            return
        self.download_dlg = DownloadDialog.DownloadProgressDialog(config)
        self.download_dlg.top_widget.connect('destroy', remove_reference)
        self.download_dlg.show()
        self.applet_icon.set_from_pixbuf(self.scaled_icon)

    def on_resize_panel(self, _widget, size):
        """Called when the panel is resized so we can scale our icon."""
        self.scaled_icon = self.icon.scale_simple(size - 4, size - 4,
            gtk.gdk.INTERP_BILINEAR)
        self.scaled_icon_green = self.icon_green.scale_simple(size - 4,
                                                              size - 4,
            gtk.gdk.INTERP_BILINEAR)
        self.applet_icon.set_from_pixbuf(self.scaled_icon)

    def browse(self, _action):
        """Opens the photo browser."""
        if not self.photo_browser:
            self.photo_browser = WebilderDesktop.WebilderDesktopWindow()
            self.photo_browser.top_widget.connect("destroy",
                                                  self.photo_browser_destroy)
        else:
            self.photo_browser.top_widget.show_all()

    def photo_browser_destroy(self, _action):
        """Called when the photo browser is closed."""
        self.photo_browser.destroy()
        self.photo_browser = None

    def quit(self, _action):
        """Called when the Quit menu item is chosen."""
        gtk.main_quit()


def main():
    """Entrypoint for the panel applet."""
    gtk.gdk.threads_init()
    ind = WebilderUnityIndicator()
    gtk.main()


if __name__ == "__main__":
    main()
