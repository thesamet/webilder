'''
File    : flickrapi.py
Author  : Nadav Samet
Contact : thesamet@gmail.com
Date    : 2010 Jun 17

Description : Simple Flickr API implementation.
'''

# Released under the BSD license

import urllib2, urllib
from xml.dom.minidom import parseString

class FlickrAPIException(Exception):
    """Wraps error messages returned by Flickr API."""
    def __init__(self, code, message):
        Exception.__init__(self, '[Error %s] %s' % (code, message))


class FlickrProxy(object):
    """Stub connected to Flickr."""
    def __init__(self, api_key):
        self.api_key = api_key

    def call(self, method, **kwargs):
        """Calls the given API method with the given arguments."""
        kwargs.update(dict(api_key=self.api_key, method=method))
        args = urllib.urlencode(kwargs)
        url = 'https://api.flickr.com/services/rest/?' + args
        print "url = ", url
        resp = urllib2.urlopen(url)
        xml = parseString(resp.read())
        rsp = xml.getElementsByTagName('rsp')[0]
        if rsp.getAttribute('stat')!='ok':
            err = rsp.getElementsByTagName('err')[0]
            code = err.attributes['code'].value
            msg = err.attributes['msg'].value
            raise FlickrAPIException(code, msg)
        return rsp # return the payload

    def photos_search(self, **kwargs):
        """Search for photos satisfying the given criteria."""
        photos = self.call('flickr.photos.search', **kwargs)
        photos = photos.getElementsByTagName('photo')
        return self._make_photo_list(photos)

    def interestingness_search(self, **kwargs):
        """Search for photos by interestingness."""
        photos = self.call('flickr.interestingness.getList', **kwargs)
        photos = photos.getElementsByTagName('photo')
        return self._make_photo_list(photos)

    def get_user_nsid(self, username):
        """Gets a user ID by username."""
        rsp = self.call('flickr.people.findByUsername', username=username)
        user = rsp.getElementsByTagName('user')[0]
        return user.getAttribute('nsid')

    def get_user_by_email(self, email):
        """Gets a user by email."""
        rsp = self.call('flickr.people.findByEmail', find_email=email)
        user = rsp.getElementsByTagName('user')[0]
        return user.getAttribute('nsid')

    def _make_photo_list(self, photos):
        """Transform a list of photo XML elements to photo objects."""
        return [FlickrPhoto(self,
            photo_id=photo.getAttribute('id'),
            title=photo.getAttribute('title'),
            secret=photo.getAttribute('secret'),
            originalsecret=photo.getAttribute('originalsecret'),
            originalformat=photo.getAttribute('originalformat'),
            server=photo.getAttribute('server'),
            farm=photo.getAttribute('farm'),
            ) for photo in photos]


class FlickrPhoto(object):
    """Object representing a single photo."""
    def __init__(self, proxy, photo_id, title, secret, originalsecret,
                 originalformat, server, farm):
        (self.photo_id, self.title, self.secret, self.originalsecret,
         self.originalformat, self.server, self.farm) = (
             photo_id, title, secret, originalsecret, originalformat,
             server, farm)
        self._proxy = proxy
        self._size_cache = None

    def get_sizes(self):
        """Get the available sizes for this photo."""
        if self._size_cache:
            return self._size_cache
        rsp = self._proxy.call('flickr.photos.getSizes', photo_id=self.photo_id)
        sizes = rsp.getElementsByTagName('size')
        result = [{
            'label': size.getAttribute('label')[0].lower(),
            'width': int(size.getAttribute('width')),
            'height': int(size.getAttribute('height')),
            'source': size.getAttribute('source')
            } for size in sizes]
        self._size_cache = result
        return result

    def get_aspect_ratio(self):
        """Get the aspect ratio of this photo."""
        sizes = self.get_sizes()
        for size in sizes:
            if size['label'] in ('t', 'o', 'm'):
                return float(size['width'])/float(size['height'])

    def get_image_url(self, size):
        """Get the image download URL for the given image size."""
        if size == 'o':
            secret = self.originalsecret
            orig_format = self.originalformat
        else:
            secret = self.secret
            orig_format = 'jpg'

        filename = '%(id)s_%(secret)s_%(size)s.%(format)s' % dict(
            id=self.photo_id,
            secret=secret,
            size=size,
            format=orig_format)
        url = ('http://farm%(farm)s.static.flickr.com/%(server)s/%(file)s' %
            dict(id = self.photo_id,
                 farm = self.farm,
                 server = self.server,
                 file=filename))
        return url

    def get_best_image_url(self):
        """Gets the best image URL available."""
        sizes = self.get_sizes()[:]
        best = sizes[0]
        for size in sizes:
            if size['width'] > best['width']:
                best = size
        return best['source'] #self.get_image_url(best['label'])

    def get_info(self):
        """Gets full photo info."""
        rsp = self._proxy.call('flickr.photos.getInfo', photo_id=self.photo_id)
        photo = rsp.getElementsByTagName('photo')[0]
        image_url = self.get_best_image_url()

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
            owner = photo.getElementsByTagName('owner')[0].getAttribute(
              'username'), title = title,
            tags = [tag_el.firstChild.data
                    for tag_el in photo.getElementsByTagName('tag')],
            url = url,
            image_url = image_url,
        )
