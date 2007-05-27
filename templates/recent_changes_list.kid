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

# Kid won't allow an '<' in a random bit of Python code for some reason.
def lteq(a, b): return a <= b
?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#" py:extends="'base.kid'">
<head>
    <title>Recent changes</title>
</head>

<body>
    <p>Recent changes ${from_} to ${from_ + len(changes)}:</p>
    <p>
        <a href="${links.recent_changes_link(from_ + n, n)}">Next ${n}</a>
        <span py:if="from_ > 0" py:strip="True">
        |
        <a href="${links.recent_changes_link(((lteq(from_ - n, 0)) and (0,) or ((from_ - n),))[0], n)}">Previous ${n}</a>
        </span>
    </p>
    <table class="history">
        <tr>
            <th>Date</th>
            <th>User</th>
            <th>Article title</th>
            <th>Comment</th>
        </tr>
        <tr py:for="c in changes">
            <td>
                <table class="date-diff-pair">
                    <tr>
                        <td>
                            <a class="article_ref"
                               href="${links.article_link(c['newest_article_title'], c['diff_revno_pair'][0])}">
                                ${str(c['date'])}
                            </a>
                        </td>
                        <td py:if="c['diff_revno_pair'][1] is not None">
                             <a class="diff_ref" href="${links.diff_link(c['newest_article_title'], c['diff_revno_pair'][0], c['diff_revno_pair'][1])}">
                diff w/previous
                             </a>
                        </td>
                    </tr>
                </table>
            </td>
            <td><a href="${links.user_page_link(c['username'])}" class="article_ref">${c['username']}</a></td>
            <td>${c['article_title']}</td>
            <td>${my_utils.truncate(200, c['comment'])}</td>
        </tr>
    </table>
</body>
</html>

