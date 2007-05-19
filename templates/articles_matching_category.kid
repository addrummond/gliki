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
    <title>Category ${category}</title>
</head>

<body>
    <p>
        You can also look at a list of <a class="category_ref" href="${links.category_list_link()}">all the categories</a> in Gliki.
        <br />
        By convention, any information relating to this category should go in
        <a class="article_ref" href="${links.category_page_link(category)}">${links.CATEGORY_PAGE_PREFIX}${category}</a>.
    </p>

    <p py:if="article_titles != []">The following articles are in category &lsquo;${category}&rsquo;:</p>

    <ol py:if="article_titles != []" class="article-list">
        <li py:for="title in article_titles"><a href="${links.article_link(title)}" class="article_ref">${title}</a></li>
    </ol>

    <p py:if="article_titles == []">
        There are currently no articles in category &lsquo;${category}&rsquo;.
    </p>
</body>
</html>

