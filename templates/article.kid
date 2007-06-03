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
import htmlutils
import links
# KID fucks up if you use an inline Python string with HTML special things.
rarr = ' &rarr; '
?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#" py:extends="'base.kid', 'comment_form.kid'">
<head>
    <title>${article_title}</title>
</head>

<body>
    <ul py:if="locals().has_key('show_prefs_link') and show_prefs_link" class="user-actions">
        <li><a class="button" href="${links.preferences_link()}">My preferences</a></li>
        <li><a class="button" href="${links.watchlist_link()}">My watchlist</a></li>
        <li><a class="button" href="${links.tracked_changes_link()}">My tracked changes</a></li>
        <li><a class="button" href="${links.delete_account_confirm_link()}">Delete my account</a></li>
    </ul> 
    <ul class="article-actions">
        <li><a class="button" href="${links.edit_article_link(newest_article_title, revision)}">Edit this article</a></li>
        <li><a class="button" href="${links.article_history_link(newest_article_title)}">View history</a></li>
        <li><a class="button" href="${links.links_here_link(newest_article_title)}">What links here?</a></li>
        <li>
            <a py:if="locals().has_key('on_watchlist') and (not on_watchlist)"
               class="button" href="${links.watch_article_link(newest_article_title)}">Watch this article</a>
        </li>
        <li>
            <a py:if="locals().has_key('on_watchlist') and on_watchlist"
               class="button" href="${links.unwatch_article_link(newest_article_title)}">Unwatch this article</a>
        </li>
    </ul>
    <p class="categories">
        <a class="article_ref" href="${links.article_link(newest_article_title, revision)}">Link to this revision</a>
        <br />

        ${categories != [] and 'Categories:' or ''}
        <span py:if="categories != []" py:for="c, is_last in my_utils.mark_last(categories)">
            <a class="category_ref" href="${links.category_link(c)}">${c.lower()}</a>
            <span py:if="not is_last" class="category-sep">|</span>
        </span>
    </p>
    <h1 class="article-title">${article_title}</h1>
    <p py:if="locals().has_key('redirects') and redirects" class="redirects">
        Redirect:
        ${XML(rarr.join(map(htmlutils.htmlencode, redirects)))}
    </p>
    <div class="article-text">
${XML(article_xhtml)}
    </div>
</body>
</html>

