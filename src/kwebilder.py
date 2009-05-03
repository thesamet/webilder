import sys, os

from qt import QPixmap, SIGNAL, QIconSet, Qt, QTimer, QToolTip

from kdecore import KApplication, i18n, KAboutData, KCmdLineArgs, KStandardDirs, KShortcut
from kdeui import KSystemTray, KStdAction, KAction, KAboutDialog

import webilder_globals as aglobals

import threading
from config import config

from base_applet import BaseApplet
import popen2

class WebilderTray(KSystemTray, BaseApplet):
    def __init__(self):
        BaseApplet.__init__(self)
        KSystemTray.__init__(self, None, 'Webilder')
        pixmap = QPixmap(os.path.join(
            aglobals.glade_dir, 'camera16.png'))
        self.setPixmap (pixmap)
        self.setCaption('Webilder')
        self.launchers = {}

        actions = self.actionCollection()
        context = self.contextMenu()

        browse = KAction(_('&Browse Collection'), 'folder_open', KShortcut(), self.browse, actions, 'browse')
        browse.plug(context)

        next = KAction(_('&Next Photo'), 'next', KShortcut(), self.next_photo, actions, 'next')
        next.plug(context)

        download = KAction(_('&Download Photos'), QIconSet(pixmap), KShortcut(), self.download, actions, 'download')
        download.plug(context)
		
        trash = KAction('&Delete Current', 'trashcan_full', KShortcut(), self.trash, actions, 'trash')
        trash.plug(context)
		
        preferences = KStdAction.preferences(self.preferences, actions)
        preferences.plug(context)

        self.timer = QTimer(self)
        self.connect(self.timer, SIGNAL('timeout ()'), self.timer_event)
        self.timer.start(60*1000)

    def _launch_unique_app(self, args, name):
        app = self.launchers.get(name, None)
        if app is not None:
            if app.poll()==-1:
                # process is alive
                app.tochild.write('present\n')
                app.tochild.flush()
                return
            else:
                app = self.launchers[name] = None

        self.launchers[name] = launch_webilder(args)


    def browse(self):
        self._launch_unique_app('', 'webilder')

    def download(self):
        self._launch_unique_app('--download', 'download')

    def trash(self):
        if self.image_file != '':
            try:
              jpg_file = self.image_file 
              inf_file = self.info_file

              self.next_photo()
              os.remove(jpg_file)
              os.remove(inf_file)
            except:
              pass
        else:
          self.next_photo()

    def preferences(self):
        launch_webilder('--configure')

    def mousePressEvent(self, event):
        KSystemTray.mousePressEvent(self, event)
        if event.button() == Qt.LeftButton:
            self.browse()

    def set_tooltip(self, text):
        QToolTip.add(self, text)

def launch_webilder(args=''):
    webilder_dir = os.path.dirname(__file__)
    return popen2.Popen3('python '+os.path.join(webilder_dir, 'WebilderDesktop.py') + ' --kwebilder ' +args)

def get_about_data():
    return KAboutData('webilder', 'Webilder', aglobals.version,
                'Photo downloader', KAboutData.License_GPL, 
                '(c) 2005-2008, Nadav Samet',
                '',
                'http://www.webilder.org/',
                'thesamet@gmail.com')

def main():
    about = get_about_data()
    KCmdLineArgs.init(sys.argv, about)
    app = KApplication()
    webilder_tray = WebilderTray()
    webilder_tray.show()
    app.connect(webilder_tray, SIGNAL("quitSelected ()"), app.quit)
    app.setMainWidget(webilder_tray)
    app.exec_loop()


if __name__=="__main__":
    main()
