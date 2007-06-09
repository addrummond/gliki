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
This module contains a parser combinator library.
"""

import sys
import inspect
import new
import itertools
import sets
import treedraw
import types
import copy

class ParserError(Exception):
    def __init__(self, line, col, message, error_point=False):
        Exception.__init__(self, line, col, message, error_point)
        self.line = line
        self.col = col
        self.message = message
        self.error_point = error_point

    def __repr__(self):
        return "Parser error at line %i column %i: %s" % \
               (self.line, self.col, self.message)

class FatalParserError(ParserError):
    """A parser error that prevents any backtracking."""
    def __init__(*args):
        ParserError.__init__(*args)

def fatalize(pe):
    """Convert a ParserError into a FatalParserError."""
    return FatalParserError(pe.line, pe.col, pe.message, pe.error_point)

class ParserParms(object):
    def __init__(self, input, input_length):
        self.input = input
        self.input_length = input_length

class ParserState(object):
    def __init__(self, index, line, col, user_state):
        self.index = index
        self.line = line
        self.col = col
        self.user_state = user_state
        self.error_stack = []
def restore_state(s1, s2):
    s1.index = s2.index
    s1.line = s2.line
    s1.col = s2.col

def advanceilc(state, c):
    state.index += 1
    if c == '\n':
        state.line += 1
        state.col = 1
    else:
        state.col += 1

def estack(state, pe):
    """Pushes an error onto the error stack of the parser state and then returns
       the error.
    """
    state.error_stack.append(pe)
    return pe

class Parser(object):
    def __init__(self, func, doc = None):
        self.func = func
        self.__doc__ = doc
        self.name = None

    def __rshift__(self, p):
        if inspect.isfunction(p):
            return Bind(self, p)
        else:
            return Seq(self, p)

    def __mul__(self, p):
        return FOr(self, p)

    def __mod__(self, name):
        self.name = name
        # If the name is enclosed in a tuple, we also make this parser an
        # ErrorPoint.
        if type(name) == types.TupleType:
            return ErrorPoint(self)
        else:
            return self

    def __getitem__(self, p):
        return Apply(p, self)

    def __call__(self, parms, state):
        return self.func(parms, state)

def parser_name(p):
    if p.name:
        return p.name
    elif hasattr(p, '__name__'):
        return p.__name__
    else:
        return p.__class__.__name__

def Thunk(f):
    """Can be useful for creating mutually recursive parsers."""
    def parser(parms, state):
        return (f())(parms, state)
    return Parser(parser)

def Return(v):
    def parser(parms, state):
        return v
    return Parser(parser)

def RError(e='', line=None, col=None):
    """A parser that fails without consuming any input."""
    def parser(parms, state):
        return estack(state, ParserError((line is not None) and line or state.line, (col is not None) and col or state.col, e))
    return Parser(parser, RError.__doc__)

def RFatalError(e='', line=None, col=None):
    def parser(parms, state):
        raise FatalParserError((line is not None) and line or state.line, (col is not None) and col or state.col, e)
    return Parser(parser, RFatalError.__doc__)

def ErrorPoint(p):
    """A wrapper which makes a parser an error point."""
    def parser(parms, state):
        r = p(parms, state)
        if isinstance(r, ParserError):
            r.error_point = True
        return r
    return Parser(parser, ErrorPoint.__doc__)

def Fatalize(p):
    """Make a parser which returns a normal error raise a fatal error."""
    def parser(parms, state):
        r = p(parms, state)
        if isinstance(r, ParserError):
            raise FatalParserError(r.line, r.col, r.message)
        else:
            return r
    return Parser(parser, Fatalize.__doc__)

def Option(opt, p):
    """A parser..."""
    def parser(parms, state):
        saved = ParserState(state.index, state.line, state.col, None)
        r = p(parms, state)
        if isinstance(r, ParserError):
            restore_state(state, saved)
            return opt
        else:
            return r
    return Parser(parser, Option.__doc__)

def eof(parms, state):
    """Matches the end of an input stream."""
    if state.index == parms.input_length:
        return None
    else:
        return estack(state, ParserError(state.line, state.col, "Expecting end of input"))
EOF = Parser(eof, eof.__doc__)

def any_chr(parms, state):
    """Recognizes any character."""
    if state.index == parms.input_length:
        return estack(state, ParserError(state.line, state.col, "Unexpected end of input"))
    state.index += 1
    return parms.input[state.index - 1]
AnyChr = Parser(any_chr, any_chr.__doc__)

def Chr(c, compl=False, name=None):
    """Recognizes a single character, or anything except a single character if
       the second argument is True.
    """
    # It's a commmon mistake to call this with a string of length > 1, so check
    # for this.
    assert len(c) == 1
    def parser(parms, state):
        if state.index == parms.input_length:
            return estack(state, ParserError(
                state.line,
                state.col,
                "Expecting %s %s, found end of input" % \
                ((name and "" or (compl and "" or "anything except")),
                 (name and name or "'" + c + "'"))
            ))
        ic = parms.input[state.index]
        if (compl and c != ic) or ((not compl) and c == ic):
            advanceilc(state, ic)
            return ic
        else:
            return estack(state, ParserError(state.line, state.col, "Expecting '%s', found '%s'" % (c, ic)))
    return Parser(parser, Chr.__doc__)
def NChr(*args):
    if len(args) == 1:
        return Chr(args[0], True)
    elif len(args) == 2:
        return Chr(args[1], True, args[0])

def ChrP(name, pred):
    """Recognizes a character which matches a given predicate."""
    def parser(parms, state):
        if state.index == parms.input_length:
            return estack(state, ParserError(state.line, state.col, "Expecting %s, found end of input" % name))
        ic = parms.input[state.index]
        if pred(ic):
            advanceilc(state, c)
            return c
        else:
            return estack(state, ParserError(state.line, state.col, "Expecting %s, found '%s'" % (name, ic)))
    return Parser(parser, ChrP.__doc__)

# Not implemented using ChrP for efficiency reasons.
def ChrRanges(name, *ranges):
    """Recognizes a list of character ranges."""
    def parser(parms, state):
        if state.index == parms.input_length:
            return estack(state, ParserError(state.line, state.col, "Expecting %s, found end of input" % name))
        ic = parms.input[state.index]
        for r in ranges:
            if ord(ic) >= ord(r[0]) and ord(ic) <= ord(r[1]):
                advanceilc(state, ic)
                return c
        return estack(state, ParserError(state.line, state.col, "Expecting %s, found '%s'" % (name, ic)))
    return Parser(parser, ChrRanges.__doc__)

# Not implemented using ChrP for efficiency reasons.
def Chrs(chrs, compl=False):
    """Recognizes one of a set of characters."""
    def parser(parms, state):
        if state.index == parms.input_length:
            return estack(state, ParserError(state.line, state.col,
                              "Expecting one of %s, found end of input" % \
                              ', '.join(["'%s'" % x for x in chrs])
                             ))
        ic = parms.input[state.index]
        if ((not compl) and ic in chrs) or (compl and ic not in chrs):
            advanceilc(state, ic)
            return ic
        return estack(state, ParserError(state.line, state.col,
                           "Expecting one of %s, found '%s'" % \
                           (', '.join(["'%s'" % x for x in chrs]), ic)
                       ))
    return Parser(parser, Chrs.__doc__)
def NChrs(chrs): return Chrs(chrs, True)

Alpha = ChrRanges('letter', ('A', 'Z'), ('a', 'z'))
Upper = ChrRanges('uppercase letter', ('A', 'Z'))
Lower = ChrRanges('lowercase letter', ('a', 'z'))
Alnum = ChrRanges('letter or number', ('A', 'Z'), ('a', 'z'), ('0', '9'))
Digit = ChrRanges('number', ('0', '9'))
Whitespace = Chrs(" \r\n\f\t")
NoNLWhitespace = Chrs(" \t")

# Since skipping multiple whitespace characters is common,
# writing this out longhand can speed things up a bit.
def skip_whitespace(include_newlines=True):
    def parser(parms, state):
        # Note that the timing of advanceilc makes saving and restoring the
        # parser state unnecessary here.
        while True:
            if state.index == parms.input_length:
                return None
            ic = parms.input[state.index]
            if ic.isspace() and (include_newlines or (ic != '\r' and ic != '\n')):
                pass
            else:
                return None

            advanceilc(state, ic)
    return Parser(parser, skip_whitespace.__doc__)
SkipWhitespace = skip_whitespace()
SkipNoNLWhitespace = skip_whitespace(False)

def Str(s, case_sensitive=True):
    """Recognizes a string of characters."""
    def parser(parms, state):
        for c in s:
            if state.index == parms.input_length:
                return estack(state, ParserError(state.line, state.col,
                                            "Expecting \"%s\", found end of input" % s))
            ic = parms.input[state.index]
            advanceilc(state, ic)
            if (case_sensitive and ic != c) or ((not case_sensitive) and ic.upper() != c.upper()):
                return estack(state, ParserError(state.line, state.col,
                                            "Expecting \"%s\"" %s))
        return s
    return Parser(parser, Str.__doc__)
def StrCI(s): return Str(s, False)

def Strs(*strings):
    """Recognizes one of a number of strings (more efficient version of
       FOr(Str(...), Str(...), ...) )
    """
    def one_of():
        return ', '.join(map(lambda s: "'%s'" %s, strings))

    def parser(parms, state):
        forbidden = sets.Set([])
        l = len(strings)
        for i in itertools.count(0):
            if state.index == parms.input_length:
                return estack(state, ParserError(state.line, state.col,
                                            "Expecting one of %s; found end of input" % one_of()))
            ic = parms.input[state.index]
            advanceilc(state, ic)
            for j in xrange(l):
                if not j in forbidden:
                    if ic != strings[j][i]:
                        forbidden.add(j)
                    elif len(strings[j]) == i + 1:
                        return strings[j]
            if l - len(forbidden) == 0:
                return estack(state, ParserError(state.line, state.col,
                                            "Expecting one of %s" % one_of()))
        return estack(state, ParserError(state.line, state.col, "Expecting one of %s" % one_of()))
    return Parser(parser, Str.__doc__)

def Seq(*parsers):
    """Recognizes a number of parsers in sequence."""
    def parser(parms, state):
        r = None
        for p in parsers:
            r = p(parms, state)
            if isinstance(r, ParserError):
                return r
        return r
    return Parser(parser, Seq.__doc__)

def Apply(func, p):
    """Composes a function with a parser."""
    def parser(parms, state):
        r = p(parms, state)
        if isinstance(r, ParserError):
            return r
        return func(r)
    return Parser(parser, Apply.__doc__)

def Or(alt, *parsers):
    """Recognizes one of a series of parsers, returning a designated value if
       none of them succeeds.
    """
    def parser(parms, state):
        saved = ParserState(state.index, state.line, state.col, None)
        for p in parsers:
            r = p(parms, state)
            if not isinstance(r, ParserError):
                return r
            restore_state(state, saved)
        return alt
    return Parser(parser, Or.__doc__)

# Copy/paste from Or for efficiency reasons.
def LimitedOr(n, alt, *parsers):
    """Like Or, but with limited backtracking/lookahead.
    """
    def parser(parms, state):
        saved = ParserState(state.index, state.line, state.col, None)
        for p in parsers:
            r = p(parms, state)
            if not isinstance(r, ParserError):
                return r
            # Did we exceed our lookahead?
            if state.index - saved.index > n:
                return r # Return the error.
            restore_state(state, saved)
        return alt
    return Parser(parser, Or.__doc__)

def FOr(*parsers):
    """Recognizes one of a series of parsers, failing if none of them succeeds.
    """
    def parser(parms, state):
        saved = ParserState(state.index, state.line, state.col, None)
        oldline, oldcol = None, None
        for p in parsers:
            r = p(parms, state)
            if not isinstance(r, ParserError):
                return r
            oldline, oldcol = state.line, state.col
            restore_state(state, saved)
        # Construct an error message based on the names of the parsers.
        e = "Expecting "
        for i in xrange(len(parsers)):
            e += parser_name(parsers[i])
            if i < len(parsers) - 1:
                e += " OR "
        return estack(state, ParserError(oldline, oldcol, e))
    return Parser(parser, FOr.__doc__)

# Copy/pasted from FOr for efficiency reasons.
def LimitedFOr(n, *parsers):
    """Like FOr, but with limited backtracking/lookahead.
       If an error occurs after the lookahead has been exceeded, a FATAL parser
       error occurs.
    """
    def parser(parms, state):
        saved = ParserState(state.index, state.line, state.col, None)
        oldline, oldcol = None, None
        for p in parsers:
            r = p(parms, state)
            if not isinstance(r, ParserError):
                return r
            # Did we exceed our lookahead?
            if state.index - saved.index > n:
                # Convert the error to a fatal error, because we MUSTN'T
                # backtrack now -- the parse has failed, full stop.
                raise fatalize(r) # Return the error.
            oldline, oldcol = state.line, state.col
            restore_state(state, saved)
        # Construct an error message based on the names of the parsers.
        e = "Expecting "
        for i in xrange(len(parsers)):
            e += parser_name(parsers[i])
            if i < len(parsers) - 1:
                e += " OR "
        return estack(state, ParserError(oldline, oldcol, e))
    return Parser(parser, FOr.__doc__)

def Bind(p, f):
    """Passes the return value of a parser to a function which returns another
       parser.
    """
    def parser(parms, state):
        r = p(parms, state)
        if isinstance(r, ParserError):
            return r
        p2 = f(r)
        return p2(parms, state)
    return Parser(parser, Bind.__doc__)

def Many(n, p):
    """Recognizes n or more repetitions of a string recognized by a given
       parser. Returns a list of the results.
    """
    def parser(parms, state):
        results = []
        while True:
            saved = ParserState(state.index, state.line, state.col, None)
            r = p(parms, state)
            if isinstance(r, ParserError):
                oldline, oldcol = state.line, state.col
                restore_state(state, saved)
                if len(results) >= n:
                    return results
                else:
                    return estack(state, ParserError(oldline, oldcol,
                                                "Expecting %s" % parser_name(p)))
            else:
                results.append(r)
    return Parser(parser, Many.__doc__)
def Many0(p): return Many(0, p)
def Many1(p): return Many(1, p)

def CMany(n, p):
    """Like Many, but returns a count instead of a list of results."""
    def parser(parms, state):
        for count in itertools.count(0):
            saved = ParserState(state.index, state.line, state.col, None)
            r = p(parms, state)
            if isinstance(r, ParserError):
                oldline, oldcol = state.line, state.col
                restore_state(state, saved)
                if count >= n:
                    return count
                else:
                    return estack(state, ParserError(oldline, oldcol,
                                                "Expecting %s %s" % (parser_name(p), str(p.__doc__))))
    return Parser(parser, CMany.__doc__)
def CMany0(p): return CMany(0, p)
def CMany1(p): return CMany(1, p)

def SMany(n, p):
    """Converts n or more repetitions of a parser returning a string into a
       string sequencing all the results.
    """
    import StringIO
    def parser(parms, state):
        buf = StringIO.StringIO()
        for i in itertools.count(0):
            saved = ParserState(state.index, state.line, state.col, None)
            r = p(parms, state)
            if isinstance(r, ParserError):
                oldline, oldcol = state.line, state.col
                restore_state(state, saved)
                if i >= n:
                    return buf.getvalue()
                else:
                    return estack(state, ParserError(oldline, oldcol,
                                                "Expecting %s" % parser_name(p)))
            else:
                buf.write(r)
    return Parser(parser, SMany.__doc__)
def SMany0(p): return SMany(0, p)
def SMany1(p): return SMany(1, p)

def Until(n, p, until, pr=False, nrw=False):
    """TODO"""
    import StringIO
    def parser(parms, state):
        lst = []
        for i in itertools.count(0):
            saved = ParserState(state.index, state.line, state.col, None)
            ru = until(parms, state)
            if not isinstance(ru, ParserError):
                if i >= n:
                    if not nrw:
                        restore_state(state, saved)
                    if pr:
                        return (lst, ru)
                    else:
                        return lst
                else:
                    oldline, oldcol = state.line, state.col
                    return estack(state, ParserError(oldline, oldcol,
                                                "Not expecting %s" % parser_name(until)))
            else:
                restore_state(state, saved)
                r = p(parms, state)
                if isinstance(r, ParserError):
                    oldline, oldcol = state.line, state.col
                    return estack(state, ParserError(oldline, oldcol,
                                                "Expecting %s" % parser_name(p)))
                else:
                    lst.append(r)
    return Parser(parser, Until.__doc__)
def Until0(p, u): return Until(0, p, u)
def Until1(p, u): return Until(1, p, u)
def UntilPr0(p, u): return Until(0, p, u, True)
def UntilPr1(p, u): return Until(1, p, u, True)
def UntilNRW0(p, u): return Until(0, p, u, False, True)
def UntilNRW1(p, u): return Until(1, p, u, False, True)
def UntilNRWPr0(p, u): return Until(0, p, u, True, True)
def UntilNRWPr1(p, u): return Until(1, p, u, True, True)

def SUntil(n, p, until, pr=False, nrw=False):
    """Parses multiple repetitions of a string recognized by a parser into a
       string, stopping when a designated parser matches the input stream.
       If the first parser fails at any point, SUntil fails.
       Rewinds the input stream to the point before the 'until' parser
       fails.
    """
    import StringIO
    def parser(parms, state):
        buf = StringIO.StringIO()
        for i in itertools.count(0):
            saved = ParserState(state.index, state.line, state.col, None)
            ru = until(parms, state)
            if not isinstance(ru, ParserError):
                if i >= n:
                    if not nrw:
                        restore_state(state, saved)
                    if pr:
                        return (buf.getvalue(), ru)
                    else:
                        return buf.getvalue()
                else:
                    oldline, oldcol = state.line, state.col
                    return estack(state, ParserError(oldline, oldcol,
                                                "Not expecting %s" % parser_name(until)))
            else:
                restore_state(state, saved)
                r = p(parms, state)
                if isinstance(r, ParserError):
                    oldline, oldcol = state.line, state.col
                    return estack(state, ParserError(oldline, oldcol,
                                                "Expecting %s" % parser_name(p)))
                else:
                    buf.write(r)
    return Parser(parser, SUntil.__doc__)
def SUntil0(p, u): return SUntil(0, p, u)
def SUntil1(p, u): return SUntil(1, p, u)
def SUntilPr0(p, u): return SUntil(0, p, u, True)
def SUntilPr1(p, u): return SUntil(1, p, u, True)
def SUntilNRW0(p, u): return SUntil(0, p, u, False, True)
def SUntilNRW1(p, u): return SUntil(1, p, u, False, True)
def SUntilNRWPr0(p, u): return SUntil(0, p, u, True, True)
def SUntilNRWPr1(p, u): return SUntil(1, p, u, True, True)

def CUntil(n, p, until, pr=False, nrw=False):
    """Like SUntil, but keeps a count instead of accumulating a string."""
    def parser(parms, state):
        for i in itertools.count(0):
            saved = ParserState(state.index, state.line, state.col, None)
            ru = until(parms, state)
            if not isinstance(ru, ParserError):
                if i >= n:
                    if not nrw:
                        restore_state(state, saved)
                    if pr:
                        return (i, ru)
                    else:
                        return i
                else:
                    oldline, oldcol = state.line, state.col
                    return estack(state, ParserError(oldline, oldcol,
                                                "Not expecting %s" % parser_name(until)))
            else:
                restore_state(state, saved)
                r = p(parms, state)
                if isinstance(r, ParserError):
                    oldline, oldcol = state.line, state.col
                    return estack(state, ParserError(oldline, oldcol,
                                                "Expecting %s" % parser_name(p)))
    return Parser(parser, SUntil.__doc__)
def CUntil0(p, u): return CUntil(0, p, u)
def CUntil1(p, u): return CUntil(1, p, u)
def CUntilPr0(p, u): return CUntil(0, p, u, True)
def CUntilPr1(p, u): return CUntil(1, p, u, True)
def CUntilNRW0(p, u): return CUntil(0, p, u, False, True)
def CUntilNRW1(p, u): return CUntil(1, p, u, False, True)
def CUntilNRWPr0(p, u): return CUntil(0, p, u, True, True)
def CUntilNRWPr1(p, u): return CUntil(1, p, u, True, True)

def SepBy(n, p, psep):
    def parser(parms, state):
        results = []
        for i in itertools.count(0):
            r = p(parms, state)
            if isinstance(r, ParserError):
                return r
            else:
                results.append(r)
            saved = ParserState(state.index, state.line, state.col, None)
            r = psep(parms, state)
            if isinstance(r, ParserError):
                if i >= n:
                    restore_state(state, saved)
                    return results
                else:
                    return r
    return Parser(parser, SepBy.__doc__)
def SepBy0(p, psep): return SepBy(0, p, psep)
def SepBy1(p, psep): return SepBy(1, p, psep)

def SetState(key, value):
    """Sets a key in the parser's state dict."""
    def parser(parms, state):
        state.user_state[key] = value
        return state.user_state
    return Parser(parser, SetState.__doc__)

def GetState(key):
    """Gets a value in the parser's state dict."""
    def parser(parms, state):
        return state.user_state[key]
    return Parser(parser, GetState.__doc__)

def UpdateState(key, f):
    """Applies a function to get a new value for an entry in the parser's state dict."""
    def parser(parms, state):
        state.user_state[key] = f(state.user_state[key])
    return Parser(parser, UpdateState.__doc__)

def DoWithState(key, f):
    """Like UpdateState, but doesn't use the return value of the function to
       change the value for the key in the parser's state dict.
    """
    def parser(parms, state):
        f(state.user_state[key])
    return Parser(parser, DoWithState.__doc__)

def DeleteState(key):
    """Deletes a key from the parser's state dict."""
    def parser(parms, state):
        del state.user_state[key]
    return Parser(parser, DeleteState.__doc__)

def ProtectState(p, copyfunc=copy.deepcopy):
    """Restores original user state if a parser fails.
       Does not restore state on fatal errors.
       Uses copy.deepcopy() for every memeber of the hash by default, or a
       user-supplied function."""
    def parser(parms, state):
        copy = { }
        us = state.user_state
        for k in us.iterkeys():
            copy[k] = copyfunc(us[k])
        r = p(parms, state)
        if isinstance(r, ParserError):
            state.user_state = copy
            return r
    return Parser(parser, ProtectState.__doc__)

def GetPos():
    def parser(parms, state):
        return state.line, state.col
    return Parser(parser, GetPos.__doc__)

def debug_print_user_state(parms, state):
    print "STATE: " + str(state.user_state)
    return None
DebugPrintUserState = Parser(debug_print_user_state)

def debug_print_input(parms, state):
    print ("INP: %i --" % len(parms.input[state.index])), parms.input[state.index:50], "--"
    return None
DebugPrintInput = Parser(debug_print_input)

def run_parser(p, input, initial_user_state):
    parms = ParserParms(input=input, input_length=len(input))
    state = ParserState(index=0, line=1, col=1, user_state=initial_user_state)
    r = None
    try:
        r = p(parms, state)
    except FatalParserError, e:
        r = e
    if isinstance(r, ParserError) and not isinstance(r, FatalParserError):
        for e in reversed(state.error_stack):
            if hasattr(e, 'error_point') and e.error_point:
                return e
    return r

#print run_parser(Strs("aa", "abbb"), 'abb', { })

