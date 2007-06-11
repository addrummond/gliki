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
This module contains various global configuration options.
"""

# These don't yet work! Setting them to anything other than utf-8 will have
# strange consequences.
ARTICLE_SOURCE_ENCODING = 'utf-8'
ARTICLE_XHTML_ENCODING  = 'utf-8'

# Generally, UTF-8 encoding is used on the web for things like unicode chars
# in URLs, etc.
WEB_ENCODING = 'utf-8'

# Encoding used for the logs in the logs/dir.
LOG_ENCODING = 'utf-8'

