#
# Copyright (C) 2025 pdnguyen of HCMC University of Technology VNU-HCM.
# All rights reserved.
# This file is part of the CO3093/CO3094 course,
# and is released under the "MIT License Agreement". Please see the LICENSE
# file that should have been included as part of this package.
#
# WeApRous release
#
# The authors hereby grant to Licensee personal permission to use
# and modify the Licensed Source Code for the sole purpose of studying
# while attending the course
#


"""
start_sampleapp
~~~~~~~~~~~~~~~~~

This module provides a sample RESTful web application using the WeApRous framework.

It defines basic route handlers and launches a TCP-based backend server to serve
HTTP requests. The application includes a login endpoint and a greeting endpoint,
and can be configured via command-line arguments.
"""

import json
import socket
import argparse

from daemon.weaprous import WeApRous

PORT = 8000  # Default port

app = WeApRous()

@app.route('/login', methods=['POST'])
def login(headers="guest", body="anonymous"):
    """
    Handle user login via POST request.

    This route simulates a login process and prints the provided headers and body
    to the console.

    :param headers (str): The request headers or user identifier.
    :param body (str): The request body or login payload.
    """
    print("sampleapp login called")

    params = {}
    for pair in body.split("&"):
        key, value = pair.split("=",1)
        params[key] = value
    
    username = params.get("username", "")
    password = params.get("password", "")

    print("[SampleApp] Logging in {} to {}".format(headers, body))

    if username == "admin" and password == "password":
        return {
            'status': 200,
            'cookies': {'session_id': 'abc123xyz789'},  # Generate session ID
            'headers': {'Content-Type': 'text/html'},
            'content': '<html><body><h1>Login Successful!</h1><a href="/dashboard">Go to Dashboard</a></body></html>'
        }
    else:
        # Failure
        return {
            'status': 401,
            'headers': {'Content-Type': 'text/html'},
            'content': '<html><body><h1>Login Failed!</h1><p>Invalid credentials</p><a href="/login.html">Try Again</a></body></html>'
        }

@app.route('/hello', methods=['PUT'])
def hello(headers, body):
    """
    Handle greeting via PUT request.

    This route prints a greeting message to the console using the provided headers
    and body.

    :param headers (str): The request headers or user identifier.
    :param body (str): The request body or message payload.
    """
    print("[SampleApp] ['PUT'] Hello in {} to {}".format(headers, body))

if __name__ == "__main__":
    # Parse command-line arguments to configure server IP and port
    parser = argparse.ArgumentParser(prog='Backend', description='', epilog='Beckend daemon')
    parser.add_argument('--server-ip', default='0.0.0.0')
    parser.add_argument('--server-port', type=int, default=PORT)
 
    args = parser.parse_args()
    ip = args.server_ip
    port = args.server_port

    # Prepare and launch the RESTful application
    app.prepare_address(ip, port)
    app.run()