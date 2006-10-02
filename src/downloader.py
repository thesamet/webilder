import os.path
import glob
import cStringIO
import plugins
import time
import os

from webshots.utils import LeechPremiumOnlyPhotoError

_recently_filtered = {}

def get_full_download_list(config):
    # get list of all photos    
    all_photos=[]
    for plugin, module in plugins.plugins.iteritems():
        photos = module.get_download_list(config)
        for photo in photos:
            photo['_plugin'] = {'name': plugin, 'module': module}
        all_photos.extend(photos)
    return all_photos

def clear_recently_filtered():
    print "clearing"
    _recently_filtered.clear()

def clear_old_filtered():
    now = time.time()
    clear = [] 
    for name, block_time in _recently_filtered.iteritems():
        if now-block_time>24*3600:
            clear.append(name)
    for name in clear:
        del _recently_filtered[name]

def filter_photos(config, photos):
    print _recently_filtered
    clear_old_filtered()
    # check if we already have any of the photos

    files = glob.glob(os.path.join(config.get('collection.dir'), '*', '*'))
    files=[os.path.basename(file) for file in files]

    filtered_photos = []
    for photo in photos:
        if photo['name'] in files:
            filtered_photos.append(photo)
            print "Skipping already existing photo '%s'" % photo['title']
            continue
        if photo['name'] in _recently_filtered and config.get('flickr.only_landscape'):
            # currently photos filtered only if only_landscape is set. to prevent
            # photos from being blocked by this cache soon after only_landscape has 
            # set to false, the right term of the 'and' above was added.
            filtered_photos.append(photo)
            print "Skipping previously filtered photo '%s'." % photo['title']
            continue

        photo['_plugin']['module'].fetch_photo_info(config, photo)
        if config.get('filter.only_landscape'):
            if 'aspect_ratio' in photo['data'] and photo['data']['aspect_ratio']<1.1:
                filtered_photos.append(photo)
                print "Skipping non-landscape photo '%s'" % photo['title']
                _recently_filtered[photo['name']] = time.time()
                continue
        files.append(photo['name'])

    for photo in filtered_photos:
        photos.remove(photo)

def download_photo(config, photo, notify):
    print "%s: Downloading '%s'" % (
        photo['_plugin']['name'], photo['title'])
    stream = photo['_plugin']['module'].get_photo_stream(config, photo)
    memfile = cStringIO.StringIO()
    try:
        content_length = int(stream.headers['Content-Length'])
    except:
        content_length = 2**37

    size = 0
    while True:
        notify(float(size)/content_length)
        block = stream.read(16384)
        size+=len(block)
        if not block:
            break
        memfile.write(block)
    stream.close()
    memfile.seek(0)
    return memfile

def save_photo(config, photo, image, metadata):
    album_dirname = metadata['albumTitle'].replace(os.sep, '_')
    dest_dir = os.path.join(config.get('collection.dir'), album_dirname)
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
 
def download_all(config, notify=lambda *args: None, terminate=lambda: False):
    notify(0, '', 'Downloading list of photos (may take some time)')
    photos = get_full_download_list(config)
    if terminate():
        return
    notify(0, '', 'Filtering photos (may take some time)')
    filter_photos(config, photos)
    if terminate():
        return
    completed = 0
    for index, photo in enumerate(photos):
        download_notifier = lambda fraction: notify(
                (float(index+1)+fraction)/(len(photos)+1),
                    'Downloading photo %d of %d from %s.' % (index+1, len(photos), photo['_plugin']['name']),
                    'Downloading <b><i>"%s"</i></b>' % photo['title'])
        try:
            memfile = download_photo(config, photo, download_notifier)
        except LeechPremiumOnlyPhotoError:
            print "   Photo is available only to premium members. Skipping."
            continue # skip this photo (goes back to for)

        if terminate():
            break
        image, metadata = photo['_plugin']['module'].process_photo(config, photo, memfile)
        save_photo(config, photo, image, metadata)
        completed += 1
   
    stats = config.get('webilder.stats')
    stats['downloads'] += completed
    config.save_config()


import socket
socket.setdefaulttimeout(120)

if __name__=="__main__":
    import config
    def notify(fraction, status, message):
        print status
    download_all(config.config, notify)
