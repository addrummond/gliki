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

"""
This module contains various global configuration options for your editing
pleasure.
"""

#
# ==== Server options ====
#

# If set to 'paste', Gliki uses a toy Python webserver (provided by the paste
# module). This should not be exposed to the internet directly. It is useful
# for testing, and may also run as a proxy behind a real web server.
# Lighttpd hasn't been tested for ages, though it shouldn't be radically
# broken. See README.
SERVER = "paste" # OR "lighttpd"

SERVER_PORT = 3000


#
# ==== Unicode/encoding options ====
#

# Generally, UTF-8 encoding is used on the web for things like unicode chars
# in URLs, etc. (Not that this is an actual official standard.)
# There's no conceivable reason for anyone ever to change this from utf-8,
# since it would just break everything.
WEB_ENCODING = 'utf-8'

# Encoding used for the logs in the logs/dir.
LOG_ENCODING = 'utf-8'

# These don't work yet! Setting them to anything other than utf-8 will have
# strange consequences.
#
# Both of these should be set to the encoding used for strings in the database.
ARTICLE_SOURCE_ENCODING = 'utf-8'
ARTICLE_XHTML_ENCODING  = 'utf-8'


#
# ==== Authentication options ====
#

# The realm used for user authentication (very unlikely that you need to change
# this).
USER_AUTH_REALM = "Wikiuser"
# The default authentication method to use for user logins. With IE6, plain
# text authentication will always be used, but this setting applies to all other
# browsers. Currently, either 'plain' or 'digest' can be given as values.
USER_AUTH_METHOD = 'digest'


#
# ==== Database options ====
#

# Name of the main (and currently only) database file.
DATABASE = "main.db"


#
# ==== Logging options ====
#
LOG_DIR = 'logs'

LOGGING_ON = True

# Some standard log names (these determine the filename of each log in the
# LOG_DIR directory).
EDITS_LOG = 'edits'
INTERNAL_LOG = 'internal'
SERVER_LOG = 'server'


#
# ==== Cache options ====
#

# If set to True, this uses the filesystem as a cache to reduce the number of
# complex queries sent to the DB. No proven speed increase, and potentially
# buggy (though there aren't any _known_ bugs). Files in directories used for
# caching can be deleted at any time while the Gliki server is running without
# bad things happening.
CACHE_THREADS_IDS = True
# The directory used for the cache.
THREADS_IDS_CACHE_DIR = 'cache/threads_id'


#
# ==== Misc. options ====
#

# The maximum length of each line in diff output.
DIFF_LINE_LENGTH = 60

