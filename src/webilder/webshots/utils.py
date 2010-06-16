import httplib
import urllib, urllib2
import cookielib
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
    cj = cookielib.CookieJar()
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
    response = opener.open(
        'http://www.webshots.com/login',
        urllib.urlencode({'done': '',
                          'username': user,
                          'password': password,
                          'lbReferer': 'http://www.webshots.com/',
                          'action': 'lb'}))
    r = response.read().lower()
    if '"c":-1' in r:
        raise WBZLoginException, 'Incorrect username or password.'

    for cookie in cj:
        if cookie.name=='daily':
            return cookie.value
    else:
        raise WBZLoginException, "Cookie not found!"

def get_download_list(config):
    if not config.get('webshots.enabled'):
        return []
    IMAGE_REGEX = r'<a href="(/pro/photo/([0-9]+)\?path=/archive)".*?<p title.*?>(.*?)</p>.*?<a href="(/entry.*?)" class="hiResLink"'

    page = urllib.urlopen(
        'http://www.webshots.com/pro/category/archive?sort=newest').read()

    photos = re.findall(IMAGE_REGEX, page, re.DOTALL)
    l = []
    for image_link, photo, title, high_res_link in photos:
        l.append({
            'name': 'webshots_d%s.jpg' % photo,
            'title': title,
            'data': {
                'photo': photo,
                'image_link': image_link,
                'high_res_link': high_res_link
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

    headers = {'Cookie':
        'daily='+config.get('webshots.cookie')+';desktop-client=unknown;site-visits=1',
    }

    url = 'http://www.webshots.com' + photo['data']['high_res_link'].replace(
        'res=high',
        'res=%s' % config.get('webshots.quality'))

    opener = urllib.FancyURLopener()
    opener.addheader('Cookie',headers['Cookie'])
    resp = opener.open(url)
    if 'text/html' in resp.info().getheader('content-type'):
        r = resp.read()
        match = re.search(r'click <a href="(.*?)">here</a>', r)
        if not match:
            raise ValueError, "Unable to download photo %s" % photo['name']
        url = match.groups()[0]
        if not url.startswith('http://p.webshots.net/'):
            raise ValueError, "Unable to download photo %s" % photo['name']
        req = urllib2.Request(url, '', headers)
        resp = urllib2.urlopen(req)

    return resp

def process_photo(config, photo, f):
    img = wbz.open(f, 'r')
    metadata = img.get_metadata()
    metadata['url'] = photo['data']['image_link']
    data = img.get_image_data()
    return data, metadata
