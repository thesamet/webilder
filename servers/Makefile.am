serverdir = $(libdir)/bonobo/servers
server_in_files = GNOME_WebilderApplet.server.in
server_DATA = $(server_in_files:.server.in=.server)

pixmapsdir = $(pkgdatadir)

$(server_DATA): $(server_in_files) Makefile
	sed -e "s|\@bindir\@|$(bindir)|g"       \
	    -e "s|\@pixmapsdir\@|$(pixmapsdir)|g" \
		< $< > $@

EXTRA_DIST =  			\
	$(server_in_files)		

DISTCLEANFILES = \
	$(server_DATA)
