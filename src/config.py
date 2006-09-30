import os, time

class ConfigObject:
    def __init__(self, file=None):
        self._dict = dict(DEFAULT_CONFIG)
        if file:
            if os.path.exists(file):
                self.load_config(file)
            else:
                self._filename = file

        if not os.path.exists(os.path.dirname(file)):
            os.mkdir(os.path.dirname(file))
            os.mkdir(self.get('collection.dir'))

        if not os.path.isdir(self.get('collection.dir')):
            raise ValueError, "collection.dir is set to a non-directory, check your config file."

    def get(self, key):
        return self._dict[key]

    def set(self, key, value):
        self._dict[key] = value

    def load_config(self, file):
        self._filename = file
        f = open(file, 'r')
        for lineno, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            index = line.find('=')
            if index<0:
                raise ValueError('Error parsing line %d of config file %s' % (lineno, file))
            key, value = line[:index].strip(), line[index+1:].strip()
            if key in self._dict:
                try:
                    self._dict[key] = eval(value)
                except:
                    raise ValueError('Error parsing line %d of config file %s' % (lineno, file))
            else:
                raise ValueError('Unrecognized key in line %d of config file %s' % (lineno, file))

    def save_config(self, file=None):
        if not file:
            file = self._filename
        file = open(file, 'w')
        for key,v in DEFAULT_CONFIG:
            file.write('%s = %r\n' % (key, self._dict[key]))
        # yes, should not be here...
        import downloader
        downloader.clear_recently_filtered()

DEFAULT_CONFIG = [
    ('collection.dir', os.path.expanduser('~/.webilder/Collection')),
    ('rotate.enabled', True),
    ('rotate.interval', 5),

    ('webshots.enabled', False),
    ('webshots.auto_download', True),
    ('webshots.username', ''),
    ('webshots.password', ''),
    ('webshots.quality', 'low'),
    ('webshots.cookie', ''),

    ('flickr.enabled', True),
    ('flickr.auto_download', True),
    ('flickr.rules', []),
    ('flickr.download_interesting', True),
    ('flickr.scale_down', (1600, 1200)),

    ('autodownload.enabled', True),
    ('autodownload.interval', 24),
    ('autodownload.last_time', None),
    ('webilder.layout', {}),
    ('webilder.wallpaper_set_method', 'gnome'),
    ('webilder.wallpaper_script', ''),
    ('webilder.installation_date', time.localtime()),
    ('webilder.stats', dict(downloads=0, rotations=0)),
    ('filter.only_landscape', False)]

DEFAULT_CONFIG_FILE = os.path.expanduser('~/.webilder/webilder.conf')

config = ConfigObject(DEFAULT_CONFIG_FILE)

def reload_config():
    config.load_config(DEFAULT_CONFIG_FILE)
     
def set_wallpaper(filename):
    use = config.get('webilder.wallpaper_set_method')
    if use=="gnome":
        import gconf
        conf_client = gconf.client_get_default()
        conf_client.set_string('/desktop/gnome/background/picture_filename', 
            filename)
    elif use=="kde":
        script = 'dcop kdesktop KBackgroundIface setWallpaper "%f" 4'
        script = script.replace('%f', filename)
        os.popen2(script)
    elif use=="script":
        script = config.get('webilder.wallpaper_script')
        script = script.replace('%f', filename)
        os.popen2(script)
    stats = config.get('webilder.stats')
    stats['rotations'] += 1
    config.save_config()

