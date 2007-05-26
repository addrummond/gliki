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

#
# This module provides some abstractions over the DB for dealing with user
# preferences. Who needs ORM when you can have a nasty hack?
#

import sys
import my_utils
# Python 2.5 has sqlite support built in, with a different module name.
# String comparison for version numbers looks dodgy but it does actually
# work.
if (sys.version.split(' ')[0]) >= '2.5':
    from sqlite3 import dbapi2 as sqlite
else:
    from pysqlite2 import dbapi2 as sqlite

def boolize(v):
    return v and True or False

USER_PREFS = dict(
    time_zone = dict(default="0", simple="True"),
    add_pages_i_create_to_watchlist = dict(default=False, simple="True", to_python=boolize)
)

def check_valid_table_name(s):
    return s

def table_name(prefname):
    assert USER_PREFS.has_key(prefname)
    return check_valid_table_name("wikiuser_" + prefname + "_prefs")
def field_name(prefname):
    assert USER_PREFS.has_key(prefname) and USER_PREFS[prefname]['simple']
    return 'value'

def set_user_preference(dbcon, cur, user_id, prefname, value):
    assert USER_PREFS.has_key(prefname)

    # Do we need to create a new table?
    res = cur.execute(
        """
        SELECT * FROM %s
        WHERE wikiusers_id = ?
        """
        % table_name(prefname),
        (user_id,)
    )
    res = list(res)
    assert len(res) == 0 or len(res) == 1

    if len(res) == 0:
        res = cur.execute(
            """
            INSERT INTO %s
            (wikiusers_id, %s)
            VALUES
            (?, ?)
            """
            % (table_name(prefname), field_name(prefname)),
            (user_id, value)
        )
    else:
        res = cur.execute(
            """
            UPDATE %s
            SET %s = ?
            WHERE wikiusers_id = ?
            """
            % (table_name(prefname), field_name(prefname)),
            (value, user_id)
        )

def get_user_preference(dbcon, cur, user_id, prefname):
    assert USER_PREFS.has_key(prefname)

    res = cur.execute(
        """
        SELECT %s FROM %s
        WHERE wikiusers_id = ?
        """
        % (field_name(prefname), table_name(prefname)),
        (user_id,)
    )
    for r in res:
        val = r[0]
        if USER_PREFS[prefname].has_key('to_python'):
            val = USER_PREFS[prefname]['to_python'](val)
        return val
    return USER_PREFS[prefname]['default']

def get_user_preferences_dict(dbcon, cur, user_id):
    d = { }
    for k in USER_PREFS.iterkeys():
        val = get_user_preference(dbcon, cur, user_id, k)
        d[k] = val
    return d

def set_default_user_preferences(dbcon, cur, user_id):
    for k, v in USER_PREFS.iteritems():
        set_user_preference(dbcon, cur, user_id, k, v['default'])

