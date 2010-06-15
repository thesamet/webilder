import glob, random, os, time
from config import config, set_wallpaper, reload_config
import urllib

from webshots.wbz import parse_metadata
from webilder import __version__

CHECK_FOR_UPDATES = True
CHECK_URL = 'http://www.webilder.org/latest.html'

random.seed()

class VersionCheckerOpener(urllib.FancyURLopener):
    version = 'Webilder/%s' % __version__

class BaseApplet:
    def __init__(self):
        self.wallpaper_list = []
        self.last_rotate = time.time()
        self.last_autodownload = config.get('autodownload.last_time') or (time.time() - 50*3600)
        self.last_version_check = time.time()-9*3600
        self._tt_photo = self._tt_announce = self.image_file =  self.info_file = ''

    def timer_event(self, *args):
        try:
            reload_config()
            now = time.time()
            rotate_interval = config.get('rotate.enabled') and config.get('rotate.interval')*60
            autodownload_interval = config.get('autodownload.enabled') and config.get('autodownload.interval')*3600
            if rotate_interval:
                # check if we have to rotate
                if now-self.last_rotate>=rotate_interval:
                    print "Rotating..."
                    self.next_photo()

            if CHECK_FOR_UPDATES and now-self.last_version_check>=8*3600:
                self.last_version_check = now
                response = VersionCheckerOpener().open(CHECK_URL)
                latest = response.readlines()
                response.close()
                if latest[0].strip()!=aglobals.version:
                    self.set_tooltip_announce(''.join(latest[1:]))
                else:
                    pass

            if autodownload_interval:
                if now-self.last_autodownload >= autodownload_interval:
                    print "Time to autodownload."
                    self.last_autodownload = now
                    import threading
                    import downloader
                    self.leech_thread = threading.Thread(
                        target=downloader.download_all)
                    self.leech_thread.setDaemon(True)
                    self.leech_thread.start()
                    config.set('autodownload.last_time', now)
                    config.save_config()
        finally:
            return True

    def next_photo(self, *args):
        reload_config()
        croot = config.get('collection.dir')
        if not self.wallpaper_list:
            self.wallpaper_list = glob.glob(
                os.path.join(croot, '*', '*.jpg'))
            random.shuffle(self.wallpaper_list)
        if self.wallpaper_list:
            self.last_rotate = time.time()-15 # to ensure next time...
            wp = self.wallpaper_list.pop()

            image_file = os.path.join(croot, wp)
            set_wallpaper(image_file)

            dirname, base = os.path.split(image_file)
            basename, ext = os.path.splitext(base)
            info_file = os.path.join(dirname, basename)+'.inf'
            try:
                f = open(info_file, 'r')
                inf = parse_metadata(f.read())
                f.close()
            except IOError:
                inf = {}
            self.image_file = image_file
            self.info_file = info_file
            title = inf.get('title', basename)
            album = inf.get('albumTitle', dirname)
            self.set_tooltip_for_photo('%s - %s' % (title, album))

    def delete_current(self, *args):
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
        self._tt_photo = text
        self._update_tooltip()

    def set_tooltip_announce(self, text):
        self._tt_announce = text
        self._update_tooltip()

    def _update_tooltip(self):
        self.set_tooltip(self._tt_announce + self._tt_photo)

    def set_tooltip(self, text):
        raise NotImplementedError()
