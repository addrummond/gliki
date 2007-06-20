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
This module maintins a block list in a user-editable file. Blocking can be
done by IP address, IP address range, or username.
"""

import re
import logging
import itertools
import types
import os
import os.path
import stat
import time

class Block(object): pass

class IPRangeBlock(Block):
    __slots__ = ['range_pairs']
    def __init__(self, range_pairs):
        self.range_pairs = range_pairs

    def __repr__(self):
        return "<IP RANGE BLOCK %s>" % str(self.range_pairs)

    def matches(self, username, ip_4tuple):
        for r, n in itertools.izip(self.range_pairs, ip_4tuple):
            l, u = r
            if not (n >= l and n <= u):
                return False
        return 'by_ip'

class UserBlock(Block):
    __slots__ = ['username']
    def __init__(self, username):
        assert type(username) == types.StringType
        self.username = username

    def __repr__(self):
        return "<USER BLOCK %s>" % self.username

    def matches(self, username, ip_4tuple):
        assert type(username) == types.StringType
        return (username == self.username) and 'by_username' or False

def in_block_list(block_list, username, ip_4tuple):
    return reduce(lambda x,y: x or y, map(lambda b: b.matches(username, ip_4tuple), block_list), False)

__comment_line = re.compile(r"\s*#.*")
__ip_line = re.compile(r"^\s*([^.]+)\.([^.]+).([^.]+).([^.]+)\s*$")
__user_line = re.compile(r"^\s*(\S*)\s*$")
__blank_line = re.compile(r"^\s*$")
__range_seg = re.compile(r"^\s*(\d{1,3})\s*-\s*(\d{1,3})\s*$")
__star_seg = re.compile(r"^\s*\*\s*$")
__const_seg = re.compile(r"^\s*(\d{1,3})\s*$")
def parse_block_list(input):
    bad_line_numbers = [] # We ignore badly formatted lines and keep a record.
    blocks = []

    for count, line in itertools.izip(itertools.count(1), input.split('\n')):
        if __comment_line.match(line) or __blank_line.match(line):
            continue
        m = __ip_line.match(line)
        if m:
            ranges = []
            was_error = False
            # Be careful not to mix up 'i' and '1' when changing the following code!
            for i in xrange(1,5):
                m2 = __range_seg.match(m.group(i))
                if m2:
                    ranges.append((int(m2.group(1)), int(m2.group(2))))
                else:
                    m2 = __star_seg.match(m.group(i))
                    if m2:
                        ranges.append((0, 255))
                    else:
                        m2 = __const_seg.match(m.group(i))
                        if m2:
                            n = int(m2.group(1))
                            ranges.append((n, n))
                        else:
                            bad_line_numbers.append(count)
                            was_error = True
                            break
            if was_error:
                continue
            blocks.append(IPRangeBlock(ranges))
        else:    
            m = __user_line.match(line)
            if m:
                blocks.append(UserBlock(m.group(1)))
            else:
                bad_line_numbers.append(count)
                continue
    return blocks, bad_line_numbers

__time_block_list_file_was_last_parsed = 0
__current_block_list = []
def is_blocked(username, ip_4tuple):
    global __time_block_list_file_was_last_parsed, __current_block_list
    last_modified = os.stat("etc/block")[stat.ST_MTIME]
    if last_modified > __time_block_list_file_was_last_parsed:
        __time_block_list_file_was_last_parsed = time.time()
        try:
            # Does etc/block exist? (If not, the user obviously isn't blocked.)
            if not os.path.exists("etc/block"):
                return False

            f = open("etc/block")
            contents = f.read()
            __current_block_list, bad_lines = parse_block_list(contents)
            if len(bad_lines) > 0:
                logging.log(config.SERVER_LOG, "Bad lines in block list at these line numbers: %s", str(bad_lines))
        except Exception, e:
            logging.log(config.SERVER_LOG, "Error opening etc/block_list: %s", str(e))

    return in_block_list(__current_block_list, username, ip_4tuple)


#
# TEST CODE.
#

#bl = """
## A comment
#
#127. * .56 - 78 .66
#fdsfsdfsdf
#sdfsdfsdf
#178.567.555.77
#"""
#pbl, bad = parse_block_list(bl)
#print pbl
#print in_block_list(pbl, "fdsfsdfsdf", (127,66,79,66))

