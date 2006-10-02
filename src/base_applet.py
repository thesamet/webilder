import glob, random, os, time
from config import config, set_wallpaper, reload_config
import urllib

import webilder_globals as aglobals

CHECK_FOR_UPDATES = True
CHECK_URL = 'http://www.thesamet.com/webilder/latest.html'

random.seed()


class BaseApplet:
    def __init__(self):
        self.wallpaper_list = []
        self.last_rotate = time.time()
        self.last_autodownload = config.get('autodownload.last_time') or (time.time() - 50*3600)
        self.last_version_check = time.time()-9*3600

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
                response = urllib.urlopen(CHECK_URL)
                latest = response.readlines()
                response.close()
                if latest[0].strip()!=aglobals.version:
                    self.set_tooltip(''. join(latest[1:]))
                else:
                    pass

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
                    reload_config()
                    config.set('autodownload.last_time', now)
                    config.save_config()
        finally:
            return True
    

    def next_photo(self, *args):
        croot = config.get('collection.dir')
        if not self.wallpaper_list:
            self.wallpaper_list = glob.glob(
                os.path.join(croot, '*', '*.jpg'))
            random.shuffle(self.wallpaper_list)
        if self.wallpaper_list:
            self.last_rotate = time.time()-15 # to ensure next time...
            wp = self.wallpaper_list.pop()
            set_wallpaper(os.path.join(croot, wp))        

    def set_tooltip(self, text):
        raise NotImplementedError()

