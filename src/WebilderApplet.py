#!/usr/bin/env python
import pygtk
pygtk.require('2.0')

import sys
import os
import time
import glob
import gtk
import gnomeapplet
import gnome
import gobject
import random
import webilder_globals as aglobals
import urllib

from config import config, set_wallpaper

# Set this to False if you don't want the software to check
# for updates.
#
# No information, except of the version request itself is sent 
# to Webilder's server.

CHECK_FOR_UPDATES = True
CHECK_URL = 'http://www.thesamet.com/webilder/latest.html'

random.seed()

class WebilderApplet:
    def __init__(self, applet, iid):
        gnome.init('WebilderApplet', aglobals.version)
        self.applet = applet
        self.tooltips = gtk.Tooltips()
        self.tooltips.enable()
        self.evtbox = gtk.EventBox()
        self.icon = gtk.gdk.pixbuf_new_from_file(
            os.path.join(aglobals.glade_dir, 'camera48.png'))
        self.icon_green = gtk.gdk.pixbuf_new_from_file(
            os.path.join(aglobals.glade_dir, 'camera48_g.png'))

        self.applet_icon = gtk.Image()
        self.scaled_icon = self.icon.scale_simple(16, 16,
                gtk.gdk.INTERP_BILINEAR)
        self.scaled_icon_green = self.icon_green.scale_simple(16, 16,
                gtk.gdk.INTERP_BILINEAR)
        
        self.applet_icon.set_from_pixbuf(self.scaled_icon)
        self.evtbox.add(self.applet_icon)
        self.applet.add(self.evtbox)
        self.propxml="""
    <popup name="button3">
        <menuitem name="Item 1" verb="Browse" label="_Browse Collection" pixtype="stock" 
pixname="gtk-directory"/>
        <menuitem name="Item 2" verb="NextPhoto" label="_Next Photo" pixtype="stock" 
pixname="gtk-go-forward"/>
        <menuitem name="Item 3" verb="Leech" label="_Download Photos" pixtype="filename" 
pixname="%s"/>
        <menuitem name="Item 4" verb="Pref" label="_Preferences" pixtype="stock" 
pixname="gtk-preferences"/>
        <menuitem name="Item 5" verb="About" label="_About" pixtype="stock" pixname="gnome-stock-about"/>
        </popup>
    """ % os.path.join(aglobals.glade_dir, 'camera16.png')
        
        self.applet.connect("change-size", self.on_resize_panel)
        self.applet.connect("button-press-event", self.on_button_press)

        self.verbs = [ 
            ( "Pref", self.preferences ),
            ( "About", self.about),
            ( "Browse", self.browse),
            ( "NextPhoto", self.next_photo),
            ( "Leech", self.leech)]        
        self.applet.setup_menu(self.propxml, self.verbs, None)
        self.applet.show_all()
        self.wallpaper_list = []
        self.last_rotate = time.time()
        self.last_autodownload = config.get('autodownload.last_time') or (time.time() - 50*3600)
        gobject.timeout_add(60*1000, self.timer_event)
        self.photo_browser = None
        self.download_dlg = None 
        self.last_version_check = time.time()-9*3600
        
    def timer_event(self, *args):
        try:
            now = time.time()
            rotate_interval = config.get('rotate.enabled') and config.get('rotate.interval')*60
            autodownload_interval = config.get('autodownload.enabled') and config.get('autodownload.interval')*3600
            if rotate_interval:
                # check if we have to rotate
                if now-self.last_rotate>=rotate_interval:
                    print "Rotating..."
                    self.next_photo()
            
            if CHECK_FOR_UPDATES and now-self.last_version_check>=8*3600:
                response = urllib.urlopen(CHECK_URL)
                latest = response.readlines()
                response.close()
                if latest[0].strip()!=aglobals.version:
                    self.tooltips.enable()
                    self.tooltips.set_tip(self.applet, ''.join(latest[1:]))                    
                else:
                    pass
                self.last_version_check = now

            if autodownload_interval:
                if now-self.last_autodownload >= autodownload_interval:
                    print "Time to autodownload."
                    self.last_autodownload = now
                    import threading
                    import downloader
                    self.leech_thread = threading.Thread(
                        target=downloader.download_all, args=(config,))
                    self.leech_thread.setDaemon(True)
                    self.leech_thread.start()                        
                    config.set('autodownload.last_time', now)
                    config.save_config()
        finally:
            return True
        
    def preferences(self, object, menu):
        import config_dialog
        config_dialog.ConfigDialog().run_dialog(config)
    
    def about(self, object, menu):
        import AboutDialog
        AboutDialog.ShowAboutDialog('Webilder Applet')

    def leech(self, object, menu):
        def remove_reference(*args):
            self.download_dlg = None

        if self.download_dlg:
            return
        import DownloadDialog
        self.download_dlg = DownloadDialog.DownloadProgressDialog(config)
        self.download_dlg._top.connect('destroy', remove_reference)
        self.download_dlg.show()
        self.applet_icon.set_from_pixbuf(self.scaled_icon)
        self.tooltips.disable()

    def on_resize_panel(self, widget, size):
        self.scaled_icon = self.icon.scale_simple(size - 4, size - 4,
            gtk.gdk.INTERP_BILINEAR)
        self.scaled_icon_green = self.icon_green.scale_simple(size - 4, size - 4,
            gtk.gdk.INTERP_BILINEAR)
        self.applet_icon.set_from_pixbuf(self.scaled_icon)

    def on_button_press(self, widget, event):
        if event.type == gtk.gdk.BUTTON_PRESS and event.button == 3:
            return False
        elif event.type == gtk.gdk.BUTTON_PRESS and event.button == 1:
            if not self.photo_browser:
                self.browse(None, None)
            else:
                toggle_window_visibility(self.photo_browser._top)

    def browse(self, object, menu):
        import WebilderDesktop
        if not self.photo_browser:
            self.photo_browser = WebilderDesktop.WebilderDesktopWindow()
            self.photo_browser._top.connect("destroy", self.photo_browser_destroy) 
        else:
            self.photo_browser._top.show_all()

    def next_photo(self, object=None, menu=None):
        croot = config.get('collection.dir')
        if not self.wallpaper_list:
            self.wallpaper_list = glob.glob(
                os.path.join(croot, '*', '*.jpg'))
            random.shuffle(self.wallpaper_list)
        if self.wallpaper_list:
            self.last_rotate = time.time()-15 # to ensure next time...
            wp = self.wallpaper_list.pop()
            set_wallpaper(os.path.join(croot, wp))        

    def photo_browser_destroy(self, event):
        self.photo_browser.destroy()
        self.photo_browser = None
        
def webilder_applet_factory(applet, iid):
    WebilderApplet(applet, iid)
    return True

def toggle_window_visibility(window):
    visible = window.get_property('visible')
    if visible:
        window.hide()
    else:
        window.show_all()
        
gtk.threads_init()

if len(sys.argv) == 2 and sys.argv[1] == "run-in-window":   
        main_window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        main_window.set_title("Webilder Applet Window")
        main_window.connect("destroy", gtk.main_quit) 
        app = gnomeapplet.Applet()
        WebilderApplet(app, None)
        app.reparent(main_window)
        main_window.show_all()
        gtk.main()
        sys.exit()
else:
    gnomeapplet.bonobo_factory("OAFIID:GNOME_WebilderApplet_Factory", 
                             gnomeapplet.Applet.__gtype__, 
                             "webilder-hello", "0", webilder_applet_factory)
