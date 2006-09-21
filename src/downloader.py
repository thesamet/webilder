import os.path
import glob
import cStringIO
import plugins

def get_full_download_list(config):
    # get list of all photos    
    all_photos=[]
    for plugin, module in plugins.plugins.iteritems():
        photos = module.get_download_list(config)
        for photo in photos:
            photo['_plugin'] = {'name': plugin, 'module': module}
        all_photos.extend(photos)
    return all_photos

def remove_existing_photos(config, photos):
    # check if we already have any of the photos
    files = glob.glob(os.path.join(config.get('collection.dir'), '*', '*'))
    files=[os.path.basename(file) for file in files]
    
    existing_photos = []
    for photo in photos:
        if photo['name'] in files:
            existing_photos.append(photo)
    
    for photo in existing_photos:
        print "Skipping already existing photo '%s'" % photo['title']
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
    dest_dir = os.path.join(config.get('collection.dir'), metadata['albumTitle'])
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
    finf.writelines([('%s=%s\n' % (key, value)).encode('utf8') for key, value in 
    metadata.iteritems()])
    finf.close()
 
def download_all(config, notify=lambda *args: None, terminate=lambda: False):
    notify(0, '', 'Downloading list of photos')
    photos = get_full_download_list(config)
    if terminate():
        return
    remove_existing_photos(config, photos)
    if terminate():
        return
    for index, photo in enumerate(photos):
        download_notifier = lambda fraction: notify(
                (float(index+1)+fraction)/(len(photos)+1),
                    photo['title'], 
                    'Downloading photo %d of %d from %s.' % (index+1, len(photos), photo['_plugin']['name']))
        memfile = download_photo(config, photo, download_notifier)
        if terminate():
            return
        image, metadata = photo['_plugin']['module'].process_photo(config, photo, memfile)
        save_photo(config, photo, image, metadata)

import socket
socket.setdefaulttimeout(120)

