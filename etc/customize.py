# SEE END OF FILE FOR LICENSE CONDITIONS.

#
# Instructions for basic customization.
# -------------------------------------
#
# 1) Change the variables defined below.
# 2) Add any necessary static files (logos, etc.) to the 'static' directory.
# 3) Possibly edit config.py, but this should not normally be necessary.
#


#
# DON'T EDIT THIS CODE.
#
import links
import htmlutils
def article_link(article_name, gloss=None):
    al = links.article_link(article_name)
    return u'<a class="article_ref" href="%s">%s</a>' % (al, gloss and gloss or article_name)
def external_link(url, gloss=None):
    return u'<a class="external_link" href="%s">%s</a>' % (url, gloss and gloss or url)
def create_account_link(gloss=None):
    l = links.create_account_link()
    return u'<a class="action" href="%s">%s</a>' % (l, gloss and gloss or l)
def login_link(gloss=None):
    l = links.login_link()
    return u'<a class="action" href="%s">%s</a>' % (l, gloss and gloss or l)


#
# CHANGE THE FOLLOWING VARIABLES.
#
# NOTE: Be careful to use unicode and non-unicode strings in the right places.
#

# Set to None if you don't want to display anything.
# MUST BE UNICODE.
LICENSE_BOILERPLATE_XHTML = \
u"""<p>
    Contributions are licensed under the %s. 
    Anyone can edit articles at any time.
</p>""" % \
(external_link(u"http://creativecommons.org/licenses/by-sa/3.0/",
 u"Creative Commons Attribution Share Alike License"))


# Set to None if you don't want the diff page to link to give any info about the
# revision numbering system.
# MUST BE UNICODE.
REVISION_NUMBERING_INFO_XHTML = \
u"""<p>You might want to read about the wiki's %s.</p>""" % \
(article_link(u"Revision numbering", u"revision numbering system"))


# Set both to None if you don't want a logo.
# The root for static files is the 'static' directory in the main Gliki
# directory. So, if the URL is "/XXX.png", the png file should be
# static/XXX.png.
# MUST BE ASCII.
LOGO_IMG_URL = '/logo.png'
LOGO_IMG_ALT = 'Gliki logo'


# Set to None if you don't want an icon.
# As for the logo (see previous comment), the icon file should be in the
# 'static' directory.
# MUST BE ASCII.
ICON_URL = '/favicon.ico'


# Sets the title of the front page and the title appended to all other pages.
# MUST BE UNICODE.
FRONT_PAGE_TITLE = u"Gliki"
# XHTML to go between <body>...</body> on the front page.
# MUST BE UNICODE.
FRONT_PAGE_BODY_XHTML = \
u"""<h1>Welcome to Gliki</h1>

<p>
Gliki is a wiki for generative linguistics.
The idea is for people to write articles collaberatively on topics which interest them.
You can write in whatever style you like, and on whatever topic.
Even topics outside linguistics altogether are OK, but
but the site has various features designed for linguists.
Currently, these mostly favor syntacticians:
numbered and glossed examples are supported,
and there is a utility for rendering labelled bracketings
as trees.
</p>
<p>
You can start editing any page in the Wiki (except this one) right now,
but you might want to %s first,
or %s if you already have an account.
</p>
<p>
<b>For more detailed information about the site,
see the %s article and the list of %s.</b>
</p>
<p>
If you're new to wikis in general, you might want to read the
<a href="http://en.wikipedia.org/wiki/Wiki" class="external_link">Wikipedia article on wikis</a>.
</p>
%s
<p>
Gliki uses custom software which is currently in the early stages of development,
so there are a few missing features, and probably some bugs.
If something needs fixing,
add a note to the %s page.
</p>
<p>
Gliki is written in %s using %s for the databse
</p>""" % \
(create_account_link(u"create an account"),
 login_link(u"log in"),
 article_link(u"Gliki"),
 article_link(u"Useful links", "list of useful links"),
 LICENSE_BOILERPLATE_XHTML,
 article_link(u"Bugs"),
 external_link(u"http://www.python.org", u"Python"),
 external_link(u"http://www.sqlite.org", u"SQLite")
)


BLOCK_MESSAGE_XHTML = \
"""<p>
    Sorry, you've been blocked.
    If you think this is a mistake,
    <a href="mailto:webmaster@gliki.whsites.net">contact the webmaster</a>.
</p>"""


#
# License conditions
# ------------------
#
# Copyright (C) 2007 Alex Drummond <a.d.drummond@gmail.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor,
# Boston, MA  02110-1301, USA.

