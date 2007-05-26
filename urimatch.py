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
# This module provides a simple parser for URIs, allowing URLs like:
#     www.foo.com/forum/thread/silly%20thread/posts/22
# to be easily matched.
#


import itertools
import my_utils


#
# Classes representing the different kinds of parser.
#

class Seqable(object):
    """A parser which can be sequenced with another parser.
       This abstract superclass exists only to define the >> operator as a
       synonim for the two-arg 'Seq' constructor.
    """
    def __rshift__(self, x):
        return Seq(self, x)
class Abs(Seqable):
    """Matches a URI as an absolute string. If this is sequenced with another
       parser, it will succeed if only an initial subpart of the URI is
       matched.
    """
    def __init__(self, uri, dict={}):
        self.uri = uri
        self.dict = dict
class Parm(Seqable):
    """Matches PARM/VALUE sections of URIs, with an optional default value
       if the URI terminates in PARM(/).
    """
    def __init__(self, parm_name, default=None):
        self.parm_name = parm_name
        self.default = default
        self.must_have_value = False
# Like Parm, but must have a value.
def VParm(parm_name):
    p = Parm(parm_name)
    p.must_have_value = True
    return p
class Selector(Seqable):
    """Matches /VALUE sections of URIs."""
    def __init__(self, parm_name):
        self.parm_name = parm_name
class Seq(Seqable):
    """Sequences two parsers, with (at least) one intervening '/' required
       between them.
    """
    def __init__(self, *patterns):
        self.patterns = patterns
        self.slash = True
# Like Seq, but does not require an intervening '/'.
def SeqNoSlash(*patterns):
    s = Seq(*patterns)
    s.slash = False
    return s
class Opt(Seqable):
    """Makes a parser optional, merging a given dictionary into the matrix
       dictionary if the parser fails.
    """
    def __init__(self, parser, default={ }):
        self.parser = parser
        self.default = default
class OptDir(Seqable):
    """Only allowed as the last parser (in linear terms). Allows an optional
       trailing slash on a URI.
    """
    pass


#
# Some utility functions.
#

def strip_initial_slash(str): return str.lstrip('/')

def strict_lstrip(str, s):
    """Only strips a single instance of the given string,
       unlike the 'lstrip' method which will strip as many as possible.
    """
    if str.startswith(s):
        return str[len(s):]
    else:
        return str

def ijoin(s, l):
    if len(l) >= 1:
        return s + s.join(l)
    else:
        return ''


#
# The pattern parser
#

def test_pattern_helper(pattern, uri, base=True):
    """The parsing algorithm."""
    if pattern.__class__ is Abs:
        uri2 = strip_initial_slash(uri)
        puri2 = strip_initial_slash(pattern.uri)
        if uri2.startswith(puri2):
            r = strict_lstrip(uri2, puri2)
            if base and r != '':
                return False
            return (pattern.dict, r)
        else: return False
    elif pattern.__class__ is Parm:
        uri2 = strip_initial_slash(uri)
        dirs = uri2.split('/')
        if dirs[0] == pattern.parm_name:
            if len(dirs) > 1 and len(dirs[1]) > 0:
                r = ijoin('/', dirs[2:])
                if base and r != '':
                    return False
                else:
                    return ({ pattern.parm_name : dirs[1] },
                              r )
            elif pattern.must_have_value:
                return False
            else:
                r = ijoin('/', dirs[1:])
                if base and r != '':
                    return False
                else:
                    return ({ pattern.parm_name : pattern.default },
                              r )
        else: return False
    elif pattern.__class__ is Selector:
        uri2 = strip_initial_slash(uri)
        dirs = uri2.split('/')
        r = ijoin('/', dirs[1:])
        if base and r != '':
            return False
        elif dirs[0] == '': # Don't allow selectors with nothing following them.
            return False
        else:
            return ({ pattern.parm_name : dirs[0] },
                    r )
    elif pattern.__class__ is Seq:
        uberdict = { }
        current_uri = uri
        for pat, i in zip(pattern.patterns, itertools.count()):
            res = test_pattern_helper(pat, current_uri, False)
            if not res:
                return False
            d, current_uri = res
            my_utils.merge_dicts(into=uberdict, from_=d)

            if pattern.slash                  and \
               i != len(pattern.patterns) - 1 and \
               len(current_uri) > 0           and \
               current_uri[0] != '/':
                return False
        if base and current_uri != '':
            return False
        else:
            return (uberdict, current_uri)
    elif pattern.__class__ is Opt:
        res = test_pattern_helper(pattern.parser, uri, False)
        if not res:
            if base and uri != '':
                return False
            return (pattern.default, uri)
        else:
            d, r = res
            if base and r != '':
                return False
            return res
    elif pattern.__class__ is OptDir:
        if uri.lstrip('/') == '':
            return ({ }, '')
        else:
            return False

def test_pattern(pattern, uri):
    res = test_pattern_helper(pattern, uri)
    if not res:
        return False
    d, _ = res
    # TODO: Find out WTF is going on.
    # Fix totally mysterious bug where test_pattern_helper keeps returning the
    # same dictionary.
    return d.copy()

# TEST CODE
#pat = Abs("foo/bar/amp") >> Abs("goo") >> Opt(Parm("foo", "oh")) >> Abs("lalala") >> Selector('gah') >> Parm("gg", "def")
#print test_pattern_helper(pat, "/foo/bar/amp/goo/lalala/value/gg/value2")

#pat = Parm("forums") >> Parm("thread") >> Opt(Parm("post", "0"), dict(post=0))
#print test_pattern(pat, "/forums/foo/thread/bar/post/1")

#pat = Parm("foo") >> Abs("amp") >> Selector("boo")
#print test_pattern(pat, "foo/bar/amp/55")

#pat = VParm("articles")
#print test_pattern(pat, "articles/foo")

