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
This module contains a parser for the Gliki markup language written using
a parser combinator library (see parcombs.py) and a translator from the
markup language to XHTML.
"""

from parcombs import *
import htmlutils
import urllib
import re
import itertools
import my_utils
import types
import links

# Work around Python's hobbled lambda.
def add1_to_last_elem_of_list(l):
    l[len(l) - 1] += 1
    return True
def set_hash(hash, key, value):
    hash[key] = value
    return True

__lrexp = r"(.*?):(.*)"
__clregexp = re.compile(__lrexp)
def link_encode(link):
    "TODO"
    if ':' in link:
        m = __clregexp.match(link)
        pref = m.group(1)
        addy = m.group(2)
        return pref + ':' + my_utils.safequote(addy)
    else:
        return link

# Allows \X escape sequences.
# Now implemented as a low-level parser for efficiency reasons.
#
#escchr = FOr(
#    Chr('\\') >> AnyChr
#    ,
#    AnyChr
#)
def escchr_(parms, state):
    """Recognizes a single character, or a "\X" sequence."""
    if state.index == parms.input_length:
        return estack(state, ParserError(state.line, state.col, "Unexpected end of input"))
    c = parms.input[state.index]
    if parms.input[state.index] == '\\':
        advanceilc(state, c)
        if state.index == parms.input_length:
            return estack(state, ParserError(state.line, state.col, "EOF after backslash"))
        advanceilc(state, c)
        return parms.input[state.index - 1]
    else:
        advanceilc(state, c)
        return c
escchr = Parser(escchr_, escchr_.__doc__)


#
# THE PARSER FOR SYNTAX TREES.
#
def tree_():
    return LimitedFOr(2,
        (Chr("[") >> Fatalize(
         DoWithState('current_path', add1_to_last_elem_of_list) >>
         SkipWhitespace >>
         # Optional label (for connecting with traces).
         Option(None,
                Str("->") >>
                Fatalize(SUntil1(AnyChr, Whitespace * Chrs('[]'))) % "No text between ':' and ':' for node label") >>
         (lambda trace_label:
         GetState('current_path') >>
         (lambda current_path:
         (trace_label and \
             DoWithState('landing_sites', lambda ls: set_hash(ls, trace_label, current_path[0:]))
                      or \
             Return(None)) >>
         SkipWhitespace >>
         SUntil1(escchr, Whitespace * Chrs("'[]")) >>
         (lambda label:
         CMany0(Chr("'")) >>
         (lambda bars:
         CMany0(Whitespace) >>
         DoWithState('current_path', lambda cp: cp.append(-1)) >>
         SepBy0(tree_(), CMany1(Whitespace)) >>
         (lambda children:
         DoWithState('current_path', lambda cp: cp.pop()) >>
         CMany0(Whitespace) >> Chr("]") >>
         Return(treedraw.TreeNode(treedraw.Label(label, bars), children)))))))))
        ,
        # Traces.
        (Str("<-") >>
         DoWithState('current_path', add1_to_last_elem_of_list) >>
         Fatalize(
         SUntil1(AnyChr, Whitespace * Chrs('[]')) >>
         (lambda trace_label:
         GetState('traces') >>
         (lambda traces:
         (GetState('current_path') >>
         (lambda current_path:
         set_hash(traces, trace_label, current_path[0:]) and \
         Return(treedraw.TreeNode(treedraw.Label("t", 0), []))))))
         ) % "No idenfitier following trace ('_')" )
        ,
        (SUntil1(escchr, Whitespace * Chr("]") * EOF) >>
         (lambda label:
         DoWithState('current_path', add1_to_last_elem_of_list) >>
         CMany0(Chr("'")) >>
         (lambda bars:
         SkipWhitespace >>
         Return(treedraw.TreeNode(treedraw.Label(label, bars), [])))))
    )
def find_movements(landing_sites, traces):
    """Given a hash matching labels with landing sites paths and a hash matching
       labels with trace paths, find all the movements and return a list of
       pairs of paths. Ignores landing sites without matching traces and vice
       versa.
    """
    movements = [ ]
    for l in landing_sites.iterkeys():
        if traces.has_key(l):
            movements.append((traces[l][1:], landing_sites[l][1:]))
    return movements
tree = \
    (SetState('current_path', [-1]) >>
     SetState('landing_sites', { }) >>
     SetState('traces', { }) >>
     tree_() >>
     (lambda r:
     DeleteState('current_path') >>
     GetState('traces') >>
     (lambda traces:
     GetState('landing_sites') >>
     (lambda landing_sites:
     DeleteState('traces') >>
     DeleteState('landing_sites') >>
     Return((r, find_movements(landing_sites, traces)))))))


#
# THE PARSER FOR THE MAIN MARKUP LANGUAGE.
#

skip_blank_lines = (
    CMany0(SkipNoNLWhitespace >> Chr("\n"))
)

section = ErrorPoint(
    CMany(2, Chr('=')) >> \
    (lambda n:
    SUntil1(escchr, Chr('=')) >>
    (lambda title:
    Fatalize(CMany1(Chr('='))) >>
    (lambda closing_eq_count:
    closing_eq_count == n      and
        skip_blank_lines >>
        Return((n - 1, title)) or
        RFatalError("Wrong number of '=' characters at the end of the section title")
    ))))

class ArticleRef(object):
    __slots__ = ['article', 'sections', 'alt']

    def __init__(self, article, sections, alt=None):
        self.article = article
        self.sections = sections
        self.alt = alt

    def __repr__(self):
        return repr(self.article) + repr(self.sections) + '|' + (self.alt and self.alt or '')

subsection_refs = Many1(Chr('#') >> SUntil1(AnyChr, Strs('#', '|', ']]')))

article_ref = (
    Str("[[") >>
    SUntil0(escchr, Strs('#', '|', ']]')) >>
    (lambda name:
        LimitedFOr(2,
            Str("]]") >>
            DoWithState('article_refs', lambda ars: name and ars.append(name)) >>
            Return(ArticleRef(name, None))
            ,
            subsection_refs >>
            (lambda subs:
            # Is the link to be displayed with a different title?
            LimitedFOr(2,
                Chr('|') >>
                SUntil1(escchr, Str(']]')) >>
                (lambda alt:
                Str(']]') >>
                DoWithState('article_refs', lambda ars: name and ars.append(name)) >>
                Return(ArticleRef((name == '' and (None,) or (name,))[0], subs, alt)))
                ,
                Str(']]') >>
                DoWithState('article_refs', lambda ars: name and ars.append(name)) >>
                # Note the use of the (TEST and (IFTRUE,) or (IFFALSE,))[0] idiom here.
                Return(ArticleRef((name == '' and (None,) or (name,))[0], subs))
            ))
            ,
            Chr('|') >>
            SUntil1(escchr, Str(']]')) >>
            (lambda alt:
            Str(']]') >>
            DoWithState('article_refs', lambda ars: name and ars.append(name)) >>
            Return(ArticleRef((name == '' and (None,) or (name,))[0], None, alt)))
        ))
)

class ExternalRef(object):
    __slots__ = ['url', 'alt']

    def __init__(self, url, alt=None):
        self.url = url
        self.alt = alt

class Image(object):
    __slots__ = ['url']

    def __init__(self, url):
        self.url = url

# Also handles image links.
external_ref = (
    Str('{{') >>
    SUntil1(escchr, Strs('|', '}}')) >>
    (lambda url:
    Return(url.endswith('.jpeg') or url.endswith('.jpg') or \
           url.endswith('.png') or url.endswith('.gif') or \
           url.endswith('.bmp') or url.endswith('.ico')) \
    >>
    (lambda is_img:
    LimitedFOr(2,
        Str("}}") >>
        (is_img and \
              Return(Image(url))
                or \
              Return(ExternalRef(url)))
        ,
        Chr("|") >>
        (is_img and \
             RFatalError("An image link can't have a label after a '|' character")
                or \
             SUntilNRW1(escchr, Str("}}")) >>
             (lambda alt:
             Return(ExternalRef(url, alt))))
    )))
)

class ExampleRef(object):
    __slots__ = ['label']

    def __init__(self, label):
        self.label = label

example_ref = (
    Str("[:") >>
    Fatalize(SUntilNRW1(escchr, Str(":]"))) % "No text between [: and :]" >>
    (lambda label:
    Return(ExampleRef(label)))
)

class Footnote(object):
    __slots__ = ['paragraphs', 'display_inline']

    def __init__(self, paragraphs, display_inline=False):
        self.paragraphs = paragraphs
        self.display_inline = display_inline

    def __repr__(self):
        return "^^(" + repr(self.paragraphs) + ")^^"

footnote = (
    Str("^^") >>
    SetState('in_footnote', True) >>
    # The parser state has an option where footnotes are just treated as
    # plain text (this is used when parsing comments.)
    # NOTE: Except it isn't now that comment have been removed!
    GetState('no_footnotes') >>
    (lambda nf:
    Apply(
        nf and (lambda x: Footnote(x, display_inline=True)) or Footnote
        ,
        UntilNRW1(paragraph, Str("^^")) >>
        (lambda p:
        SetState('in_footnote', False) >>
        Return(p))))
)

class Formatted(object):
    __slots__ = ['kind', 'text', 'children']

    def __init__(self, kind, text, children):
        self.kind = kind
        # One of the following must be None.
        self.text = text
        self.children = children

    def __repr__(self):
        return "{%s : %s : %s}" % (self.kind, self.text, str(self.children))

class MDash(object):
    __slots__ = []
class LDQuo(object):
    __slots__ = []
class RDQuo(object):
    __slots__ = []

#
# Earlier versions of the parser parsed nested formatting tags
# (e.g. "**//foo//**") using a straightforward recursive parser. However,
# this made it difficult to sufficiently restrict the grammar. For example,
# there was no easy way of ruling out "**//**foo**//**", with bold nested
# within bold; but in practice the string "**//**" would surely indicate an
# error which ought to be reported.
#
# The strategy now used is to first parse formatted text as a sequence of
# symbols (e.g. ["//", "some plain text", "//"], and then manually construct
# a tree from this sequence. This ends up not being much more complicated,
# and is much more robust when it comes to error reporting.
#
class Elem(object):
    __slots__ = ['line', 'col', 'special', 'text']

    def __init__(self, line, col, special, text):
        self.line = line
        self.col = col
        self.special = special
        self.text = text
def build_formatted(list):
    currently_in = []
    current_node = Formatted('plain', text=None, children=None)
    parent_stack = []

    def error(line, col, x):
        #print "ERROR", x
        return (line, col, x)

    regular_map = {
        '//' : 'italic',
        '**' : 'bold',
        '||' : 'sc',
        '__' : 'underline'
    }

    def ensure_children(node):
        if node.children is None:
            node.children = []
        return node

    for elem in list:
        if isinstance(elem, Elem) and elem.special:
            if regular_map.has_key(elem.text):
                if elem.text in currently_in:
                    if currently_in[len(currently_in) - 1] != elem.text:
                        return error(elem.line, elem.col, "Found '%s' when expecting '%s'" % (elem.text, currently_in[len(currently_in) - 1]))
                    else:
                        current_node = parent_stack.pop()
                        currently_in.pop()
                else:
                    currently_in.append(elem.text)
                    parent_stack.append(current_node)
                    newnode = Formatted(regular_map[elem.text], None, [])
                    ensure_children(current_node).children.append(newnode)
                    current_node = newnode
            elif not elem.text:
                pass
            elif elem.text == "|^":
                if '|^' in currently_in:
                    return error(elem.line, elem.col, "Found '|^' when already in superscript")
                else:
                    currently_in.append(elem.text)
                    parent_stack.append(current_node)
                    newnode = Formatted('sup', None, [])
                    ensure_children(current_node).children.append(newnode)
                    current_node = newnode
            elif elem.text == "^|":
                if currently_in[len(currently_in) - 1] != '|^':
                    if '|^' in currently_in:
                        return error(elem.line, elem.col, "Found closing '^|' before all formatted text after '|^' was closed.")
                    else:
                        return error(elem.line, elem.col, "Found '^|' without preceding opening '|^'")
                else:
                    current_node = parent_stack.pop()
                    currently_in.pop()
            elif elem.text == "|_":
                if '|_' in currently_in:
                    return error(elem.line, elem.col, "Found '|_' when already in subscript")
                else:
                    currently_in.append(elem.text)
                    parent_stack.append(current_node)
                    newnode = Formatted('sub', None, [])
                    ensure_children(current_node).children.append(newnode)
                    current_node = newnode
            elif elem.text == "_|":
                if currently_in[len(currently_in) - 1] != '|_':
                    if '|_' in currently_in:
                        return error(elem.line, elem.col, "Found closing '_|' before all formatted text after '|_' was closed.")
                    else:
                        return error(elem.line, elem.col, "Found '_|' without preceding opening '|_'")
                else:
                    current_node = parent_stack.pop()
                    currently_in.pop()
            elif elem.text == "--":
                ensure_children(current_node).children.append(MDash())
            elif elem.text == '``':
                ensure_children(current_node).children.append(LDQuo())
            elif elem.text == "''":
                ensure_children(current_node).children.append(RDQuo())
            else:
                assert False
        elif isinstance(elem, ArticleRef) or isinstance(elem, ExternalRef) or \
             isinstance(elem, Footnote) or isinstance(elem, ExampleRef):
            ensure_children(current_node).children.append(elem)
        else: # Plain text.
            text = elem.text
            if '||' in currently_in:
                text = text.upper()
            ensure_children(current_node).children.append(Formatted('plain', text, None))

    # Check that we aren't missing any closing tags.
    if not len(currently_in) == 0:
        return error(None, None,
                     "End of input reached without the following opening tags being closed: %s" %
                     ', '.join(map(lambda x: "'%s'" % x, currently_in)))

    return current_node

def formatted_(stop_with_single_newline, stop_with_gt, stop_with_bullet):
    return Many1(
        LimitedFOr(3,
            Str("://") >> GetPos() >> (lambda lc: Return(Elem(lc[0], lc[1], False, '://')))
            ,
            # Categories.
            Chr('#') >>
            GetPos() >>
            (lambda lc:
            Fatalize(
                StrCI("category") >>
                SkipWhitespace >>
                Str("[[") >>
                SUntilNRW0(escchr, Str("]]")) >>
                (lambda cat:
                UpdateState('categories', lambda cats: cats.append(cat.lower()) or cats) >>
                Return(Elem(lc[0], lc[1], False, '')))
            ))
            ,
            Apply(lambda x_lc: Elem(x_lc[1][0], x_lc[1][1], True, x_lc[0]),
                  Strs("//", "**", "__", "||", "|^", "^|", "|_", "_|", "--", "``", "''") >>
                  (lambda str:
                  GetPos() >>
                  (lambda lc:
                  Return((str, lc)))))
            ,
            article_ref
            ,
            external_ref
            ,
            example_ref
            ,
            # Don't try to parse a footnote if we're already in a footnote.
            GetState('in_footnote') >>
            (lambda in_footnote:
            (not in_footnote) and footnote or RError())
            ,
            GetPos() >>
            (lambda lc:
            SUntil1(
                escchr,
                Strs("://", "//", "**", "__", "^^", "||", "[[", "{{", "|^", "^|", "|_", "_|", "[:", "--", "#", "``", "''") *
                (stop_with_single_newline and Chr("\n") or Str("\n\n"))                *
                (stop_with_gt and Chr('>') or RError())                                *
                (stop_with_bullet and (Str("(*)") * Str("(#)")) or RError())           *
                EOF 
                ) >> \
            (lambda text:
            Return(Elem(lc[0], lc[1], False, text))))
        )
    )

def fudge(r):
    k = build_formatted(r)
    if isinstance(k, Formatted):
        return Return(k)
    else:
        return RFatalError(k[2], k[0], k[1])
formatted = (
    formatted_(False, False, False) >>
    (lambda r:
    fudge(r))
)
formatted_snl = (
    formatted_(True, False, False) >>
    (lambda r:
    fudge(r))
)
formatted_in_gloss = (
    formatted_(False, True, False) >>
    (lambda r:
    fudge(r))
)
formatted_in_bullets = (
    formatted_(False, False, True) >>
    (lambda r:
    fudge(r))
)

class Paragraph(object):
    __slots__ = ['text_nodes', 'preformatted', 'left_indent', 'right_indent',
                 # This one is used for a rather nasty hack in translate_to_xhtml.
                 'xhtml_preamble'
                ]

    def __init__(self, text_nodes, preformatted, left_indent, right_indent):
        # text_nodes is None and preformatted is a string if this is
        # preformatted text.
        self.text_nodes = text_nodes
        self.preformatted = preformatted
        self.left_indent = left_indent
        self.right_indent = right_indent

    def __repr__(self):
        return "p" + repr(self.text_nodes)
def paragraph_():
    return (
    FOr(
        Str("@@") >>
        SUntilNRW1(escchr, Str("@@")) >>
        (lambda pre:
        Option(None, Str("\n\n") * EOF) >>
        Return(pre))
        ,
        formatted >>
        (lambda r:
        # Check for the end of the paragraph.
        FOr(
            CMany(2, Chr("\n")) * EOF >>
            Return([r])
            ,
            Apply(lambda x: [r] + x, paragraph_())))
            ,
            Return([])
        )
    )

paragraph = (
    CMany0(Chr('>')) >>
    (lambda left_indent:
    CMany0(Chr('<')) >>
    (lambda right_indent:
    paragraph_() >>
    (lambda r:
    r == [] and \
        RError("Couldn't find paragraph")
            or \
                ((type(r) == types.StringType or type(r) == types.UnicodeType) and \
                    Return(Paragraph(None, r, left_indent, right_indent)) \
                                                 or \
                    Return(Paragraph(r, None, left_indent, right_indent))))))
)

acceptability = Or(None, SMany1(Chrs('*!#?')))
label = Chr(':') >> Fatalize(SUntilNRW1(escchr, Chr(':'))) % "No text between ':' and ':' for label"

class SimpleExample(object):
    __slots__ = ['label', 'acceptability', 'formatted_elems']

    def __init__(self, label, acceptability, formatted_elems):
        self.label = label
        self.acceptability = acceptability
        self.formatted_elems = formatted_elems

def __repr__(self):
    return (self.label and ":-" + self.label + "-:" or '') + (self.acceptability and self.acceptability or '') + '"' + self.text + '"'

class GlossedExample(object):
    __slots__ = ['label', 'acceptability', 'native_elts', 'lit_elts', 'gloss']

    def __init__(self, label, acceptability, native_elts, lit_elts, gloss):
        self.label = label
        self.acceptability = acceptability
        self.native_elts = native_elts
        self.lit_elts = lit_elts
        self.gloss = gloss

    def __repr__(self):
        return repr(self.label) + " " + repr(self.acceptability) + " " + repr(self.native_elts) + " " + repr(self.lit_elts) + " " + repr(self.gloss)

class ExampleGroup(object):
    __slots__ = ['label', 'examples']

    def __init__(self, label, examples):
        self.label = label
        self.examples = examples

example = (
    Option(None, label) >>
    (lambda l:
    SkipWhitespace >>
    acceptability >>
    (lambda a:
    SkipWhitespace >>
    # Is this a glossed example?
    Option(None, Chr('<')) >>
    (lambda c:
    # Both simple_example and glossed_example consume a single terminating "\n",
    # so we have to check for (optional) following "\n"s.
    (c and \
        glossed_example(l, a)
               or \
        simple_example(l, a)) >>
    (lambda ret:
    EOF * CMany0(Chr("\n")) >>
    Return(ret)))))
)

def simple_example(l, a):
    return (
        UntilNRW0(formatted_snl, Chr("\n") * EOF) >>
        (lambda formatted_elems:
        Return(SimpleExample(l, a, formatted_elems)))
)

def glossed_example(l, a):
    return (
        Until0(formatted_in_gloss, Chr(">")) >>
        (lambda first_elt:
        Chr(">") >>
        SkipNoNLWhitespace >>
        Many0(Chr("<") >> Until0(formatted_in_gloss, Chr(">")) >> (lambda elt: Chr(">") >> SkipNoNLWhitespace >> Return(elt))) >>
        (lambda native_elts:
        Chr("\n") >> SkipWhitespace >>
Many0(Chr("<") >> Until0(formatted_in_gloss, Chr(">")) >> (lambda elt: Chr(">") >> SkipNoNLWhitespace >> Return(elt))) >>
        (lambda lit_elts:
        Chr("\n") >> SkipNoNLWhitespace >>
        (Many1(formatted_snl) * Return(None)) >>
        (lambda gloss:
        Chr("\n") * EOF >>
        Return(GlossedExample(l, a, [first_elt] + native_elts, lit_elts, gloss))))))
    )

example_group = (
    FOr(
        Option(None, label) >>
        (lambda label:
        SkipWhitespace >>
        Str("(+)") >>
        SkipNoNLWhitespace >>
        SepBy1(example, SkipNoNLWhitespace >> Str("(+)") >> SkipNoNLWhitespace) >>
        (lambda lst:
        Return(ExampleGroup(label, lst))))
        ,
        Apply(lambda x: ExampleGroup(None, [x]), example)
    )
)

class BulletList(object):
    __slots__ = ['bullets', 'numbered']

    def __init__(self, bullets, numbered=False):
        self.bullets = bullets # Each bullet is a list of Formatted objects.
        self.numbered = numbered

    def __repr__(self):
        return "bullets" + str(self.bullets)

bullet_list = (
    UntilNRW1(Str("(*)") >> Many0(formatted_in_bullets), Str("\n\n") * (SkipWhitespace >> EOF)) >>
    (lambda bl:
    Return(BulletList(bl)))
)
numbered_list = (
    UntilNRW1(Str("(#)") >> Many0(formatted_in_bullets), Str("\n\n") * (SkipWhitespace >> EOF)) >>
    (lambda bl:
    Return(BulletList(bl, numbered=True)))
)

docelement = ((CMany(4, Chr(" ")) * Chr("\t")) >> LimitedFOr(3, bullet_list, numbered_list, example_group)) * paragraph
docelement_after_section_title = (
    # Blank lines after section heading have been skipped.
    # Try for an example/list, then skip all whitespace if it fails.
    ((CMany(4, Chr(" ")) * Chr("\t")) >> LimitedFOr(3, bullet_list, numbered_list, example_group)) *
    (
        SkipWhitespace >>
        paragraph
    )
)

def check_section_list(sections):
    """Check that each section is a subsection of the previous one."""
    last = -1
    for num, title in sections:
        if not num > last:
            return RFatalError("Empty section(s)")
        last = num
    return Return(True)
    
def document_(can_be_empty=True, after_section_title=False):
    return \
    FOr(
        EOF >>
        (can_be_empty and \
             Apply(lambda st: st.get_tree(), GetState('section_tree'))
                      or \
             RFatalError("Nothing after section title"))
        ,
        Many1(section) >>
        (lambda ss:
        check_section_list(ss) >>
        DoWithState('section_tree', lambda st: map(lambda s: st.add_section(s[0], s[1]), ss)) >>
        document_(can_be_empty=False, after_section_title=True))
        ,
        (after_section_title and docelement_after_section_title or docelement) >>
        (lambda p:
        DoWithState('section_tree', lambda st: st.add_elem(p)) >>
        document_())
        ,
        SkipWhitespace >>
        EOF >>
        (can_be_empty and \
            Apply(lambda st: st.get_tree(), GetState('section_tree'))
                      or \
            RFatalError("Nothing after section title"))
    )

class Redirect(object):
    __slots__ = ['title']

    def __init__(self, title):
        self.title = title

redirect = (
    SkipWhitespace >>
    Chr('#') >>
    StrCI('redirect') >>
    SkipWhitespace >>
    Str("[[") >>
    SUntilNRW0(escchr, Str("]]")) >>
    (lambda name:
    SkipWhitespace >>
    EOF >>
    Return(Redirect(name))))

class Document(object):
    __slots__ = ['root', 'categories']

    def __init__(self, root, categories):
        self.root = root
        self.categories = categories

    def __repr__(self):
        return "DOC(" + str(self.root) + ")"

document = (
    skip_blank_lines >>
    (redirect * document_()) >>
    (lambda r:
    isinstance(r, Redirect) and \
        Return(r)           or \
        (
            GetState('categories') >>
            (lambda cats:
            Return(Document(r, cats)))
        )
    )
)

class SectionTreeBuilder(object):
    __slots__ = ['node', 'tits']

    class Node(object):
        __slots__ = ['level', 'parent', 'title', 'children']

        def __init__(self, level, parent, title, children):
            self.level = level
            self.parent = parent
            self.title = title
            self.children = children

        def __repr__(self):
            return \
                ("(level: %i, title: %s [" % (self.level, self. title)) + \
                ''.join([repr(c) for c in self.children]) + \
                "])"

    class Error(Exception):
        __slots__ = ['section_title']

        def __init__(self, section_title):
            self.section_title = section_title

    def __init__(self):
        self.node = self.Node(
            level = 0,
            parent = None,
            title = None,
            children = []
        ) 
        self.tits = { }

    def __add_to_tits(self, node):
        t = []
        n = node
        # Note that we're building the list with subsection titles first.
        while n and n.title:
            t.append(n.title)
            n = n.parent
        st = '\0'.join(t)
        if self.tits.has_key(st):
            raise self.Error('#'.join(t))
        self.tits['\0'.join(t)] = True

    def add_section(self, level, title):
        if self.node.level == level:
            parent = self.node.parent
            nd = self.Node(
                level = level,
                parent = parent,
                title = title,
                children = []
            )
            self.__add_to_tits(nd)
            parent.children.append(nd)
            self.node = nd
        elif level > self.node.level:
            # If the level jump is > 1, we'll correct this silently.
            if level - self.node.level != 1:
                level = self.node.level + 1
            nd = self.Node(
                level = level,
                parent = self.node,
                title = title,
                children = []
            )
            self.__add_to_tits(nd)
            self.node.children.append(nd)
            self.node = nd
        else: # if level < self.node.level
            diff = self.node.level - level
            parent2 = self.node.parent
            for i in xrange(diff):
                parent2 = parent2.parent
            self.node = self.Node(
                level = level,
                parent = parent2,
                title = title,
                children = []
            )
            self.__add_to_tits(self.node)
            parent2.children.append(self.node)

    def add_elem(self, elem):
        self.node.children.append(elem)

    def get_tree(self):
        nd = self.node
        while nd.level != 0:
            nd = nd.parent
        return nd

def make_initial_state():
    return dict(section_tree=SectionTreeBuilder(), article_refs=[], categories=[], in_footnote=False)

class Siginfo(object):
    __slots__ = ['username', 'date']

    def __init__(self, username, date):
        assert type(date) == my_utils.ZonedDate
        self.username = username
        self.date = date

def parse_wiki_document(istr, siginfo, footnotes=True):
    try:
        # Do signatures.
        if siginfo:
            quname = urllib.quote(siginfo.username)
            istr = istr.replace('~~~~~', "//**%s**//" % str(siginfo.date))
            istr = istr.replace('~~~~', "//**[[%s%s|%s]] %s**//" % (links.USER_PAGE_PREFIX, quname, quname, str(siginfo.date)))
            istr = istr.replace('~~~', "//**[[%s%s|%s]]**//" % (links.USER_PAGE_PREFIX, quname, quname))

        s = make_initial_state()
        s['no_footnotes'] = not footnotes
        r = run_parser(document, istr, s)
        # Article refs list may contain duplicates.
        s['article_refs'] = my_utils.unique(map(my_utils.unfutz_article_title, map(urllib.unquote, s['article_refs'])))

        # TODO: Find out why duplicate categories sometimes get added to the
        # list. Really obscure behavior no doubt caused by too much backtracking.
        if not (isinstance(r, ParserError) or isinstance(r, Redirect)):
            r.categories = my_utils.unique(r.categories)

        if isinstance(r, ParserError):
            return r
        else:
            return r, s, istr
    except SectionTreeBuilder.Error, e:
        return ParserError(0, 0, "Duplicate section title: '%s'" % e.section_title)


#
# THE TRANSLATOR
#

class IndentingWriter(object):
    """This makes it easy to output nicely indented XHTML."""

    __slots__ = ['writer', 'indent', 'indent_is_written', 'next_on_own_line', 'last']

    def __init__(self, writer):
        self.writer = writer
        self.indent = 0
        self.indent_is_written = False
        self.next_on_own_line = False
        self.last = None

    def indentplus(self, n):
        self.indent += n

    def nlindentplus(self, n):
        self.indent += n
        self.write('\n')
        self.last = '\n'

    def indentminus(self, n):
        assert self.indent - n >= 0
        self.indent -= n

    def nlindentminus(self, n):
        assert self.indent - n >= 0
        self.indent -= n
        self.write('\n')
        self.last = '\n'

    def ownline(self):
        self.next_on_own_line = True

    def setindent(self, i): self.indent = i
    def getindent(self): return self.indent

    def write(self, s):
        if self.next_on_own_line:
            self.next_on_own_line = False
            if self.last and self.last != '\n':
                self.writer.write('\n')
                self.indent_is_written = True
                self.writer.write(''.join(' ' for i in xrange(self.indent)))
                self.last = ' '
        for c in s:
            self.writer.write(c)
            self.last = c
            if c == '\n':
                self.indent_is_written = False
            if not self.indent_is_written:
                self.indent_is_written = True
                self.writer.write(''.join(' ' for i in xrange(self.indent)))
                self.last = ' '

def number_to_letter(n):
    """Converts a number to a letter (used for subexample numbering)."""
    assert n > 0
    if n <= 25:
        return chr(ord('a') + n - 1)
    elif n <= 51:
        return chr(ord('A') + n - 1)
    else:
        # Don't actually convert it to a letter.
        return n

def get_section_number(node):
    nums = []
    while node.parent:
        i = 1
        for n in node.parent.children:
            if n is node:
                nums.insert(0, str(i))
                break
            if isinstance(n, SectionTreeBuilder.Node):
                i += 1
        node = node.parent
    return '.'.join(nums)

# Some values used by the translate_to_xhtml_ and translate_to_xhtml functions.
markup = {
    'bold'      : ('<b>', '</b>'),
    'italic'    : ('<i>', '</i>'),
    'underline' : ('<u>', '</u>'),
    'sc'        : ('<small>', '</small>'),
    'sup'       : ('<sup>', '</sup>'),
    'sub'       : ('<sub>', '</sub>')
}
EXAMPLE_REF_ID_PREFIX  = "__EXAMPLE__"
SECTION_REF_ID_PREFIX  = "__SECTION__"
FOOTNOTE_REF_ID_PREFIX = "__FOOTNOTE__"
ARTICLE_URL_PREFIX     = "/articles/"

def translate_to_xhtml_(state, elem, writer, article_exists_pred):
    assert type(elem) is not Redirect

    def handle_single_example(elem, prefix, i, example_no_class):
        if isinstance(elem, SimpleExample):
            writer.write('<table')
            if elem.label:
                writer.write(' id="')
                writer.write(prefix)
                writer.write(htmlutils.htmlencode(elem.label))
                writer.write('"')
            writer.write(' class="example">')
            writer.nlindentplus(4)
            writer.write('<tr>')
            writer.nlindentplus(4)
            writer.write('<th class="%s">' % example_no_class)
            writer.write(str(i))
            writer.write('</th>\n')
            if elem.acceptability:
                writer.write('<td class="acceptability">')
                writer.write(htmlutils.htmlencode(elem.acceptability))
                writer.write('</td>\n')
            writer.write('<td>')
            writer.nlindentplus(4)
            for fe in elem.formatted_elems:
                translate_to_xhtml_(state, fe, writer, article_exists_pred)
            writer.nlindentminus(4)
            writer.write('</td>')
            writer.nlindentminus(4)
            writer.write('</tr>')
            writer.nlindentminus(4)
            writer.write('</table>\n')
        elif isinstance(elem, GlossedExample):
            writer.write('<table')
            if elem.label:
                writer.write(' id="')
                writer.write(prefix)
                writer.write(htmlutils.htmlencode(elem.label))
                writer.write('"')
            writer.write('>')
            writer.nlindentplus(4)
            writer.write('<tr>')
            writer.nlindentplus(4)
            writer.write('<th class="%s">' % example_no_class)
            writer.write(str(i))
            writer.write('</th>\n')
            if elem.acceptability:
                writer.write('<td class="acceptability">')
                writer.write(htmlutils.htmlencode(elem.acceptability))
                writer.write('</td>\n')
            writer.write('<td>')
            writer.nlindentplus(4)
            writer.write('<table>')
            writer.nlindentplus(4)
            writer.write('<tr>')
            writer.nlindentplus(4)
            for elt in elem.native_elts:
                writer.write('<td>')
                for e in elt:
                    translate_to_xhtml_(state, e, writer, article_exists_pred)
                writer.write('</td>')
            writer.nlindentminus(4)
            writer.write('</tr>')
            writer.write('\n')
            writer.write('<tr>')
            writer.nlindentplus(4)
            for elt in elem.lit_elts:
                writer.write('<td>')
                for e in elt:
                    translate_to_xhtml_(state, e, writer, article_exists_pred)
                writer.write('</td>')
            writer.nlindentminus(4)
            writer.write('</tr>')
            writer.write('\n')
            if elem.gloss:
                def biggest(x, y):
                    if x > y:
                        return x
                    else:
                        return y
                writer.write('<tr>')
                writer.nlindentplus(4)
                writer.write('<td colspan="%i"><i>' % biggest(len(elem.native_elts), len(elem.lit_elts)))
                for e in elem.gloss:
                    translate_to_xhtml_(state, e, writer, article_exists_pred)
                writer.write('</i></td>')
                writer.nlindentminus(4)
                writer.write('</tr>')
            writer.nlindentminus(4)
            writer.write('</table>')
            writer.nlindentminus(4)
            writer.write('</td>')
            writer.nlindentminus(4)
            writer.write('</tr>')
            writer.nlindentminus(4)
            writer.write('</table>')

    if isinstance(elem, SectionTreeBuilder.Node):
        if elem.level > 0:
            writer.ownline()
            writer.write("<h")
            writer.write(str(elem.level + 1)) # We start with h2 to save h1 for
                                              # article titles.
            # Get titles of supersections.
            e = elem.parent
            tit = elem.title
            while e.parent:
                tit = e.title + '__' + tit
                e = e.parent
            writer.write(' id="%s%s">' % (SECTION_REF_ID_PREFIX, urllib.quote(tit)))
            writer.write(get_section_number(elem))
            writer.write('&nbsp;')
            writer.write(htmlutils.htmlencode(elem.title))
            writer.write("</h")
            writer.write(str(elem.level + 1))
            writer.write(">")
            titstack = [elem.title]
            parent = elem.parent
            while parent.parent:
                titstack.append(parent.title)
                parent = parent.parent
            e = elem
            numstack = []
            while e.parent:
                import itertools
                i = 1
                for c in e.parent.children:
                    if c is e:
                        numstack.append(i)
                        break
                if isinstance(c, SectionTreeBuilder.Node):
                    i += 1
                e = e.parent
            numstack.reverse()
            state.sectits_to_nums['\0'.join(reversed(titstack))] = numstack
        for c in elem.children:
            translate_to_xhtml_(state, c, writer, article_exists_pred)
    elif isinstance(elem, Paragraph):
        if elem.left_indent != 0 or elem.right_indent != 0:
            writer.ownline()
            for _ in range(elem.left_indent):
                writer.write('<div class="left-indent">')
            for _ in range(elem.right_indent):
                writer.write('<div class="right-indent">')
            writer.nlindentplus(4)
        if elem.preformatted:
            writer.ownline()
            writer.write('<pre>')
            ind = writer.getindent()
            writer.setindent(0)
            if hasattr(elem, 'xhtml_preamble'):
                writer.write(elem.xhtml_preamble)
            writer.write(htmlutils.htmlencode(elem.preformatted))
            writer.setindent(ind)
            writer.write('</pre>\n')
        else:
            writer.ownline()
            writer.write('<p>')
            writer.nlindentplus(4)
            if hasattr(elem, 'xhtml_preamble'):
                writer.write(elem.xhtml_preamble)
            for n in elem.text_nodes:
                translate_to_xhtml_(state, n, writer, article_exists_pred)
            writer.indentminus(4)
            writer.ownline()
            writer.write("</p>\n")
        if elem.left_indent != 0 or elem.right_indent != 0:
            writer.indentminus(4)
            writer.ownline()
            for _ in range(elem.left_indent + elem.right_indent):
                writer.write('</div>')
            writer.write('\n')
    elif isinstance(elem, Formatted):
        if elem.kind in markup:
            writer.write(markup[elem.kind][0])
        text = elem.text
        if elem.text is not None:
            writer.write(htmlutils.htmlencode(text))
        else:
            for ch in elem.children:
                translate_to_xhtml_(state, ch, writer, article_exists_pred)
        #if elem.kind == 'sc':
        #    writer.write('\n')
        if elem.kind in markup:
            writer.write(markup[elem.kind][1])
    elif isinstance(elem, MDash):
        writer.write('&mdash;')
    elif isinstance(elem, LDQuo):
        writer.write('&ldquo;')
    elif isinstance(elem, RDQuo):
        writer.write('&rdquo;')
    elif isinstance(elem, ExternalRef):
        writer.write('<a class="external_link" href="')
        writer.write(link_encode(elem.url))
        writer.write('">')
        if elem.alt:
            writer.write(elem.alt)
        else:
            writer.write(htmlutils.htmlencode(elem.url))
        writer.write("</a>")
    elif isinstance(elem, Image):
        writer.write('<img src="%s" />' % link_encode(elem.url))
    elif isinstance(elem, ArticleRef):
        writer.write('<a class="article_ref" ')
        if article_exists_pred and (not article_exists_pred(elem.article)):
            writer.write(' class="non-existent" ')
        writer.write(' href="')
        if elem.article:
            writer.write(ARTICLE_URL_PREFIX)
            writer.write(urllib.quote(my_utils.futz_article_title(elem.article)))
        if elem.sections:
            section_string = '#' + SECTION_REF_ID_PREFIX + \
                '__'.join(map(urllib.quote, elem.sections))
            writer.write(section_string)
        writer.write('">')
        if elem.alt:
            writer.write(htmlutils.htmlencode(elem.alt))
        elif elem.article:
            writer.write(htmlutils.htmlencode(elem.article))
        else:
            t = '\0'.join(elem.sections)
            if not state.sectits_to_nums.has_key(t):
                # The section doesn't exist.
                writer.write('&sect;[non-existent section ')
                writer.write(htmlutils.htmlencode('#'.join(elem.sections)))
                writer.write(']')
            else:
                nums = state.sectits_to_nums[t]
                writer.write('&sect;')
                writer.write('.'.join(map(str, nums)))
        writer.write('</a>')
    elif isinstance(elem, ExampleRef):
        writer.write('<a class="example_ref" href="#')
        writer.write(EXAMPLE_REF_ID_PREFIX)
        writer.write(elem.label)
        writer.write('">[')
        writer.write(str(state.examples[elem.label]))
        writer.write(']</a>')
    elif isinstance(elem, BulletList):
        if elem.numbered:
            writer.write('<ol>')
        else:
            writer.write('<ul>')
        writer.nlindentplus(4)
        for b in elem.bullets:
            writer.write('<li>')
            writer.nlindentplus(4)
            for formatted_text in b:
                translate_to_xhtml_(state, formatted_text, writer, article_exists_pred)
            writer.write('</li>')
            writer.nlindentminus(4)
        writer.nlindentminus(4)
        if elem.numbered:
            writer.write('</ol>\n')
        else:
            writer.write('</ul>\n')
    elif isinstance(elem, ExampleGroup):
        if len(elem.examples) != 1:
            writer.ownline()
            writer.write('<table')
            if elem.label:
                writer.write(' id="')
                writer.write(EXAMPLE_REF_ID_PREFIX)
                writer.write(htmlutils.htmlencode(elem.label))
                writer.write('"')
            writer.write(' class="example">')
            writer.nlindentplus(4)
            writer.write('<tr>')
            writer.nlindentplus(4)
            writer.write('<th class="example-number">')
            writer.write(str(state.example_no))
            state.examples[elem.label] = state.example_no
            state.example_no += 1
            writer.write('</th>\n')
            writer.write('<td>')
            writer.nlindentplus(4)
            writer.write('<table>')
            writer.nlindentplus(4)
            import itertools
            for ex, i in itertools.izip(elem.examples, itertools.count(1)):
                writer.write('<tr><td>')
                writer.nlindentplus(4)
                if ex.label:
                    state.examples[ex.label] = str(state.example_no - 1) + number_to_letter(i)
                handle_single_example(ex, EXAMPLE_REF_ID_PREFIX, number_to_letter(i), "subexample-number")
                writer.nlindentminus(4)
                writer.write('</td></tr>')
                if i != len(elem.examples):
                    writer.write('\n')
            writer.nlindentminus(4)
            writer.write('</table>')
            writer.nlindentminus(4)
            writer.write('</td>')
            writer.nlindentminus(4)
            writer.write('</tr>')
            writer.nlindentminus(4)
            writer.write('</table>')
        else:
            translate_to_xhtml_(state, elem.examples[0], writer, article_exists_pred)
    elif isinstance(elem, SimpleExample) or isinstance(elem, GlossedExample):
        no = state.example_no
        state.examples[elem.label] = state.example_no
        state.example_no += 1
        handle_single_example(elem, EXAMPLE_REF_ID_PREFIX, no, "example-number")
    elif isinstance(elem, Footnote):
        if not elem.display_inline:
            writer.write('<a href="#%s%i" class="footnote-link"><sup>%i</sup></a>' %
                         (FOOTNOTE_REF_ID_PREFIX, state.footnote_no,
                          state.footnote_no))
            state.footnotes[state.footnote_no] = elem.paragraphs
            state.footnote_no += 1
        else:
            for p in elem.paragraphs:
                translate_to_xhtml_(state, p, writer, article_exists_pred)
    else:
        assert False

class TranslatorState(object):
    __slots__ = ['example_no', 'examples', 'sectits_to_nums', 'footnote_no', 'footnotes']

    def __init__(self):
        self.example_no = 1
        self.examples = { }
        self.sectits_to_nums = { }
        self.footnote_no = 1
        self.footnotes = { }

def translate_to_xhtml(document, writer, article_exists_pred=None):
    elem = document.root
    st = TranslatorState()
    writer = IndentingWriter(writer)
    r = translate_to_xhtml_(st, elem, writer, article_exists_pred)
    # Write out the footnotes (if there are any).
    if len(st.footnotes) != 0:
        writer.ownline()
        writer.write('<hr />\n\n')
        writer.write('<h1>Notes</h1>\n')
        for k, v in st.footnotes.iteritems():
            writer.write('<div class="footnote">')
            writer.nlindentplus(4)
            for paragraph in v:
                paragraph.xhtml_preamble = \
                    '<sup id="%s%i">%i</sup>&nbsp;' % (FOOTNOTE_REF_ID_PREFIX, k, k)
                translate_to_xhtml_(st, paragraph, writer, article_exists_pred)
            writer.nlindentminus(4)
            writer.write('</div>\n')

#
# TEST CODE.
#

#import StringIO
#s = """==Blah== ggg\n\n===Foo=== Blah blah blah [[article#fo!!o#bar|goof]] {{http://www.google.com/foo.jpeg}} **bold**\n\n__underlined__\n\n    :group: (+) :label: * <foo> <bar>\n<bloo> <blar>\nGloss\n(+) :bar:Another one\n\n #fo**o**[:label:][:group:] and [:bar:] and [[#Blahh#Foo]]"""
#r = parse_wiki_document(s)
#print r
#sb = StringIO.StringIO()
#translate_to_xhtml(r[0], sb)
#print sb.getvalue()

#import StringIO
#s = make_initial_state()
#r = run_parser(bullet_list, "(*) foo", s)
#r = parse_wiki_document("    (*) foo")
#print r[0]
#sb = StringIO.StringIO()
#translate_to_xhtml(r, sb)
#print sb.getvalue()

#import StringIO
#s = "^^Foo blah footnote.^^"
#ist = make_initial_state()
#ist['no_footnotes'] = False
#r = run_parser(footnote, s, ist)
#print r
#sb = StringIO.StringIO()
#translate_to_xhtml(r, sb)
#print sb.getvalue()

#s = make_initial_state()
#r = run_parser(paragraph, '@@\nfdsfsdf@@\n\n', s)
#print r.preformatted

#import treedraw
#import cairo
#from treedraw import *
#surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 700, 700)
#context = cairo.Context(surface)
#cs = CairoState(surface, 20)
#s = "[IP [->t NP [D the] [N dog]] [I' [->was I was] [VP [V <-was] [VP [VP [V seen] <-t] [PP [P by] [NP [D the] [N cat]]]]]]]"
#rr = run_parser(tree, s, { })
#print rr
#r, m = rr
#draw_tree(r, m, cs)
#print r.dimensions
#surface.write_to_png("test.png")

