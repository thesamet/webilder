#!/usr/bin/env python

from distutils.core import setup
from distutils.cmd import Command

from distutils.command.build import build as _build
from distutils.command.install import install as _install

import os

class file_build_command(Command):
    def initialize_options(self):
        self.build_base = None
        self.build_lib = None
        self.install_dir = None
        self.install_data = None

    def finalize_options(self):
        self.set_undefined_options('build', 
                ('build_base', 'build_base'),
                ('build_lib', 'build_lib'))
        self.set_undefined_options('install', 
                ('install_scripts', 'install_dir'),
                ('install_data', 'install_data'),
            )

    def run(self):
        dest_dir = self.get_dest_dir()
        self.mkpath(dest_dir, 1)
        fc = file(os.path.join(self.dir, self.filename + '.in'), 'r').read()
        fw = file(os.path.join(dest_dir, self.filename), 'w')
        fw.write(fc % dict(
            bin_dir = self.install_dir,
            data_dir = os.path.join(self.install_data, 'share', 'webilder'),
            version = self.distribution.get_version()))
        fw.close()

class build_server(file_build_command):
    description ='Builds the bonobo server file representing the applet.'
    dir = 'servers'
    filename = 'GNOME_WebilderApplet.server'
    get_dest_dir = lambda self: 'servers'

class build_globals(file_build_command):
    description = 'Building Webilder global settings file.'
    dir = 'src'
    filename = 'webilder_globals.py'
    get_dest_dir = lambda self: os.path.join(self.build_lib, 'webilder')

class build(_build):
    sub_commands = []
    sub_commands.extend(_build.sub_commands)
    sub_commands.append(('build_server', None))
    sub_commands.append(('build_globals', None))

class install_links(Command):
    def initialize_options(self):
        self.install_dir = None
        self.install_lib = None

    def finalize_options(self):
        self.set_undefined_options('install', 
                ('install_lib', 'install_lib'),
                ('install_scripts', 'install_dir'))
        
    def run(self):
        self.mkpath(self.install_dir)
        for src, dest in [('WebilderDesktop.py', 'webilder_desktop'), 
                ('wbz_handler.py', 'wbz_handler'),
                ('WebilderApplet.py', 'WebilderApplet')]:
            src = os.path.join(self.install_lib, 'webilder', src)
            dest = os.path.join(self.install_dir, dest)
            try:
                os.unlink(dest)
            except OSError:
                pass
            os.symlink(src, dest)
            os.chmod(src, 0755)
        
class install(_install):
    sub_commands = []
    sub_commands.extend(_install.sub_commands)
    sub_commands.append(('install_links', None))

class install_kde(Command):
    description = 'Install support for KDE system tray.'
    sub_commands = [
        ('install_kde_icons', None), 
        ('install_kde_script', None)]

setup(name='Webilder',
      version='0.5',
      description='Webilder Desktop',
      author='Nadav Samet',
      author_email='thesamet@gmail.com',
      url='http://www.webilder.org',
      packages=['webilder', 'webilder.webshots', 'webilder.flickr'],
      package_dir = {'webilder': 'src'},
      cmdclass = {'build': build, 'build_server': build_server, 'build_globals': build_globals, 'install': install, 'install_links': install_links, 'install_kde': install_kde},
      data_files = [
        (os.path.join('share', 'webilder'), ['ui/config.glade', 'ui/webilder.glade', 'ui/webilder_desktop.glade', 'ui/camera48.png', 'ui/camera48_g.png', 'ui/camera16.png', 'ui/logo.png']
        ),
        (os.path.join('lib', 'bonobo', 'servers'), ['servers/GNOME_WebilderApplet.server'])
      ],
      scripts= ['scripts/webilder_downloader']
     )
