'''
File    : thumbs.py
Author  : Nadav Samet
Contact : thesamet@gmail.com
Date    : 2010 Jun 17

Description : Thumbnailing functionality.
'''
import gtk
import os
import gc

THUMB_SIZE = 160

class ThumbLoader(object):
    """Thumbnail processing object."""
    def __init__(self, iconview, model, image_list):
        self.iconview, self.model, self.image_list = (
            iconview, model, list(image_list))
        # list of images with no thumbnail, to be generated.
        self.thumbnail_na = []
        self.thumbnail_generator = None

    def destroy(self):
        """Destroys the thumbnail generator."""
        self.model = None
        gc.collect()

    def __call__(self):
        if ((self.iconview.get_model() is not self.model) and
            (self.thumbnail_generator is None)):
            # if there's a different model for the icon view, then we are not
            # interesting anymore...
            self.destroy()
            return False

        if (not self.image_list and not self.thumbnail_na and
            self.thumbnail_generator is None):
            # we are done
            self.destroy()
            return False

        # Try to load as many as 20 images for which thumbnails are available
        count = 0
        while self.image_list and count < 20:
            image_dict = self.image_list.pop()
            item_data = image_dict['data']
            thumb = item_data['thumb']
            if (not os.path.exists(thumb) or
                os.path.getmtime(thumb) < os.path.getmtime(
                    item_data['filename'])):
                self.thumbnail_na.append(image_dict)
            else:
                pic = gtk.gdk.pixbuf_new_from_file(thumb)
                # IV_PIXBUF_COLUMN
                self.model.set_value(image_dict['position'], 1, pic)
                count += 1

        if self.thumbnail_na and self.thumbnail_generator is None:
            image_dict = self.thumbnail_na.pop()
            self.thumbnail_generator = thumbnail_generator(image_dict)

        if self.thumbnail_generator:
            try:
                pic = self.thumbnail_generator.next()
            except Exception:  # pylint: disable=W0703
                # many things can go wrong here.
                self.thumbnail_generator = None
            else:
                if pic is not None:
                    # IV_PIXBUF_COLUMN
                    self.model.set_value(pic[0]['position'], 1, pic[1])
                    self.thumbnail_generator = None

        return True

def thumbnail_generator(image_dict):
    """Generates a thumbnail. Loads the data slowly."""
    # Why is it a generator-function and not just a function?
    thumb_dir = os.path.dirname(image_dict['data']['thumb'])
    if not os.path.exists(thumb_dir):
        os.mkdir(thumb_dir)
    loader = gtk.gdk.PixbufLoader()
    try:
        fin = open(image_dict['data']['filename'], 'rb')
        while 1:
            data = fin.read(32768)
            if data:
                loader.write(data)
                yield None
            else:
                break
        pixbuf = loader.get_pixbuf()
        if pixbuf is None:
            raise ValueError(_("Invalid picture"))
        scaled = scale_image(pixbuf, image_dict['data']['thumb'])
        loader.close()
        loader = None
        fin.close()
        gc.collect()
        yield (image_dict, scaled)
    except (IOError, ValueError), exc:
        print image_dict['data']['filename'] + ': ' + str(exc)
        loader.close()
        loader = None
        raise

def scale_image(img, thumb):
    """Scales down a loaded image."""
    width, height = img.get_width(), img.get_height()
    scaled = img.scale_simple(THUMB_SIZE, THUMB_SIZE*height/width,
        gtk.gdk.INTERP_BILINEAR)
    scaled.save(thumb, 'jpeg', {"quality": "75"})
    return scaled
