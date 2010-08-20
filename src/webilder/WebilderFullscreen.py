'''
File    : WebilderFullscreen.py
Author  : Nadav Samet
Contact : thesamet@gmail.com
Date    : 2010 Jun 17

Description : Full screen image viewer
'''

import gtk
import pango

class FullscreenViewer(gtk.Window):
    """Fullscreen viewer implementation."""
    def __init__(self, parent, data):
        gtk.Window.__init__(self)
        self._data = data
        self._parent = parent
        self.window_width, self.window_height = 0, 0
        self.p_title = None
        self.p_album = None
        self.p_credit = None
        self.new_w, self.new_h = 0, 0
        self.pixbuf = None
        self.pixmap = None


    def quit(self, *_args):
        """Closes the fullscreen viewer"""
        self.destroy()

    def expose(self, widget, event):
        """Displays the viewer."""
        area = event.area
        graphics_context = widget.get_style().fg_gc[gtk.STATE_NORMAL]
        widget.window.draw_drawable(graphics_context,
                                    self.pixmap, area[0], area[1],
            area[0], area[1],
            area[2], area[3])
        return False

    def prepare_window(self):
        """Called before drawing to load the data."""
        # We need to know the width and height of the monitor which is going
        # to show the full screen picture. We try to guess which monitor it is
        # going to be by inspecting where the mouse pointer is at.
        xpos, ypos, _ = gtk.gdk.get_default_root_window().get_pointer()
        monitor = gtk.gdk.Screen().get_monitor_at_point(xpos, ypos)
        rect = gtk.gdk.Screen().get_monitor_geometry(monitor)

        if rect.width:
            self.window_width, self.window_height = rect.width, rect.height
        else:
            # Workaroun for VESA on xorg<1.4.99. The monitor data structure
            # may be uninitialized. See
            # https://bugs.launchpad.net/ubuntu/+source/xorg-server/+bug/246585
            self.window_width, self.window_height = (gtk.gdk.screen_width(),
                                                     gtk.gdk.screen_height())
        self.p_title = self._data['title']
        self.p_album = self._data['album']
        self.p_credit = self._data['credit']

        drawing_area = gtk.DrawingArea()

        evt_box = gtk.EventBox()
        evt_box.add(drawing_area)
        self.add(evt_box)
        evt_box.connect('key-press-event', self.quit)
        evt_box.connect('button-press-event', self.quit)
        self.connect('key-press-event', self.quit)
        drawing_area.connect('configure-event', self.configure)
        drawing_area.connect('expose-event', self.expose)
        drawing_area.set_events(gtk.gdk.EXPOSURE_MASK)
        self.pixbuf = gtk.gdk.pixbuf_new_from_file(
            self._data['filename'])

        width, height = self.pixbuf.get_width(), self.pixbuf.get_height()
        if self.window_height >= height*self.window_width/width:
            self.new_w, self.new_h = (self.window_width,
                                      height*self.window_width/width)
        else:
            self.new_w, self.new_h = (width*self.window_height/height,
                                      self.window_height)
        self.pixbuf = self.pixbuf.scale_simple(self.new_w, self.new_h,
            gtk.gdk.INTERP_BILINEAR)

    def configure(self, widget, _event):
        """Handles window configuration event."""
        self.pixmap = gtk.gdk.Pixmap(
            self.window, self.window_width, self.window_height)
        graphics_context = widget.get_style().black_gc
        self.pixmap.draw_rectangle(graphics_context, True,
            0, 0, self.window_width, self.window_height)
        center_x, center_y = ((self.window_width - self.new_w)/2,
                              (self.window_height-self.new_h)/2)
        self.pixmap.draw_pixbuf(graphics_context, self.pixbuf, 0, 0,
            center_x, center_y,
            self.new_w, self.new_h)
        context = self.create_pango_context()
        fsize = context.get_font_description().get_size()*3/2
        font = context.get_font_description()
        font.set_size(fsize)
        context.set_font_description(font)
        layout = pango.Layout(context)
        layout.set_alignment(pango.ALIGN_CENTER)
        layout.set_markup(self.p_title+'\n'+self.p_credit)
        psize_x, _unused_psize_y = layout.get_pixel_size()
        self.pixmap.draw_layout(graphics_context,
            (self.window_width-psize_x)/2, center_y+23, layout)
        self.pixmap.draw_layout(widget.get_style().white_gc,
                (self.window_width-psize_x)/2-3, center_y+20,
                layout)

    def run(self):
        """Shows the fullscreen viewer."""
        self.fullscreen()
        self.prepare_window()
        self.show_all()
