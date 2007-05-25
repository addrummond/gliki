<?python
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
?>

<?python
import urllib
import my_utils
import itertools
import links
?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#" py:extends="'base.kid'">
<head>
    <title>${locals().has_key('username') and username + ' - ' or ''}Preferences</title>
</head>

<body>
    <p py:if="not found">
        No preferences could be found.
        This is probably because you are not
        <a class="action" href="${links.login_link()}">logged in</a>.
    </p>
    <p py:if="found and not updated">
        The following preferences are currently set for user ${username}:
    </p>
    <p py:if="found and updated">
        <b>Your preferences have been updated:</b>
    </p>
    <form py:if="found" method="POST" action="${links.update_preferences_link()}">
        <input type="hidden" name="username" value="${username}"></input>
        <table class="preferences">
            <tr>
                <th>Time zone offset from UTC</th>
                <td>
                    <input type="text" size="3" name="time_offset" value="${time_offset}"></input>
                </td>
                <td class="explanation">
                    (for example, enter &lsquo;-5&rsquo; for Eastern Standard Time)
                </td>
            </tr>
            <tr>
                <th>Add pages I create to my watchlist</th>
                <td colspan="2">
                    <input type="checkbox" py:attrs="add_pages_i_create_to_watchlist and dict(checked='') or { }"></input>
                </td>
            </tr>
        </table>
    </form>
</body>
</html>

