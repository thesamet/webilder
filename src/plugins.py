plugin_names = ['flickr', 'webshots']

plugins = {}

for plugin in plugin_names:
    plugins[plugin] = __import__(plugin, globals(), locals())
