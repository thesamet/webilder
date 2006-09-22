import pygtk
import gtk
import gtk.glade
import os
import webilder_globals as aglobals

from uitricks import UITricks

pygtk.require("2.0")

rotation_consts = {
    1: '1 minute',
    2: '2 minutes',
    5: '5 minutes',
    10: '10 minutes',
    20: '20 minutes',
    30: '30 minutes',
    60: '1 hour',
    120: '2 hours',
    240: '4 hours',
    24*60: '1 day'}
quality_names = ['high', 'wide', 'low']

class ConfigDialog(UITricks):
    def __init__(self):
        UITricks.__init__(self, os.path.join(aglobals.glade_dir, 'config.glade'), 'config_dialog')
        self.on_flickr_enabled__toggled()
        self.on_webshots_enabled__toggled()
        self.on_autodownload_bool__toggled()
        self.on_rotate_bool__toggled()
        self.on_wallpaper_use_script__toggled()

        for index, value in enumerate(['Album', 'Tags']):
            cell = gtk.CellRendererText()
            cell.set_property('editable', True)
            column = gtk.TreeViewColumn(value, cell, text=index)
            column.set_resizable(True)
            self.flickr_rules.append_column(column)
            cell.connect('edited', self.on_cell_edited, index)
        self.rotate_interval.get_model().clear()
        for time in sorted(rotation_consts.keys()):
            self.rotate_interval.append_text(rotation_consts[time])
        self.wallpaper_widgets = dict(gnome=self.wallpaper_use_gnome,
                kde=self.wallpaper_use_kde,
                script=self.wallpaper_use_script)
             

    def run_dialog(self, config):
        self.load_config(config)
        while 1:
            response = self.run()
            if response != 0:
                break

            cdir = self.collection_dir.get_text()
            if not os.path.exists(cdir):
                mb = gtk.MessageDialog(type=gtk.MESSAGE_QUESTION, buttons=gtk.BUTTONS_YES_NO, message_format=
                    "Collection directory %s does not exist. Would you like it to be created?" % cdir)
                mbval = mb.run()
                mb.destroy()
                if (mbval == gtk.RESPONSE_YES):
                    os.mkdir(cdir)
                else:
                    self.collection_dir.grab_focus()
                    continue

            if not os.path.isdir(cdir):
                mb = gtk.MessageDialog(type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK, message_format="%s is not a directory." % cdir)
                mb.run()
                mb.destroy()
                self.collection_dir.grab_focus()
                continue
            
            self.update_config(config)
            config.save_config()
            break
        self._top.destroy()

    def load_config(self, config):
        # general tab
        self.rotate_bool.set_active(config.get('rotate.enabled'))
        interval = config.get('rotate.interval')
        if interval not in rotation_consts:
            if interval<=0:
                interval = 1
            interval = max([t for t in rotation_consts.keys() if t<=interval])
        interval = sorted(rotation_consts.keys()).index(interval)
        self.rotate_interval.set_active(interval)

        self.autodownload_bool.set_active(config.get('autodownload.enabled'))
        self.autodownload_interval.set_value(config.get('autodownload.interval'))


        # flickr tab
        self.flickr_enabled.set_active(config.get('flickr.enabled'))
        model = gtk.ListStore(str, str)
        for rule in config.get('flickr.rules'):
            model.append([rule['album'], rule['tags']])
        self.flickr_rules.set_model(model)

        # webshots tab
        self.webshots_enabled.set_active(config.get('webshots.enabled'))
        self.webshots_username.set_text(config.get('webshots.username'))
        self.webshots_password.set_text(config.get('webshots.password'))
        quality = config.get('webshots.quality')
        if quality not in quality_names:
            quality = 'low'
        getattr(self, quality).set_active(True)

        # advanced tab
        self.collection_dir.set_text(config.get('collection.dir'))
        wallpaper_active_widget = self.wallpaper_widgets.get(
                config.get('webilder.wallpaper_set_method'), self.wallpaper_use_gnome)
        wallpaper_active_widget.set_active(True)
        self.script.set_text(config.get('webilder.wallpaper_script'))


    def update_config(self, config):
        # rotator tab
        config.set('rotate.enabled', self.rotate_bool.get_active())
        config.set('rotate.interval', sorted(rotation_consts.keys())[
            self.rotate_interval.get_active()])

        config.set('autodownload.enabled', self.autodownload_bool.get_active())
        config.set('autodownload.interval', self.autodownload_interval.get_value())

        # flickr tab
        config.set('flickr.enabled', self.flickr_enabled.get_active())
        rules = []
        for rule in self.flickr_rules.get_model():
            rules.append({'album': rule[0], 'tags': rule[1], 'tagmode': 'ALL'})
        config.set('flickr.rules', rules)

        # webshots tab
        config.set('webshots.enabled', self.webshots_enabled.get_active())
        config.set('webshots.username', self.webshots_username.get_text())
        config.set('webshots.password', self.webshots_password.get_text())
        config.set('webshots.cookie', '')

        res = 'low'
        for q in quality_names:
            if getattr(self, q).get_active():
                res = q
        config.set('webshots.quality', res)

        # advanced tab
        config.set('collection.dir', self.collection_dir.get_text())
        use = 'gnome'
        for name, widget in self.wallpaper_widgets.iteritems():
            if widget.get_active():
                use = name
        config.set('webilder.wallpaper_set_method', use)
        config.set('webilder.wallpaper_script', self.script.get_text())
        

    def on_rotate_bool__toggled(self, *args):
        self.rotate_interval.set_sensitive(self.rotate_bool.get_active())

    def on_autodownload_bool__toggled(self, *args):
        self.autodownload_interval.set_sensitive(self.autodownload_bool.get_active())

    def on_flickr_enabled__toggled(self, *args):
        self.flickr_frame.set_sensitive(self.flickr_enabled.get_active())

    def on_webshots_enabled__toggled(self, *args):
        self.webshots_login_frame.set_sensitive(self.webshots_enabled.get_active())
        self.webshots_res_frame.set_sensitive(self.webshots_enabled.get_active())

    def on_wallpaper_use_script__toggled(self, *args):
        self.script.set_sensitive(self.wallpaper_use_script.get_active())

    def on_add__clicked(self, widget):
        iter = self.flickr_rules.get_model().append(['Album Name','tag1,tag2'])
        # self.flickr_rules.scroll_to_cell(path)
        
    def on_remove__clicked(self, widget):
        model, iter = self.flickr_rules.get_selection().get_selected()
        if iter:
            model.remove(iter)

    def on_flickr_rules__selection_changed(self, *args):
        self.remove.set_sensitive(
                self.flickr_rules.get_selection().get_selected()[1] is not None)

    def on_cell_edited(self, cell, path, new_text, data):
        if data==1:
            new_text = new_text.split(',')
            new_text = [tag.strip() for tag in new_text]
            new_text = ','.join(new_text)

        self.flickr_rules.get_model()[path][data] = new_text

    def on_directory_browse__clicked(self, sender):
        fs = gtk.FileChooserDialog(action=gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER,
                buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OK,gtk.RESPONSE_OK))
        if fs.run()==gtk.RESPONSE_OK:
            self.collection_dir.set_text(fs.get_filename())
        fs.destroy()
