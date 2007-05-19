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

import my_utils
import time

LOG_DIR = 'logs'

# Some standard log names.
EDITS_LOG = 'edits'
INTERNAL_LOG = 'internal'
SERVER_LOG = 'server'

LOGGING_ON = True

def log(logname, text):
    assert not ('/' in logname)
    if LOGGING_ON:
        try:
            f = open(LOG_DIR + '/' + logname, "a")
            f.write(my_utils.standard_date_format(time.gmtime()) + ': ' + text)
            if text[len(text) -1] != '\n':
                f.write('\n')
            f.close()
        except IOError:
            pass

