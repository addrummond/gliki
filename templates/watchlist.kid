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
import links
?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#" py:extends="'base.kid'">
<head>
    <title>${username} - Watchlist</title>
</head>

<body>
    <p py:if="locals().has_key('error')">
        ${error}
    </p>

    <p py:if="not locals().has_key('error') and len(article_titles) == 0">
        Currently, you do not have any articles on your watchlist.
    </p>

    <p py:if="not locals().has_key('error') and len(article_titles) > 0">
        You can look at the list of
        <a href="${links.tracked_changes_link()}">articles on your watchlist which have recently changed</a>.
    </p>
    <p py:if="not locals().has_key('error') and len(article_titles) > 0">
        The following articles are on your watchlist:
    </p>

    <ol py:if="not locals().has_key('error') and len(article_titles) > 0" class="article-list">
        <li py:for="title in article_titles"><a href="${links.article_link(title)}" class="article_ref">${title}</a></li>
    </ol>
</body>
</html>

