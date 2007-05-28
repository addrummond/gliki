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
# This module provides functions for generating links,
# allowing the format of both to be changed with relatively minor revisions
# to the code base.
#

import my_utils
import urllib
import types

#
# Some utilities.
#
def qaf(s):
    return urllib.quote(my_utils.futz_article_title(s))

def assert_is_int(i):
    assert int(i)
def assert_is_int_or_none(i):
    if i:
        try:
            int(i)
        except:
            assert False

#
# Code for generating links.
#
ARTICLE_LINK_PREFIX = 'articles'
ARTICLE_LIST = 'article-list'
REVISIONS_SUFFIX = 'revisions' 
DIFF_SUFFIX = 'diff'
EDIT_SUFFIX = 'edit'
RECENT_CHANGES = 'recent-changes'
FROM_SUFFIX = 'from'
REVISE_SUFFIX = 'revise'
REVISE_PREFIX = 'revise'
CATEGORIES_PREFIX = 'categories'
CATEGORY_LIST = 'category-list'
COMMENT_SUFFIX = 'comment'
HISTORY_SUFFIX = 'history'
LINKS_HERE_SUFFIX = 'links-here'
MAKE_NEW_ACCOUNT = 'make-new-account'
CREATE_ACCOUNT = 'create-account'
LOGIN = 'login'
LOGIN_NEW_ACCOUNT = 'login-new'
DELETE_ACCOUNT_CONFIRM = 'delete-account-confirm'
DELETE_ACCOUNT = 'delete-account'
PREFERENCES = 'preferences'
UPDATE_PREFERENCES = 'update-preferences'
WATCH_SUFFIX = 'watch'
UNWATCH_SUFFIX = 'unwatch'
WATCHLIST = 'watchlist'
TRACKED_CHANGES = 'tracked-changes'
RENDER_SYNTAX_TREE = 'render-tree'
SYNTAX_TREE = 'syntax-tree'
DELETE_SUFFIX = 'delete'

USER_PAGE_PREFIX = 'user '
CATEGORY_PAGE_PREFIX = 'category '

def article_link(title, revision=None):
    assert_is_int_or_none(revision)
    return '/' + ARTICLE_LINK_PREFIX + '/' + qaf(title) + \
           (revision and "/revisions/%i" % revision or '')

def user_page_link(name):
    return '/' + ARTICLE_LINK_PREFIX + '/' + qaf(USER_PAGE_PREFIX + name)

def category_page_link(name):
    return '/' + ARTICLE_LINK_PREFIX + '/' + qaf(CATEGORY_PAGE_PREFIX + name)

def article_list_link():
    return '/' + ARTICLE_LIST

def edit_article_link(title, revision=None):
    assert_is_int_or_none(revision)
    return article_link(title, revision) + '/' + EDIT_SUFFIX

def revise_link_by_title(title):
    return article_link(title) + '/' + REVISE_SUFFIX

def revise_link_by_threads_id(threads_id):
    assert_is_int(threads_id)
    return '/' + REVISE_PREFIX + '/' + str(threads_id)

def comment_on_wiki_article(title):
    return '/' + ARTICLE_LINK_PREFIX + '/' + qaf(title)

def diff_link(title, rev1, rev2):
    return '/' + ARTICLE_LINK_PREFIX + '/' + qaf(title) + '/' + \
           DIFF_SUFFIX + '/' + str(rev1) + '/' + str(rev2)

def recent_changes_link(from_, n):
    assert_is_int_or_none(from_)
    assert_is_int_or_none(n)
    return '/' + RECENT_CHANGES + '/' + \
           (from_ and FROM_SUFFIX + '/' + str(from_) + '/' or '') + \
           (n and str(n) or '')

def category_link(name):
    return '/' + CATEGORIES_PREFIX + '/' + qaf(name.lower())

def category_list_link():
    return '/' + CATEGORY_LIST

def article_history_link(title):
    return '/' + ARTICLE_LINK_PREFIX + '/' + qaf(title) + '/' + HISTORY_SUFFIX

def links_here_link(title):
    return '/' + ARTICLE_LINK_PREFIX + '/' + qaf(title) + '/' + LINKS_HERE_SUFFIX

def login_link():
    return '/' + LOGIN

def login_new_account_link():
    return '/' + LOGIN_NEW_ACCOUNT

def make_new_account_link():
    return '/' + MAKE_NEW_ACCOUNT

def create_account_link():
    return '/' + CREATE_ACCOUNT

def delete_account_confirm_link():
    return '/' + DELETE_ACCOUNT_CONFIRM

def delete_account_link():
    return '/' + DELETE_ACCOUNT

def preferences_link():
    return '/' + PREFERENCES

def update_preferences_link():
    return '/' + UPDATE_PREFERENCES

def watch_article_link(title):
    return '/' + ARTICLE_LINK_PREFIX + '/' + qaf(title) + '/' + WATCH_SUFFIX

def unwatch_article_link(title):
    return '/' + ARTICLE_LINK_PREFIX + '/' + qaf(title) + '/' + UNWATCH_SUFFIX

def watchlist_link():
    return '/' + WATCHLIST

def tracked_changes_link():
    return '/' + TRACKED_CHANGES

def render_syntax_tree_link():
    return '/' + RENDER_SYNTAX_TREE

def syntax_tree_link():
    return '/' + SYNTAX_TREE

