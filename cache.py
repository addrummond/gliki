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
This module implements a simple caching system associating article titles with
threads_id numbers.
"""

import os
import os.path
import types
import base64
import thread

class FSThreadsIdCache(object):
    """Provides caching of threads_id number using the file system.
       Thread safe.
    """

    __cache_dirs = [] # Used to ensure that we don't have multiple caches in
                      # the same directory.

    def __init__(self, path):
        assert os.path.isdir(path) and not path in FSThreadsIdCache.__cache_dirs
        self.path = path.rstrip(os.sep)
        self.lock = thread.allocate_lock()

    def __fname(self, title):
        """Returns an ASCII string."""
        return self.path + os.sep + base64.encode(title.encode('utf-8'))

    def is_cached(self, title):
        assert type(title) == types.UnicodeType
        return os.path.isfile(self.__fname(title))

    def get_threads_id(self, title):
        if not self.is_cached(title):
            return False
        try:
            try:
                f = open(self.__fname(title))
                id = int(f.read().strip())
                return id
            except:
                return False
        finally:
            f.close()

    def set_threads_id(self, title, threads_id):
        assert type(threads_id) == types.IntType

        try:
            self.lock.acquire()

            try:
                f = open(self.__fname(title), self.is_cached(title) and "w" or "w+")
                f.write(str(threads_id))
            except:
                pass # If we can't cache it, just ignore it.
        finally:
            self.lock.release()
            f.close()

    def stop_caching(self, title):
        """Stops caching the threads_id for the given title. Returns True on
           success or False on failure.
        """
        fname = self.__fname(title)
        assert os.path.isfile(fname)

        try:
            try:
                self.lock.acquire()
                os.remove(fname)
            except:
                return False
        finally:
            self.lock.release()
        return True

