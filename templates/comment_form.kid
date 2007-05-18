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
?>

<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#">

<body>
<form class="comment-form"
      py:match="item.tag=='{http://www.w3.org/1999/xhtml}comment_form'"
      py:attrs="item.items()"
      method="POST"
      action="/articles/${urllib.quote(newest_article_title)}/comment"
      id="____edit">
    <input type="hidden" name="threads_id" py:attrs="dict(value=threads_id)"></input>
    <table>
        <tr>
            <th><label for="____title">Title</label></th>
            <td>
                <input id="____title" type="text" name="title" size="50"
                       py:attrs="locals().has_key('default_title') and dict(value=default_title) or dict(value='')">
                </input>
            </td>
        </tr>
        <tr>
            <th><label for="____comment">Enter your comment here:</label></th>
        </tr>
        <tr>
            <td colspan="2">
                <textarea id="____comment" name="source" cols="100" rows="15">${locals().has_key('default_comment') and default_comment or ''}</textarea>
            </td>
        </tr>
        <tr>
            <td>
                <input name="submit" type="submit" value="Post comment"></input>
                <input name="preview" type="submit" value="Preview comment"></input>
            </td>
        </tr>
    </table>
</form>
</body>
</html>

