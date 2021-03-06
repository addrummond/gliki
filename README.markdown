**Note:** This is an old Wiki engine that I wrote for a linguistics Wiki many years ago. Not useful now, but there is some interesting code in here. For example, the Python parser combinator library (`parcombs.py`) which is used to parse the Wiki syntax (`sourceparser.py`).

1. Introduction
----------
This is the software behind the Gliki website, licensed under the GPL (see
the LICENSE file for details). The software is written by Alex Drummond
<a.d.drummond@gmail.com>, with much work on the HTML and CSS by James Adams
("Mue", http://www.bluezen.co.uk/james).


2. Running Gliki
----------
First, check that you have all the dependencies listed in the DEPENDENCIES file
installed and working correctly.

I assume you are using some sort of vaguely Unixy system. It is (almost
certainly) possible to run Gliki on Windows, but it would be necessary to
install some sort of Unix environment (e.g. Cygwin) and I haven't actually
tested it on Windows.

First, do the following in the main Gliki directory:

    * Execute 'sh build_main.css.sh' to build the CSS file.
    * Execute 'sh compile_templates.sh' to compile the Cheetah templates.
    * Create an sqlite3 database called main.db using the sql script
      'dbcreate.sql'. (Use the '.read' command at the sqlite3 prompt.)
    * Execute 'python gliki.py'

The last command starts the website on port 3000. You can change the port by
editing etc/config.py. Note that this uses a toy Python webserver which you
really shouldn't expose to the internet directly; the real Gliki site hides it
behind Apache. Way back when, it was also possible to run Gliki on lighttpd
using fastcgi, and the code to do so is still included. However, I haven't
tested it for ages and it's not documented here (see mostly control.py if you're
interested, and the included httpd.conf for lighttpd).


3. Configuration and customization
----------
By default, Gliki looks exactly like the Gliki website. You can make basic
changes (e.g. changing the name of the site) by editing the etc/customize.tmpl
template. You'll need to look at the Cheetah template system documentation if
you want to do anything advanced, but the basic format should be fairly
intuitive. Note that comment lines must begin with two '#' characters in a
row (a single '#' is used to indicate the start of a Cheetah directive).
After making changes to customize.tmpl (or any other .tmpl file) you must
execute 'sh compile_templates.sh' and restart gliki.py.

Various configuration options (e.g. the port the server runs on) can be set
by editing etc/config.py.

The CSS file (main.css) should not be edited directly since it's built using
the m4 macro prepocessor. Instead, edit main.css.m4 and run
'sh buld_main.css.sh' to generate main.css. More extensive changes to the site's
appearence will require editing the templates in the 'templates' directory.

If you want to change the URIs for various parts of the
site (e.g. if you want to use "/pages/Gliki" instead of "/articles/Gliki")
you can edit links.py. This file defines a number of string constants and should
be fairly self-explanatory.


4. Blocking users.
----------
You can block users, either by username or by IP address, by editing the
etc/block file in the main Gliki directory (it is not necessary to restart Gliki
after editing the file for the changes to take effect).

The block file has the following syntax. Lines beginning with '#' are ignored.
A line containing an IP address specifies that the IP address should be
blocked; similarly for a line containing a username. It is also possible to
specify IP address ranges, as in the following examples:

    83.64.77.*
    56-66.5.6-8.8

The first line specifies that any IP address beginning 83.64.77 should be
blocked. The second line blocks any IP address with first number 56-66
inclusive, second number 5, third number 6-8 inclusive, and last number 8.
Here's an example block file:

    # A comment.
    167.8.7.8
    john
    156.55.77.*
    77.88.99.12-19

Badly formatted lines in the block file are ignored, but warnings are
logged in logs/server if there are badly formatted lines. Note that it is NOT
possible to have a comment on the same line as a block directive.


6. Administrators
----------
Currently, Gliki doesn't support a full system of permissions for different
users. However, you can make a user an "administrator", which allows them to
delete pages (as opposed to merely blanking them). At the moment, this requires
a manual DB edit. You need to add an entry in the "admins" table (see
dbcreate.sql). At some point in the future I'll add some scripts for doing
this.

Administrators can delete a page called Foo by going to the following URL:

    http://my.web.site/articles/Foo/delete

THERE WILL BE NO REQUEST FOR CONFIRMATION! The article and its edit history
will be immediately and irreversibly deleted.


7. Standard pages
----------
The standard_pages directory contains the source for some of the pages in
Gliki, which you may or may not find useful.


8. Some brief notes on the code for developers.
----------
    * Gliki doesn't use a web framework (other than wsgi) or an ORM. This is
      because I could never really get my head around ORM (I don't want to use
      my database as an object store, and I can't be bothered to learn fancy
      ORMs like sqlalchemy which allow you to go beyond this).
    * The code for parsing the markup language (sourceparser.py) uses the
      "parser combinator" technique. Reading up about this technique will make
      the code a lot easier to understand. Gliki uses its own parser
      combinator library, parcombs.py.
    * As of yet, there are no plans to make Gliki work with a "real" DB since
      sqlite seems to work pretty well. Modfifying Gliki to work with another
      DB would not be difficult (but since it uses raw SQL, it wouldn't be
      trivial either).


