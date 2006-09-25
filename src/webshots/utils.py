import httplib
import urllib, urllib2
import re
import wbz

class WBZLoginException(Exception):
    pass

class LeechPremiumOnlyPhotoError(Exception):
    pass

class LeechHighQualityForPremiumOnlyError(Exception):
    pass

def get_cookie(user, password):
    """Returns a webshots daily cookie given a user and a password."""
    params = urllib.urlencode({'username': user, 'password': password})
    conn = httplib.HTTPConnection(r'daily.webshots.com')
    conn.request("GET", '/login?' + params)
    response = conn.getresponse()
    r = response.read().lower()
    if 'username or password' in r or 'username and password' in r:
        raise WBZLoginException, 'Incorrect username or password.'

    header = response.getheader('set-cookie')
    m = re.search('daily=([^;]+)', header)
    if m:
        return m.groups()[0]
    else:
        raise WBZLoginException, "Cookie not found!"

def get_download_list(config):
    if not config.get('webshots.enabled'):
        return []
    DAILYPIC_RE = r'(http://www.webshots.com/g/d.*/.*/([0-9]*).html)'
    PHOTO_DESCRIPTION = r'alt="([^"]+)" src="http://p.webshots.com/ProThumbs/[0-9]+/%s_wallpaper150.jpg.*\n.*<em(.*)\n'
    page = urllib.urlopen('http://www.webshots.com').read()
    photos = re.findall(DAILYPIC_RE, page)
    l = []
    for image_link, photo in photos:
        match = re.search(PHOTO_DESCRIPTION % photo, page)
        if match:
            title, nextline = match.groups()
            is_premium = 'Premium Only' in nextline
        else:
            title, is_premium = '', False
        l.append({
            'name': 'webshots_d%s.jpg' % photo, 
            'title': title, 
            'data': {
                'photo': photo,
                'image_link': image_link,
                'is_premium': is_premium,
                }
            });
    return l

def get_photo_stream(config, photo):
    cookie = config.get('webshots.cookie')
    if not cookie:
        cookie = get_cookie(
                config.get('webshots.username'),
                config.get('webshots.password'))
        config.set('webshots.cookie', cookie)
        config.save_config()

    args = urllib.urlencode({
        'res' : config.get('webshots.quality'), 
        'targetmode' : 'daily',
        'photos' : photo['data']['photo']})
    headers = {'Cookie': 
        'daily='+config.get('webshots.cookie'),
    }

    opener = urllib.FancyURLopener()
    opener.addheader('Cookie',headers['Cookie'])
    resp = opener.open('http://www.webshots.com/scripts/PhotoDownload.fcgi?'+args)

    if 'text/html' in resp.info().getheader('content-type'):
        r = resp.read()
        if 'r/Premium/Popup/Exclusive' in r:
            raise LeechPremiumOnlyPhotoError, "Only Webshots premium members can download this photo."
        if ('r/Premium/Popup/Wide' in r) or ('r/Premium/Popup/High' in r):
            raise LeechHighQualityForPremiumOnlyError, "Only Webshots Premium members can download highest quality or wide photos."
        match = re.search("document.location.href='([^']+)'", r)
        if match:
            req = urllib2.Request('http://www.webshots.com' +
                    match.groups()[0], '', headers)
            resp = urllib2.urlopen(req)
        else:
            raise ValueError, "Unable to download photo %s" % photo['name']
    return resp

def process_photo(config, photo, f):
    img = wbz.open(f, 'r')
    metadata = img.get_metadata()
    metadata['url'] = photo['data']['image_link']
    data = img.get_image_data()
    return data, metadata
 
