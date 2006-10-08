#!/usr/bin/env python

from distutils.core import setup
from distutils.cmd import Command

from distutils.command.build import build as _build
from distutils.command.install import install as _install
from distutils.spawn import find_executable
from distutils.errors import DistutilsError

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
    sub_commands = _build.sub_commands[:]
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
        
def ask_kde_config(question):
    # Look for the kde-config program
    kdeconfig = find_executable("kde-config", os.environ['PATH'] + os.pathsep + \
        os.pathsep.join(['/bin','/usr/bin','/opt/kde3/bin','/opt/kde/bin','/usr/local/bin']))
    if kdeconfig!=None:
        # Ask the kde-config program for the
        fhandle = os.popen(kdeconfig+' ' + question,'r')
        result = fhandle.read()
        fhandle.close()
        return result
    else:
        return None

def check_modules(*modules):
    for module in modules:
        import imp
        try:
            imp.find_module(module)
        except ImportError, e:
            raise DistutilsError, 'Could not find module %s. Make sure all dependencies are installed.' % e

class install(_install):
    user_options = _install.user_options[:]
    user_options.append(('with-kde', None, 'Install with KDE support'))
    user_options.append(('kde-prefix=', None, 'Base directory of KDE installation'))

    sub_commands = _install.sub_commands[:]
    sub_commands.append(('install_links', None))

    def initialize_options(self):
        self.with_kde = False
        self.kde_prefix = None
        _install.initialize_options(self)

    def finalize_options(self):
        _install.finalize_options(self)

    def run(self):
        check_modules('gtk', 'pygtk', 'gnome', 'gnomeapplet')
        _install.run(self)
        if self.with_kde:
            self.run_command('install_kde')

class install_kde(Command):
    user_options = []

    def initialize_options(self):
        self.kde_prefix = None

    def finalize_options(self):
        self.set_undefined_options('install', ('kde_prefix', 'kde_prefix'))
        if self.kde_prefix is None:
            self.announce('Detecting KDE installation directory')
            self.kde_prefix = ask_kde_config('--prefix').strip()
            if not self.kde_prefix:
                raise DistutilsError, 'Could not detect KDE installation directory. Please provide --kde-prefix argument'
            self.announce('KDE installation directory is '+self.kde_prefix)

    def run(self):
        check_modules('qt', 'kdecore', 'kdeui')
        self.copy_file(
                'desktop/kwebilder.desktop', 
                os.path.join(self.kde_prefix, 'share', 'applications', 'kde', 'kwebilder.desktop'))

        self.copy_file(
                'ui/camera48.png', 
                os.path.join(self.kde_prefix, 'share', 'icons', 'hicolor', '48x48', 'apps', 'webilder.png'))

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
        (os.path.join('share', 'webilder'), ['ui/config.glade', 'ui/webilder.glade', 'ui/webilder_desktop.glade', 'ui/camera48.png', 'ui/camera48_g.png', 'ui/camera16.png', 'ui/logo.png']),
        (os.path.join('share', 'pixmaps'), ['ui/camera48.png']),
        (os.path.join('share', 'applications'), ['desktop/webilder_desktop.desktop']),
        (os.path.join('lib', 'bonobo', 'servers'), ['servers/GNOME_WebilderApplet.server']),
      ],
      scripts = ['scripts/webilder_downloader']
)
