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
    <title>${title} - Deleted</title>
</head>

<body>
    <p py:if="not (locals().has_key('is_admin') and is_admin)">
        You have to be an administrator to delete pages.
    </p>
    <p py:if="locals().has_key('is_admin') and is_admin and exists_and_deleted">
        The article &lsquo;${title}&rsquo; was deleted.
    </p>
    <p py:if="locals().has_key('is_admin') and is_admin and (not exists_and_deleted)">
        No such article (&lsquo;${title}&rsquo;).
    </p>
</body>
</html>

