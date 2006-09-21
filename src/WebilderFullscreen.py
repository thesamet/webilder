#!/usr/bin/env python

import os
import gtk
import pango
from webshots import wbz

class FullscreenViewer(gtk.Window):

    def myevent(self, *args):
        self.destroy()

    def expose(self, widget, event):
        area = event.area
        gc = widget.get_style().fg_gc[gtk.STATE_NORMAL]
        widget.window.draw_drawable(gc, self.pixmap, area[0], area[1], 
            area[0], area[1],
               area[2], area[3])
        return False

    def __init__(self, data):
        gtk.Window.__init__(self)
        inf_file = data['info_file']
        self.W, self.H = gtk.gdk.screen_width(), gtk.gdk.screen_height()
        self.p_title = data['filename']
        self.p_album=''
        self.p_credit=''
        if os.path.exists(inf_file):
            inf = wbz.parse_metadata(open(inf_file,'r').read())
            self.p_title = "<b>%s</b>" % inf['title']
            self.p_album = inf['albumTitle']
            self.p_credit = "%s" % inf['credit']
        drawing_area = gtk.DrawingArea()

        evt_box = gtk.EventBox()
        evt_box.add(drawing_area)
        self.add(evt_box)
        evt_box.connect('key-press-event', self.myevent)
        evt_box.connect('button-press-event', self.myevent)
        self.connect('key-press-event', self.myevent)
        drawing_area.connect('configure-event', self.configure)
        drawing_area.connect('expose-event', self.expose)
        drawing_area.set_events(gtk.gdk.EXPOSURE_MASK)
        self.pixbuf = gtk.gdk.pixbuf_new_from_file(
            data['filename'])

        w,h = self.pixbuf.get_width(), self.pixbuf.get_height()
        if self.H>=h*self.W/w:
            self.new_w, self.new_h = self.W, h*self.W/w
        else:
            self.new_w, self.new_h = w*self.H/h, self.H
        self.pixbuf=self.pixbuf.scale_simple(self.new_w, self.new_h,
            gtk.gdk.INTERP_BILINEAR)

    def configure(self, widget, event):
        self.pixmap = gtk.gdk.Pixmap(self.window, self.W, self.H)
        gc = widget.get_style().black_gc
        self.pixmap.draw_rectangle(gc, True,
            0, 0, self.W, self.H)
        cx, cy = (self.W - self.new_w)/2, (self.H-self.new_h)/2
        self.pixmap.draw_pixbuf(gc, self.pixbuf, 0, 0, 
            cx, cy, 
            self.new_w, self.new_h)
        context = self.create_pango_context()
        fsize=context.get_font_description().get_size()*3/2
        font = context.get_font_description()
        font.set_size(fsize)
        context.set_font_description(font)
        layout = pango.Layout(context)
        layout.set_alignment(pango.ALIGN_CENTER)
        layout.set_markup(self.p_title+'\n'+self.p_credit)
        psize_x, psize_y = layout.get_pixel_size()
        self.pixmap.draw_layout(gc, (self.W-psize_x)/2, cy+23, 
                layout)
        self.pixmap.draw_layout(widget.get_style().white_gc, 
                (self.W-psize_x)/2-3, cy+20, 
                layout)
    
    def run(self):
        self.fullscreen()
        self.show_all()
        
