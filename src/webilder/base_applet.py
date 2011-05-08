'''
File    : base_applet.py
Author  : Nadav Samet
Contact : thesamet@gmail.com
Date    : 2010 Jun 17

Description : Base class for applet (used to be shared by GNOME and KDE
applets.)
'''

from webilder.config import config, set_wallpaper, reload_config
from webilder import __version__
from webilder import downloader
from webilder import infofile
from webilder.webshots.wbz import parse_metadata

import glob, random, os, time
import threading
import urllib


CHECK_FOR_UPDATES = True
CHECK_URL = 'http://www.webilder.org/latest.html'

random.seed()

class VersionCheckerOpener(urllib.FancyURLopener):
    """UserAgent for the version checker."""
    version = 'Webilder/%s' % __version__

class BaseApplet:
    """Implementation of base applet."""
    def __init__(self):
        self.wallpaper_list = []
        self.last_rotate = time.time()
        self.last_autodownload = (config.get('autodownload.last_time') or
                                  (time.time() - 50*3600))
        self.last_version_check = time.time()-9*3600
        self.leech_thread = None
        self._tt_photo = self._tt_announce = self.image_file = ''
        self.info_file = ''

    def timer_event(self, *_args):
        """Called on regular basis to check if it is time to download photos
        or change wallpaper."""
        try:
            reload_config()
            now = time.time()
            rotate_interval = (config.get('rotate.enabled') and
                               config.get('rotate.interval')*60)
            autodownload_interval = (config.get('autodownload.enabled') and
                                     config.get('autodownload.interval')*3600)
            if rotate_interval:
                # check if we have to rotate
                if now-self.last_rotate >= rotate_interval:
                    print "Rotating..."
                    self.next_photo()

            if CHECK_FOR_UPDATES and now-self.last_version_check >= 8*3600:
                self.last_version_check = now
                response = VersionCheckerOpener().open(CHECK_URL)
                latest = response.readlines()
                response.close()
                if latest[0].strip() != __version__:
                    self.set_tooltip_announce(''.join(latest[1:]))
                else:
                    pass

            if autodownload_interval:
                if now-self.last_autodownload >= autodownload_interval:
                    print "Time to autodownload."
                    self.last_autodownload = now
                    self.leech_thread = threading.Thread(
                        target=downloader.download_all)
                    self.leech_thread.setDaemon(True)
                    self.leech_thread.start()
                    config.set('autodownload.last_time', now)
                    config.save_config()
        finally:
            return True  # pylint: disable=W0150

    def next_photo(self, *_args):
        """Changes to the next photo."""
        reload_config()
        croot = config.get('collection.dir')
        if not self.wallpaper_list:
            self.wallpaper_list = glob.glob(
                os.path.join(croot, '*', '*.jpg'))
            png_images = glob.glob(
                os.path.join(croot, '*', '*.png'))
            self.wallpaper_list.extend(png_images)
            random.shuffle(self.wallpaper_list)
        if self.wallpaper_list:
            self.last_rotate = time.time()-15 # to ensure next time...
            wallpaper = self.wallpaper_list.pop()

            image_file = os.path.join(croot, wallpaper)
            set_wallpaper(image_file)

            dirname, base = os.path.split(image_file)
            basename, _unused_ext = os.path.splitext(base)
            self.info_file = os.path.join(dirname, basename)+'.inf'
            self.image_info = infofile.parse_info_file(self.info_file)
            self.image_file = image_file
            title = self.image_info.get('title', basename)
            album = self.image_info.get('albumTitle', dirname)
            self.set_tooltip_for_photo('%s - %s' % (title, album))

    def delete_current(self, *_args):
        """Deletes the currently set wallpaper."""
        if self.image_file != '':
            jpg_file = self.image_file
            inf_file = self.info_file
            self.next_photo()
            try:
                os.remove(jpg_file)
                os.remove(inf_file)
                banned = open(os.path.expanduser('~/.webilder/banned_photos'),
                              'a')
                banned.write(os.path.basename(jpg_file)+'\n')
                banned.close()
            except IOError:
                pass
        else:
            self.next_photo()



    def set_tooltip_for_photo(self, text):
        """Sets the current tooltip for the given photo."""
        self._tt_photo = text
        self._update_tooltip()

    def set_tooltip_announce(self, text):
        """Sets the current tooltip to announce a new version."""
        self._tt_announce = text
        self._update_tooltip()

    def _update_tooltip(self):
        """Sets the tooltip to the cached string."""
        self.set_tooltip(self._tt_announce + self._tt_photo)

    def set_tooltip(self, text):
        """Sets the tooltip. Implemented by derived classes."""
        raise NotImplementedError()
