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
# Some random functions which don't fit anywhere in particular.
#

import time
import itertools
import StringIO

def truncate(n, s):
    """Truncates a string s to at most n chars,
       appending '...' if the string is truncated.
    """
    if len(s) >= n:
        x = n - 3
        if x < 1: x = 1
        return s[0:x] + "..."
    else:
        return s

def standard_date_format(stime):
    """Formats a time to a string given the return value of time.gmtime(...)
       or the like.
    """
    return time.strftime("%Y-%m-%d %H:%M:%S UTC", stime)

def futz_article_title(title):
    return title.replace(' ', '-')
def unfutz_article_title(title):
    return title.replace('_', ' ').replace('-', ' ')

def get_ymdhms_tuple():
    """Get a tuple (year, month, day, hour, minute, second)."""
    f_time = time.time()
    stime = time.gmtime(f_time)
    int_time = int(f_time)
    year   = time.strftime("%Y", stime)
    month  = time.strftime("%m", stime)
    day    = time.strftime("%d", stime)
    hour   = time.strftime("%H", stime)
    minute = time.strftime("%M", stime)
    second = time.strftime("%S", stime)
    return (year, month, day, hour, minute, second)

def merge_dicts(into, from_):
    """Merge values from one dictionary into another, returning the 'into'
       argument."""
    for k in from_.keys():
        into[k] = from_[k]
    return into

def diff_lists(old, new):
    new_elts      = filter(lambda x: not (x in old), new)
    removed_elts  = filter(lambda x: not (x in new), old)
    return new_elts, removed_elts

def flatten_list(L):
    if type(L) != type([]): return [L]
    if L == []: return L
    return flatten_list(L[0]) + flatten_list(L[1:])

# From the Python cookbook.
def unique(s):
    """Return a list of the elements in s, but without duplicates.

    For example, unique([1,2,3,1,2,3]) is some permutation of [1,2,3],
    unique("abcabc") some permutation of ["a", "b", "c"], and
    unique(([1, 2], [2, 3], [1, 2])) some permutation of
    [[2, 3], [1, 2]].

    For best speed, all sequence elements should be hashable.  Then
    unique() will usually work in linear time.

    If not possible, the sequence elements should enjoy a total
    ordering, and if list(s).sort() doesn't raise TypeError it's
    assumed that they do enjoy a total ordering.  Then unique() will
    usually work in O(N*log2(N)) time.

    If that's not possible either, the sequence elements must support
    equality-testing.  Then unique() will usually work in quadratic
    time.
    """

    n = len(s)
    if n == 0:
        return []

    # Try using a dict first, as that's the fastest and will usually
    # work.  If it doesn't work, it will usually fail quickly, so it
    # usually doesn't cost much to *try* it.  It requires that all the
    # sequence elements be hashable, and support equality comparison.
    u = {}
    try:
        for x in s:
            u[x] = 1
    except TypeError:
        del u  # move on to the next method
    else:
        return u.keys()

    # We can't hash all the elements.  Second fastest is to sort,
    # which brings the equal elements together; then duplicates are
    # easy to weed out in a single pass.
    # NOTE:  Python's list.sort() was designed to be efficient in the
    # presence of many duplicate elements.  This isn't true of all
    # sort functions in all languages or libraries, so this approach
    # is more effective in Python than it may be elsewhere.
    try:
        t = list(s)
        t.sort()
    except TypeError:
        del t  # move on to the next method
    else:
        assert n > 0
        last = t[0]
        lasti = i = 1
        while i < n:
            if t[i] != last:
                t[lasti] = last = t[i]
                lasti += 1
            i += 1
        return t[:lasti]

    # Brute force is all that's left.
    u = []
    for x in s:
        if x not in u:
            u.append(x)
    return u

#
# What was I smoking when I wrote this?
# Seems a shame to delete it even though it's no use.
#
#def group_by_preds(lst, *predicates):
#    """
#    Groups a list into a list of lists using a list of predicates.
#    Each element in the original list is given an index determined by the
#    predicate which it matches (or a different index if none of the predicates
#    match). Consecutive elements with identical indices are then grouped.
#    """
#    def index():
#        for elem in lst:
#            matched = False
#            for p, i in itertools.izip(predicates, itertools.count(1)):
#                if p(elem):
#                    matched = True
#                    yield (elem, i)
#            if not matched:
#                yield (elem, 0)
#    def group(it):
#        current_list = []
#        for elem in it:
#            if len(current_list) == 0:
#                current_list.append(elem)
#            else:
#                if elem[1] == current_list[len(current_list) - 1][1]:
#                    current_list.append(elem)
#                else:
#                    yield current_list
#                    current_list = [elem]
#        if len(current_list) != 0:
#            yield current_list
#    def fst(it):
#        while True:
#            yield [x[0] for x in it.next()]
#    return list(fst(group(index())))

class PrettyDiffError(Exception):
    def __init__(*args):
        Exception.__init__(*args)
def sys_diff(s2, s1):
    import tempfile
    import os
    import time
    s1f = None
    s2f = None

    # Might be unicode strings in UTF-8, in which case make sure we convert
    # them to byte arrays before we write them to temporary files.
    import types
    using_unicode = False
    if s2.__class__ == types.UnicodeType:
        using_unicode = True
        s2 = s2.encode('utf-8')
    if s1.__class__ == types.UnicodeType:
        using_unicode = True
        s1 = s1.encode('utf-8')

    try:
        try:
            s1f = tempfile.NamedTemporaryFile()
            s2f = tempfile.NamedTemporaryFile()

            s1f.write(s1 + (s1[len(s1) - 1] != '\n' and '\n' or ''))
            s2f.write(s2 + (s2[len(s2) - 1] != '\n' and '\n' or ''))
            s1f.flush()
            s2f.flush()

            diff = os.popen("/usr/bin/diff -a %s %s" % (s1f.name, s2f.name), "r")
            return using_unicode and diff.read().decode('utf-8') or diff.read()
        except Exception, e:
            print e
            raise PrettyDiffError() 
    finally:
        if s1f: s1f.close()
        if s2f: s2f.close()

class Change(object):
    def __init__(self, lines, oldtext, newtext):
        self.lines = lines
        self.oldtext = oldtext
        self.newtext = newtext

    def __repr__(self):
        return "(lines: %s, oldtext: %s, newtext: %s)" % (str(self.lines), str(self.oldtext), str(self.newtext))

def parse_diff(difftext):
    """
    This assumes that the difftext is correctly formatted, but it will
    always raise some kind of runtime exception for invalid input.
    """
    def ris(s):
        """TODO."""
        if s[1] == ' ':
            return s[2:]
        else:
            return s[1:]

    def lines(s):
        spl = s.split(',')
        if len(spl) == 1:
            n = int(s)
            return (n, n)
        else:
            return (int(spl[0]), int(spl[1]))

    state = 'initial' 
    changes = []
    current_change = None
    for l, linecount in itertools.izip(difftext.split('\n'), itertools.count(0)):
        if len(l) == 0:
            continue

        if state == 'add':
            if l[0] == '>':
                current_change.newtext.append(ris(l))
            else:
                changes.append(current_change)
                current_change = None
                # FALLTHROUGH TO INITIAL STATE WITHOUT LOOPING AGAIN.
                state = 'initial'
        elif state == 'delete':
            if l[0] == '<':
                current_change.oldtext.append(ris(l))
            else:
                changes.append(current_change)
                current_change = None
                # FALLTHROUGH TO INITIAL STATE WITHOUT LOOPING AGAIN.
                state = 'initial'
        elif state == 'change_old':
            if l[0] == '<':
                current_change.oldtext.append(ris(l))
            else:
                # FALLTHROUGH TO CHANGE_NEW1 STATE WITHOUT LOOPING AGAIN.
                state = 'change_new1'
        if state == 'change_new1':
            assert l[1] == '-'
            state = 'change_new2'
        elif state == 'change_new2':
            if l[0] == '>':
                current_change.newtext.append(ris(l))
            else:
                changes.append(current_change)
                current_change = None
                # FALLTHROUGH TO INITIAL STATE WITHOUT LOOPING AGAIN.
                state = 'initial'

        if state == 'initial':
            spl = l.split('a')
            if len(l.split('a')) != 1:
                state = 'add'
                current_change = Change(lines(spl[0]), None, [])
                continue
            spl = l.split('d')
            if len(spl) != 1:
                state = 'delete'
                current_change = Change(lines(spl[0]), [], None)
                continue
            spl = l.split('c')
            if len(spl) != 1:
                state = 'change_old'
                current_change = Change(lines(spl[0]), [], [])
                continue
            else:
                assert False

    if current_change:
        changes.append(current_change)
    return changes

def pretty_diff(doc1, doc2, max_chars_per_line=80):
    """Diffs two docs and outputs the result in in XHTML.
       Assumes everything is in UTF-8."""
    def add_brs(text, n):
        """Add <br /> tags into a string to ensure that line breaks follow
           as soon as possible after n characters (line breaks are only
           inserted in place of whitespace).
        """
        sstack = []
        i = 0
        while i < len(text):
            found_space = False
            j = i + n
            while j < len(text):
                if text[j].isspace():
                    sstack.append(text[i : j])
                    found_space = True
                    i = j + 1
                    break
                j += 1
            if not found_space:
                sstack.append(text[i:])
                break
        return u'<br />'.join(sstack)

    difftext = sys_diff(doc1, doc2)
    changes = parse_diff(difftext)

    if len(changes) == 0: return None

    import StringIO
    import htmlutils
    xhtml = StringIO.StringIO()

    xhtml.write(u'<table class="diff">\n')
    for c in changes:
        xhtml.write(u'    <tr>\n')
        if c.oldtext:
            xhtml.write(u'        <td class="old-text-minus">-</td>\n')
            xhtml.write(u'        <td class="old-text">\n')
            for line in c.oldtext:
                xhtml.write(u'            ')
                xhtml.write(add_brs(htmlutils.htmlencode(line), max_chars_per_line))
                xhtml.write(u'<br />\n')
            xhtml.write(u'        </td>\n')
        if c.newtext:
            xhtml.write(u'        <td class="new-text-plus">+</td>\n')
            if not c.oldtext:
                xhtml.write(u'        <td></td>\n')
            xhtml.write(u'        <td class="new-text">\n')
            for line in c.newtext:
                xhtml.write(u'            ')
                xhtml.write(add_brs(htmlutils.htmlencode(line), max_chars_per_line))
                xhtml.write(u'<br />\n')
            xhtml.write('        </td>\n')
        xhtml.write(u'    </tr>\n')
    xhtml.write(u'</table>')

    return xhtml.getvalue().encode('utf-8')

# TODO: Is there a standard Python module for handling this format?
def csv_parse(string):
    """Parses key/value pairs in the format key1="value1", key2="value2", ...
       Quotes around values are optional.
       Returns None on failure and a dictionary on success.
    """
    d = { }
    state = 'initial'
    current_key = None
    current_value = None
    for c in string:
        if state == 'initial':
            if c.isspace():
                pass
            else:
                current_key = StringIO.StringIO()
                current_key.write(c)
                state = 'in_key'
        elif state == 'in_key':
            if c == '=':
                state = 'waiting_for_opening_quote'
            else:
                current_key.write(c)
        elif state == 'waiting_for_opening_quote':
            if c.isspace():
                pass
            elif c == '"':
                current_value = StringIO.StringIO()
                state = 'in_value'
            else:
                current_value = StringIO.StringIO()
                current_value.write(c)
                state = 'in_bare_value'
        elif state == 'in_value':
            if c == '"':
                d[current_key.getvalue()] = current_value.getvalue()
                state = 'waiting_for_comma'
            else:
                current_value.write(c)
        elif state == 'in_bare_value':
            if c.isspace() or c == ',':
                d[current_key.getvalue()] = current_value.getvalue()
                if c == ',':
                    state = 'initial'
                else:
                    state = 'waiting_for_comma'
            else:
                current_value.write(c)
        elif state == 'waiting_for_comma':
            if c.isspace():
                pass
            elif c == ',':
                state = 'initial'
            else:
                return None # Indicates error.
        else:
            assert False
    
    if state == 'in_bare_value':
        d[current_key.getvalue()] = current_value.getvalue()

    # Better to have a maximally permissive parser for our purposes.
    #
    #if state != 'initial' and state != 'waiting_for_comma' and state != 'in_bare_value':
    #    return None # Indicates error

    return d

def mark_last(seq):
    """Given a sequence, yields a (X, boolean) pair for each X in the sequence.
       The boolean is True if X is the last element in the sequence and false
       otherwise. This is a lazy as possible (only computes one element in the
       sequence ahead).
    """
    seq = iter(seq)
    previous = []
    while True:
        try:
            r1 = seq.next()
        except StopIteration:
            for p in previous: yield p, True
            break
        for p in previous: yield p, False
        previous = [r1]

# TEST CODE.
#print pretty_diff("  aa\nbb\n\n\nfoo", "aa\naa\n\n\nbar")

