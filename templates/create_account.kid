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
import links
?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#" py:extends="'base.kid'">
<head>
    <title>Create a Gliki account</title>
</head>

<body>
    <p py:if="locals().has_key('error')">
        <b class="error">${error}</b>
    </p>
    <form class="create-account" method="POST" action="${links.make_new_account_link()}">
        <table>
            <tr>
                <th>Email</th>
                <td><input type="text" name="email" value="${locals().has_key('default_email') and default_email or ''}"></input></td>
                <td><i>(optional)</i></td>
            </tr>
            <tr>
                <th>Username</th>
                <td><input type="text" name="username" value="${locals().has_key('default_username') and default_username or ''}"></input></td>
            </tr>
            <tr>
                <th>Password</th>
                <td><input type="password" name="password" value=""></input></td>
            </tr>
            <tr>
                <td><input type="submit" value="Create"></input></td>
            </tr>
        </table>
    </form>
    <p>
    If you give an email address, it may be used to send you a new password,
    or for correspondence in exceptional circumstances.
    It will not be published on the site
    and no regular email will be sent to it.
    </p>
</body>
</html>

