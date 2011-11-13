'''
File    : config.py
Author  : Nadav Samet
Contact : thesamet@gmail.com
Date    : 2010 Jun 17

Description : Webilder configur object and its load and save methods.
'''

import gettext
import os
import time

gettext.install('webilder')

class ConfigObject:
    """Represents webilder user's perferences."""
    def __init__(self, filename=None):
        self._dict = dict(DEFAULT_CONFIG)
        self._dirty_keys = set()
        if filename:
            if os.path.exists(filename):
                self.load_config(filename)
            else:
                self._filename = filename

        if not os.path.exists(os.path.dirname(filename)):
            os.mkdir(os.path.dirname(filename))
            os.mkdir(self.get('collection.dir'))
            self.save_config(filename)

        if not os.path.isdir(self.get('collection.dir')):
            raise ValueError, _("collection.dir is set to a non-directory, "
                                "check your config file. Current value: %s" %
                                self.get('collection.dir'))

    def get(self, key, *args):
        """Get a preference by key."""
        return self._dict.get(key, *args)

    def set(self, key, value):
        """Set a preference given key and value."""
        self._dirty_keys.add(key)
        self._dict[key] = value

    def load_config(self, filename):
        """Loads config from a file."""
        self._filename = filename
        fileobj = open(filename, 'r')
        for lineno, line in enumerate(fileobj):
            line = line.strip()
            if not line:
                continue
            index = line.find('=')
            if index < 0:
                raise ValueError(
                    _('Error parsing line %d of config file %s') % (lineno,
                                                                    filename))
            key, value = line[:index].strip(), line[index+1:].strip()
            if key in self._dict:
                try:
                    self._dict[key] = eval(value)
                except Exception:  # pylint: disable=W0703
                    if (key == 'webilder.installation_date' and
                        value.startswith('time.struct_time')):
                        self._dict[key] = time.localtime()[:3]
                    else:
                        raise ValueError(_('Error parsing line %d of config'
                            ' file %s') % (lineno, filename))
            else:
                raise ValueError(
                    _('Unrecognized key in line %d of config file %s') % (
                      lineno, filename))
        fileobj.close()

    def save_config(self, filename=None):
        """Saves config to a file."""
        if not filename:
            filename = self._filename
        org_cfg = ConfigObject(filename)

        fileobj = open(filename, 'w')
        for key, _unused_value in DEFAULT_CONFIG:
            try:
                if key in self._dirty_keys:
                    value = self._dict[key]
                else:
                    value = org_cfg.get(key, None)
                fileobj.write('%s = %r\n' % (key, value))
            except (KeyError, ValueError, TypeError), exc:
                fileobj.write('# '+str(exc))
        fileobj.close()
        self._dirty_keys.clear()

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
    ('webilder.wallpaper_set_method', 'gnome3'),
    ('webilder.wallpaper_script', ''),
    ('webilder.wallpaper_compiz_screen_face', 'screen0,0'),
    ('webilder.installation_date', time.localtime()[:3]),
    ('webilder.stats', dict(downloads=0, rotations=0)),
    ('filter.only_landscape', False)]

DEFAULT_CONFIG_FILE = os.path.expanduser('~/.webilder/webilder.conf')

config = ConfigObject(DEFAULT_CONFIG_FILE)  # pylint: disable=C0103

def reload_config():
    """Reloads the config file."""
    config.load_config(DEFAULT_CONFIG_FILE)

def set_wallpaper(filename):
    import gconf
    """Sets the wallpaper to the given filename."""
    use = config.get('webilder.wallpaper_set_method')
    if use == "gnome3":
        script = ('gsettings set org.gnome.desktop.background picture-uri '
                  'file://"%s"' % filename)
        os.popen2(script)
    elif use == "gnome":
        conf_client = gconf.client_get_default()
        conf_client.set_string('/desktop/gnome/background/picture_filename',
            filename)
    elif use == "kde":
        script = 'dcop kdesktop KBackgroundIface setWallpaper "%f" 4'
        script = script.replace('%f', filename)
        os.popen2(script)
    elif use == "xfce":
        script = ('xfconf-query -c xfce4-desktop '
                  '-p /backdrop/screen0/monitor0/image-path -s "%f"')
        script = script.replace('%f', filename)
        os.popen2(script)
    elif use == "compiz_wallpaper":
        set_compiz_wallpaper(filename)
    elif use == "script":
        script = config.get('webilder.wallpaper_script')
        script = script.replace('%f', filename)
        os.popen2(script)
    stats = config.get('webilder.stats')
    stats['rotations'] += 1
    config.set('webilder.stats', stats)
    config.save_config()

def set_compiz_wallpaper(filename):
    """Sets the wallpaper on one of the faces of the cube, as specified
    in webilder.wallpaper_compiz_screen_face configuration key, and sets
    this key to the next face."""

    import gconf

    # Get which screen and which face the wallpaper should be set on
    screen_face = config.get('webilder.wallpaper_compiz_screen_face',
                             'screen0,0')
    try:
        screen, face = screen_face.split(',')
        face = int(face)
    except ValueError:
        screen, face = 'screen0', 0

    # Get a list of all compiz screens
    conf_client = gconf.client_get_default()
    screens = [s.split('/')[-1]
               for s in conf_client.all_dirs('/apps/compiz/general')
               if s.split('/')[-1][:6] == 'screen']

    # Check that the screen is one of the ones supported by compiz
    if screen not in screens:
        screen = screens[0]

    # Get the number of faces on this screen
    number_of_faces = (
        conf_client.get_int('/apps/compiz/general/%s/options/hsize' % screen) *
        conf_client.get_int('/apps/compiz/general/%s/options/vsize' % screen))

    # Get the current list of wallpapers on this screen
    wallpapers = conf_client.get_list(
        '/apps/compiz/plugins/wallpaper/%s/options/bg_image' % screen,
        gconf.VALUE_STRING)

    # If list of wallpapers is too short, populate it to the correct length
    if len(wallpapers) < number_of_faces:
        wallpapers.extend([filename] * (number_of_faces - len(wallpapers)))
        prefix = '/apps/compiz/plugins/wallpaper/%s/options/' % screen
        settings = {
            'bg_color1'   : (gconf.VALUE_STRING, '#000000ff'),
            'bg_color2'   : (gconf.VALUE_STRING, '#000000ff'),
            'bg_fill_type': (gconf.VALUE_INT,    0),
            'bg_image_pos': (gconf.VALUE_INT,    0),
        }
        for key, value in settings.items():
            ext_list = conf_client.get_list(prefix + key, value[0])
            ext_list.extend([value[1]] * (number_of_faces - len(ext_list)))
            conf_client.set_list(prefix + key, value[0], ext_list)

    # Correct face if invalid
    if face >= number_of_faces or face < 0:
        face = 0

    # Set wallpaper
    wallpapers[face] = filename
    conf_client.set_list(
        '/apps/compiz/plugins/wallpaper/%s/options/bg_image' % screen,
        gconf.VALUE_STRING,
        wallpapers)

    # Set screen and face to the next value
    if face >= number_of_faces - 1:
        screen = screens[(screens.index(screen) + 1) % len(screens)]
        face = 0
    else:
        face += 1
    config.set('webilder.wallpaper_compiz_screen_face',
        '%s,%d' % (screen, face))
    config.save_config()
