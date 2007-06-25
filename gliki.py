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

"""
This module contains some code for accessing the DB, and all of the HTTP request
handlers registered with control.py.
"""

import etc.config as config
import sys
import re
from urimatch import *
import control
from control import ok_text, ok_html, ok_xhtml
import urllib
# Python 2.5 has sqlite support built in, with a different module name.
# String comparison for version numbers looks dodgy but it does actually
# work.
if (sys.version.split(' ')[0]) >= '2.5':
    from sqlite3 import dbapi2 as db
else:
    from pysqlite2 import dbapi2 as db
import kid
import time
import htmlutils
import itertools
import myitertools
import my_utils
import sourceparser
import treedraw
import types
import base64
import parcombs
import cairo
import StringIO
import links
import logging
import diffengine
import userprefs
import aes.Python_AES as pyaes
import block
import cache
import cgi
from my_utils import *

threads_id_cache = cache.FSThreadsIdCache(config.THREADS_IDS_CACHE_DIR)

#
# Code for the AES-32/base64 encryption scheme used for user account passwords.
# See dbcreate.sql for a description of the encryption scheme.
#
AES_PASSWORD_KEY = "%$GHnfgh;['*(12SDvZ\\dfgt><?@:{!!"
AES_MODE = 2 # Must be 2, don't ask me why...
def pad_string(s):
    r = len(s) % 16
    return s + (':' * (16 - r))
def unpad_string(s):
    return s.rstrip(':')
def make_len16(s):
    if len(s) > 16:
        return s[:16]
    else:
        rem = len(s) % 16
        return s + (':' * (16 - rem))
def encrypt_password(iv, plaintext):
    a = pyaes.Python_AES(AES_PASSWORD_KEY, AES_MODE, make_len16(iv))
    return base64.b64encode(a.encrypt(pad_string(plaintext)))
def decrypt_password(iv, ciphertext):
    a = pyaes.Python_AES(AES_PASSWORD_KEY, AES_MODE, make_len16(iv))
    dec = base64.b64decode(ciphertext)
    return unpad_string(a.decrypt(dec).decode('utf-8'))

def showkid(file, serializer=kid.HTMLSerializer(encoding=config.ARTICLE_XHTML_ENCODING)):
    """Decorator for handler methods which passes the return value of the method
       into a Kid template.
    """
    #kid.enable_import()

    def decorator(f):
        template_module = kid.load_template(file, cache=1)

        def r(*args):
            parms = f(*args)
            t = template_module.Template(file=file, **parms)
            return [t.serialize(output=serializer)]
        return r
    return decorator

__ie6_regex = re.compile(r"MSIE\s*([^;]+)")
__number_regex = re.compile(r"(\d*)(\.)?(\d*)")
def browser_is_ie6_or_earlier(extras):
    """Used to prevent digest authentication being used with IE6, which has
       a broken implementation (typical).
    """
    agent = extras.env['HTTP_USER_AGENT']
    m = __ie6_regex.search(agent)
    if not m:
        return False
    else:
        number_string = m.groups(1)[0]
        majmi = __number_regex.search(number_string)
        if not majmi: # Should never be true, really.
            return False
        else:
            n = float(majmi.groups(0)[0])
            return n < 7.0

def update_last_seen(dbcon, cur, user_id):
    """Updates the record for when a given user was last seen. Returns the
       previous time recorded for the user's last visit, or 0 if no previous
       visit is recorded.
    """
    # Is there already a last_seen record for this user.
    res = cur.execute(
        """
        SELECT seen_on FROM last_seens
        WHERE wikiusers_id = ?
        """,
        (user_id,)
    )
    res = list(res)

    assert len(res) <= 1
    if len(res) == 0:
        # Create a new last_seen record.
        res2 = cur.execute(
            """
            INSERT INTO
                last_seens (wikiusers_id, seen_on)
                VALUES
                (?, ?)
            """,
            (user_id, int(time.time()))
        )
        dbcon.commit()
        return 0
    else:
        # Update the existing record.
        res2 = cur.execute(
            """
            UPDATE last_seens
            SET seen_on = ?
            WHERE wikiusers_id = ?
            """,
            (int(time.time()), user_id)
        )
        dbcon.commit()
        return res[0][0]

def dbcon_update_last_seen(user_id):
    try:
        dbcon = get_dbcon()
        cur = dbcon.cursor()
        return update_last_seen(dbcon, cur, user_id)
    except db.Error, e:
        dberror(e)

def get_auth_method(extras):
    """IE6 has a buggy digest auth implementation, and I haven't yet got round
       to adding support for it.
    """
    if browser_is_ie6_or_earlier(extras):
        return 'basic'
    else:
        return config.USER_AUTH_METHOD

def merge_login(dbcon, cur, extras, dict, dont_update_last_seen=False):
    """Merges username and user_id into a dictionary if the HTTP header
       has auth information. Raises AuthenticationRequired if auth info is
       given but is incorrect."""
    if not extras.auth:
        # Is their IP blocked?
        ip = parse_ip_to_4tuple(extras.remote_ip)
        assert ip
        if block.is_blocked('', ip):
            raise control.SwitchHandler(block_handler, { 'because' : 'by_ip' }, 'GET')
        return dict
    elif isinstance(extras.auth, control.Extras.DigestAuth) and extras.auth.bad_auth_header:
        raise control.AuthenticationRequired(
            config.USER_AUTH_REALM,
            get_auth_method(extras),
            stale=extras.auth.bad_because == 'stale_nonce')
    elif isinstance(extras.auth, control.Extras.BasicAuth) or isinstance(extras.auth, control.Extras.DigestAuth):
        authfunc = None
        if isinstance(extras.auth, control.Extras.BasicAuth):
            authfunc = lambda p: p == extras.auth.password
        else:
            authfunc = extras.auth.test

        id = check_bonafides(dbcon, cur, extras.auth.username, authfunc)
        if not id:
            raise control.AuthenticationRequired(config.USER_AUTH_REALM, get_auth_method(extras))

        # Is this user blocked?
        ip = parse_ip_to_4tuple(extras.remote_ip)
        assert ip
        because = block.is_blocked(extras.auth.username, ip)
        if because: 
            raise control.SwitchHandler(block_handler, { 'because' : because }, 'GET')

        # Has the user's userpage been edited since they last logged on?
        if not dont_update_last_seen:
            previously_seen = update_last_seen(dbcon, cur, id)
            rev = get_revision(dbcon, cur, unicode(links.USER_PAGE_PREFIX + extras.auth.username), -1)
            if rev and rev['revision_date'] != 0 and rev['revision_date'] > previously_seen:
                # Add a key to the dict indicating that a "your user page has been
                # updated" message should be shown.
                dict['user_page_updated'] = True

        # Get the user's preferences.
        dict['preferences'] = userprefs.get_user_preferences_dict(dbcon, cur, id)

        # Is the user an admin?
        res = cur.execute(
            """
            SELECT * FROM admins WHERE wikiusers_id = ?
            """,
            (id,)
        )
        res = list(res)
        assert len(res) == 0 or len(res) == 1
        if len(res) == 1:
            dict['is_admin'] = True
        else:
            dict['is_admin'] = False

        dict['username'] = extras.auth.username
        dict['user_id'] = id
        return dict
    else:
        assert False

def dbcon_merge_login(extras, dict, dont_update_last_seen=False):
    try:
        dbcon = get_dbcon()
        cur = dbcon.cursor()
        return merge_login(dbcon, cur, extras, dict, dont_update_last_seen)
    except db.Error, e:
        dberror(e)

def get_ZonedDate(d, time):
    """Given a time (as given by time.time()) and a dictionary which may have
       a 'preferences' field, return a suitable ZonedDate object.
    """
    tz = userprefs.USER_PREFS['time_zone']['default']
    if d.has_key('preferences'):
        tz = d['preferences']['time_zone']
    return ZonedDate(time, tz)

def get_username(current, deleted):
    """
    After performing a query which LEFT JOINs wikiusers and deleted_wikiusers,
    we want to get the username (one of these will be NULL).
    """
    if current:
        return current
    elif deleted:
        return deleted + ' (deleted)'
    else:
        # A user ID should either belong to a current user or a deleted user.
        assert False

__threads_id_select = \
    """
    (SELECT threads_id
     FROM
         (SELECT MAX(revision_date), threads_id, title
          FROM revision_histories
          INNER JOIN articles ON articles.id = revision_histories.articles_id
          GROUP BY revision_histories.threads_id
         ) query1
     WHERE query1.title = ?
    ) 
    """
__qstring_template = \
    """
    SELECT articles.title, articles.source, articles.cached_xhtml, articles.id, revision_histories.threads_id, revision_histories.revision_date, revision_histories.user_comment, articles.redirect, wikiusers.username, deleted_wikiusers.username
        FROM
            %s query2
            INNER JOIN revision_histories ON revision_histories.threads_id = query2.threads_id
            INNER JOIN articles ON articles.id = revision_histories.articles_id
            LEFT JOIN wikiusers ON revision_histories.wikiusers_id = wikiusers.id
            LEFT JOIN deleted_wikiusers ON revision_histories.wikiusers_id = deleted_wikiusers.id
        ORDER BY revision_histories.revision_date %s
        LIMIT -1 OFFSET %i
    """

def get_threads_id_select_statement(title):
    """Returns (statment, should_add_threads_id_to_cache_now_boolean, pass_title_to_query)"""
    threads_id_select = None
    if config.CACHE_THREADS_IDS:
        id = threads_id_cache.get_threads_id(title)
        if id is not False:
            return ("(SELECT threads_id FROM (SELECT %i AS threads_id))" % id, False, False)
        else:
            return __threads_id_select, True, True
    else:
        return __threads_id_select, False, True

def __row_to_hash(r):
    return {
        'title'         : r[0],
        'source'        : r[1],
        'cached_xhtml'  : r[2],
        'articles_id'   : r[3],
        'threads_id'    : r[4],
        'revision_date' : r[5],
        'comment'       : r[6],
        'redirect'      : r[7],
        'username'      : get_username(r[8], r[9])
    }

def get_revision(dbcon, cur, title, revision):
    """Get a particular revision of a particular title
       (returns a dictionary).
    """
    assert revision != 0
    assert type(title) == types.UnicodeType

    use_desc = True
    if revision > 0:
        use_desc = False
    offset = abs(revision) - 1

    stmt, add_to_cache, give_title = get_threads_id_select_statement(title)
    qstring = __qstring_template % (stmt, use_desc and "DESC" or "", offset)

    rows = cur.execute(
        qstring,
        give_title and (title,) or ()
    )
    rows = list(rows)

    for r in rows:
        h = __row_to_hash(r)
        if add_to_cache:
            threads_id_cache.set_threads_id(title, h['threads_id'])
        return h
    # If no revisions for this title were found.
    return None

def make_article_exists_pred(dbcon, cur):
    """Returns predicate to be passed to sourceparser.translate_to_xhtml(...)"""
    def pred(title):
        rev = get_revision(dbcon, cur, title, 1)
        if rev:
            return True
        else:
            return False

def get_ordered_revisions(dbcon, cur, title):
    """Get all revisions of a title, most recent first."""
    assert type(title) == types.UnicodeType

    stmt, add_to_cache, give_title = get_threads_id_select_statement(title)
    qstring = __qstring_template % (stmt, "DESC", 0)
    rows = cur.execute(
        qstring,
        give_title and (title,) or ()
    )
    rows = map(__row_to_hash, rows)
    l = len(rows)
    for i, row in itertools.izip(itertools.count(0), rows):
        row['diff_revs_pair'] = (l - i,
                                 l - i != 1 and l - i - 1 or None)
    if l > 0 and add_to_cache:
        threads_id_cache.set_threads_id(title, rows[0]['threads_id'])
    return rows

def get_diff_revision_number_pair(dbcon, cur, threads_id, revision_date):
    revs = cur.execute(
        """
        SELECT revision_date FROM revision_histories
        WHERE revision_histories.threads_id = ?
        ORDER BY revision_date ASC
        """,
        (threads_id,)
    )

    for num, rev in itertools.izip(itertools.count(1), revs):
        if rev[0] == revision_date:
            if num == 1:
                return((1, None))
            else:
                return((num, num - 1))
    return None # Error.

def delete_article(dbcon, cur, title):
    """Delete an article with a given title.
       Returns True if the article exists, or False if it doesn't.
    """
    assert type(title) == types.UnicodeType

    rev = get_revision(dbcon, cur, title, -1)
    if not rev:
        return False

    # The magic of triggers will delete all the other stuff.
    cur.execute(
        """
        DELETE FROM threads WHERE id = ?
        """,
        (rev['threads_id'],)
    )

    dbcon.commit()

    return True

def article_is_on_watchlist(dbcon, cur, username, title):
    """Checks whether an article is on a given user's watchlist.
       Returns a boolean.
    """
    assert type(title) == types.UnicodeType

    # Is this article already on the user's watchlist?
    res = cur.execute(
        """
        SELECT q1.articles_id FROM
            (SELECT MAX(revision_date), articles_id, threads_id
             FROM revision_histories
             GROUP BY revision_histories.threads_id) q1
        INNER JOIN watchlist_items ON
            (watchlist_items.wikiusers_id IN
                 (SELECT id FROM wikiusers WHERE username = ?))
            AND
            watchlist_items.threads_id = q1.threads_id
        INNER JOIN articles ON
            articles.title = ? AND
            q1.articles_id = articles.id
        """,
        (username, title)
    )

    for r in res:
        if len(r) == 1:
            return True
    return False

def dbcon_article_is_on_watchlist(username, title):
    try:
        dbcon = get_dbcon()
        cur = dbcon.cursor()
        return article_is_on_watchlist(username, title)
    except db.Error, e:
        dberror(e)

def get_list_of_categories_for_thread(dbcon, cur, thread):
    res = cur.execute(
              """
              SELECT name FROM category_specs
              WHERE category_specs.threads_id = ?
              """,
              (thread,)
          ) 
    return list(map(lambda x: x[0].lower(), res))

def add_thread_to_categories(dbcon, cur, thread, categories):
    # SQLITE DOESN'T SUPPORT THIS SYNTAX.
    #values = ','.join(itertools.repeat('(?, ?)', len(categories)))
    #qstring = """
    #    INSERT INTO category_specs (threads_id, name)
    #    VALUES %s
    #""" % values
    #print qstring
    #cur.execute(qstring, my_utils.flatten_list(map(lambda cat: (thread, cat), categories)))

    for c in categories:
        assert type(c) == types.UnicodeType
        cur.execute(
            """
            INSERT INTO category_specs (threads_id, name)
            VALUES (?, ?)
            """,
            (thread, c.lower())
        )

def remove_thread_from_categories(dbcon, cur, thread, categories):
    # SQLITE DOESN'T SUPPORT THIS SYNTAX.
    #expr = 'OR '.join(itertools.repeat('category_specs.name = ?', len(categories)))
    #qstring = """
    #    DELETE FROM category_specs
    #    WHERE category_specs.threads_id = ? AND (%s)
    #""" % expr
    #print qstring
    #cur.execute(qstring, [thread] + categories)

    for c in categories:
        assert type(c) == types.UnicodeType
        cur.execute(
            """
            DELETE FROM category_specs
            WHERE threads_id = ? AND name = ?
            """,
            (thread, c)
        )

def update_categories_for_thread(dbcon, cur, parse_result, thread):
    current_cats = get_list_of_categories_for_thread(dbcon, cur, thread)
    specified_cats = parse_result.categories
    new, removed = diff_lists(current_cats, specified_cats)
    add_thread_to_categories(dbcon, cur, thread, new)
    remove_thread_from_categories(dbcon, cur, thread, removed)

def check_bonafides(dbcon, cur, username, check_func):
    res = cur.execute(
        """
        SELECT wikiusers.id, wikiusers.password, wikiusers.encrypted_password FROM wikiusers
        WHERE wikiusers.username = ?
        """,
        (username,)
    )
    rlist = list(res)
    if len(rlist) == 0:
        return False

    password = rlist[0][1]
    if rlist[0][2]:
        password = decrypt_password(username, password)

    if check_func(password):
        return rlist[0][0] # The user ID.
    else:
        return False

def dbcon_check_bonafides(username, check_func):
    try:
        dbcon = get_dbcon()
        cur = dbcon.cursor()
        return check_bonafides(dbcon, cur, username, check_func)
    except db.Error, e:
        dberror(e)

class DatabaseError(object):
    @ok_html()
    def GET(self, dict, extras):
        r = ''
        if dict['exception']:
            r = str(dict['exception'])
        return ['<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">',
                '<html><head><title>Database error - Gliki</title></head>',
                '<body><h2>Server error</h2>',
                '<p>There was an error connecting to the database: "%s"</p>' % htmlutils.htmlencode(str(dict['exception'])),
                '</body></html>'
               ]
database_error = DatabaseError()

def dberror(e): raise control.SwitchHandler(database_error, dict(exception=e), 'GET')

def get_dbcon():
    return db.connect(config.DATABASE)

def get_anon_user_wikiuser_id(ipaddress):
    """Given an IP address, return the user ID for the anonymous user at this
       address. A new account is created if necessary.
    """
    try:
        dbcon = get_dbcon()
        cur = dbcon.cursor()

        # Does this anon user already exist?
        rows = cur.execute(
        """
        SELECT wikiusers.id FROM wikiusers WHERE username = ?
        """,
        (ipaddress,)
        )
        for r in rows:
            if len(r) == 1:
                return r[0] # Return the wikiuser.id field

        # We need to create the user.
        cur.execute(
        """
        INSERT INTO wikiusers (id, username, email, password, encrypted_password)
        VALUES
        (NULL, ?, NULL, NULL, NULL)
        """,
        (ipaddress,)
        )

        id = cur.lastrowid
        dbcon.commit()
        return id
    except db.Error, e:
        dberror(e)

class GenericInternalError(object):
    @ok_html()
    def GET(self, dict, extras):
        return ['<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">',
                '<html><head><title>Server error - Gliki</title></head>',
                '<body><h2>Server error</h2>',
                "<p>Something's up with the server</p>",
                '</body></html>'
               ]
generic_internal_error = GenericInternalError()

def get_redirect_path(dbcon, cur, goingfrom, to):
    """Check whether or not a putative redirect
       would create a circularity.
    """
    visited = [goingfrom, to]
    while True:
        rev = get_revision(dbcon, cur, visited[len(visited) - 1], -1)
        if not rev:
            return False, visited
        if not rev['redirect']:
            return False, visited
        else:
            if rev['redirect'] in visited:
                visited.append(rev['redirect'])
                return True, visited
            visited.append(rev['redirect'])

class EditWikiArticle(object):
    def __init__(self, exists):
        self.exists = exists

    uris = [VParm(links.ARTICLE_LINK_PREFIX) >> Opt(VParm(links.REVISIONS_SUFFIX), { links.REVISIONS_SUFFIX: '-1' }) >> Abs(links.EDIT_SUFFIX) >> OptDir()]

    @ok_html()
    @showkid('templates/edit.kid')
    def GET(self, parms, extras):
        int_time = int(time.time()) # For edit_time key for template dict.

        title = unfutz_article_title(uu_decode(parms[links.ARTICLE_LINK_PREFIX]))
        text = ''
        revision = None
        try:
            revision = int(uu_decode(parms[links.REVISIONS_SUFFIX]))
            if revision == 0: raise ValueError()
        except (KeyError, ValueError):
            raise control.BadRequestError()

        rev = None
        if self.exists:
            try:
                dbcon = get_dbcon()
                cur = dbcon.cursor()

                rev = get_revision(dbcon, cur, title, revision)
            except db.Error, e:
                dberror(e)
        source = ''
        if rev:
            source = rev['source']
        comment = ''
        if source == '': comment = 'First version'
        return dbcon_merge_login(extras,
                                 dict(article_source=source,
                                 article_title=title,
                                 old_article_title=title,
                                 # This allows the edit form to edit the correct
                                 # article even if the article is renamed while
                                 # the user is editing it.
                                 threads_id=(rev and rev['threads_id'] or None),
                                 comment=comment,
                                 error_message=None,
                                 edit_time=int_time))
edit_wiki_article = EditWikiArticle(True)

class NoSuchRevision(object):
    def __init__(self, kind, title):
        assert kind == 'show' or kind == 'diff'
        self.kind = kind
        self.title = title

    @ok_html()
    @showkid('templates/no_such_revision.kid')
    def GET(self, parms, extras):
        return dict(kind=self.kind, article_title=self.title)

class ShowWikiArticle(object):
    uris = [VParm(links.ARTICLE_LINK_PREFIX) >> Opt(VParm(links.REVISIONS_SUFFIX), {links.REVISIONS_SUFFIX: '-1' }) >> OptDir()]

    def __init__(self, redirect_path=[]):
        self.redirect_path = redirect_path

    @ok_html()
    @showkid('templates/article.kid')
    def GET(self, d, extras):
        try:
            title = unfutz_article_title(uu_decode(d[links.ARTICLE_LINK_PREFIX]))
            revision = None
            try:
                revision = int(uu_decode(d[links.REVISIONS_SUFFIX]))
                if revision == 0: raise ValueError()
            except (KeyError, ValueError):
                raise control.BadRequestError()
            dbcon = get_dbcon()
            cur = dbcon.cursor()
            rows = None

            row = get_revision(dbcon, cur, title, revision)
            if not row:
                # Let's see whether or not /some/ revision of the article exists.
                row = get_revision(dbcon, cur, title, 1)
                if row:
                    # The article exists, but that revision of it doesn't.
                    raise control.SwitchHandler(NoSuchRevision('show', title), { }, 'GET')
                else:
                    # The article doesn't exist at all.
                    newd = d.copy()
                    d[links.REVISIONS_SUFFIX] = '-1'
                    raise control.SwitchHandler(
                        EditWikiArticle(exists=False), newd, 'GET')

            # Is this a redirect?
            if row['redirect']:
                # TODO: Using SwitchHandler here is unnecessary and a bit of a
                # hack.
                is_circular, path = get_redirect_path(dbcon, cur, title, row['redirect'])
                if is_circular:
                    logging.log(config.INTERNAL_LOG, 'Unexpected circular redirect,"%s"\n' % htmlutils.htmlencode(row['title']))
                    raise control.SwitchHandler(generic_internal_error, { }, 'GET')
                # We use a temporary redirect because the redirect could go
                # away at any time, and we don't want any weird cash issues.
                newd = d.copy()
                newd[links.ARTICLE_LINK_PREFIX] = webencode(path[len(path) -1])
                raise control.SwitchHandler(ShowWikiArticle(path), newd, 'GET')

            ntitle = row['title']
            cached_xhtml = row['cached_xhtml']
            articles_id = row['articles_id']
            threads_id = row['threads_id']

            # Get the list of categories that the article belongs to.
            res = cur.execute(
                """
                SELECT DISTINCT name FROM category_specs WHERE category_specs.threads_id = ?
                """,
                (row['threads_id'],)
            )
            categories = list(map(lambda x: x[0], res))

            # We pass in the threads_id so that this can be added as a hidden
            # value in the comment submission form.
            rdict = dict(article_xhtml=cached_xhtml,
                         article_title=ntitle,
                         newest_article_title=title,
                         revision=revision,
                         threads_id=threads_id,
                         categories=categories,
                         redirects=self.redirect_path)
            merge_login(dbcon, cur, extras, rdict)
            # If this is a user page, add login info.
            if ntitle.startswith(links.USER_PAGE_PREFIX):
                # If this is the currently' logged in user's userpage,
                # add a link to the user's preferences.
                if rdict.has_key('username') and rdict['username'] == ntitle.lstrip(links.USER_PAGE_PREFIX):
                    rdict['show_prefs_link'] = True
            # Show a watch/unwatch link if the user is logged in.
            if rdict.has_key('username'):
                rdict['on_watchlist'] = article_is_on_watchlist(dbcon, cur, rdict['username'], ntitle)

            return rdict
        except db.Error, e:
            dberror(e)
show_wiki_article = ShowWikiArticle()

class RecentChangesList(object):
    # /recent-changes/             List of 50 most recent changes
    # /recent-changes/100          List of 100 most recent changes
    # /recent-changes/from/65      List of 50 most recent changes with offset 65
    # /recent-changes/from/65/100  List of 100 most recent changes with offset 65
    uris = [Abs(links.RECENT_CHANGES) >> Opt(VParm(links.FROM_SUFFIX), {'from' : '0'}) >> Opt(Selector('n'), {'n' : '50'}) >> OptDir()]

    @ok_html()
    @showkid('templates/recent_changes_list.kid')
    def GET(self, parms, extras):
        from_, n = None, None
        try:
            from_ = int(uu_decode(parms['from']))
            n = int(uu_decode(parms['n']))
        except ValueError:
            raise control.BadRequestError()

        # Don't allow enormous requests.
        if n > 1000:
            raise control.BadRequestError()

        try:
            dbcon = get_dbcon()
            cur = dbcon.cursor()

            d = { }
            merge_login(dbcon, cur, extras, d)

            # Quite complex because we need to get the most recent title for
            # each thread (otherwise we get diff links with old article titles
            # which don't work).
            most_recent_revisions = cur.execute(
                """
                SELECT title, user_comment, revision_date, threads_id, wikiusers.username, deleted_wikiusers.username, newest_title FROM revision_histories
                INNER JOIN articles ON revision_histories.articles_id = articles.id
                LEFT JOIN wikiusers ON wikiusers_id = wikiusers.id
                LEFT JOIN deleted_wikiusers ON wikiusers_id = deleted_wikiusers.id
                INNER JOIN (
                    SELECT MAX(revision_date), articles.title AS newest_title, threads_id AS matching_threads_id FROM revision_histories
                    INNER JOIN threads ON threads.id = revision_histories.threads_id
                    INNER JOIN articles ON articles.id = revision_histories.articles_id
                    GROUP BY revision_histories.threads_id
                ) ON threads_id = matching_threads_id
                ORDER BY revision_date DESC
                LIMIT ?
                OFFSET ?
                """,
                (n, from_)
            )
            most_recent_revisions = list(most_recent_revisions)

            # For each of these changes, we want to find out the revision number
            # of the preceding revision so we can give a link to a diff.
            revnos = []
            for r in most_recent_revisions:
                threads_id = r[3]
                revision_date = r[2]

                rnp = get_diff_revision_number_pair(dbcon, cur, threads_id, revision_date)
                assert rnp
                revnos.append(rnp)

            changes = map(lambda r_and_n:
                              dict(article_title=r_and_n[0][0],
                                   newest_article_title=r_and_n[0][6],
                                   comment=r_and_n[0][1],
                                   date=get_ZonedDate(d, int(r_and_n[0][2])),
                                   username=get_username(r_and_n[0][4], r_and_n[0][5]),
                                   diff_revno_pair=r_and_n[1]),
                          itertools.izip(most_recent_revisions, revnos))

            return merge_login(dbcon, cur, extras, dict(changes=changes, from_=from_, n=n))
        except db.Error, e:
            dberror(e)
recent_changes_list = RecentChangesList()

class ReviseWikiArticle(object):
    # We allow the article to be specified either by the threads_id or the title.
    uris = [
        # By title.
        VParm(links.ARTICLE_LINK_PREFIX) >> Abs(links.REVISE_SUFFIX) >> OptDir() >>
        SetDict(by_title=True),
        # By threads_id.
        VParm(links.REVISE_PREFIX) >> OptDir() >>
        SetDict(by_threads_id=True)
    ]

    @ok_html()
    @showkid('templates/edit.kid')
    def POST(self, parms, extras):
        int_time = int(time.time())

        title, source, threads_id = None, None, None
        
        # Can't specify both title and threads_id.
        if parms.has_key('by_title') and parms.has_key('by_threads_id'):
            raise control.BadRequestError()

        try:
            if parms.has_key(links.ARTICLE_LINK_PREFIX):
                title = unfutz_article_title(uu_decode(parms[links.ARTICLE_LINK_PREFIX]))
            else:
                threads_id = int(uu_decode(parms[links.REVISE_SUFFIX]))
            source = urllib.unquote(parms['source']).decode(config.ARTICLE_SOURCE_ENCODING)
        except (KeyError, ValueError), e:
            raise control.BadRequestError()
        new_title = title
        if parms.has_key('new_title'):
            new_title = uu_decode(parms['new_title'])
        comment = ''
        if parms.has_key('comment'):
            comment = uu_decode(parms['comment'])
        # This should be specified if editing by threads_id so that we can
        # include the title of the page being edited in any pages we send
        # back.
        redundant_title = None
        if parms.has_key('redundant_title'):
            redundant_title = uu_decode(parms['redundant_title'])
        def get_title_for_user():
            # Oh dear.
            if title:
                if redundant_title and title != redundant_title:
                    raise control.BadRequestError()
                return new_title
            elif redundant_title:
                if new_title:
                    return new_title
                else:
                    return redundant_title
            else:
                return '[unknown title]'
        title_for_user = get_title_for_user()
        def get_old_title():
            if title:
                return title
            else:
                return redundant_title
        old_title = get_old_title()

        dbcon,cur = None,None
        try:
            dbcon = get_dbcon()
            cur = dbcon.cursor()
        except db.Error, e:
            dberror(e)

        # Find out who's making the revision.
        revision_user_id = None
        d = { }
        merge_login(dbcon, cur, extras, d)
        if not d.has_key('username'):
            # Note that get_anon_wikiuser_id(...) raises an exception if there's
            # a DB error.
            revision_user_id = get_anon_user_wikiuser_id(extras.remote_ip)
        else:
            try:
                revision_user_id = d['user_id']
            except ValueError:
                raise control.BadRequestError()

        # Check for an edit conflict if an edit time is specified.
        if parms.has_key('edit_time'):
            try:
                et = int(parms['edit_time'])
            except ValueError:
                raise control.BadRequestError()

            def edit_conflict(old_source, new_source):
                """old_source is the source before either user edited it.
                   new_source is the source of the edit made by the user who
                   created the edit conflict."""
                return dict(
                    article_source = source,
                    article_title = title_for_user,
                    old_article_title = old_title,
                    threads_id = threads_id, # If there's an edit conflict, the article must exist, so there will be a threads_id.
                    comment = comment,
                    error = "edit_conflict",
                    line = None,
                    column = None,
                    diff_xhtml = diffengine.pretty_diff(new_source, old_source or '', config.DIFF_LINE_LENGTH),
                    edit_time = int_time
                )

            if parms.has_key('by_title'):
                rev = get_revision(dbcon, cur, title, -1)
                if rev and rev['revision_date'] >= et:
                    # EDIT CONFLICT!
                    old_source = None
                    orev = get_revision(dbcon, cur, title, -2)
                    if orev:
                        old_source = orev['source']
                    return edit_conflict(old_source, rev['source'])
            elif parms.has_key('by_threads_id'):
                # Article was specified by threads_id.
                res = cur.execute(
                    """
                    SELECT revision_date, source FROM revision_histories
                    INNER JOIN articles ON id = articles_id
                    WHERE threads_id = ?
                    ORDER BY revision_date DESC
                    LIMIT 2
                    """,
                    (threads_id,)
                )
                res = list(res)
                assert len(res) == 0 or len(res) == 1 or len(res) == 2
                if len(res) > 0 and res[0][0] >= et:
                    # EDIT CONFLICT!
                    old_source = None
                    if len(res) == 2:
                        old_source = res[1][1]
                    return edit_conflict(old_source, res[0][1])

        # Cant' have '-' or '_' in the title.
        tfu = get_title_for_user()
        if '-' in tfu or '_' in tfu:
            return my_utils.merge_dicts(
                d,
                dict(
                    article_source = source,
                    article_title = title_for_user,
                    old_article_title = old_title,
                    threads_id = threads_id,
                    comment = comment,
                    error = "bad_title_char",
                    line = None,
                    column = None,
                    edit_time = int_time
                )
            )

        year,month,hour,day,minute,second = my_utils.get_ymdhms_tuple()

        # Parse the wiki markup.
        uname = d.has_key('username') and d['username'] or extras.remote_ip
        sinfo = sourceparser.Siginfo(uname, ZonedDate(int_time, 0))
        result = sourceparser.parse_wiki_document(unixify_text(source), sinfo)
        if isinstance(result, sourceparser.ParserError):
            # This goes to the edit.kid template.
            return my_utils.merge_dicts(
                d,
                dict(
                    article_source=source,
                    article_title=get_title_for_user(),
                    old_article_title=old_title,
                    threads_id = threads_id,
                    comment=comment,
                    error = "parse_error",
                    parse_error = result.message,
                    line=result.line,
                    column=result.col,
                    edit_time = int_time
                )
            )
        # sig_source is the source with signatures replaced.
        r, sourceparser_state, sig_source = result

        # If it was parsed successfully AND it's not a redirect,
        # convert the source to XHTML.
        xhtml_output = None
        if not isinstance(r, sourceparser.Redirect):
            try:
                #dbcon = get_dbcon() # For marking existent/non-existent article links.
                #cur = dbcon.cursor()
                sb = StringIO.StringIO()
                sourceparser.translate_to_xhtml(r, sb) #, make_article_exists_pred(dbcon, cur))
                xhtml_output = sb.getvalue() # TODO: Some unicode stuff?
            except db.Error, e:
                dberror(e)

        # Now, if it's a preview, we'll go straight to the preview page.
        if parms.has_key('preview'):
            # You can't preview a redirect!
            if xhtml_output is None: # If it's a redirect.
                return my_utils.merge_dicts(
                    d,
                    dict(
                        article_source = sig_source,
                        article_title = get_title_for_user(),
                        old_article_title = old_title,
                        threads_id = threads_id,
                        comment = comment,
                        error = "preview_redirect",
                        line = None,
                        column = None,
                        edit_time = int_time,
                    )
                )
            return my_utils.merge_dicts(
                d,
                dict(
                    article_source = sig_source,
                    article_title = get_title_for_user(),
                    old_article_title = old_title,
                    threads_id = threads_id,
                    comment = comment,
                    preview = xhtml_output,
                    edit_time = int_time
                )
            )

        # If it's not a preview, we'd better update the DB.
        try:
            # If threads_id is set make sure it is valid.
            if threads_id:
                res = cur.execute(
                    """
                    SELECT * FROM threads WHERE id = ?
                    """,
                    (threads_id,)
                )
                if len(list(res)) == 0:
                    raise control.BadRequestError()

            def make_thread(title):
                """Find/create the article using the title provided
                   Returns a threads_id.
                """
                if not threads_id:
                    rev = get_revision(dbcon, cur, title, 1)
                    if not rev:
                        # Create a new thread.
                        res = cur.execute(
                            """
                            INSERT INTO threads (id) VALUES (NULL)
                            """
                        )
                        return cur.lastrowid
                    else:
                        return rev['threads_id']

            #
            # TODO: Really need some refactoring here.
            # THE BIG IF: Is it a redirect or not?
            #
            if isinstance(r, sourceparser.Redirect):
                # Check for circular redirects.
                is_circular, path = get_redirect_path(dbcon, cur, new_title, r.title)
                if is_circular:
                    return my_utils.merge_dicts(
                        d,
                        dict(
                            article_source = sig_source,
                            article_title = title_for_user,
                            old_article_title = old_title,
                            threads_id = threads_id,
                            comment = comment,
                            error = "circular_redirect",
                            redirects = path,
                            line = None,
                            column = None,
                            edit_time = int_time
                        )
                    )

                res = cur.execute(
                    """
                    INSERT INTO articles
                    (id, source, redirect, cached_xhtml, title)
                    VALUES
                    (NULL, ?, ?, NULL, ?)
                    """,
                    (sig_source, r.title, new_title)
                )
                articles_id = cur.lastrowid

                # Find/create the article using either the title or threads_id provided.
                if not threads_id:
                    threads_id = make_thread(title)

                res = cur.execute(
                    """
                    INSERT INTO revision_histories
                        (threads_id, articles_id, revision_date, wikiusers_id, user_comment)
                        VALUES
                        (?, ?, ?, ?, ?)
                    """,
                    (threads_id, articles_id, int_time, revision_user_id, comment)
                )

                dbcon.commit()

                logging.log(
                    config.EDITS_LOG,
                    u'%s,%s,%s,redirect,"%s",%i\n' % (
                        extras.remote_ip,
                        d.has_key('username') and d['username'] or u'',
                        threads_id,
                        htmlutils.htmlencode(comment),
                        int_time
                    )
                )
            else: # if it's not a redirect.
                # Check that they're not renaming the article to the title of an
                # existing article (you cunning bastard, Mue).
                # Some nasty logic here because we're dealing with two cases:
                # one where the revision is specified by title, and the other
                # where it's specified by threads_id.
                if new_title and ((title is None) or (title != new_title)):
                    rev = get_revision(dbcon, cur, new_title, 1)
                    if rev and ((title is not None) or (rev['threads_id'] != threads_id)):
                        return my_utils.merge_dicts(
                            d,
                            dict(
                                article_source = sig_source,
                                article_title = title_for_user,
                                old_article_title = old_title,
                                threads_id = threads_id,
                                comment = comment,
                                error = "rename_to_existing",
                                line = None,
                                column = None,
                                edit_time = int_time
                            )
                        )

                # Create a new article.
                res = cur.execute(
                    """
                    INSERT INTO articles
                        (id, source, redirect, cached_xhtml, title)
                        VALUES
                        (NULL, ?, NULL, ?, ?)
                    """,
                    (sig_source, xhtml_output, new_title)
                )
                articles_id = cur.lastrowid

                # Find/create the article using either the title or threads_id provided.
                if not threads_id:
                    threads_id = make_thread(title)

                # THE threads_id VARIABLE IS NOW SET.
                res = cur.execute(
                    """
                    INSERT INTO revision_histories
                       (threads_id, articles_id, revision_date, wikiusers_id, user_comment)
                       VALUES
                       (?, ?, ?, ?, ?)
                    """,
                    (threads_id, articles_id, int_time, revision_user_id, comment)
                )

                # Update the links table. First, delete all the old links.
                cur.execute(
                    """
                    DELETE FROM links WHERE threads_id = ?
                    """,
                    (threads_id,)
                )
                # Now insert the new links.
                linked_to = sourceparser_state['article_refs']
                for lt in linked_to:
                    cur.execute(
                    """
                    INSERT INTO links (threads_id, to_title)
                    VALUES
                    (?, ?)
                    """,
                    (threads_id, lt)
                    )

                # Update the categories for this article.
                update_categories_for_thread(dbcon, cur, r, threads_id)

                # If the title changed, update the threads_id cache.
                if old_title != new_title:
                    threads_id_cache.move_if_cached(old_title, new_title)

                dbcon.commit()

                # Make a log of the edit.
                logging.log(
                    config.EDITS_LOG,
                    u'%s,%s,%s,edit,"%s",%i\n' % (
                        extras.remote_ip,
                        d.has_key('username') and d['username'] or '',
                        threads_id,
                        htmlutils.htmlencode(comment),
                        int_time
                    )
                )
        except db.Error, e:
            dberror(e)
        raise control.Redirect(links.article_link(new_title),
                               'text/html; charset=UTF-8',
                               'see_other')
revise_wiki_article = ReviseWikiArticle()

class Category(object):
    uris = [VParm(links.CATEGORIES_PREFIX) >> OptDir()]

    @ok_html()
    @showkid('templates/articles_matching_category.kid')
    def GET(self, parms, extras):
        # NOTE THAT CATEGORIES ARE CASE INSENSITIVE, SO THERE ARE SOME
        # CASE INSENSITIVE SQL STRING COMPARISONS HERE.

        category = unfutz_article_title(uu_decode(parms[links.CATEGORIES_PREFIX])).lower()

        try:
            dbcon = get_dbcon()
            cur = dbcon.cursor()

            res = cur.execute(
                """
                SELECT query1.title
                FROM
                    (SELECT MAX(revision_date), threads_id, title
                     FROM revision_histories
                     INNER JOIN articles ON articles.id = revision_histories.articles_id
                     GROUP BY revision_histories.threads_id
                    ) query1
                INNER JOIN category_specs ON query1.threads_id = category_specs.threads_id AND
                                             category_specs.name = ?
                """,
                (category,)
            )

            return merge_login(dbcon, cur, extras, dict(category=category, article_titles=list(map(lambda x: x[0], res))))
        except db.Error, e:
            dberror(e)
category = Category()

class CategoryList(object):
    uris = [Abs(links.CATEGORIES_PREFIX) >> OptDir(),
            Abs(links.CATEGORY_LIST) >> OptDir()]

    @ok_html()
    @showkid('templates/category_list.kid')
    def GET(self, parms, extras):
        try:
            dbcon = get_dbcon()
            cur = dbcon.cursor()

            res = cur.execute(
                """
                SELECT DISTINCT NAME FROM category_specs
                """
            )

            return merge_login(dbcon, cur, extras, dict(categories=list(map(lambda x: x[0].lower(), res))))
        except db.Error, e:
            raise dberror(e)
category_list = CategoryList()

class WikiArticleHistory(object):
    uris = [VParm(links.ARTICLE_LINK_PREFIX) >> Abs(links.HISTORY_SUFFIX) >> OptDir()]

    @ok_html()
    @showkid('templates/history.kid')
    def GET(self, parms, extras):
        title = unfutz_article_title(uu_decode(parms[links.ARTICLE_LINK_PREFIX]))

        try:
            dbcon = get_dbcon()
            cur = dbcon.cursor()

            rows = get_ordered_revisions(dbcon, cur, title)
            if not rows:
                raise control.NotFoundError()
            d = { }
            merge_login(dbcon, cur, extras, d)
            return merge_dicts(d,
                               dict(article_title = title,
                                    revisions =
                                        [dict(article_title = row['title'],
                                              revision_date = get_ZonedDate(d, int(row['revision_date'])),
                                              username      = row['username'],
                                              comment       = row['comment'],
                                              diff_revs_pair = row['diff_revs_pair'])
                                         for row in rows
                                        ]
                               ))
        except db.Error, e:
            dberror(e)
        except ValueError:
            # The use of int(...) above could potentially raise an exception.
            logging.log(config.INTERNAL_LOG, "Not int\n")
            raise control.SwitchHandler(generic_internal_error, { }, 'GET')
wiki_article_history = WikiArticleHistory()

class WikiArticleList(object):
    uris = [Abs(links.ARTICLE_LINK_PREFIX) >> OptDir(),
            Abs(links.ARTICLE_LIST) >> Opt(VParm(links.FROM_SUFFIX), {'from' : '0'}) >> OptDir()]

    @ok_html()
    @showkid('templates/article_list.kid')
    def GET(self, parms, extras):
        index = None
        if parms.has_key('from'):
            index = uu_decode(parms['from'])
            try:
                index = int(index)
            except ValueError:
                raise control.BadRequestError()
        else:
            raise control.Redirect(links.article_list_link(), 'text/html; charset=UTF-8', 'permanent')

        try:
            dbcon = get_dbcon()
            cur = dbcon.cursor()

            # Get the (alphabetically) first 100 article titles.
            rows = cur.execute(
                """
                SELECT MAX(revision_date), title FROM revision_histories
                INNER JOIN articles ON articles.id = revision_histories.articles_id
                GROUP BY revision_histories.threads_id
                ORDER BY articles.title
                LIMIT 100 OFFSET ?
                """,
                (index,)
            )

            titles = [row[1] for row in rows]
            return merge_login(dbcon, cur,
                               extras,
                               dict(article_titles=titles,
                                    starting_from=index + 1,
                                    going_to=index + len(titles),
                                    partial=len(titles) == 100))
        except db.Error, e:
            dberror(e)
wiki_article_list = WikiArticleList()

class LinksHere(object):
    uris = [VParm(links.ARTICLE_LINK_PREFIX) >> Abs(links.LINKS_HERE_SUFFIX) >> OptDir()]

    @ok_html()
    @showkid('templates/links-here.kid')
    def GET(self, parms, extras):
        title = unfutz_article_title(uu_decode(parms[links.ARTICLE_LINK_PREFIX]))

        try:
            dbcon = get_dbcon()
            cur = dbcon.cursor()

            rows = cur.execute(
            """
            SELECT title FROM links
            INNER JOIN
                (SELECT MAX(revision_date), threads_id, title
                 FROM revision_histories
                 INNER JOIN articles
                 ON articles.id = articles_id
                 GROUP BY revision_histories.threads_id) query1
            ON query1.threads_id = links.threads_id
            WHERE links.to_title = ?;
            """,
            (title,)
            )

            titles = map(lambda x: x[0], list(rows))
            return merge_login(dbcon, cur, extras, dict(article_title=title, titles=titles))
        except db.Error, e:
            dberror(e)
links_here = LinksHere()

class Diff(object):
    uris = [VParm(links.ARTICLE_LINK_PREFIX) >> VParm(links.DIFF_SUFFIX) >> Selector('with') >> OptDir()]

    @ok_html()
    @showkid('templates/diff.kid')
    def GET(self, parms, extras):
        title = unfutz_article_title(uu_decode(parms[links.ARTICLE_LINK_PREFIX]))
        rev1 = uu_decode(parms[links.DIFF_SUFFIX])
        rev2 = uu_decode(parms['with'])
        try:
            rev1 = int(rev1)
            rev2 = int(rev2)
            if rev1 == 0 or rev2 == 0: raise ValueError()
        except ValueError:
            raise control.BadRequestError()

        try:
            dbcon = get_dbcon()
            cur = dbcon.cursor()

            r1 = get_revision(dbcon, cur, title, rev1)
            r2 = get_revision(dbcon, cur, title, rev2)
            if not (r1 and r2):
                raise control.SwitchHandler(NoSuchRevision('diff', title), { }, 'GET')
            rev1src = r1['source']
            rev2src = r2['source']
            rev1title = r1['title']
            rev2title = r2['title']
            revision_comment = r1['comment']

            # formertitle is set if both of the specified revisions have the
            # same title, but the newest revision of the article has a different
            # title. oldtitle and newtitle are both set if the specified
            # revisions do not have the same title. formertitle and
            # oldtitle/newtitle are never both set.
            formertitle, oldtitle, newtitle = None, None, None
            if rev1title != rev2title:
                oldtitle = rev1title
                newtitle = rev2title
            elif rev1title != title:
                formertitle = rev1title

            return merge_login(dbcon, cur,
                               extras,
                               dict(article_title=title,
                                    diff_html=diffengine.pretty_diff(rev1src, rev2src, config.DIFF_LINE_LENGTH),
                                    rev1=rev1,
                                    rev2=rev2,
                                    formertitle=formertitle,
                                    newtitle=newtitle,
                                    oldtitle=oldtitle,
                                    revision_comment=revision_comment))
        except db.Error, e:
            dberror(e)
diff = Diff()

class FrontPage(object):
    uris = [Abs("")]

    @ok_html()
    @showkid('templates/frontpage.kid')
    def GET(self, parms, extras):
        return dbcon_merge_login(extras, { })
front_page = FrontPage()

class Block(object):
    # No uris because this is only ever switched to.

    @ok_html()
    @showkid('templates/block.kid')
    def GET(self, parms, extras):
        return dict(because=parms['because'])
block_handler = Block()

class CreateAccount(object):
    uris = [Abs(links.CREATE_ACCOUNT) >> OptDir()]

    @ok_html()
    @showkid('templates/create_account.kid')
    def GET(self, parms, extras):
        return dbcon_merge_login(extras, { })
create_account = CreateAccount()

class MakeNewAccount(object):
    uris = [Abs(links.MAKE_NEW_ACCOUNT) >> OptDir()]

    ip_addy_regex_string = r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}"
    ip_addy_regex = re.compile(ip_addy_regex_string)

    @ok_html()
    @showkid('templates/create_account.kid') # Go here if there's an error.
    def POST(self, parms, extras):
        if not (parms.has_key('username') and
                parms.has_key('password')):
            return dict(default_email=(parms.has_key('email') and uu_decode(parms['email']) or ''),
                        default_username=(parms.has_key('username') and uu_decode(parms['username']) or ''),
                        error="missing_fields")
        username, password = uu_decode(parms['username']), uu_decode(parms['password'])
        email = None
        if parms.has_key('email') and parms['email'] != '':
            email = uu_decode(parms['email'])

        # Usernames and passwords must be ASCII since (so far as I know) there's
        # no standard way of dealing with unicode in the HTTP digest protocol.
        try:
            username = username.encode('ascii')
            password = password.encode('ascii')
        except UnicodeEncodeError:
            return dict(error="contains_non_ascii",
                        default_username=username)

        # Usernames and passwords can't contain the ':' character because that
        # interferes with the HTTP AUTH mechanism.
        if ':' in username or ':' in password:
            return dict(default_email=email,
                        default_username=username,
                        error="contains_colon")

        try:
            dbcon = get_dbcon()
            cur = dbcon.cursor()

            # Does an account with this username or email already exist?
            res = cur.execute(
                """
                SELECT wikiusers.email, wikiusers.username FROM wikiusers
                WHERE (wikiusers.email IS NOT NULL AND wikiusers.email = ?) OR
                      wikiusers.username = ?
                """,
                (email, username)
            )
            res = list(res)
            if len(res) != 0:
                if res[0][0] is not None and res[0][0] == email:
                    return dict(default_email=email,
                                default_username=username,
                                error="email_exists")
                else:
                    return dict(default_email=email,
                                default_username=username,
                                error="username_exists")
            # Also, you can't create an account with an IP address name, since
            # they're reserved for anon users.
            if self.ip_addy_regex.match(username):
                return dict(default_email=email,
                            default_username=username,
                            error="username_is_ip_address")

            # User's need a user page. Perhaps someone has mischeivously created
            # a user-$USERNAME page already.
            rev = get_revision(dbcon, cur, (links.USER_PAGE_PREFIX + username).decode(config.ARTICLE_SOURCE_ENCODING), 1)
            if rev:
                return dict(default_email=email,
                            default_username=username,
                            error="userpage_exists")

            # All clear: we can go ahead and create a new account.
            res = cur.execute(
                """
                INSERT INTO wikiusers
                (id, email, username, password, encrypted_password)
                VALUES
                (NULL, ?, ?, ?, ?)
                """,
                (email, username, encrypt_password(username, password), True)
            )
            wikiusers_id = cur.lastrowid

            # And the default preferences for the new account.
            userprefs.set_default_user_preferences(dbcon, cur, wikiusers_id)

            int_time = int(time.time())

            # Now create the user's user page.
            userpage_source = "#CATEGORY [[user pages]]\n\nThis is the user page for %s." % username
            userpage_title = links.USER_PAGE_PREFIX + username
            result = sourceparser.parse_wiki_document(userpage_source, siginfo=None)
            assert not isinstance(result, sourceparser.ParserError)
            r, sourceparser_state, _ = result
            import StringIO
            sb = StringIO.StringIO()
            sourceparser.translate_to_xhtml(r, sb) #, make_article_exists_pred(dbcon, cur))
            cached_xhtml = sb.getvalue()
            res = cur.execute(
                """
                INSERT INTO articles
                (id, source, redirect, cached_xhtml, title)
                VALUES
                (NULL, ?, NULL, ?, ?)
                """,
                (userpage_source,
                 cached_xhtml,
                 userpage_title)
            )
            user_page_id = cur.lastrowid
            res = cur.execute(
                """
                INSERT INTO threads (id) VALUES (NULL)
                """
            )
            threads_id = cur.lastrowid
            res = cur.execute(
                """
                INSERT INTO revision_histories
                (threads_id, articles_id, revision_date, wikiusers_id, user_comment)
                VALUES
                (?, ?, ?, ?, ?)
                """,
                # User ID 1 is the "system" user.
                (threads_id, user_page_id, int_time, 1, "Automatically created user page")
            )

            update_categories_for_thread(dbcon, cur, r, threads_id)

            dbcon.commit()

            raise control.Redirect(links.login_new_account_link(), 'text/html; charset=UTF-8', 'see_other')
        except db.Error, e:
            dberror(e)
make_new_account = MakeNewAccount()

class DeleteAccountConfirm(object):
    uris = [Abs(links.DELETE_ACCOUNT_CONFIRM)]

    @ok_html()
    @showkid('templates/delete_account_confirm.kid')
    def GET(self, parms, extras):
        d = { }
        dbcon_merge_login(extras, d)

        if not d.has_key('username'):
            return dict(error=u"You cannot delete your account because you are not logged in.")
        else:
            return d
delete_account_confirm = DeleteAccountConfirm()

class DeleteAccount(object):
    uris = [Abs(links.DELETE_ACCOUNT)]

    @ok_html()
    @showkid('templates/delete_account.kid')
    def POST(self, parms, extras):
        try:
            dbcon = get_dbcon()
            cur = dbcon.cursor()

            d = { }
            merge_login(dbcon, cur, extras, d)
            if not d.has_key('username'):
                return dict(error=u"You cannot delete your account because you are not logged in.")
            username = uu_decode(d['username'])

            # Check this user exists.
            res = cur.execute(
                """
                SELECT id FROM wikiusers WHERE
                username = ?
                """,
                (username,)
            )

            for r in res:
                # Delete the user.
                res2 = cur.execute(
                    """
                    DELETE FROM wikiusers WHERE
                    id = ?
                    """,
                    (r[0],)
                )

                dbcon.commit()

                # Delete the user's userpage (this function will just do nothing
                # if the page doesn't exist).
                delete_article(dbcon, cur, unicode(links.USER_PAGE_PREFIX) + username)

                # We don't merge login info, since if we do the user will be
                # informed that they're logged in as the user we've just deleted.
                return dict(username_=username)

            # Should never get here -- it would mean that a non-existent user
            # was logged in.
            assert False
        except db.Error, e:
            dberror(e)
delete_account = DeleteAccount()

class Login(object):
    uris = [Abs(links.LOGIN), Abs(links.LOGIN_NEW_ACCOUNT, dict(new_account=True))]

    @ok_html()
    def GET(self, parms, extras):
        d = { }
        # Updating the last seen thingy will happen when they're redirected to
        # their user page. However, if this is a new account, we'll update
        # the last seen field now, because we don't want the user page updated
        # message to be displayed the first time they log in.
        dbcon_merge_login(extras, d, dont_update_last_seen=(not parms.has_key('new_account')))
        # They might be logged in already.
        if d.has_key('username'):
            raise control.Redirect(links.user_page_link(extras.auth.username),
                                   'text/html; charset=UTF-8',
                                   'see_other')
        else:
            raise control.AuthenticationRequired(config.USER_AUTH_REALM, get_auth_method(extras))
login = Login()

class Preferences(object):
    uris = [Abs(links.PREFERENCES)]

    @ok_html()
    @showkid('templates/preferences.kid')
    def GET(self, parms, extras):
        # Get the preferences for this user.
        try:
            dbcon = get_dbcon()
            cur = dbcon.cursor()

            d = { }
            merge_login(dbcon, cur, extras, d) # Raises control.[something] if auth incorrect.
            if len(d) == 0:
                return dict(found=False)

            return merge_dicts(
                d,
                dict(found=True,
                     updated=False,
                     username=d['username'],
                     preferences=d['preferences'])
            )
        except db.Error, e:
            dberror(e)
preferences = Preferences()

class UpdatePreferences(object):
    uris = [Abs(links.UPDATE_PREFERENCES)]

    def POST(self, parms, extras, start_response):
        try:
            # TODO: Lots of unnecessary duplication here, but unless we add
            # a lot more preferences, I'm not sure if it's worth the effort
            # required to create a nice abstraction for setting/getting prefs.
            dbcon = get_dbcon()
            cur = dbcon.cursor()

            d = { }
            merge_login(dbcon, cur, extras, d)
            if len(d) == 0:
                # We'll redirect back to the preferences page, which in turn
                # will give a "you must be logged in" error.
                # Note that this is a very unlikely code path, since the
                # user would somehow have to log out in between loading
                # the prefs page and submitting the form.
                raise control.Redirect(links.preferences_link(),
                                       'text/html; charset=UTF-8',
                                       'see_other')

            if parms.has_key('time_zone'):
                if not userprefs.set_user_preference(dbcon, cur, d['user_id'], 'time_zone', int(parms['time_zone'])):
                    raise control.BadRequestError()
            if not userprefs.set_user_preference(dbcon, cur, d['user_id'], 'add_pages_i_create_to_watchlist', parms.has_key('add_pages_i_create_to_watchlist')):
                raise control.BadRequestError()

            dbcon.commit()

            # Redirect to the preferences view.
            raise control.Redirect(links.preferences_link(),
                                   'text/html; charset=UTF-8',
                                   'see_other')
        except db.Error, e:
            dberror(e)
        except ValueError: # Use of int(...) above
            raise control.BadRequestError()
update_preferences = UpdatePreferences()

class Watch(object):
    uris = [VParm(links.ARTICLE_LINK_PREFIX) >> Abs(links.WATCH_SUFFIX) >> OptDir()]

    # Unfortunately we can't use a POST here because of inconsistent display of
    # the form across browsers. Using a GET with Pragma: no-cache instead.
    @ok_html(cache=False)
    @showkid('templates/watch.kid')
    def GET(self, parms, extras):
        title = unfutz_article_title(uu_decode(parms[links.ARTICLE_LINK_PREFIX]))

        try:
            dbcon = get_dbcon()
            cur = dbcon.cursor()

            d = { }
            merge_login(dbcon, cur, extras, d)
            if len(d) == 0:
                return dict(error=u"You must be logged in to add an item to your watchlist.")

            if article_is_on_watchlist(dbcon, cur, d['username'], title):
                return merge_dicts(d, dict(error=u"The article is already on your watchlist."))

            res = cur.execute(
                """
                INSERT INTO watchlist_items
                (wikiusers_id, threads_id)
                VALUES
                (
                    (SELECT id FROM wikiusers WHERE wikiusers.username = ? LIMIT 1)
                    ,
                    (SELECT q1.threads_id FROM
                         (SELECT MAX(revision_date), threads_id, articles_id
                          FROM revision_histories
                          GROUP BY revision_histories.threads_id) q1
                     INNER JOIN articles ON
                         articles.title = ? AND
                         articles.id = q1.articles_id
                     LIMIT 1)
                )
                """,
                (d['username'], title)
            )

            dbcon.commit()

            d['article_title'] = title
            return d
        except db.Error, e:
            dberror(e)
watch = Watch()

class Unwatch(object):
    uris = [VParm(links.ARTICLE_LINK_PREFIX) >> Abs(links.UNWATCH_SUFFIX) >> OptDir()]

    # Unfortunately we can't use a POST here because of inconsistent display of
    # the form across browsers. Using a GET with Pragma: no-cache instead.
    @ok_html(cached=False)
    @showkid('templates/unwatch.kid')
    def GET(self, parms, extras):
        title = unfutz_article_title(uu_decode(parms[links.ARTICLE_LINK_PREFIX]))

        try:
            dbcon = get_dbcon()
            cur = dbcon.cursor()

            d = { }
            merge_login(dbcon, cur, extras, d)
            if len(d) == 0:
                return dict(error=u"You must be logged in to remove an item from your watchlist.")

            if not article_is_on_watchlist(dbcon, cur, d['username'], title):
                return merge_dicts(d, dict(error=u"The article is not on your watchlist."))

            res = cur.execute(
                """
                DELETE FROM watchlist_items
                WHERE threads_id IN
                    (SELECT q1.threads_id FROM
                         (SELECT MAX(revision_date), threads_id, articles_id
                          FROM revision_histories
                          GROUP BY revision_histories.threads_id) q1
                     INNER JOIN articles ON
                     articles.title = ? AND
                     articles.id = q1.articles_id)
                """,
                (title,)
            )

            dbcon.commit()

            d['article_title'] = title
            return d
        except db.Error, e:
            dberror(e)
unwatch = Unwatch()

class Watchlist(object):
    uris = [Abs(links.WATCHLIST)]

    @ok_html()
    @showkid('templates/watchlist.kid')
    def GET(self, parms, extras):
        try:
            dbcon = get_dbcon()
            cur = dbcon.cursor()

            d = { }
            merge_login(dbcon, cur, extras, d)
            if len(d) == 0:
                return dict(error=u"You must be logged in to view your watchlist.")

            res = cur.execute(
                # Don't actually need a subquery here, but putting the second
                # join outside the subquery should be more efficient.
                """
                SELECT title FROM
                    (SELECT MAX(revision_date), articles_id FROM watchlist_items
                     INNER JOIN revision_histories ON revision_histories.threads_id = watchlist_items.threads_id
                     WHERE watchlist_items.wikiusers_id IN
                         (SELECT id FROM wikiusers WHERE wikiusers.username = ?)
                     GROUP BY revision_histories.threads_id) q1
                INNER JOIN articles ON articles.id = q1.articles_id
                """,
                (d['username'],)
            )

            d['article_titles'] = [r[0] for r in res if len(r) == 1]
            return d
        except db.Error, e:
            dberror(e)
watchlist = Watchlist()

class TrackedChanges(object):
    uris = [Abs(links.TRACKED_CHANGES)]

    @ok_html()
    @showkid('templates/tracked_changes.kid')
    def GET(self, parms, extras):
        try:
            dbcon = get_dbcon()
            cur = dbcon.cursor()

            d = { }
            merge_login(dbcon, cur, extras, d)
            if len(d) == 0:
                return dict(error=u"You must be logged in to view your recent changes list.")

            # Select the 50 items on the watchlist with the most recent changes.
            res = cur.execute(
                """
                SELECT title, revision_date, _threads_id, wikiusers.username, deleted_wikiusers.username, user_comment
                FROM
                    (SELECT MAX(revision_date), revision_date, articles_id, user_comment, revision_histories.threads_id AS _threads_id, revision_histories.wikiusers_id AS _wikiusers_id FROM watchlist_items
                     INNER JOIN revision_histories ON revision_histories.threads_id = watchlist_items.threads_id
                     WHERE watchlist_items.wikiusers_id IN
                         (SELECT id FROM wikiusers WHERE wikiusers.username = ?)
                     GROUP BY revision_histories.threads_id
                     LIMIT 50) q1
                INNER JOIN articles ON articles.id = articles_id
                LEFT JOIN wikiusers ON wikiusers.id = q1._wikiusers_id
                LEFT JOIN deleted_wikiusers ON wikiusers.id = q1._wikiusers_id
                ORDER BY q1.revision_date DESC
                """,
                (d['username'],)
            )
            res = list(res)

            # TODO: Some minor copy/pasting from RecentChangesList.
            # For each of these changes, we want to find out the revision number
            # of the preceding revision so we can give a link to a diff.
            revnos = []
            for r in res:
                threads_id = r[2]
                revision_date = r[1]

                rnp = get_diff_revision_number_pair(dbcon, cur, threads_id, revision_date)
                assert rnp
                revnos.append(rnp)

            revisions = \
                map(
                    lambda r_and_d:
                        dict(article_title = r_and_d[0][0],
                             revision_date=get_ZonedDate(d, int(r_and_d[0][1])),
                             username=get_username(r_and_d[0][3], r_and_d[0][4]),
                             comment=r_and_d[0][5],
                             diff_revs_pair=r_and_d[1]),
                    itertools.izip(res, revnos)
                )
                    
            d['revisions'] = revisions
            return d
        except db.Error, e:
            dberror(e)
tracked_changes = TrackedChanges()

class Search(object):
    uris = [FollowedByQuery(links.SEARCH_PREFIX)]

    search_query_regex = re.compile(r"""\s*((?:(?:"|')[^\"]*(?:"|'))|(?:\S+))\s*""")

    @ok_html()
    @showkid('templates/search.kid')
    def GET(self, parms, extras):
        assert parms.has_key('query') # This key will be added by FollowedByQuery.

        qs = cgi.parse_qs(parms['query'])
        if not qs.has_key('query'):
            # Temporary measure; should do something sensible in this case.
            raise control.BadRequestError()

        # Now decode the query string (since we've been working in ASCII so far).
        qs['query'][0] = qs['query'][0].decode(config.WEB_ENCODING)
        #print qs['query'][0]

        strings = re.findall(Search.search_query_regex, qs['query'][0])
        if not strings:
            raise control.BadRequestError()
        strings = map(lambda s: s.strip(u'"').strip(u"'"), strings)

        try:
            dbcon = get_dbcon()
            cur = dbcon.cursor()

            for s in strings:
                like_string = '%' + s.replace('%', '\\%').replace('_', '\\_') + '%'

                res = cur.execute(
                    u"""
                    SELECT DISTINCT query1.threads_id, query1.title
                    FROM
                        (SELECT MAX(revision_date), revision_histories.threads_id AS threads_id, title
                         FROM revision_histories
                         INNER JOIN articles ON articles.id = revision_histories.articles_id
                         GROUP BY revision_histories.threads_id
                        ) query1
                    INNER JOIN category_specs ON category_specs.threads_id = query1.threads_id
                    WHERE query1.title LIKE ? OR category_specs.name LIKE ?
                """,
                (like_string, like_string)
                )

                for r in res:
                    print r[0], r[1]

            return merge_login(dbcon, cur, extras, dict())
        except db.Error, e:
            dberror(e)
search = Search()

class RenderTree(object):
    uris = [Abs(links.RENDER_SYNTAX_TREE)]

    def POST(self, parms, extras, start_response):
        if not parms.has_key('tree'):
            raise control.BadRequestError()
        tree_source = uu_decode(parms['tree'])
        font_size = 20
        if parms.has_key('font_size'):
            try:
                font_size = int(uu_decode(parms['font_size']))
            except ValueError:
                raise control.BadRequestError()
        
        r = sourceparser.run_parser(sourceparser.tree, tree_source, { })
        if isinstance(r, parcombs.ParserError):
            raise control.BadRequestError()
        tree, movements = r

        # This is just a temporary surface, since we need to create a surface
        # in order to get font metrics etc. Once we've determined how big
        # the tree will be, we'll create the real surface.
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1)
        context = cairo.Context(surface)
        cs = treedraw.CairoState(surface, font_size)
        tree.size(cs, root=True)
        # Found the size of the (image containing the) tree, so create a
        # surface to draw it on.
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, int(tree.dimensions[0]) + 5, int(tree.dimensions[1]) + 5)
        context = cairo.Context(surface)
        cs = treedraw.CairoState(surface, font_size)        
        treedraw.draw_tree(tree, movements, cs)

        buffer = StringIO.StringIO()
        surface.write_to_png(buffer)

        start_response('200 OK', [('Content-Type', 'image/png'), ('Accept-Range', 'bytes')])
        return [ buffer.getvalue() ]
render_tree = RenderTree()

class SyntaxTree(object):
    uris = [Abs(links.SYNTAX_TREE)]

    @ok_html()
    @showkid('templates/syntax_tree.kid')
    def GET(self, parms, extras):
        d = { }
        dbcon_merge_login(extras, d)
        return d
syntax_tree = SyntaxTree()

class DeleteArticle(object):
    uris = [VParm(links.ARTICLE_LINK_PREFIX) >> Abs(links.DELETE_SUFFIX) >> OptDir()]

    @ok_html()
    @showkid('templates/deleted.kid')
    def GET(self, parms, extras):
        try:
            dbcon = get_dbcon()
            cur = dbcon.cursor()

            title = unfutz_article_title(uu_decode(parms[links.ARTICLE_LINK_PREFIX]))

            d = { }
            merge_login(dbcon, cur, extras, d)

            if (not d.has_key('is_admin')) or (not d['is_admin']):
                return merge_dicts(d, dict(title=title))

            if delete_article(dbcon, cur, title):
                # The article exists and was deleted. Before committing to the
                # DB, make sure we remove the threads_id cache entry.
                if not threads_id_cache.stop_caching(title):
                    # Log a warning that the cache is now incorrect.
                    logging.log(config.INTERNAL_LOG, "WARNING: Could not remove threads_id cache for '%s'; cache now incorrect." % title)
                dbcon.commit()
                return merge_dicts(d, dict(title=title, exists_and_deleted=True))
            else:
                # Couldn't be deleted because it didn't exist in the first place.
                return merge_dicts(d, dict(title=title, exists_and_deleted=False))
        except db.Error, e:
            dberror(e)
delete_article_page = DeleteArticle() # Named so as not to conflict with delete_article function

control.register_handlers([front_page,
                           show_wiki_article,
                           edit_wiki_article,
                           revise_wiki_article,
                           wiki_article_history,
                           wiki_article_list,
                           create_account,
                           delete_account,
                           make_new_account,
                           login,
                           links_here,
                           diff,
                           preferences,
                           update_preferences,
                           watch,
                           unwatch,
                           watchlist,
                           tracked_changes,
                           render_tree,
                           syntax_tree,
                           delete_account_confirm,
                           category,
                           category_list,
                           recent_changes_list,
                           delete_article_page,
                           search])
control.start_server(config.SERVER_PORT)

