'''
File    : WebilderDesktop.py
Author  : Nadav Samet
Contact : thesamet@gmail.com
Date    : 2010 Jun 17

Description : Controller for the photo browser. Can work as a
              standalone program.
'''

from webilder import AboutDialog
from webilder import config_dialog
from webilder import DownloadDialog
from webilder import infofile
from webilder import wbz_handler
from webilder import WebilderFullscreen
from webilder.thumbs import ThumbLoader
from webilder.uitricks import UITricks, open_browser

import sys, os, time, glob, gc
import optparse
import gtk, gobject
import pkg_resources


try:
    import gnomevfs
except ImportError:
    gnomevfs = None  # pylint: disable=C0103

from webilder.config import config, set_wallpaper, reload_config

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

EMPTY_PICTURE = gtk.gdk.pixbuf_new_from_file_at_size(
    pkg_resources.resource_filename(__name__, 'ui/camera48.png'), 160, 120)

def connect_to_menu(wtree, item, callback):
    """Connects a callback to a menu item."""
    wtree.get_widget(item).connect('activate', callback)

class WebilderDesktopWindow(UITricks):
    """Implementation of photo browser controller."""
    def __init__(self):
        UITricks.__init__(self, 'ui/webilder_desktop.glade',
            'WebilderDesktopWindow')
        self.sort_combo.set_active(1)       # date
        renderer = gtk.CellRendererText()
        self.tree.append_column(
            column=gtk.TreeViewColumn("Album", renderer, markup=0))
        self.tree.columns_autosize()
        self.load_collection_tree(config.get('collection.dir'))
        self.iconview.set_pixbuf_column(IV_PIXBUF_COLUMN)
        self.iconview.set_markup_column(IV_TEXT_COLUMN)
        self.on_iconview_handle_selection_changed(self.iconview)
        self.collection_monitor = dict(monitor=None, dir=None)
        self.image_popup = ImagePopup(self)
        self.download_dialog = None

        if gnomevfs:
            self.tree_monitor = gnomevfs.monitor_add(
                config.get('collection.dir'),
                gnomevfs.MONITOR_DIRECTORY,
                self.collection_tree_changed)

        self.restore_window_state()
        self.top_widget.show_all()

        self.hand_cursor = gtk.gdk.Cursor(gtk.gdk.HAND2)
        # self.donate_button_box.window.set_cursor(self.hand_cursor)

    def load_collection_tree(self, root):
        """Loads the collection in the given root to the model."""
        model = gtk.TreeStore(gobject.TYPE_STRING, gobject.TYPE_STRING,
                              gobject.TYPE_STRING)
        model.append(None, (_('<b>Recent Photos</b>'), '', TV_KIND_RECENT))
        dirlist = os.listdir(root)
        for entry in sorted(dirlist):
            fullpath = os.path.join(root, entry)
            entry = html_escape(entry)
            if os.path.isdir(fullpath):
                model.append(None, (entry, fullpath, TV_KIND_DIR))
        self.tree.set_model(model)

    # pylint: disable=C0103

    def on_tree_handle_selection_changed(self, tree_selection):
        """Called when the selection in the tree changed."""
        if not tree_selection:
            return
        model, selection = tree_selection.get_selected_rows()
        for path in selection:
            iterator = model.get_iter(path)
            rootdir = self.tree.get_model().get_value(iterator, TV_PATH_COLUMN)
            kind = self.tree.get_model().get_value(iterator, TV_KIND_COLUMN)
            if kind == TV_KIND_DIR:
                self.load_directory_collection(rootdir)
            else:
                self.load_recent_photos()

    def load_directory_collection(self, dirname):
        """Loads the file inside dirname into the photo browser."""
        images = glob.glob(os.path.join(dirname, '*.jpg'))
        png_images = glob.glob(os.path.join(dirname,'*.png'))
        images.extend(png_images)
        self.load_collection(images, monitor_dir=dirname)

    def load_recent_photos(self):
        """Loads the most recent photos (72hrs)."""
        images = glob.glob(
            os.path.join(config.get('collection.dir'), '*', '*.jpg'))
        png_images = glob.glob(
            os.path.join(config.get('collection.dir'), '*', '*.png'))
        images.extend(png_images)
        recent_time = time.time() - 72*3600
        images = [(os.path.getmtime(fname), fname) for fname in images]
        images = [pair for pair in images if pair[0] > recent_time]
        images = [pair[1] for pair in sorted(images, reverse=True)]
        self.load_collection(images)

    def load_collection(self, images, monitor_dir=None):
        """Loads a list of images into the photo browser."""
        model = gtk.ListStore(gobject.TYPE_STRING, gtk.gdk.Pixbuf,
                              gobject.TYPE_PYOBJECT)

        image_list = []
        for image in images:
            dirname, filename = os.path.split(image)
            basename, ext = os.path.splitext(filename)
            thumb = os.path.join(dirname,
                            '.thumbs', basename+'.thumbnail'+ext)
            info_file = os.path.join(dirname, basename) + '.inf'
            inf = infofile.parse_info_file(info_file)
            title = inf.get('title', basename)
            album = inf.get('albumTitle', dirname)
            credit = inf.get('credit', _('Not available'))
            tags = inf.get('tags', '')

            title = html_escape(title)
            album = html_escape(album)
            credit = html_escape(credit)
            tags = html_escape(tags)


            data = dict(title=title,
                        filename=image,
                        thumb=thumb,
                        inf = inf,
                        info_file = info_file,
                        album = album,
                        tags = tags,
                        file_time = os.path.getctime(image),
                        credit = credit)

            if len(title)>24:
                title = title[:21] + '...'
            if 0 <= time.time() - os.path.getmtime(image) < 24*3600:
                title = _('<b>*New* %s</b>') % title
            position = model.append((title, EMPTY_PICTURE, data))
            image_list.append(dict(
                position=position,
                data=data))
        old_model = self.iconview.get_model()
        if old_model is not None:
            old_model.clear()
        self.sort_photos(model)
        self.iconview.set_model(model)
        gobject.idle_add(ThumbLoader(self.iconview, model,
                         reversed(image_list)))
        self.on_iconview_handle_selection_changed(self.iconview)
        if gnomevfs:
            if self.collection_monitor['monitor'] is not None:
                gobject.idle_add(gnomevfs.monitor_cancel,
                                 self.collection_monitor['monitor'])
                self.collection_monitor = dict(monitor=None, dir=None)
            if monitor_dir:
                self.collection_monitor['dir'] = monitor_dir
                self.collection_monitor['monitor'] = gnomevfs.monitor_add(
                    monitor_dir,
                    gnomevfs.MONITOR_DIRECTORY,
                    self.collection_directory_changed)
        gc.collect()
        # this proves that pygtk has a memory leak, and it is related to
        # sorting.
        # print len([x for x in gc.get_objects() if
        #           isinstance(x, gtk.ListStore)])

    def on_set_as_wallpaper_handle_activate(self, _menu_item):
        """Sets the current photo as wallpaper."""
        selected = self.iconview.get_selected_items()
        if selected:
            selected = selected[-1]
        if selected:
            self.on_iconview_handle_item_activated(
                self.iconview,
                selected)

    def on_iconview_handle_item_activated(self, icon_view, path):
        """Implements an item activations: sets as wallpaper."""
        iterator = icon_view.get_model().get_iter(path)
        data = icon_view.get_model().get_value(iterator, IV_DATA_COLUMN)
        set_wallpaper(data['filename'])
        gc.collect()


    def on_view_fullscreen_handle_activate(self, _menu_item):
        """Called when fullscreen menuitem is clicked."""
        selected = self.iconview.get_selected_items()
        if selected:
            # FIXME: Make a nice slideshow here, maybe?
            selected = selected[-1]
            path = selected
            iterator = self.iconview.get_model().get_iter(path)
            data = self.iconview.get_model().get_value(iterator,
                IV_DATA_COLUMN)
            WebilderFullscreen.FullscreenViewer(self.top_widget, data).run()
        gc.collect()

    def on_download_photos_handle_activate(self, _menu_item):
        """Called when download photos is clicked."""
        def remove_reference(*_args):
            """Called when download dialog is closed."""
            self.download_dialog = None

        if not self.download_dialog:
            self.download_dialog = DownloadDialog.DownloadProgressDialog(config)
            self.download_dialog.top_widget.connect('destroy', remove_reference)
            self.download_dialog.show()
        else:
            self.download_dialog.top_widget.present()

    def on_iconview_handle_selection_changed(self, icon_view):
        """Called when the photo selection changed."""
        selection = icon_view.get_selected_items()
        if len(selection)>0:
            selection = selection[-1]
        title = album = credit = tags = ""
        if selection:
            iterator = icon_view.get_model().get_iter(selection)
            data = icon_view.get_model().get_value(iterator, IV_DATA_COLUMN)
            title = "<b>%s</b>" % data['title']
            album = data['album']
            credit = data['credit']
            tags = data['tags']

        self.photo_title.set_markup(title)
        self.photo_album.set_markup(album)
        self.photo_credit.set_markup(credit)
        self.photo_tags.set_markup(tags)

    def collection_directory_changed(self, *_args):
        """Called when a file changed under the collection directory."""
        self.on_tree_handle_selection_changed(self.tree.get_selection())

    def on_preferences_handle_activate(self, _menu_item):
        """Called when the preferences menu item was clicked."""
        configure()

    def on_iconview_handle_button_press_event(self, icon_view, event):
        """Handle mouse click events on the photo browser. Used for the right
        click popup menu."""
        if event.button == 3:
            xpos, ypos = [int(event.x), int(event.y)]
            path = icon_view.get_path_at_pos(xpos, ypos)
            if not path:
                return
            if not (event.state & gtk.gdk.CONTROL_MASK):
                icon_view.unselect_all()
            icon_view.select_path(path)

            self.image_popup.top_widget.popup(None, None, None, event.button,
                    event.time)
        return False

    def collection_tree_changed(self, *_args):
        """Called when the collection tree changes."""
        self.load_collection_tree(config.get('collection.dir'))

    def on_quit_handle_activate(self, _event):
        """Handles click on the quit menu item."""
        self.on_WebilderDesktopWindow_handle_delete_event(None, None)

    def on_about_handle_activate(self, _event):
        """Hanles the About menu item."""
        AboutDialog.show_about_dialog('Webilder Desktop')

    def on_WebilderDesktopWindow_handle_delete_event(self, _widget, _event):
        """"Handle window close event."""
        self.save_window_state()
        self.destroy()
        return False

    def save_window_state(self):
        """Save windows location and layout to config."""
        top = self.top_widget
        layout = {'window_position': top.get_position(),
                  'window_size': top.get_size(),
                  'hpaned_position': self.hpaned.get_position(),
                  'info_expander': self.photo_info_expander.get_expanded(),}
        config.set('webilder.layout', layout)
        config.save_config()

    def restore_window_state(self):
        """Restores windows location and layout from config."""
        d = config.get('webilder.layout')
        if d.has_key('window_position'):
            self.top_widget.move(*d['window_position'])
        if d.has_key('window_size'):
            self.top_widget.resize(*d['window_size'])
        if d.has_key('hpaned_position'):
            self.hpaned.set_position(d['hpaned_position'])
        if d.has_key('info_expander'):
            self.photo_info_expander.set_expanded(d['info_expander'])

    def on_file_webshots_import_handle_activate(self, _event):
        """Handle Import menu item."""
        dlg = gtk.FileChooserDialog(
            _('Choose files to import'),
            None,
            action=gtk.FILE_CHOOSER_ACTION_OPEN,
            buttons = (_("_Import"), gtk.RESPONSE_OK, _("_Cancel"),
                       gtk.RESPONSE_CANCEL))
        dlg.set_select_multiple(True)
        try:
            response = dlg.run()
            if response == gtk.RESPONSE_OK:
                files = dlg.get_filenames()
            else:
                files = []
        finally:
            dlg.destroy()
        import_files(files)

    def on_donate_handle_activate(self, _widget):
        """Donate menu item clicked."""
        donate_dialog = DonateDialog()
        donate_dialog.run()
        donate_dialog.destroy()

    def on_photo_properties_handle_activate(self, _event):
        """Called when photo properties has been clicked."""
        selected = self.iconview.get_selected_items()
        if not selected:
            return

        win = UITricks('ui/webilder.glade', 'PhotoPropertiesDialog')
        selected = selected[-1]
        path = selected
        iterator = self.iconview.get_model().get_iter(path)
        data = self.iconview.get_model().get_value(iterator,
            IV_DATA_COLUMN)
        win.title.set_markup('<b>%s</b>' % data['title'])
        win.album.set_markup(data['album'])
        win.file.set_text(data['filename'])
        win.tags.set_text(data['tags'])
        win.size.set_text(_('%.1f KB') % (os.path.getsize(data['filename']) /
                                          1024.0))
        win.date.set_text(time.strftime('%c', time.localtime(os.path.getctime(
            data['filename']))))
        win.url.set_text(data['inf'].get('url', ''))

        win.closebutton.connect('clicked', lambda *args: win.destroy())
        win.show()

    def sort_photos(self, model):
        """Sorts the photoso in the model."""
        if model is None:
            return

        def sort_by_date(data1, data2):
            """Use date sorting"""
            return -cmp(data1['file_time'], data2['file_time'])

        def sort_by_title(data1, data2):
            """Use title sorting"""
            return cmp(data1['title'], data2['title'])

        sort_func = {0: sort_by_title,
                     1: sort_by_date}[self.sort_combo.get_active()]
        model.set_default_sort_func(lambda m, iter1, iter2:
                sort_func(
                    m.get_value(iter1, IV_DATA_COLUMN),
                    m.get_value(iter2, IV_DATA_COLUMN),
                    ))
        model.set_sort_column_id(-1, gtk.SORT_ASCENDING)
        del model

    def on_sort_combo_handle_changed(self, _widget):
        """Called when the sort method changed."""
        self.sort_photos(self.iconview.get_model())

    def on_delete_handle_activate(self, _widget):
        """Called when photo delete menu item was clicked."""
        delete_files(self, forever=False)

class ImagePopup(UITricks):
    """Controller for the popup menu shown when a photo is right clicked."""

    # pylint: disable=C0103
    def __init__(self, main_window):
        self.main_window = main_window
        self.on_view_full_screen_handle_activate = (
            main_window.on_view_fullscreen_handle_activate)
        self.on_set_as_wallpaper_handle_activate = (
            main_window.on_set_as_wallpaper_handle_activate)
        self.on_photo_properties_handle_activate = (
            main_window.on_photo_properties_handle_activate)
        UITricks.__init__(self, 'ui/webilder_desktop.glade',
                          'WebilderImagePopup')

    def on_delete_images_handle_activate(self, _event):
        """Called when delete images menu item was clicked."""
        delete_files(self.main_window, forever=False)

    def on_delete_forever_handle_activate(self, _event):
        """Called when 'delete forever' images menu item was clicked."""
        delete_files(self.main_window, forever=True)

def delete_files(main_window, forever):
    """Delete the selected files."""
    iconview = main_window.iconview
    selected = iconview.get_selected_items()
    if selected and len(selected)>1:
        if forever:
            message = _('Would you like to permanently delete the '
                        'selected images?')
        else:
            message = _('Would you like to delete the selected images?')

        dlg = gtk.MessageDialog(type=gtk.MESSAGE_QUESTION,
            buttons=gtk.BUTTONS_YES_NO,
            message_format=message)
        response = dlg.run()
        dlg.destroy()
        if response != gtk.RESPONSE_YES:
            return

    banned = open(os.path.expanduser('~/.webilder/banned_photos'), 'a')
    model = iconview.get_model()

    monitor = main_window.collection_monitor
    if monitor['monitor'] is not None:
        gnomevfs.monitor_cancel(monitor['monitor'])
        monitor['monitor'] = None

    for path in selected:
        iterator = model.get_iter(path)
        data = model.get_value(iterator,
            IV_DATA_COLUMN)
        for fname in (data['filename'], data['info_file'], data['thumb']):
            try:
                os.remove(fname)
            except (IOError, OSError):
                pass
        if forever:
            banned.write(os.path.basename(data['filename'])+'\n')
        model.remove(iterator)

    if monitor['dir']:
        monitor['monitor'] = gnomevfs.monitor_add(
            monitor['dir'],
            gnomevfs.MONITOR_DIRECTORY,
            main_window.collection_directory_changed)

    banned.close()



HTML_ESCAPE_TABLE = {
    "&": "&amp;",
    '"': "&quot;",
    "'": "&apos;",
    ">": "&gt;",
    "<": "&lt;",
    }

def html_escape(text):
    """Produce entities within text."""
    output = []
    for char in text:
        output.append(HTML_ESCAPE_TABLE.get(char, char))
    return "".join(output)

class DonateDialog(UITricks):
    """Controller for the Donate dialog."""
    def __init__(self):
        UITricks.__init__(self, 'ui/webilder.glade', 'DonateDialog')
        text = _('''
Webilder is trying hard to make your desktop the coolest in town.

Since you installed it on %(inst_date)s, it downloaded <b>%(downloads)d photos</b>
for you and changed your wallpaper <b>%(rotations)d times</b>.

It takes a lot of time and hard work to develop and maintain Webilder.

If you'd like to see Webilder becomes even better, you can help us
a lot by making a small donation.

Any donation will be GREATLY appreciated. You can even donate $5.

After clicking on the <i>Yes</i> button below you'll be taken to
the donation page. If the page does not appear, please visit:
%(url)s

Would you like to donate to Webilder?
''')

        stats = config.get('webilder.stats')
        self.url = 'http://www.webilder.org/donate.html'
        context = dict(
                downloads = stats['downloads'],
                rotations = stats['rotations'],
                inst_date = time.strftime('%B %Y'),
                url = self.url
                )

        self.donate_copy.set_markup(text % context)

    def run(self):
        val = UITricks.run(self)
        if val == 0:
            open_browser(self.url, no_browser_title=_('Thank You!'),
                         no_browser_markup=_(
                             '<b>Thanks for your interest in supporting '
                             'Webilder.</b>\n\n'
                             'Please follow this link to send us a '
                             'donation:\n\n%s') % self.url)


def configure():
    """Shows the configuration dialog."""
    reload_config()
    config_dialog.ConfigDialog().run_dialog(config)


def import_files(files):
    success_count = 0
    for afile in files:
        try:
            success_count += wbz_handler.handle_file(afile)
        except (IOError, KeyError, ValueError), e:
            mbox = gtk.MessageDialog(type=gtk.MESSAGE_ERROR,
                                     buttons=gtk.BUTTONS_OK)
            mbox.set_title(_("File import error."))
            mbox.set_markup(_("Could not import '%s': %s") % (afile, e))
            mbox.run()
            mbox.destroy()

    if success_count:
        mbox = gtk.MessageDialog(type=gtk.MESSAGE_INFO,
                                 buttons=gtk.BUTTONS_OK)
        mbox.set_title(_("Import complete."))
        mbox.set_markup(_("%d photos have been added to your collection.")
                        % success_count)
        mbox.run()
        mbox.destroy()


def main():
    """Command line entrypoint."""
    parser = optparse.OptionParser()
    parser.add_option(
        '--configure', dest="configure", help="Open configuration dialog"
        "and quit.", action="store_true", default=False)
    parser.add_option(
        '--download', dest="download", help="Download photos and quit.",
        action="store_true", default=False)
    options, args = parser.parse_args()

    gtk.gdk.threads_init()
    if options.configure:
        configure()
        return

    if options.download:
        download_dialog = DownloadDialog.DownloadProgressDialog(config)
        main_window = download_dialog
        download_dialog.top_widget.connect('destroy', gtk.main_quit)
        download_dialog.show()
        gtk.main()
        return

    if args:
        import_files(args)
        return

    main_window = WebilderDesktopWindow()
    main_window.top_widget.connect("destroy", gtk.main_quit)
    gtk.main()

if __name__ == "__main__":
    main()
