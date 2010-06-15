import os
import gtk
import threading

from progress_dialog import *

class DownloadProgressDialog(ProgressDialog):
    def __init__(self, config):
        ProgressDialog.__init__(self, text=_("""<b>Downloading photos</b>

Downloading photos... Download times vary according to your connection speed.."""))
        self.leech_thread = LeechThread(self, config)
        self.leech_thread.start()

class LeechThread(ProgressThread):
    def __init__(self, pdialog, config):
        ProgressThread.__init__(self, pdialog)
        self.config=config

    @progress_thread_run
    def run(self):
        import downloader
        import webshots
        try:
            downloader.download_all(notify=self.status_notify, terminate = self.should_terminate)
        except webshots.utils.LeechHighQualityForPremiumOnlyError:
            self.safe_message_dialog(
                            _("<b>Only Webshots Premium members can download "
                            "wide or highest quality photos.</b>\n\n"
                            'Go to the Preferences window, choose "Regular Quality" and try again.'))
        except webshots.utils.WBZLoginException:
            self.safe_message_dialog(
                            _("<b>Incorrect Webshots Username or Password</b>\n\n"
                            'Please check your username and password in the preferences dialog.'))
        except (IOError, ValueError), e:
            self.safe_message_dialog(
                            _("<b>Error occured while downloading images</b>\n\n%s") % html_escape(str(e)))
            raise e


def html_escape(text):
    """Produce entities within text."""
    L=[]
    for c in text:
        L.append(html_escape_table.get(c,c))
    return "".join(L)

html_escape_table = {
    "&": "&amp;",
    '"': "&quot;",
    "'": "&apos;",
    ">": "&gt;",
    "<": "&lt;",
    }
