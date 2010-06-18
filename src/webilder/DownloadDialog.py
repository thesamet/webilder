'''
File    : DownloadDialog.py
Author  : Nadav Samet
Contact : thesamet@gmail.com
Date    : 2010 Jun 17

Description : Download dialog
'''

from webilder import progress_dialog
from webilder import downloader
from webilder import webshots


class DownloadProgressDialog(progress_dialog.ProgressDialog):
    """Dialog that shows download progress."""
    def __init__(self, config):
        progress_dialog.ProgressDialog.__init__(
            self, text=_("<b>Downloading photos</b>\n\nDownloading photos..."
                         "Download times vary according to your connection "
                         "speed.."""))
        self.leech_thread = LeechThread(self, config)
        self.leech_thread.start()

class LeechThread(progress_dialog.ProgressThread):
    """The thread that does the actual work."""
    def __init__(self, pdialog, config):
        progress_dialog.ProgressThread.__init__(self, pdialog)
        self.config = config

    @progress_dialog.progress_thread_run
    def run(self):
        try:
            downloader.download_all(notify=self.status_notify,
                                    terminate = self.should_terminate)
        except webshots.utils.LeechHighQualityForPremiumOnlyError:
            self.safe_message_dialog(
                            _("<b>Only Webshots Premium members can download "
                            "wide or highest quality photos.</b>\n\n"
                            'Go to the Preferences window, choose "Regular '
                            'Quality" and try again.'))
        except webshots.utils.WBZLoginException:
            self.safe_message_dialog(
                            _("<b>Incorrect Webshots Username or Password</b>"
                              "\n\nPlease check your username and password in"
                              " the preferences dialog."))
        except (IOError, ValueError), exc:
            self.safe_message_dialog(
                            _('<b>Error occured while downloading '
                              'images</b>\n\n%s') % html_escape(str(exc)))
            raise exc


def html_escape(text):
    """Produce entities within text."""
    output = []
    for char in text:
        output.append(HTML_ESCAPE_TABLE.get(char, char))
    return "".join(output)

HTML_ESCAPE_TABLE = {
    "&": "&amp;",
    '"': "&quot;",
    "'": "&apos;",
    ">": "&gt;",
    "<": "&lt;",
    }
