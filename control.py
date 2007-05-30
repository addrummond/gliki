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

# ADVANCED CONFIGURATION SYSTEM.
SERVER = "paste" # OR "lighttpd"

if SERVER == "lighttpd":
   from flup.server.fcgi import WSGIServer
elif SERVER == "paste":
   from paste import httpserver
import itertools
import urimatch
import inspect
import types
import cgi
import urllib
import base64
import random
import mimetools
import my_utils
import time
import md5
import logging
import config

__http_methods = ["OPTIONS", "GET", "HEAD", "POST", "PUT", "DELETE", "TRACE", "CONNECT"]

# Inconsistent environment variable naming with different WSGI implementations!
def get_uri(env):
    if SERVER == "lighttpd":
        return env['REQUEST_URI']
    elif SERVER == "paste":
        return env['PATH_INFO']
    assert False
def get_content_length(env):
    if SERVER == "lighttpd":
        return env['HTTP_CONTENT_LENGTH']
    elif SERVER == "paste":
        return env['CONTENT_LENGTH']
    assert False

def signal_error(code, name, headers, start_response, text=None):
    """This provides a simple template for error messages."""
    import htmlutils
    start_response(code + ' ' + name, [('Content-Type', 'text/html; charset=UTF-8')] + headers)
    return ['<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">',
            '<html><head><title>%s</title></head>' % (code + ' - ' + name),
            '<body><h2>%s</h2></body></html>' % (text or code + ' - ' + name)]

__handlers = []
def register_handler(app):
    __handlers.append(app)
def register_handlers(apps):
    __handlers.extend(apps)

class Message(Exception):
    pass

class InvalidRequestMethodError(Message):
    def __init__(self, allowed):
        self.allowed = allowed

    def __str__(self):
        return "(InvalidRequestMethodError: " + str(self.allowed) + ")"
class NotFoundError(Message):
    def __init__(self):
        return

    def __str__(self):
        return "(NotFoundError)"
class BadRequestError(Message):
    def __init__(self):
        return

    def __str__(self):
        return "(BadRequestError)"
class Redirect(Message):
    def __init__(self, url, content_type, kind=301, headers=[]):
        self.url = url
        self.content_type = content_type
        self.kind = kind
        self.headers = headers
class AuthenticationRequired(Message):
    def __init__(self, realm, type, stale=False):
        assert type == 'basic' or type == 'digest'
        self.realm = realm
        self.type = type
        self.stale = stale

def dispatch(type, uri):
    for h in __handlers:
        for p in h.uris:
            r = urimatch.test_pattern(p, uri)
            if not (r is False):
                att = None
                try:
                    att = getattr(h, type)
                    return (att, r)
                except AttributeError:
                    # If HEAD doesn't exist, we can just do a GET and
                    # not bother with the body.
                    if type == "HEAD" and hasattr(h, "GET"):
                        def wrapper(*args):
                            getattr(h, "GET")(*args)
                            return []
                        return (wrapper, r)

                    # We really can't handle this method, so find the methods
                    # which are allowed and raise a 405.
                    allowed = []
                    for m in dir(h.__class__):
                        if not(m.startswith('__')) and inspect.ismethod(getattr(h.__class__, m)):
                            allowed.append(m)
                    raise InvalidRequestMethodError(allowed)
    raise NotFoundError()

def random_string(length):
    return \
    reduce(lambda x, y: x + y,
           random.sample('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz1234567890', length))

# Various bits of state used in digest authentication and some functions which manipulate it.
__nonce_to_time = { }
__nonce_to_opaque = { }
__nonce_to_count = { }
def __add_nonce():
    rs = random_string(32)
    __nonce_to_time[rs] = time.time()
    opaque = random_string(32)
    __nonce_to_opaque[rs] = opaque
    __nonce_to_count[rs] = 0
    return rs, opaque
__last_nonce_pruning_time = 0
def __prune_nonces():
    # Don't prune more than every 5 seconds.
    global __last_nonce_pruning_time
    tm = time.time()
    if tm - __last_nonce_pruning_time < 5000:
        return
    __last_nonce_pruning_time = tm

    # Do the actual pruning.
    for k in __nonce_to_time.iterkeys():
        if time.time() - __nonce_to_time[k] > 30000:
            del __nonce_to_time[k]
            del __nonce_to_opaque[k]
            del __nonce_to_count[k]

class MessageHandlers(object):
    def not_found_error(self, uri, start_response):
        return signal_error('404', 'Not Found', [], start_response)

    def invalid_request_method_error(self, uri, method, allowed, start_response):
        # HEAD is always allowed if GET is.
        if (not "HEAD" in allowed) and ("GET" in allowed):
            allowed.append("HEAD")
        # Do we need to set a Content-Type here, and if so what should it be?
        return signal_error('400', 'Method Not Allowed', [('Allow', ', '.join(allowed))], start_response)

    # post_data is set to None if not a POST request.
    def bad_request_error(self, uri, start_response):
        return signal_error('400', 'Bad Request', [], start_response)

    def redirect(self, uri, content_type, kind, headers, start_response):
        if kind == 301 or kind == 'permanent':
            start_response('301 Moved Permanently',
                           [('Content-Type', content_type),
                            ('Location', uri)]
                           + headers)
        elif kind == 302 or kind == 'temporary':
            start_response('302 Moved Temporarily',
                           [('Content-Type', content_type),
                            ('Location', uri)]
                           + headers)
        elif kind == 303 or kind == 'see_other':
            start_response('303 See Other',
                           [('Content-Type', content_type),
                            ('Location', uri)]
                           + headers)
        else:
            raise "Unknown redirict kind in control.py MessageHandlers.redirect method"
        return []

    def authentication_required(self, uri, realm, type, start_response, stale=False):
        if type == 'basic':
            start_response('401 Unauthorized',
                           [('WWW-Authenticate', 'Basic realm="%s"' % urllib.quote(realm))])
            return []
        elif type == 'digest':
            nonce, opaque = globals()['__add_nonce']()
            start_response(
                '401 Unauthorized',
                [('WWW-Authenticate',
                  'Digest realm="%s", URI="%s", qop="auth", stale="%s", algorithm="MD5", opaque="%s", nonce="%s"' %
                  (realm, urllib.quote(uri), stale and "TRUE" or "FALSE", opaque, nonce))]
            )
            return []
        assert False

__message_handlers = MessageHandlers()
def set_default_error_handlers(h):
    __message_handlers = h

# Decorators for making it easier to do simple '200 OK' responses.
# These work with normal handler methods but NOT (necessarily) with the methods
# of MessageHandlers.
def ok(content_type, **args):
    lst = [('Content-Type', content_type)]
    if args.has_key('cached') and args['cached']:
        lst.append([('Pragma', 'no-cache')])
    def decorator(f):
        def r(self, d, extras, start_response):
            out = f(self, d, extras)
            start_response('200 OK', lst)
            return out
        return r
    return decorator
def ok_text(**args): return ok('text/plain; charset=UTF-8', **args)
def ok_html(**args): return ok('text/html; charset=UTF-8', **args)
def ok_xhtml(**args): return ok('text/xhtml; charset=UTF-8', **args)

def make_cookie_headers(*cookies):
    """'cookies' arguemt is list of dict(var=*, value=*, expires=*, path=*)"""

    # We can't use urllib.quote on the expiration value, but we'd better check
    # that it doesn't contain ';' or '='.
    for c in cookies:
        if c.has_key('expires') and (';' in c['expires'] or '=' in c['expires']):
            raise "Badly formatted expiry date for cookie"
        if not c.has_key('expires'):
            c['expires'] = ''

    return \
        [("Set-Cookie",
          "%s=%s; expires=%s; path=%s" %
          (urllib.quote(c['var']), urllib.quote(c['value']),
           c['expires'], urllib.quote(c['path'])) +
          # Do we need to add the 'secure' option?
          ((c.has_key('secure') and c['secure']) and '; secure' or '')
         )
         for c in cookies
        ]

# Decorator for setting a cookie.
# The cookie is only set if the reponse is 200 OK.
def set_cookies(cookies):
    """'cookies' arguemt is list of dict(var=*, value=*, expires=*, path=*)"""

    def decorator(f):
        def r(self, parms, extras, start_response):
            def my_start_response(kind, headers):
                if kind.startswith('200 '):
                    return start_response(
                        kind,
                        headers +
                        make_cookie_headers(cookies)
                    )
                else:
                    return start_response(kind, headers)
            return f(self, parms, extras, my_start_response)
        return r
    return decorator

# Decorator for adding an authentication requirement. This sends back a 401
# if the function it decorates sends back a 201. Should be stacked above the
# ok_* decorators.
#def auth(realm):
#    def decorator(f):
#        def r(self, d, start_response):
#            def my_start_response(kind, headers):
#                if kind.startswith('200 '):
#                    start_response('401 Authentication Required', ...)
#                else:
#                    start_response(kind, headers):
#            return f(self, d, my_start_response)
#        return r
#    return f

class SwitchHandler(Message):
    def __init__(self, handler_instance, dict={ }, method=None):
        self.handler_instance = handler_instance
        self.dict = dict
        self.method = method

class Extras(object):
    """The class for the juicy extra info passed to handler methods."""
    class BasicAuth:
        """This is used to hold 'realm', 'username' and 'password' fields."""
        pass
    class DigestAuth:
        """This is used to hold 'username', """
        pass

def control(env, start_response):
    """This is the callback passed to the WSGI server."""

    def add_basic_auth_info(extras):
        auth = env['HTTP_AUTHORIZATION']
        s = auth.split(' ')
        # If it's badly formatted we'll just ignore it.
        if len(s) == 2:
            base64_string = s[1]
            decoded = None
            try:
                decoded = base64.decodestring(base64_string)
                up = decoded.split(':')
                # If it's badly formatted we'll just ignore it.
                if len(up) == 2:
                    extras.auth = Extras.BasicAuth()
                    extras.auth.username = up[0]
                    extras.auth.password = up[1]
            except base64.binascii.Error:
                pass

    def add_digest_auth_info(extras):
        auth = env['HTTP_AUTHORIZATION'].lstrip('Digest')
        options = my_utils.csv_parse(auth)
        must_haves = [ 'nonce', 'opaque', 'response', 'username', 'uri' ]
        for k in must_haves:
            if not options.has_key(k):
                raise BadRequestError()

        # Either qop and cnonce are both present, or neither is present.
        if options.has_key('qop') and (not options.has_key('cnonce')):
            raise BadRequestError()
        if options.has_key('cnonce') and (not options.has_key('qop')):
            raise BadRequestError()

        # qop must be "auth" if present.
        if options.has_key('qop') and options['qop'] != "auth":
            raise BadRequestError()

        # Algorithm is either not present or specified as MD5.
        if options.has_key('algorithm') and options['algorithm'] != 'MD5':
            raise BadRequestError()

        # Remove any stale nonces before we do anything else.
        __prune_nonces()

        # Check for a bad opaque string.
        if __nonce_to_opaque.has_key(options['nonce']) and \
           options['opaque'] != __nonce_to_opaque[options['nonce']]:
            extras.auth = Extras.DigestAuth()
            extras.auth.bad_auth_header = True
            extras.auth.bad_because = 'bad_opaque'
        # Check the nonce.
        elif not __nonce_to_opaque.has_key(options['nonce']):
            extras.auth = Extras.DigestAuth()
            extras.auth.bad_auth_header = True
            extras.auth.bad_because = 'stale_nonce'
        # Check for a bad nonce count.
        # TODO.
        else:
            # Update nonce count.
            __nonce_to_count[options['nonce']] += 1

            # WE'VE GOT A GOOD REQUEST, NOW WE JUST NEED TO CHECK THAT THE
            # USERNAME AND PASSWORD ARE CORRECT.

            def test(password):
                # Redundant test to ensure password is ASCII.
                try: password = password.encode('ascii')
                except UnicodeError: assert False

                ha1 = md5.md5("%s:%s:%s" % (options['username'], options['realm'], password)).hexdigest()
                ha2 = md5.md5("%s:%s" % (env['REQUEST_METHOD'], options['uri'])).hexdigest()

                # Format of the digest string will be different depending on whether
                # or not qop is present.
                big_hash = None
                if options.has_key('qop'):
                    big_hash = md5.md5("%s:%s:%s:%s:auth:%s" % (ha1, options['nonce'], options['nc'], options['cnonce'], ha2)).hexdigest()
                else:
                    big_hash = md5.md5("%s:%s:%s" % (ha1, options['nonce'], ha2)).hexdigest()

                return big_hash == options['response'].lower()

            extras.auth = Extras.DigestAuth()
            extras.auth.bad_auth_header = False
            extras.auth.username = options['username']
            extras.auth.test = test # Should we use instancemethod?

    #
    # THE MAIN LOOP.
    #
    goto, goto_dict = None, None
    while True:
        try:
            if not goto:
                goto, goto_dict = dispatch(env['REQUEST_METHOD'], get_uri(env))

            # Add POST data to the dict if this is a post request.
            if env['REQUEST_METHOD'] == 'POST':
                post_data = env['wsgi.input'].read(int(get_content_length(env)))
                for k, v in cgi.parse_qs(post_data).iteritems():
                    goto_dict[k] = v[0]

            extras = Extras()

            # Add the remote IP to the Extras object.
            if env.has_key('HTTP_X_FORWARDED_FOR'):
                extras.remote_ip = env['HTTP_X_FORWARDED_FOR']
            elif env.has_key('REMOTE_ADDR'):
                extras.remote_ip = env['REMOTE_ADDR']

            # Add cookies to the Extras object if there's an HTTP_COOKIE header.
            extras.cookies = { }
            if env.has_key('HTTP_COOKIE'):
                cookies = env['HTTP_COOKIE'].split(';')
                cookies = [s.strip(' ') for s in cookies]
                kvpairs = [s.split('=') for s in cookies]
                for l in kvpairs:
                    if len(l) == 2:
                        extras.cookies[urllib.unquote(l[0])] = urllib.unquote(l[1])

            # Add authentication information to the Extras object
            # (currently we ignore everything except Basic and Digest).
            extras.auth = None
            if env.has_key('HTTP_AUTHORIZATION'):
                if env['HTTP_AUTHORIZATION'].startswith('Basic'):
                    add_basic_auth_info(extras)
                elif env['HTTP_AUTHORIZATION'].startswith('Digest'):
                    add_digest_auth_info(extras)

            # Add the complete (F)CGI environment to the extras.
            extras.env = env

            r = goto(goto_dict, extras, start_response)
            if type(r) == types.GeneratorType:
                return list(r)
            else:
                return r
        except InvalidRequestMethodError, e:
            return __message_handlers.invalid_request_method_error(
                get_uri(env),
                env['REQUEST_METHOD'],
                e.allowed,
                start_response)
        except NotFoundError, e:
            return __message_handlers.not_found_error(get_uri(env), start_response)
        except BadRequestError, e:
            return __message_handlers.bad_request_error(get_uri(env), start_response)
        except Redirect, e:
            return __message_handlers.redirect(e.url, e.content_type, e.kind, e.headers, start_response)
        except AuthenticationRequired, e:
            return __message_handlers.authentication_required(get_uri(env), e.realm, e.type, start_response, e.stale)
        except SwitchHandler, e:
            method = get_uri(env)
            if e.method is not None:
                method = e.method
            handler_method = getattr(e.handler_instance, method)
            if not handler_method:
                logging.log(logging.SERVER_LOG, 'WARNING: Bad SwitchHandler,"%s","%s","%s"' % \
                                                (str(e.handler_instance), str(e.method), str(e.dict)))
                raise NotFoundError()
            goto = handler_method
            goto_dict = e.dict
            continue

def paste_server_static_wrapper(path, control_func):
    """Given a document root and a control function, return a new control
       function which checks for the existence of a static file and
       serves it if available. If no static file is available, this function
       defers to the given control function."""
    import os.path
    types = { "html" : ("text/html", "UTF-8"),
              "png"  : ("image/png", None),
              "jpg"  : ("image/jpeg", None),
              "jpeg" : ("image/jpeg", None),
              "gif"  : ("image/gif", None),
              "css"  : ("text/css", "UTF-8") }
    def control(env, start_response):
        local_path = path + '/' + get_uri(env)
        if not (os.path.exists(local_path) and os.path.isfile(local_path)):
            return control_func(env, start_response)
        else:
            s = get_uri(env).split('.')
            if len(s) > 1 and (s[len(s) - 1] in types):
                # We've found a static file and we know what kind of file it is.
                f = None
                contents = None
                try:
                    try:
                        f = open(local_path, "r")
                        contents = f.read()
                    except e:
                        return signal_error('500', 'Internal Server Error', [], start_response)
                finally:
                    f.close()
                type = types[s[len(s) - 1]][0]
                coding = types[s[len(s) - 1]][1]
                ct = type + (coding and ('; charset=' + coding,) or ('',))[0]
                start_response('200 OK', [('Content-Type', ct)])
                return [contents]
            else:
                # We found the file, but it didn't have an extension so we
                # couldn't work out what kind of file it was.
                logging.log(logging.SERVER_LOG, "WARNING: 500 error due to unknown file type of %s" % local_path)
                return signal_error('500', 'Internal Server Error', [], start_response)
    return control

def start_server(port):
    if SERVER == "lighttpd":
        WSGIServer(control, bindAddress = '/tmp/fcgi.sock').run() 
    elif SERVER == "paste":
        httpserver.serve(paste_server_static_wrapper('static', control), port=port)
    else:
        assert False

