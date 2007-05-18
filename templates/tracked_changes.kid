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
    <title>${username} - Tracked changes</title>
</head>

<body>
    <p py:if="locals().has_key('error')">
        ${error}
    </p>

    <p py:if="not locals().has_key('error') and len(revisions) == 0">
        Currently, you do not have any articles on your watchlist.
    </p>

    <p py:if="not locals().has_key('error') and len(revisions) > 0">
        The following articles on your watchlist have recently been modified:
    </p>

    <table py:if="not locals().has_key('error') and len(revisions) > 0" class="history">
        <tr>
            <th>Date</th>
            <th>User</th>
            <th>Article title</th>
            <th>Comment</th>
        </tr>
        <tr py:for="r in revisions">
            <td>
                <table class="date-diff-pair">
                    <tr>
                        <td>
                            <a class="article_ref" href="${links.article_link(r['article_title'], r['diff_revs_pair'][0])}">
                                ${my_utils.standard_date_format(r['revision_date'])}
                            </a>
                        </td>
                        <td py:if="r['diff_revs_pair'][1] is not None">
                            <a class="diff_ref" href="${links.diff_link(r['article_title'], r['diff_revs_pair'][0], r['diff_revs_pair'][1])}">
                                diff w/previous
                            </a>
                        </td>
                    </tr>
                </table>
            </td>
            <td>
                <a class="article_ref" href="${links.user_page_link(r['username'])}">${r['username']}</a>
            </td>
            <td>
                <a href="${links.article_link(r['article_title'])}">${r['article_title']}</a>
            </td>
            <td>
                ${r['comment']}
            </td>
        </tr>

    </table>
</body>
</html>

