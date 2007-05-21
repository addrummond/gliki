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
# Python conversion of the Wikimedia code in diff.php.
#

import types
import md5
from itertools import *

class PhpArray(dict):
    """Implementation of a PHP-like array."""
    def __init__(self, *elems):
        self.default = 0
        for i, e in izip(count(0), elems):
            self[i] = e

    def __getitem__(self, k):
        try:
            return dict.__getitem__(self, k)
        except KeyError:
            return self.default

    __iter__ = dict.itervalues

    def append(self, elem):
        biggest_num = -1
        # Keys are sorted, so we just need to get the biggest integer key,
        # which will be the first integer in the reversed list of keys.
        for k in reversed(self.keys()):
            if type(k) == types.IntType:
                biggest_num = k
                break
        self[biggest_num + 1] = elem

    def to_python_array(self):
        last = None
        for k in reversed(self.keys()):
            if type(k) == types.IntType:
                last = k
                break
        a = map(lambda x: None, xrange(last))
        for k,v in self.iteritems():
            if type(k) == types.IntType:
                a[k] = v

# Won't work for negative offsets, but it's never used with them.
def array_slice(array, offset, length=None, preserve_keys=None):
    """Implementation of PHP's array_slice function for PhpArray objects."""
    result = {}
    for k in array.keys():
        if offset > 0:
            continue
        else:
            offset -= 1
        if length is None:
            result[k] = array[k]
        elif length > 0:
            result[k] = array[k]
            length -= 1
        else:
            break

    if preserve_keys:
        return result
    else:
        newarray = PhpArray()
        for i, k in izip(count(0), result.iterkeys()):
            newarray[i] = result[k]
        return newarray

def array_splice(array, offset, length, replacement):
    """Implementation of PHP's array_splice function for PhpArray objects."""
    start = None
    if offset < 0:
        start = len(array) + offset
    else:
        start = offset

    for i, j in izip(xrange(start, length), count(0)):
        assert array.has_key(i) and replacement.has_key(j)
        array[i] = replacement[j]

class DiffOp(object):
    def reverse(self): assert False
    def norig(self):
        return self.orig and len(self.orig) or 0
    def nclosing(self):
        return self.closing and len(self.closing) or 0

class DiffOpCopy(DiffOp):
    def __init__(self, orig, closing=False):
        if type(closing) == types.ListType:
            closing = orig
        self.orig = orig
        self.closing = closing

    def __repr__(self):
        return "Copy(orig: %s, closing: %s)" % (str(self.orig), str(self.closing))

class DiffOpDelete(DiffOp):
    def __init__(self, lines):
        self.orig = lines
        self.closing = False

    def reverse(self):
        return DiffOpAdd(self.orig)

    def __repr__(self):
        return "Delete(orig: %s, closing: %s)" % (str(self.orig), str(self.closing))

class DiffOpAdd(DiffOp):
    def __init__(self, lines):
        self.closing = lines
        self.orig = lines

    def reverse(self):
        return DiffOpDelete(self.closing)

    def __repr__(self):
        return "Add(orig: %s, closing: %s)" % (str(self.orig), str(self.closing))

class DiffOpChange(DiffOp):
    def __init__(self, orig, closing):
        self.orig = orig
        self.closing = closing

    def reverse(self):
        return DiffOpChange(self.closing, self.orig)

    def __repr__(self):
        return "Change(orig: %s, closing: %s)" % (str(self.orig), str(self.closing))

MAX_XREF_LENGTH = 10000

class DiffEngine(object):
    def __init__(self):
        self.seq = PhpArray()

    def diff(self, from_lines, to_lines):
        xhash = PhpArray()
        yhash = PhpArray()

        n_from = len(from_lines)
        n_to = len(to_lines)

        self.xchanged = PhpArray()
        self.ychanged = PhpArray()
        self.xv = PhpArray()
        self.yv = PhpArray()
        self.xind = PhpArray()
        self.yind = PhpArray()

        # Skip leading common lines.
        skip = 0
        while skip < n_from and skip < n_to:
            if from_lines[skip] != to_lines[skip]:
                break
            self.xchanged[skip], self.ychanged[skip] = False, False
            skip += 1

        # Skip trailing common lines.
        xi, yi = n_from, n_to
        endskip = 0
        xi -= 1
        yi -= 1
        while xi > skip and yi > skip:
            if from_lines[xi] != to_lines[yi]:
                break
            self.xchanged[xi], self.ychanged[yi] = False, False
            endskip += 1
            xi -= 1
            yi -= 1

        # Ignore lines which do not exist in both files.
        xi = skip
        while xi < n_from - endskip:
            xhash[self.line_hash(from_lines[xi])] = 1
            xi += 1

        yi = skip
        while yi < n_to - endskip:
            line = to_lines[yi]
            keyvalue = self.line_hash(line)
            if xhash.has_key(keyvalue):
                self.ychanged[yi] = len(xhash[keyvalue]) == 0 and 1 or 0
            else:
                self.ychanged[yi] = ''
            if self.ychanged[yi]:
                yi += 1 # This is in the for loop in the PHP code.
                continue
            yhash[self.line_hash(line)] = 1
            self.yv.append(line)
            self.yind.append(yi)
            yi += 1
        xi = skip
        while xi < n_from - endskip:
            line = from_lines[xi]
            keyvalue = self.line_hash(line)
            if yhash.has_key(keyvalue):
                self.xchanged[xi] = len(yhash[self.line_hash(line)]) == 0 and 1 or 0
            else:
                self.xchanged[xi] = ''
            if self.xchanged[xi]:
                xi += 1 # This is in the for loop in the PHP code.
                continue
            self.xv.append(line)
            self.xind.append(xi)
            xi += 1

        # Find the LCS.
        self.compareseq(0, len(self.xv), 0, len(self.yv))

        # Merge edits when possible
        self.shift_boundries(from_lines, self.xchanged, self.ychanged)
        self.shift_boundries(to_lines, self.ychanged, self.xchanged)

        # Compute the edit operations.
        edits = PhpArray()
        xi, yi = 0, 0
        while xi < n_from or yi < n_to:
            # Skip matching "snake".
            copy = PhpArray()
            while xi < n_from and yi < n_to and (not self.xchanged[xi]) and (not self.ychanged[yi]):
                copy.append(from_lines[xi])
                xi += 1
                yi += 1
            if copy:
                edits.append(DiffOpCopy(copy))

            # Find deletes and adds.
            delete = PhpArray()
            while xi < n_from and self.xchanged[xi]:
                delete.append(from_lines[xi])
                xi += 1

            add = PhpArray()
            while yi < n_to and self.ychanged[yi]:
                add.append(to_lines[yi])
                yi += 1

            if delete and add:
                edits.append(DiffOpChange(delete, add))
            elif delete:
                edits.append(delete)
            elif add:
                edits.append(add)

        return edits

    def line_hash(self, line):
        if len(line) > MAX_XREF_LENGTH:
            return md5.md5(line).hexdigest()
        else:
            return line

    def diag(self, xoff, xlim, yoff, ylim, nchunks):
        ymatches = PhpArray()
        ymids = PhpArray()

        flip = False
        if xlim - xoff > ylim - yoff:
            flip = True
            xoff, xlim, yoff, ylim = yoff, ylim, xoff, xlim

        if flip:
            i = ylim - 1
            while i >= yoff:
                keyvalue = self.xv[i]
                if not ymatches.has_key(keyvalue):
                    ymatches[keyvalue] = PhpArray()
                ymatches[keyvalue].append(i)
                i -= 1
        else:
            i = ylim - 1
            while i >= yoff:
                kevalue = self.yv[i]
                if not ymatches.has_key(keyvalue):
                    ymatches[keyvalue] = PhpArray()
                ymatches[keyvalue].append(i)
                i -= 1

        self.lcs = 0
        self.seq[0] = yoff - 1
        self.in_seq = PhpArray()
        self.ymids = PhpArray()

        number = xlim - xoff + nchunks - 1
        x = xoff
        chunk = 0
        while chunk < nchunks:
            if chunk > 0:
                i = 0
                while i <= self.lcs:
                    if not ymids.has_key(i):
                        ymids[i] = PhpArray()
                    ymids[i][chunk - 1] = self.seq[i]
                    i += 1

            x1 = xoff + int((number + (xlim-xoff)*chunk) / nchunks)
            while x < x1:
                line = (flip and (self.yv[x],) or (self.xv[x],))[0]
                if (not ymatches.has_key(line)) or len(ymatches[line]) == 0:
                    x += 1 # This is in the for loop in the PHP code.
                    continue
                matches = ymatches[line]
                index_on_break = 0
                for junk, y in matches:
                    if len(self.in_seq[y]) == 0:
                        k = self.lcs_pos(y)
                        assert k > 0
                        ymids[k] = ymids[k-1]
                        break
                    index_on_break += 1
                for junk, y in array_slice(matches, index_on_break + 1, None, True):
                    if y > self.seq[k-1]:
                        assert y < self.seq[k]
                        # Optimization (see original PHP for more details).
                        self.in_seq[self.seq[k]] = False
                        self.seq[k] = y
                        self.in_seq[y] = 1
                    elif len(seql.in_seq[y]) == 0:
                        k = self.lcs_pos(y)
                        assert k > 0
                        ymids[k] = ymids[k-1]
                x += 1
            chunk += 1

        seps = flip and PhpArray(yoff, xoff) or PhpArray(xoff, yoff)
        ymid = ymids[self.lcs]
        for n in xrange(nchunks - 1):
            x1 = xoff + int((number + (xlim - xoff) * n) / nchunks)
            y1 = ymid[n] + 1
            seps = flip and PhpArray(y1, x1) or PhpArray(x1, y1)
        seps = flip and PhpArray(ylim, xlim) or PhpArray(xlim, ylim)

        return PhpArray(self.lcs, seps)

    def lcs_pos(ypos):
        end = self.lcs
        if end == 0 or ypos > self.seq[end]:
            self.lcs += 1
            self.seq[self.lcs] = ypos
            self.in_seq[ypos] = 1
            return self.lcs

        beg = 1
        while beg < end:
            mid = int((beg + end) / 2)
            if ypos > self.seq[mid]:
                beg = mid + 1
            else:
                end = mid

        assert ypos != self.seq[end]

        self.in_seq[self.seq[end]] = False
        self.seq[end] = ypos
        self.in_seq[ypos] = 1
        return end

    def compareseq(self, xoff, xlim, yoff, ylim):
        while xoff < xlim and yoff < ylim and self.xv[xoff] == self.yv[yoff]:
            xoff += 1
            yoff += 1

        while xlim > xoff and ylim > yoff and self.xv[xlim - 1] == self.yv[ylim - 1]:
            xlim -= 1
            ylim -= 1

        lcs, seps = None, PhpArray()
        if xoff == xlim or yoff == ylim:
            lcs = 0
        else:
            nchunks = min(7, xlim - xoff, ylim - yoff) + 1
            lcs, seps = self.diag(xoff, xlim, yoff, ylim, nchunks)

        if lcs == 0:
            while yoff < ylim:
                yoff += 1
                self.ychanged[self.yind[yoff]] = 1
            while xoff < xlim:
                xoff += 1
                self.xchanged[self.xind[xoff]] = 1
        else:
            pt1 = seps[0]
            for pt2 in seps:
                self.compareseq(pt1[0], pt2[0], pt1[1], pt2[1])
                pt1 = pt2

    def shift_boundries(self, lines, changed, other_changed):
        i = 0
        j = 0

        assert len(lines) == len(changed)
        len_ = len(lines)
        other_len = len(other_changed)

        while True:
            while j < other_len and other_changed[j]:
                j += 1

            while i < len_ and (not changed[i]):
                assert j < other_len and (not other_changed[j])
                i += 1
                j += 1
                while j < other_len and other_changed[j]:
                    j += 1

            if i == len_:
                break

            start = i

            i += 1
            while i < len_ and changed[i]:
                i += 1

            while True: # Translation of do...while; condition at bottom.
                runlength = i - start

                while start > 0 and lines[start - 1] == lines[i - 1]:
                    start -= 1
                    changed[start] = 1
                    i -= 1
                    changed[i] = False
                    while start > 0 and changed[start - 1]:
                        start -= 1
                    assert j > 0
                    j -= 1
                    while other_changed[j]:
                        j -= 1
                    assert j >= 0 and (not other_changed[j])

                corresponding = ((j < other_len) and (i,) or (len_,))[0]

                while i < len_ and lines[start] == lines[i]:
                    start += 1
                    changed[start] = False
                    i += 1
                    changed[i] = 1
                    while i < len_ and changed[i]:
                        i += 1

                    assert j < other_len and (not other_changed[j])
                    j += 1
                    if j < other_len and other_changed[j]:
                        corresponding = i
                        while j < other_len and other_changed[j]:
                            j += 1

                # Condition for PHP do...while loop.
                if not (runlength != i - start):
                    break

            while corresponding < i:
                start -= 1
                changed[start] = 1
                i -= 1
                changed[i] = 0
                assert j > 0
                j -= 1
                while other_changed[j]:
                    j -= 1
                assert j >= 0 and (not other_changed[j])

class Diff(object):
    def __init__(self, from_lines, to_lines):
        eng = DiffEngine()
        self.edits = eng.diff(from_lines, to_lines)

    def reverse(self):
        edits_copy = array_slice(self.edits, 0, None, True) # Copy the array.
        self.edits = PhpArray()
        for edit in edits_copy:
            redit = edit.reverse()
            self.edits.append(redit)

    def is_empty(self):
        for edit in self.edits:
            if edit.type != 'copy':
                return False
        return True

    def lcs(self):
        lcs = 0
        for edit in self.edits:
            if edit.type == 'copy':
                lcs += len(edit.orig)
        return lcs

    def orig(self):
        lines = PhpArray()

        for edit in self.edits:
            if edit.orig:
                array_splice(lines, len(lines), 0, edit.orig)
        return lines

    def closing(self):
        lines = PhpArray()

        for edit in self.edits:
            if edit.closing:
                array_splice(lines, len(lines), 0, edit.closing)
        return lines

e = DiffEngine()
r = e.diff(PhpArray("foooo", "bar", "foooo"), PhpArray("fooooaa", "fooo"))
for l in r: print l

