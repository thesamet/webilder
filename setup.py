#!/usr/bin/env python

from distutils.core import setup
from distutils.cmd import Command
from distutils.util import change_root

from distutils.command.build import build as _build
from distutils.command.install import install as _install
from distutils.spawn import find_executable
from distutils.errors import DistutilsError

import os
import sys

if sys.argv[-1] == 'setup.py':
    print "To install, run 'python setup.py install'"
    print 

class file_build_command(Command):
    def initialize_options(self):
        self.build_lib = None
        self.install_scripts = None
        self.install_data = None

    def finalize_options(self):
        self.set_undefined_options('build', 
                ('build_lib', 'build_lib'))
        self.set_undefined_options('install', 
                ('install_scripts', 'install_scripts'),
                ('install_data', 'install_data'),
            )
        inst_cmd = self.get_finalized_command('install')
        if inst_cmd.root is not None:
            self.install_scripts = inst_cmd._original_install_scripts
            self.install_data = inst_cmd._original_install_data


    def run(self):
        dest_dir = self.get_dest_dir()
        self.mkpath(dest_dir)
        fc = file(os.path.join(self.dir, self.filename + '.in'), 'r').read()
        fw = file(os.path.join(dest_dir, self.filename), 'w')
        fw.write(fc % dict(
            bin_dir = self.install_scripts,
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
        print """
Installation completed successfully.

  GNOME Users: Right-click on the GNOME panel, choose "Add to panel", 
               and select "Webilder Webshots Applet".  If it
               is not in the list - log off and log in again.

  KDE Users:   From the graphics menu, start KWebilder.

If you prefer the command line, you can run webilder_desktop
to configure Webilder and manage your photos. It is also
possible to start photo downloading from the command line by
starting webilder_downloader.  

Please report any problem to thesamet at gmail.com. 
"""

    def change_roots(self, *names):
        # in case we are going to perform a rooted install, store the original
        # path names, so we can use them in file_build_command's.
        for name in names:
            attr = 'install_' + name
            backup_attr = '_original_install_' + name
            setattr(self, backup_attr, getattr(self, attr))
        _install.change_roots(self, *names)


    def get_outputs(self):
        # webilder_globals will now go to the installation record, which is required
        # in order to build RPMs
        return (_install.get_outputs(self) + 
               [os.path.join(self.install_lib, 'webilder/webilder_globals.py'),
                os.path.join(self.install_lib, 'webilder/webilder_globals.pyc')])

class install_kde(Command):
    user_options = []

    def initialize_options(self):
        self.kde_prefix = None
        self.root = None

    def finalize_options(self):
        self.set_undefined_options('install', ('kde_prefix', 'kde_prefix'), ('root', 'root'))
        if self.kde_prefix is None:
            self.announce('Detecting KDE installation directory')
            self.kde_prefix = ask_kde_config('--prefix').strip()
            if not self.kde_prefix:
                raise DistutilsError, 'Could not detect KDE installation directory. Please provide --kde-prefix argument'
            self.announce('KDE installation directory is '+self.kde_prefix)
            if self.root is not None:
                self.kde_prefix = change_root(self.root, self.kde_prefix)

    def run(self):
        check_modules('qt', 'kdecore', 'kdeui')
        dir = os.path.join(self.kde_prefix, 'share', 'applications', 'kde')
        self.mkpath(dir)
        self.copy_file(
                'desktop/kwebilder.desktop', 
                os.path.join(dir, 'kwebilder.desktop'))

        dir = os.path.join(self.kde_prefix, 'share', 'icons', 'hicolor', '48x48', 'apps')
        self.mkpath(dir)
        self.copy_file(
                'ui/camera48.png', 
                os.path.join(dir, 'webilder.png'))

        dir = os.path.join(self.kde_prefix, 'bin')
        self.mkpath(dir)
        kwebilder = os.path.join(dir, 'kwebilder')
        self.copy_file(
                'scripts/kwebilder', 
                kwebilder
                )
        os.chmod(kwebilder, 0755)


setup(name='Webilder',
      version='0.6.3',
      description='Webilder Desktop',
      author='Nadav Samet',
      author_email='thesamet@gmail.com',
      url='http://www.webilder.org',
      packages=['webilder', 'webilder.webshots', 'webilder.flickr'],
      package_dir = {'webilder': 'src'},
      cmdclass = {'build': build, 'build_server': build_server, 'build_globals': build_globals, 'install': install, 'install_kde': install_kde},
      data_files = [
        (os.path.join('share', 'webilder'), ['ui/config.glade', 'ui/webilder.glade', 'ui/webilder_desktop.glade', 'ui/camera48.png', 'ui/camera48_g.png', 'ui/camera16.png', 'ui/logo.png', 'ui/camera16.xpm']),
        (os.path.join('share', 'pixmaps'), ['ui/camera48.png']),
        (os.path.join('share', 'applications'), ['desktop/webilder_desktop.desktop']),
        (os.path.join('lib', 'bonobo', 'servers'), ['servers/GNOME_WebilderApplet.server']),
      ],
      scripts = ['scripts/webilder_downloader', 'scripts/webilder_desktop', 'scripts/WebilderApplet', 'scripts/wbz_handler']
)
