'''
File    : downloader.py
Author  : Nadav Samet
Contact : thesamet@gmail.com
Date    : 2010 Jun 17

Description : Implements the download logic. Also works as a standalone script.
'''

from webilder import plugins
from webilder.webshots.utils import LeechPremiumOnlyPhotoError
from webilder.config import config

import cStringIO
import glob
import os
import os.path
import time

__recently_filtered__ = {}

def get_full_download_list(config_obj):
    """Get list of all photos avaialable for download."""
    all_photos = []
    for plugin, module in plugins.PLUGINS.iteritems():
        photos = module.get_download_list(config_obj)
        for photo in photos:
            photo['_plugin'] = {'name': plugin, 'module': module}
        all_photos.extend(photos)
    return all_photos

def clear_recently_filtered():
    """Clears the list of recently filtered photos."""
    __recently_filtered__.clear()

def clear_old_filtered():
    """Clears the lsit of photos which were filtered yesterday."""
    now = time.time()
    clear = []
    for name, block_time in __recently_filtered__.iteritems():
        if now-block_time > 24*3600:
            clear.append(name)
    for name in clear:
        del __recently_filtered__[name]

def filter_photos(config_obj, photos):
    """Filter photos (removed banned, not landscape, etc)."""
    clear_old_filtered()
    # load photo names of permanently deleted photos...
    banned_photos_file = os.path.expanduser('~/.webilder/banned_photos')
    if os.path.exists(banned_photos_file):
        banned_photos = open(banned_photos_file, 'r').readlines()
        banned_photos = [line.strip() for line in banned_photos]
    else:
        banned_photos = []

    # check if we already have any of the photos

    files = glob.glob(os.path.join(config_obj.get('collection.dir'), '*', '*'))
    files = [os.path.basename(filename) for filename in files]

    filtered_photos = []
    for photo in photos:
        if photo['name'] in files:
            filtered_photos.append(photo)
            print _("Skipping already existing photo '%s'") % photo['title']
            continue
        if photo['name'] in banned_photos:
            print _("Skipping banned photo '%s'.") % photo['title']
            filtered_photos.append(photo)
            continue
        if (photo['name'] in __recently_filtered__ and
            config_obj.get('filter.only_landscape')):
            # currently photos filtered only if only_landscape is set. to
            # prevent # photos from being blocked by this cache soon after
            # only_landscape has set to false, the right term of the 'and'
            # above was added.
            filtered_photos.append(photo)
            print _("Skipping previously filtered photo '%s'.") % photo['title']
            continue

        photo['_plugin']['module'].fetch_photo_info(config_obj, photo)
        if config_obj.get('filter.only_landscape'):
            if ('aspect_ratio' in photo['data'] and
                photo['data']['aspect_ratio'] < 1.1):
                filtered_photos.append(photo)
                print _("Skipping non-landscape photo '%s'") % photo['title']
                __recently_filtered__[photo['name']] = time.time()
                continue
        files.append(photo['name'])

    for photo in filtered_photos:
        photos.remove(photo)

def download_photo(config_obj, photo, notify):
    """Downloads a given photo object."""
    print _("%s: Downloading '%s'") % (
        photo['_plugin']['name'], photo['title'])
    stream = photo['_plugin']['module'].get_photo_stream(config_obj, photo)
    memfile = cStringIO.StringIO()
    try:
        content_length = int(stream.headers['Content-Length'])
    except ValueError:
        content_length = 2**37

    size = 0
    while True:
        notify(float(size)/content_length)
        block = stream.read(16384)
        size += len(block)
        if not block:
            break
        memfile.write(block)
    stream.close()
    memfile.seek(0)
    return memfile

def save_photo(config_obj, photo, image, metadata):
    """Saves the given photo file and metadata."""
    album_dirname = metadata['albumTitle'].replace(os.sep, '_')
    dest_dir = os.path.join(config_obj.get('collection.dir'), album_dirname)
    dest_thumb_dir = os.path.join(dest_dir, '.thumbs')
    dest_img = os.path.join(dest_dir, photo['name'])
    dest_inf = os.path.splitext(dest_img)[0]+'.inf'
    if not os.path.isdir(dest_dir):
        os.mkdir(dest_dir)
        os.mkdir(dest_thumb_dir)
    elif not os.path.isdir(dest_thumb_dir):
        os.mkdir(dest_thumb_dir)

    fjpg = open(dest_img, 'wb')
    fjpg.write(image)
    fjpg.close()

    finf = open(dest_inf, 'w')
    lines = []
    for key, value in metadata.iteritems():
        if isinstance(value, unicode):
            value = value.encode('utf8')
        if isinstance(key, unicode):
            key = key.encode('utf8')
        lines.append('%s=%s\n' % (key, value))

    finf.writelines(lines)
    finf.close()

def download_all(notify=lambda *args: None, terminate=lambda: False):
    """Downloads all photos available to us."""
    notify(0, '', _('Downloading list of photos (may take some time)'))
    photos = get_full_download_list(config)
    if terminate():
        return
    notify(0, '', _('Filtering photos (may take some time)'))
    filter_photos(config, photos)
    if terminate():
        return
    completed = 0
    for index, photo in enumerate(photos):
        download_notifier = lambda fraction: notify(
                (float(index+1)+fraction)/(len(photos)+1),
                    _('Downloading photo %d of %d from %s.') % (
                        index+1, len(photos), photo['_plugin']['name']),
                    _('Downloading <b><i>"%s"</i></b>') % photo['title'])
        try:
            memfile = download_photo(config, photo, download_notifier)
        except LeechPremiumOnlyPhotoError:
            print _("   Photo is available only to premium members. Skipping.")
            continue # skip this photo (goes back to for)

        if terminate():
            break
        try:
            image, metadata = photo['_plugin']['module'].process_photo(
                config, photo, memfile)
            save_photo(config, photo, image, metadata)
        except IOError, exc:
            print "IOError: ", str(exc)
        else:
            completed += 1

    stats = config.get('webilder.stats')
    stats['downloads'] += completed
    config.set('webilder.stats', stats)
    config.save_config()


import socket
socket.setdefaulttimeout(120)

def main():
    """Command line interface for photo downloader."""
    def notify(_fraction, status, message):
        """Called when the download logic wants to notify us."""
        print message, status
    download_all(notify)

if __name__ == "__main__":
    main()
