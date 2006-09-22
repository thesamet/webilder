import re
import urllib

def get_download_list(config):
    if not config.get('flickr.enabled'):
        return []
    import feedparser
    rules = config.get('flickr.rules')
    images = []
    for rule in rules:
        params_dict = {'tags': rule['tags'], 'tagmode': rule['tagmode']}
        params = urllib.urlencode(params_dict)
        opener = urllib.urlopen('http://api.flickr.com/services/feeds/photos_public.gne?'+params)
        feed=feedparser.parse(opener)
        for entry in feed.entries:
            title = entry.title
            value = entry.content[0].value
            id = str(entry.id.split('/')[-1])
            img_url = re.search('src="([^"]*)"', value).groups()[0]
            img_url = img_url.replace('m.jpg', 'o.jpg')
            images.append({
                'name': 'flickr_%s.jpg' % id,
                'title': title,
                'data': {
                    'entry': entry,
                    'image_link': entry.links[0]['href'],
                    'image_url': img_url,
                    'rule': rule
                }});
    return images

def get_photo_stream(config, photo):
    stream = urllib.urlopen(photo['data']['image_url'])
    return stream

def process_photo(config, photo, f):
    metadata = {
            'albumTitle': photo['data']['rule']['album'],
            'title': photo['title'],
            'credit': photo['data']['entry']['author'],
            'image_link': photo['data']['image_link'],
            }
    return f.read(), metadata

