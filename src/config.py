import os

class ConfigObject:
    def __init__(self, file=None):
        self._dict = dict(DEFAULT_CONFIG)
        if file:
            if os.path.exists(file):
                self.load_config(file)
            else:
                self._filename = file


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

DEFAULT_CONFIG = [
    ('collection.dir', '/home/thesamet/.webilder/Collection'),
    ('rotate.enabled', True),
    ('rotate.interval', 5),

    ('webshots.enabled', True),
    ('webshots.auto_download', True),
    ('webshots.username', ''),
    ('webshots.password', ''),
    ('webshots.quality', 'low'),
    ('webshots.cookie', ''),

    ('flickr.enabled', True),
    ('flickr.auto_download', True),
    ('flickr.rules', []),

    ('autodownload.enabled', True),
    ('autodownload.interval', 24),
    ('autodownload.last_time', None),
    ('webilder.layout', {})]


config = ConfigObject(os.path.expanduser('~/.webilder/webilder.conf'))

def set_wallpaper(filename):
    use = 'gnome' # config.get('webilder.wallpaper_method')

    if use=="gnome":
        import gconf
        conf_client = gconf.client_get_default()
        conf_client.set_string('/desktop/gnome/background/picture_filename', 
            filename)
    elif use=="script":
        script = GetWallpaperScript()
        script = script.replace('%f', filename)
        os.popen2(script)
        
