import pygtk
import gtk
import gtk.glade

pygtk.require("2.0")

class IconList(gtk.Button):
    def __init__(self):
        super(IconList, self).__init__('Hello')
        self.connect('expose-event', self.expose)
        self.show()

    def expose(self, *args):
        print args
    

app = gtk.Window()
app.add(IconList())
app.connect('destroy', gtk.main_quit)
app.show()
gtk.main()

