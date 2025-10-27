#
# Copyright (C) 2025 pdnguyen of HCMC University of Technology VNU-HCM.
# All rights reserved.
# This file is part of the CO3093/CO3094 course.
#
# WeApRous release
#
# The authors hereby grant to Licensee personal permission to use
# and modify the Licensed Source Code for the sole purpose of studying
# while attending the course
#

"""
daemon.request
~~~~~~~~~~~~~~~~~

This module provides a Request object to manage and persist 
request settings (cookies, auth, proxies).
"""
from .dictionary import CaseInsensitiveDict

class Request():
    """The fully mutable "class" `Request <Request>` object,
    containing the exact bytes that will be sent to the server.

    Instances are generated from a "class" `Request <Request>` object, and
    should not be instantiated manually; doing so may produce undesirable
    effects.

    Usage::

      >>> import deamon.request
      >>> req = request.Request()
      ## Incoming message obtain aka. incoming_msg
      >>> r = req.prepare(incoming_msg)
      >>> r
      <Request>
    """
    __attrs__ = [
        "method",
        "url",
        "headers",
        "body",
        "reason",
        "cookies",
        "body",
        "routes",
        "hook",
    ]

    def __init__(self):
        #: HTTP verb to send to the server.
        self.method = None
        #: HTTP URL to send the request to.
        self.url = None
        #: dictionary of HTTP headers.
        self.headers = None
        #: HTTP path
        self.path = None        
        # The cookies set used to create Cookie header
        self.cookies = None
        #: request body to send to the server.
        self.body = None
        #: Routes
        self.routes = {}
        #: Hook point for routed mapped-path
        self.hook = None
    #POST /login HTTP/1.1 to
    # method = POST
    # path = /login
    # version = HTTP/1.1
    def extract_request_line(self, request):
        try:
            lines = request.splitlines()
            first_line = lines[0]
            method, path, version = first_line.split()

            if path == '/':
                path = '/index.html'
        except Exception:
            return None, None

        return method, path, version
        # 'Host: localhost:8000',
        # 'User-Agent: Mozilla/5.0',
        # 'Content-Type: application/x-www-form-urlencoded',
        # 'Cookie: session_id=abc123',
    def prepare_headers(self, request):
        """Prepares the given HTTP headers."""
        lines = request.split('\r\n')
        headers = {}
        for line in lines[1:]:
            if ': ' in line:
                key, val = line.split(': ', 1)
                headers[key.lower()] = val
        return headers

    def prepare(self, request, routes=None):
        """Prepares the entire request with the given parameters."""

        # Prepare the request line from the request header
        self.method, self.path, self.version = self.extract_request_line(request)
        print("[Request] {} path {} version {}".format(self.method, self.path, self.version))

        #
        # @bksysnet Preapring the webapp hook with WeApRous instance
        # The default behaviour with HTTP server is empty routed
        #
        # TODO manage the webapp hook in this mounting point
        #
        
        if not routes == {}:
            self.routes = routes
            self.hook = routes.get((self.method, self.path))
            #
            # self.hook manipulation goes here
            # ...
            #
            if self.hook is not None:
                print("[Request] hook found for {} {}".format(self.method, self.path))

                if not callable(self.hook):
                    print("[Request] hook is not callable")
                    self.hook = None
            else:
                print("[Request] no hook found for {} {}".format(self.method, self.path))

        self.headers = self.prepare_headers(request)

        if '\r\n\r\n' in request:
            header_part, self.body = request.split('\r\n\r\n', 1)
            content_length = self.prepare_content_length(self.body)
            print ("[Request] body prepared with length {}".format(content_length))

        else :
            self.body = None
            print ("[Request] no body found")
        cookies_header = self.headers.get('cookie', '')

        self.cookies = {}
        if cookies_header:
            for pair in cookies_header.split('; '):
                if '=' in pair:
                    key, value = pair.split('=', 1)
                    self.cookies[key.strip()] = value.strip()
        print("[Request] cookies parsed: {}".format(self.cookies))
            #
            #  TODO: implement the cookie function here
            #        by parsing the header            #

        return

    def prepare_body(self, data, files, json=None):

        
        #
        # TODO prepare the request authentication
        #
	# self.auth = ...

        return


    def prepare_content_length(self, body):
        #
        # TODO prepare the request authentication
        #
	# self.auth = ...
        if self.headers is None:
            self.headers = {}
        if body is not None:
            if isinstance(body, str):
                length = len(body.encode('utf-8'))
            elif isinstance(body, bytes):
                length = len(body)
            else:
                length = 0
            self.headers["Content-Length"] = str(length)
        else :
            self.headers["Content-Length"] = "0"
        return




    def prepare_auth(self, auth, url=""):
        #
        # TODO prepare the request authentication
        #
	# self.auth = ...
        return

    def prepare_cookies(self, cookies):
            self.headers["Cookie"] = cookies
