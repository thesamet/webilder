#                                               -*- Autoconf -*-
# Process this file with autoconf to produce a configure script.

AC_PREREQ(2.59)
AC_INIT([webilder], 0.4, [thesamet@gmail.com])
AM_INIT_AUTOMAKE

AC_PREFIX_DEFAULT(/usr)

AM_MAINTAINER_MODE
# Checks for programs.

AC_PROG_LN_S
AM_PATH_PYTHON(2.3)

# Checks for libraries.

PKG_CHECK_MODULES(PYGTK, pygtk-2.0 >= 2.6)

# Checks for header files.

# Checks for typedefs, structures, and compiler characteristics.

# Checks for library functions.

AC_CONFIG_FILES([Makefile
                 images/Makefile
                 servers/Makefile
                 src/Makefile])

AC_OUTPUT
