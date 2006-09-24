#!/usr/bin/env python

import sys
import os
import time
import glob
import gc

import gtk
import gtk.glade
import gobject

from uitricks import UITricks
from thumbs import ThumbLoader
import WebilderFullscreen

try:
    import gnomevfs
except ImportError:
    gnomevfs = None
    
import webilder_globals as aglobals
from config import config, set_wallpaper


# Iconview column constants
IV_TEXT_COLUMN = 0
IV_PIXBUF_COLUMN = 1
IV_DATA_COLUMN = 2

# Treeview column constants
TV_TEXT_COLUMN = 0
TV_PATH_COLUMN = 1
TV_KIND_COLUMN = 2

TV_KIND_DIR = "dir"
TV_KIND_RECENT = "recent"

empty_picture = gtk.gdk.pixbuf_new_from_file_at_size(
    os.path.join(aglobals.glade_dir, 'camera48.png'),160,120)

def connect_to_menu(wTree, item, callback):
    wTree.get_widget(item).connect('activate', callback)
    
class WebilderDesktopWindow(UITricks):
    def __init__(self):
        UITricks.__init__(self, os.path.join(aglobals.glade_dir, 'webilder_desktop.glade'), 
            'WebilderDesktopWindow')
        renderer = gtk.CellRendererText()        
        self.tree.append_column(
            column=gtk.TreeViewColumn("Album", renderer, markup=0))
        self.tree.columns_autosize()
        self.load_collection_tree(config.get('collection.dir'))
        self.iconview.set_pixbuf_column(IV_PIXBUF_COLUMN)
        self.iconview.set_markup_column(IV_TEXT_COLUMN)
        self.on_iconview__selection_changed(self.iconview)
        self.collection_monitor = None
        self.image_popup = ImagePopup(self)
       
        if gnomevfs:
            self.tree_monitor = gnomevfs.monitor_add(
                config.get('collection.dir'),
                gnomevfs.MONITOR_DIRECTORY,
                self.collection_tree_changed)
        
        self.restore_window_state()
        self._top.show_all()

        self.hand_cursor = gtk.gdk.Cursor(gtk.gdk.HAND2)
        self.donate_button_box.window.set_cursor(self.hand_cursor)

    def load_collection_tree(self, root):                
        model = gtk.TreeStore(gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_STRING)
        model.append(None, ('<b>Recent Photos</b>', '', TV_KIND_RECENT))
        l = os.listdir(root)
        for entry in sorted(l):
            fullpath = os.path.join(root, entry)
            if os.path.isdir(fullpath):
                model.append(None, (entry, fullpath, TV_KIND_DIR))
        self.tree.set_model(model)

    def on_tree__selection_changed(self, tree_selection):
        model, selection = tree_selection.get_selected_rows()
        for path in selection:
            iter=model.get_iter(path)
            self.current_collection_iter = iter
            rootdir=self.tree.get_model().get_value(iter, TV_PATH_COLUMN)
            kind=self.tree.get_model().get_value(iter, TV_KIND_COLUMN)
            if kind==TV_KIND_DIR:    
                self.load_directory_collection(rootdir)
            else:
                self.load_recent_photos()
 
    def load_directory_collection(self, l):
        images = glob.glob(os.path.join(l,'*.jpg'))
        self.load_collection(images, monitor_dir=l)

    def load_recent_photos(self):
        images = glob.glob(
            os.path.join(config.get('collection.dir'), '*', '*.jpg'))
        recent_time = time.time() - 72*3600
        images = [(os.path.getmtime(fname), fname) for fname in images]
        images = [pair for pair in images if pair[0]>recent_time]
        images = [pair[1] for pair in sorted(images, reverse=True)]
        self.load_collection(images)

    def load_collection(self, images, monitor_dir=None):
        from webshots import wbz
        model = gtk.ListStore(gobject.TYPE_STRING, gtk.gdk.Pixbuf, gobject.TYPE_PYOBJECT)
        
        image_list = []
        for image in images:
            dirname, filename = os.path.split(image)
            basename, ext = os.path.splitext(filename)
            thumb = os.path.join(dirname,
                            '.thumbs', basename+'.thumbnail'+ext)
                
            info_file = os.path.join(dirname, basename)+'.inf'
            try:
                f = open(info_file, 'r')
                inf = wbz.parse_metadata(f.read())
                f.close()
            except IOError:
                inf = {}
            title = inf.get('title', basename)
            album = inf.get('albumTitle', dirname)
            credit = inf.get('credit', 'Not available')
            tags = inf.get('tags', '')
            title = html_escape(title)
            album = html_escape(album)
            credit= html_escape(credit)
            tags = html_escape(tags)
            

            data = dict(title=title,
                        filename=image,
                        thumb=thumb,
                        info_file=info_file,
                        album = album,
                        tags = tags,
                        credit = credit)
            if len(title)>24:
                title=title[:21]+'...'
            if 0<=time.time()-os.path.getmtime(image)<24*3600:
                title='<b>*New* %s</b>' % title
            position = model.append((title, empty_picture, data))
            image_list.append(dict(
                position=position,
                data=data))

        image_list.reverse()
        self.iconview.set_model(model)
        gobject.idle_add(ThumbLoader(self.iconview, model, image_list))
        self.on_iconview__selection_changed(self.iconview)
        if gnomevfs:
            if self.collection_monitor is not None:
                gobject.idle_add(gnomevfs.monitor_cancel, self.collection_monitor)
                self.collection_monitor = None        
            if monitor_dir:
                self.collection_monitor = gnomevfs.monitor_add(
                    monitor_dir,
                    gnomevfs.MONITOR_DIRECTORY,
                    self.collection_directory_changed)
        gc.collect()

    def on_set_as_wallpaper__activate(self, menu_item):
         selected = self.iconview.get_selected_items()
         if selected:
             selected=selected[-1]
         if selected:
             self.on_iconview__item_activated(
                 self.iconview, 
                 selected)

    def on_iconview__item_activated(self, icon_view, path):
        import gconf
        iter = icon_view.get_model().get_iter(path)
        data = icon_view.get_model().get_value(iter, IV_DATA_COLUMN)
        set_wallpaper(data['filename'])
        gc.collect()
        
         
    def on_view_fullscreen__activate(self, menu_item):
        selected = self.iconview.get_selected_items()
        if selected:
            # FIXME: Make a nice slideshow here, maybe?
            selected=selected[-1]            
            path = selected;
            iter = self.iconview.get_model().get_iter(path)
            data = self.iconview.get_model().get_value(iter,
                IV_DATA_COLUMN)
            WebilderFullscreen.FullscreenViewer(data).run()
        gc.collect()

    def on_download_photos__activate(self, menu_item):
        def remove_reference(*args):
            del self.download_dialog

        import DownloadDialog
        if not hasattr(self, 'download_dialog'):
            self.download_dialog = DownloadDialog.DownloadProgressDialog(config)
            self.download_dialog._top.connect('destroy', remove_reference)
            self.download_dialog.show()
        else:
            self.download_dialog._top.present()
    
    def on_iconview__selection_changed(self, icon_view):
        selection = icon_view.get_selected_items()
        if len(selection)>0:
            selection=selection[-1]
        title = album = credit = tags = ""
        if selection:
            iter = icon_view.get_model().get_iter(selection)
            data = icon_view.get_model().get_value(iter, IV_DATA_COLUMN)
            title = "<b>%s</b>" % data['title']
            album = data['album']
            credit = data['credit']
            tags = data['tags']
                    
        self.photo_title.set_markup(title)
        self.photo_album.set_markup(album)
        self.photo_credit.set_markup(credit)
        self.photo_tags.set_markup(tags)

    def collection_directory_changed(self, *args):
        self.on_tree__selection_changed(self.tree.get_selection())

    def on_preferences__activate(self, menu_item):
        import config_dialog
        dlg = config_dialog.ConfigDialog().run_dialog(config)
            
    def on_iconview__button_press_event(self, icon_view, event):
        if event.button==3:
            x, y = map(int, [event.x, event.y])
            path = icon_view.get_path_at_pos(x, y)
            if not path:
                return
            if not (event.state & gtk.gdk.CONTROL_MASK):
                icon_view.unselect_all()
            icon_view.select_path(path)

            self.image_popup._top.popup(None, None, None, event.button,
                    event.time)
        return False
        
    def collection_tree_changed(self, *args):
        """Called when the collection tree changes."""
        self.load_collection_tree(config.get('collection.dir'))

    def on_quit__activate(self, event):
        self.on_WebilderDesktopWindow__delete_event(None, None)
        
    def on_about__activate(self, event):
        import AboutDialog
        AboutDialog.ShowAboutDialog('Webilder Desktop')

    def on_WebilderDesktopWindow__delete_event(self, widget, event):
        self.save_window_state()
        self.destroy()
        return False
        
    def save_window_state(self):
        top = self._top
        layout = {'window_position': top.get_position(),
                  'window_size': top.get_size(),
                  'hpaned_position': self.hpaned.get_position()}
        config.set('webilder.layout', layout)
        config.save_config()
    
    def restore_window_state(self):
        d = config.get('webilder.layout')
        if d.has_key('window_position'):
            self._top.move(*d['window_position'])
        if d.has_key('window_size'):
            self._top.resize(*d['window_size'])
        if d.has_key('hpaned_position'):
            self.hpaned.set_position(d['hpaned_position'])
      
    def on_file_webshots_import__activate(self, event):
        dlg = gtk.FileChooserDialog(
            'Choose files to import',
            None,
            action=gtk.FILE_CHOOSER_ACTION_OPEN,
            buttons=("_Import", gtk.RESPONSE_OK, "_Cancel", gtk.RESPONSE_CANCEL))
        dlg.set_select_multiple(True)
        try:
            response = dlg.run()
            if response==gtk.RESPONSE_OK:
                files = dlg.get_filenames()
            else:
                files = []
        finally:
            dlg.destroy()        
        
        import wbz_handler
        for afile in files:
            wbz_handler.handle_file(afile)

    def on_donate_button_box__button_press_event(self, button, event):
        def _iscommand(cmd):
            """Return True if cmd can be found on the executable search path."""
            path = os.environ.get("PATH")
            if not path:
                return False
            for d in path.split(os.pathsep):
                exe = os.path.join(d, cmd)
                if os.path.isfile(exe):
                    return True
            return False
        donate_url = 'http://www.thesamet.com/webilder/donate'
        if _iscommand('gnome-open'):
            os.system('gnome-open %s' % donate_url)
        elif _iscommand('kfmclient'):
            os.system('kfmclient openURL %s' % donate_url)
        else:
            mb = gtk.MessageDialog(type=gtk.MESSAGE_INFO, buttons=gtk.BUTTONS_OK)
            mb.set_title('Thank You!')
            mb.set_markup("<b>Thanks for your interest in supporting Webilder.</b>\n\n"
                    'Please follow this link to send us a donation:\n\n%s' % donate_url)
            mbval = mb.run()
            mb.destroy()

class ImagePopup(UITricks):
    def __init__(self, main_window):
        self.main_window = main_window
        self.on_view_full_screen__activate = main_window.on_view_fullscreen__activate
        self.on_set_as_wallpaper__activate = main_window.on_set_as_wallpaper__activate
        UITricks.__init__(self, os.path.join(aglobals.glade_dir, 'webilder_desktop.glade'), 'WebilderImagePopup')

    def on_delete_images__activate(self, event):
        iconview = self.main_window.iconview
        selected = iconview.get_selected_items()
        if selected:
            dlg = gtk.MessageDialog(type=gtk.MESSAGE_QUESTION, 
                buttons=gtk.BUTTONS_YES_NO, 
                message_format="Would you like to delete the selected images?")
            response = dlg.run()
            dlg.destroy()
            if response == gtk.RESPONSE_YES:
                for path in selected:                
                    iter = iconview.get_model().get_iter(path)
                    data = iconview.get_model().get_value(iter,
                        IV_DATA_COLUMN)
                    for fname in (data['filename'], data['info_file'], data['thumb']):
                        try:
                            os.remove(fname)
                        except:
                            pass
            
html_escape_table = {
    "&": "&amp;",
    '"': "&quot;",
    "'": "&apos;",
    ">": "&gt;",
    "<": "&lt;",
    }

def html_escape(text):
    """Produce entities within text."""
    L=[]
    for c in text:
        L.append(html_escape_table.get(c,c))
    return "".join(L)

if __name__ == "__main__":
    gtk.threads_init()
    main_window = WebilderDesktopWindow()
    main_window._top.connect("destroy", gtk.main_quit)
    gtk.main()

