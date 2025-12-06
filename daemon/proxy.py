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
daemon.proxy
~~~~~~~~~~~~~~~~~

This module implements a simple proxy server using Python's socket and threading libraries.
It routes incoming HTTP requests to backend services based on hostname mappings and returns
the corresponding responses to clients.

Requirement:
-----------------
- socket: provides socket networking interface.
- threading: enables concurrent client handling via threads.
- response: customized :class: `Response <Response>` utilities.
- httpadapter: :class: `HttpAdapter <HttpAdapter >` adapter for HTTP request processing.
- dictionary: :class: `CaseInsensitiveDict <CaseInsensitiveDict>` for managing headers and cookies.

"""
import socket
import threading
from .response import *
from .httpadapter import HttpAdapter
from .dictionary import CaseInsensitiveDict

#: A dictionary mapping hostnames to backend IP and port tuples.
#: Used to determine routing targets for incoming requests.

_rr_idx = {}
_rr_lock = threading.Lock()

def forward_request(host, port, request):
    """
    Forwards an HTTP request to a backend server and retrieves the response.

    :params host (str): IP address of the backend server.
    :params port (int): port number of the backend server.
    :params request (str): incoming HTTP request.

    :rtype bytes: Raw HTTP response from the backend server. If the connection
                  fails, returns a 404 Not Found response.
    """

    backend = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        backend.connect((host, port))
        backend.sendall(request.encode())
        response = b""
        while True:
            chunk = backend.recv(4096)
            if not chunk:
                break
            response += chunk
        return response
    except socket.error as e:
      print("Socket error: {}".format(e))
      return (
            "HTTP/1.1 404 Not Found\r\n"
            "Content-Type: text/plain\r\n"
            "Content-Length: 13\r\n"
            "Connection: close\r\n"
            "\r\n"
            "404 Not Found"
        ).encode('utf-8')


def resolve_routing_policy(hostname, routes):
    """
    Handles an routing policy to return the matching proxy_pass.
    It determines the target backend to forward the request to.

    :params host (str): IP address of the request target server.
    :params port (int): port number of the request target server.
    :params routes (dict): dictionary mapping hostnames and location.
    """

    proxy_map, policy = routes.get(hostname, ('127.0.0.1:9000', 'round-robin'))
    target = proxy_map

    if isinstance(proxy_map, list) and len(proxy_map) >= 2 and (policy or '').lower() == 'round-robin':
        with _rr_lock:
            next_idx = _rr_idx.get(hostname, 0) % len(proxy_map)
            _rr_idx[hostname] = next_idx + 1
        target = proxy_map[next_idx]
    elif isinstance(proxy_map, list):
        target = proxy_map[0]

    proxy_host, proxy_port = target.rsplit(':', 1)
    return proxy_host, proxy_port

def handle_client(ip, port, conn, addr, routes):
    """
    Handles an individual client connection by parsing the request,
    determining the target backend, and forwarding the request.

    The handler extracts the Host header from the request to
    matches the hostname against known routes. In the matching
    condition,it forwards the request to the appropriate backend.

    The handler sends the backend response back to the client or
    returns 404 if the hostname is unreachable or is not recognized.

    :params ip (str): IP address of the proxy server.
    :params port (int): port number of the proxy server.
    :params conn (socket.socket): client connection socket.
    :params addr (tuple): client address (IP, port).
    :params routes (dict): dictionary mapping hostnames and location.
    """
    try:
        # Read full request including body
        buffer = b""
        while b"\r\n\r\n" not in buffer:
            chunk = conn.recv(4096)
            if not chunk:
                break
            buffer += chunk
        
        if not buffer:
            conn.close()
            return
        
        # Split headers and body
        headers_part, body_part = buffer.split(b"\r\n\r\n", 1)
        
        # Parse Content-Length
        content_length = 0
        headers_str = headers_part.decode('iso-8859-1', errors='ignore')
        hostname = None
        
        for line in headers_str.split('\r\n'):
            if line.lower().startswith('host:'):
                hostname = line.split(':', 1)[1].strip()
            elif line.lower().startswith('content-length:'):
                try:
                    content_length = int(line.split(':', 1)[1].strip())
                except ValueError:
                    pass
        
        # Read remaining body if needed
        while len(body_part) < content_length:
            chunk = conn.recv(min(4096, content_length - len(body_part)))
            if not chunk:
                break
            body_part += chunk
        
        # Reconstruct full request
        request = (headers_part + b"\r\n\r\n" + body_part).decode('iso-8859-1', errors='ignore')
        
        if not hostname:
            conn.sendall(b"HTTP/1.1 400 Bad Request\r\n\r\n")
            conn.close()
            return

        print("[Proxy] {} at Host: {}".format(addr, hostname))

        # Resolve the matching destination in routes
        resolved_host, resolved_port = resolve_routing_policy(hostname, routes)
        try:
            resolved_port = int(resolved_port)
        except ValueError:
            print("Not a valid integer")

        if resolved_host:
            print("[Proxy] Host name {} is forwarded to {}:{}".format(hostname, resolved_host, resolved_port))
            response = forward_request(resolved_host, resolved_port, request)        
        else:
            response = (
                "HTTP/1.1 404 Not Found\r\n"
                "Content-Type: text/plain\r\n"
                "Content-Length: 13\r\n"
                "Connection: close\r\n"
                "\r\n"
                "404 Not Found"
            ).encode('utf-8')
        conn.sendall(response)
        conn.close()
    except Exception as e:
        print("[Proxy] Error handling client {}: {}".format(addr, e))
        try:
            error_response = (
                "HTTP/1.1 500 Internal Server Error\r\n"
                "Content-Type: text/plain\r\n"
                "Content-Length: 21\r\n"
                "Connection: close\r\n"
                "\r\n"
                "500 Internal Server Error"
            ).encode('utf-8')
            conn.sendall(error_response)
            conn.close()
        except:
            pass

def run_proxy(ip, port, routes):
    """
    Starts the proxy server and listens for incoming connections. 

    The process dinds the proxy server to the specified IP and port.
    In each incomping connection, it accepts the connections and
    spawns a new thread for each client using `handle_client`.
 

    :params ip (str): IP address to bind the proxy server.
    :params port (int): port number to listen on.
    :params routes (dict): dictionary mapping hostnames and location.

    """

    proxy = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        proxy.bind((ip, port))
        proxy.listen(50)
        print("[Proxy] Listening on IP {} port {}".format(ip,port))
        while True:
            conn, addr = proxy.accept()
            #
            #  TODO: implement the step of the client incomping connection
            #        using multi-thread programming with the
            #        provided handle_client routine
            #
            client_thread = threading.Thread(target=handle_client, args=(ip, port, conn, addr, routes))
            client_thread.start()
    except socket.error as e:
      print("Socket error: {}".format(e))

def create_proxy(ip, port, routes):
    """
    Entry point for launching the proxy server.

    :params ip (str): IP address to bind the proxy server.
    :params port (int): port number to listen on.
    :params routes (dict): dictionary mapping hostnames and location.
    """

    run_proxy(ip, port, routes)
