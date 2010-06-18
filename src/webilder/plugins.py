'''
File    : plugins.py
Author  : Nadav Samet
Contact : thesamet@gmail.com
Date    : 2010 Jun 17

Description : List of available webilder plugins.
'''
PLUGIN_NAMES = ['flickr', 'webshots']

PLUGINS = {}

for plugin in PLUGIN_NAMES:
    PLUGINS[plugin] = __import__(plugin, globals(), locals())
