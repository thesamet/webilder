globalsfile = webilder_globals.py
globalsfile_in = webilder_globals.py.in

pkgpython_SCRIPTS = \
	AboutDialog.py      WebilderFullscreen.py  plugins.py    uitricks.py \
	DownloadDialog.py   config.py              		         wbz_handler.py \
	WebilderApplet.py   config_dialog.py       progress_dialog.py         \
	WebilderDesktop.py  downloader.py          thumbs.py     base_applet.py\
	KWebilder.py
	$(globalsfile)

nobase_pkgpython_SCRIPTS = \
	webshots/__init__.py  webshots/utils.py  webshots/wbz.py \
	webshots/fileutil.py  webshots/wbp.py         \
	flickr/__init__.py flickr/flickrapi.py

uidir = $(pkgdatadir)

$(globalsfile): $(globalsfile_in) Makefile
	sed -e "s|\@uidir\@|$(uidir)|g"       \
	    -e "s|\@VERSION\@|$(VERSION)|g" \
                < $< > $@

DISTCLEANFILES = \
	$(globalsfile)

install-exec-hook:
	$(mkdir_p) $(DESTDIR)$(bindir) && \
	cd $(DESTDIR)$(bindir) && \
	$(RM) webilder webilder_desktop wbz_handler && \
	$(LN_S) $(pkgpythondir)/WebilderApplet.py webilder && \
	$(LN_S) $(pkgpythondir)/WebilderDesktop.py webilder_desktop && \
	$(LN_S) $(pkgpythondir)/wbz_handler.py wbz_handler

EXTRA_DIST =                    \
    $(pkgpython_SCRIPTS) $(nobase_pkgpython_SCRIPTS) $(globalsfile_in)

