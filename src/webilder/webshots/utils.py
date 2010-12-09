'''
File    : utils.py
Author  : Nadav Samet
Contact : thesamet@gmail.com
Date    : 2010 Jun 17

Description : Webshots scraping functionality
'''

from xml.dom import minidom
from webilder.webshots import wbz
import urllib, urllib2
import cookielib
import re

class WBZLoginException(Exception):
    """Exception raised when login failed."""

class LeechPremiumOnlyPhotoError(Exception):
    """Exception raised when attempting to download premium only photo."""

class LeechHighQualityForPremiumOnlyError(Exception):
    """Exception raised when attempting to download high quality photo which
    the user is not allowed to download."""

def get_cookie(user, password):
    """Returns a webshots daily cookie given a user and a password."""
    cookie_jar = cookielib.CookieJar()
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie_jar))
    response = opener.open(
        'http://www.webshots.com/login',
        urllib.urlencode({'done': '',
                          'username': user,
                          'password': password,
                          'lbReferer': 'http://www.webshots.com/',
                          'action': 'lb'}))
    resp = response.read().lower()
    if '"c":-1' in resp:
        raise WBZLoginException, 'Incorrect username or password.'

    for cookie in cookie_jar:
        if cookie.name == 'daily':
            return cookie.value
    else:
        raise WBZLoginException, "Cookie not found!"

IMAGE_REGEX = (r'<a href="(/pro/photo/([0-9]+)\?path=/archive)".*?<p title.*?>'
               r'(.*?)</p>.*?<a href="(/entry.*?)" class="hiResLink"')

def get_download_list(config):
    """Returns a list of photos available to download."""
    if not config.get('webshots.enabled'):
        return []

    page = urllib.urlopen(
        'http://www.webshots.com/rss?type=daily').read()
    doc = minidom.parseString(page)
    items = doc.getElementsByTagName('item')
    titles = [item.getElementsByTagName('title')[0].childNodes[0].data for item
              in items]
    links = [item.getElementsByTagName('link')[0].childNodes[0].data for item
              in items]
    assert len(titles)==len(links)
    photo_ids = [re.match(
        r'http://www.webshots.com/pro/photo/(\d+)', link).group(1) for
        link in links]
    result = []
    for image_link, photo, title in zip(links, photo_ids, titles):
        result.append({
            'name': 'webshots_d%s.jpg' % photo,
            'title': title,
            'data': {
                'photo': photo,
                'image_link': image_link,
                'high_res_link': 'https://subs.webshots.com/regsub?vhost=www'
                                 '&photos=%s&res=high' % photo
                }
            })
    return result

def get_photo_stream(config, photo):
    """Starts downloading the given photo."""
    cookie = config.get('webshots.cookie')
    if not cookie:
        cookie = get_cookie(
                config.get('webshots.username'),
                config.get('webshots.password'))
        config.set('webshots.cookie', cookie)
        config.save_config()

    headers = {'Cookie':
        'daily='+config.get('webshots.cookie')+
        ';desktop-client=unknown;site-visits=1',
    }

    url = photo['data']['high_res_link'].replace(
        'res=high',
        'res=%s' % config.get('webshots.quality'))

    opener = urllib.FancyURLopener()
    opener.addheader('Cookie', headers['Cookie'])
    conn = opener.open(url)
    content_type = conn.info().getheader('content-type')
    if content_type == 'application/x-webshots-package':
        return conn
    elif content_type.startswith('text/html'):
        resp = conn.read()
        if 'Credit Card Information' in resp:
            raise LeechPremiumOnlyPhotoError(
                "This photo can be downloaded at resolution '%s' only by "
                "Premium members." % config.get('webshots.quality'))
        if 'NO, THANK YOU.' in resp:
            match = re.search(
                r'<a href="(.*?)" class="no-btn">NO, THANK YOU.', resp)
            if not match:
                raise ValueError, "Unable to download photo %s" % photo['name']
            url = match.groups()[0]
            req = urllib2.Request(url, '', headers)
            resp = urllib2.urlopen(req).read()
            match = re.search(
                r'<a href="(.*\.wbz)">', resp)
        else:
            match = re.search(r'<a href="http://(.*?)">here</a>', resp)

        if not match:
            raise ValueError, "Unable to download photo %s" % photo['name']
        url = match.groups()[0]
        if not url.startswith('http://p.webshots.net/'):
            raise ValueError, "Unable to download photo %s" % photo['name']
        req = urllib2.Request(url, '', headers)
        resp = urllib2.urlopen(req)
        return resp
    else:
        raise ValueError("Unexpected content type header: '%s'" % content_type)


def process_photo(_config, photo, fileobj):
    """Process a photo filestream."""
    img = wbz.open(fileobj, 'r')
    metadata = img.get_metadata()
    metadata['url'] = photo['data']['image_link']
    data = img.get_image_data()
    return data, metadata
