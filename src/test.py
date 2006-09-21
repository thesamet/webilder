import config
from flickr.configure import *

app = FlickrDialog()
app.load_config(config.ConfigObject('webilder.conf'))

app.show()
gtk.main()

