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
daemon.httpadapter
~~~~~~~~~~~~~~~~~

This module provides a http adapter object to manage and persist 
http settings (headers, bodies). The adapter supports both
raw URL paths and RESTful route definitions, and integrates with
Request and Response objects to handle client-server communication.
"""

import socket
from .request import Request
from .response import Response
from .dictionary import CaseInsensitiveDict

class HttpAdapter:
    """
    A mutable :class:`HTTP adapter <HTTP adapter>` for managing client connections
    and routing requests.

    The `HttpAdapter` class encapsulates the logic for receiving HTTP requests,
    dispatching them to appropriate route handlers, and constructing responses.
    It supports RESTful routing via hooks and integrates with :class:`Request <Request>` 
    and :class:`Response <Response>` objects for full request lifecycle management.

    Attributes:
        ip (str): IP address of the client.
        port (int): Port number of the client.
        conn (socket): Active socket connection.
        connaddr (tuple): Address of the connected client.
        routes (dict): Mapping of route paths to handler functions.
        request (Request): Request object for parsing incoming data.
        response (Response): Response object for building and sending replies.
    """

    __attrs__ = [
        "ip",
        "port",
        "conn",
        "connaddr",
        "routes",
        "request",
        "response",
    ]

    def __init__(self, ip, port, conn, connaddr, routes):
        """
        Initialize a new HttpAdapter instance.

        :param ip (str): IP address of the client.
        :param port (int): Port number of the client.
        :param conn (socket): Active socket connection.
        :param connaddr (tuple): Address of the connected client.
        :param routes (dict): Mapping of route paths to handler functions.
        """

        #: IP address.
        self.ip = ip
        #: Port.
        self.port = port
        #: Connection
        self.conn = conn
        #: Conndection address
        self.connaddr = connaddr
        #: Routes
        self.routes = routes
        #: Request
        self.request = Request()
        #: Response
        self.response = Response()

    def handle_client(self, conn, addr, routes):
        """
        Handle an incoming client connection.

        This method reads the request from the socket, prepares the request object,
        invokes the appropriate route handler if available, builds the response,
        and sends it back to the client.

        :param conn (socket): The client socket connection.
        :param addr (tuple): The client's address.
        :param routes (dict): The route mapping for dispatching requests.
        """

        # Connection handler.
        self.conn = conn        
        # Connection address.
        self.connaddr = addr
        # Request handler
        req = self.request
        # Response handler
        resp = self.response

        
        # Handle the request
        try:
            buffer = b""
            
            # 1. Read until we have headers (Double CRLF)
            while b"\r\n\r\n" not in buffer:
                chunk = conn.recv(4096)
                if not chunk:
                    break
                buffer += chunk
            
            if not buffer:
                print("[HttpAdapter] Empty request received from {}:{}".format(addr[0], addr[1]))
                conn.close()
                return

            # 2. Extract Content-Length to know how much body to read
            headers_part, body_part = buffer.split(b"\r\n\r\n", 1)
            content_length = 0
            
            # Simple parsing to find Content-Length in the binary headers
            # We decode just the headers to search for the string
            try:
                headers_str = headers_part.decode('utf-8', errors='ignore')
                for line in headers_str.split('\r\n'):
                    if line.lower().startswith('content-length:'):
                        content_length = int(line.split(':')[1].strip())
                        break
            except Exception as e:
                print(f"[HttpAdapter] Error parsing content length: {e}")

            # 3. Read the rest of the body if we haven't received it all yet
            while len(body_part) < content_length:
                to_read = content_length - len(body_part)
                # We read up to 4096 or exactly what's left, whichever is smaller
                chunk = conn.recv(min(4096, to_read))
                if not chunk:
                    break
                body_part += chunk

            # Combine headers and full body back into a string for existing logic
            msg = (headers_part + b"\r\n\r\n" + body_part).decode('utf-8')
            req.prepare(msg, routes)

            public_path = [
                '/login.html',
                ]
                
            is_public = (
                req.path in public_path or
                req.path.startswith('/static/') or
                req.path.startswith('/api/') or 
                req.path.startswith('/images/')
            )

            # Handle request hook
            if req.hook:
                print("[HttpAdapter] hook in route-path METHOD {} PATH {}".format(req.hook._route_path,req.hook._route_methods))
                
                hook_result = req.hook(headers=str(req.headers), body = req.body)
                

                if hook_result is not None:
                    if req.hook._route_path == '/login' and req.hook._route_methods == ['POST']:
                        response = hook_result.encode('utf-8')
                        print("[HttpAdapter] Hook processed for login {}".format(response))  
                    else:
                        if req.cookies.get('auth','') == 'true':
                            response = hook_result.encode('utf-8')
                            if req.hook._route_path != '/ping': 
                                print("[HttpAdapter] Hook processed for protected route {}".format(response))
                        else:
                            response = self.build_error_response(401, "Unauthorized")
                            print("[HttpAdapter] Unauthorized access attempt to protected route via hook")

            elif req.method == 'POST' and req.path == '/login':
                print("[HttpAdapter] Handling login POST request")
                response = self.handle_login(req, resp)
            elif (req.path == '/index.html' or req.path == '/') and not is_public:
                print("[HttpAdapter] Handling protected route request")
                response = self.handle_protected_route(req, resp)
            else:
                print("[HttpAdapter] Handling general request")
                response = resp.build_response(req)
                #
                # TODO: handle for App hook here
                #

            # Build response
        except Exception as e:
            print(f"[HttpAdapter] Error handling client {addr}: {e}")
            response = self.build_error_response(500, "Internal Server Error")

            #print(response)
        conn.sendall(response)
        conn.close()
        

    def extract_cookies(self, req):
        """
        Build cookies from the :class:`Request <Request>` headers.

        :param req:(Request) The :class:`Request <Request>` object.
        :rtype: cookies - A dictionary of cookie key-value pairs.
        """
        
        return req.cookies

    def build_response(self, req, resp):
        """Builds a :class:`Response <Response>` object 

        :param req: The :class:`Request <Request>` used to generate the response.
        :param resp: The  response object.
        :rtype: Response
        """
        response = Response()

        # Set encoding.
        response.encoding = 'utf-8'
        response.raw = resp
        response.reason = getattr(response.raw, 'reason', 'OK')

        if isinstance(req.url, bytes):
            response.url = req.url.decode('utf-8')
        else:
            response.url = req.url
        
        response.cookies = self.extract_cookies(req)

        response.request = req
        response.connection = self

        return response




    def add_headers(self, request):
        """
        Add headers to the request.

        This method is intended to be overridden by subclasses to inject
        custom headers. It does nothing by default.

        
        :param request: :class:`Request <Request>` to add headers to.
        """
        pass

    def build_proxy_headers(self, proxy):
        """Returns a dictionary of the headers to add to any request sent
        through a proxy. 

        :class:`HttpAdapter <HttpAdapter>`.

        :param proxy: The url of the proxy being used for this request.
        :rtype: dict
        """
        headers = {}
        #
        # TODO: build your authentication here
        #       username, password =...
        # we provide dummy auth here
        #
        username, password = ("user1", "password")

        if username:
            headers["Proxy-Authorization"] = (username, password)

        return headers
    
    def handle_login(self, req, resp):
        """
        Handle login requests.

        :param req: The incoming :class:`Request <Request>`.
        :param resp: The :class:`Response <Response>` object to build the reply.
        :rtype: bytes - The raw HTTP response bytes.
        """
        # Dummy login logic for demonstration
        form_data = req.parse_form_data()
        username = form_data.get('username', '')
        password = form_data.get('password', '')

        print ("[HttpAdapter] Login attempt with username: {}, password: {}".format(username, password))

        if username == 'admin' and password == 'admin':
            resp.status_code = 200
            resp.set_cookie('auth', 'true')
            req.path = '/index.html'
            print("[HttpAdapter] Login successful for user: {}".format(username))
            return resp.build_response(req)
        else:
            return self.build_error_response(401, "Unauthorized")
    
    def handle_loginchat(self, req, resp):
        """
        Handle login requests.

        :param req: The incoming :class:`Request <Request>`.
        :param resp: The :class:`Response <Response>` object to build the reply.
        :rtype: bytes - The raw HTTP response bytes.
        """
        # Dummy login logic for demonstration
        form_data = req.parse_form_data()
        username = form_data.get('username', '')
        password = form_data.get('password', '')

        print ("[HttpAdapter] Login attempt with username: {}, password: {}".format(username, password))

        if username == 'admin' and password == 'admin':
            resp.status_code = 200
            resp.set_cookie('auth', 'true')
            req.path = '/index.html'
            print("[HttpAdapter] Login successful for user: {}".format(username))
            return resp.build_response(req)
        else:
            return self.build_error_response(401, "Unauthorized")


    def handle_protected_route(self, req, resp):
        """
        Handle access to protected routes.

        :param req: The incoming :class:`Request <Request>`.
        :param resp: The :class:`Response <Response>` object to build the reply.
        :rtype: bytes - The raw HTTP response bytes.
        """
        cookies = req.cookies
        auth_cookie = cookies.get('auth', '')

        if auth_cookie == 'true':
            if req.path == '/':
                req.path = '/index.html'
            return resp.build_response(req)
        else:
            return self.build_error_response(401, "Unauthorized")
        
    def build_error_response(self, status_code, message):
        """
        Build an error response.

        :param status_code: HTTP status code.
        :param message: Error message.
        :rtype: bytes - The raw HTTP response bytes.
        """
        if status_code == 401:
            response_body = """
            <html><body>
            <h1>401 Unauthorized</h1>
            <p>{}</p>
            <a href="/login.html">Login Here for Access /index.html</a>
            <a href="/loginchat.html">Login here toGo to Chat Room</a>
            </body></html>
            """.format(message)
        else:
            response_body = """
            <html><body>
            <h1>{} {}</h1>
            <p>An error occurred: {}</p>
            </body></html>
            """.format(status_code, message, message)
        
        response_text = """HTTP/1.1 {} {}
            Content-Type: text/html
            Content-Length: {}
            Connection: close

            {}""".format(status_code, message, len(response_body), response_body)
                    
        return response_text.encode('utf-8')