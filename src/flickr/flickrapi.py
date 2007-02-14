# Flickr API for Python - thesamet, 2006
# 
# Released under the GPL license

import urllib2, urllib
from xml.dom.minidom import parseString

class FlickrAPIException(Exception):
    def __init__(self, code, message):
        Exception.__init__(self, '[Error %s] %s' % (code, message))


class FlickrProxy(object):
    def __init__(self, api_key):
        self.api_key = api_key

    def call(self, method, **kwargs):
        kwargs.update(dict(api_key=self.api_key, method=method))
        args = urllib.urlencode(kwargs)
        resp = urllib2.urlopen('http://api.flickr.com/services/rest/?' + args)
        xml = parseString(resp.read())
        rsp = xml.getElementsByTagName('rsp')[0]
        if rsp.getAttribute('stat')!='ok':
            err = rsp.getElementsByTagName('err')[0]
            code = err.attributes['code'].value
            msg = err.attributes['msg'].value
            raise FlickrAPIException(code, msg)
        return rsp # return the payload

    def photos_search(self, **kwargs):
        photos = self.call('flickr.photos.search', **kwargs)
        photos = photos.getElementsByTagName('photo')
        return self._makePhotoList(photos)

    def interestingness_search(self, **kwargs):
        photos = self.call('flickr.interestingness.getList', **kwargs)
        photos = photos.getElementsByTagName('photo')
        return self._makePhotoList(photos)

    def get_user_nsid(self, username):
        rsp = self.call('flickr.people.findByUsername', username=username)
        user = rsp.getElementsByTagName('user')[0]
        return user.getAttribute('nsid')

    def get_user_by_email(self, email):
        rsp = self.call('flickr.people.findByEmail', find_email=email)
        user = rsp.getElementsByTagName('user')[0]
        return user.getAttribute('nsid')

    def _makePhotoList(self, photos):
        return [FlickrPhoto(self, 
            photo_id=photo.getAttribute('id'), 
            title=photo.getAttribute('title'),
            secret=photo.getAttribute('secret'),
            server=photo.getAttribute('server'),
            ) for photo in photos]


class FlickrPhoto(object):
    def __init__(self, proxy, photo_id, title, secret, server):
        self.photo_id, self.title, self.secret, self.server = photo_id, title, secret, server
        self._proxy = proxy

    def get_aspect_ratio(self):
        rsp = self._proxy.call('flickr.photos.getSizes', photo_id=self.photo_id)
        sizes = rsp.getElementsByTagName('size')
        for size in sizes:
            if size.getAttribute('label').lower() in ('original', 'large', 'medium', 'small', 'thumbnail'):
                return float(size.getAttribute('width'))/float(size.getAttribute('height'))
        return None

    def get_image_url(self, size, format='jpg'):
        return 'http://static.flickr.com/%(server)s/%(id)s_%(secret)s_%(size)s.%(format)s' % dict(
            id = self.photo_id,
            server = self.server,
            secret = self.secret,
            format = 'jpg', 
            size = size)
            
    def get_info(self):
        rsp = self._proxy.call('flickr.photos.getInfo', photo_id=self.photo_id)
        photo = rsp.getElementsByTagName('photo')[0]
        image_url = self.get_image_url('o', format=photo.getAttribute('originalformat'))

        title = photo.getElementsByTagName('title')[0]
        if title.firstChild:
            title = title.firstChild.data
        else:
            title = ''
        url = photo.getElementsByTagName('url')[0]
        if url.firstChild:
            url = url.firstChild.data
        else:
            url = ''

        return dict(
            owner = photo.getElementsByTagName('owner')[0].getAttribute('username'),
            title = title,
            tags = [tag_el.firstChild.data for tag_el in photo.getElementsByTagName('tag')],
            url = url,
            image_url = image_url,
            )

