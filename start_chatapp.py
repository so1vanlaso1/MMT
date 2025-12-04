# import json
# import socket
# import argparse
# import threading
# import time
# from datetime import datetime

# from daemon.weaprous import WeApRous

# PORT = 8000  # Default port

# active_peers = {}
# channel_messages = {}
# peer_id = {}

# app = WeApRous()

# @app.route('/login', methods=['POST'])
# def login(headers="guest", body="anonymous"):
#     """
#     Handle user login via POST request.

#     This route simulates a login process and prints the provided headers and body
#     to the console.

#     :param headers (str): The request headers or user identifier.
#     :param body (str): The request body or login payload.
#     """
#     try:
#         data=json.loads(body) if body else {}
#         username = data.get("username", "guest")
#         password = data.get("password", "anonymous")
#         print("[SampleApp] Logging in {} to {}".format(headers, body))

#         if username and password:
#             response = {
#                 "status": "success",
#                 "message": "User {} logged in successfully.".format(username),
#                 "userid": username,
#                 "timestamp": datetime.now().isoformat()
#             }
#         else:
#             response = {
#                 "status": "error",
#                 "message": "Invalid username or password."
#             }
#         return json.dumps(response)
#     except Exception as e:
#         print(f"[SampleApp] Error in login: {e}")
#         return json.dumps({
#             "status": "error",
#             "message": "An error occurred during login."
#         })

# @app.route('/submit-info', methods=['POST'])
# def submit_peer_info(headers="", body=""):
#     """
#     Handle peer information submission via POST request.

#     This route processes the submitted peer information and stores it in the
#     active_peers dictionary.

#     :param headers (str): The request headers or user identifier.
#     :param body (str): The request body or peer information payload.
#     """
#     try:
#         data = json.loads(body) if body else {}
#         peer_id = data.get("peer_id")
#         peer_ip = data.get("ip")
#         peer_port = data.get("port")

#         if peer_id and peer_ip and peer_port:
#             active_peers[peer_id] = {
#                 "ip": peer_ip,
#                 "port": peer_port,
#                 "last_active": time.time()
#             }
#             print(f"[SampleApp] Registered peer {peer_id} at {peer_ip}:{peer_port}")

#             response = {
#                 "status": "success",
#                 "message": f"Peer {peer_id} registered successfully.",
#                 "peer_id": peer_id
#             }

#         else:
#             response = {
#                 "status": "error",
#                 "message": "Missing peer information."
#             }
#         return json.dumps(response)
#     except Exception as e:
#         print(f"[SampleApp] Error in submit-info: {e}")
#         return json.dumps({
#             "status": "error",
#             "message": "An error occurred while submitting peer information."
#         })


# @app.route('/get-list', methods=['GET'])
# def get_peer_list(headers="", body=""):
#     """
#     Handle request to get the list of active peers via GET request.

#     This route returns the list of currently active peers.

#     :param headers (str): The request headers or user identifier.
#     :param body (str): The request body (not used in this route).
#     """
#     try:
#         current_time = time.time()
#         expired_peers = [peer for peer, info in active_peers.items() if current_time - info["last_active"] > 300]
#         for peer in expired_peers:
#             del active_peers[peer]
#             print(f"[SampleApp] Removed expired peer {peer}")
#         peer_list = []
#         for peer_id, info in active_peers.items():
#             peer_list.append({
#                 "peer_id": peer_id,
#                 "ip": info["ip"],
#                 "port": info["port"]
#             })
        
#         response = {
#             "status": "success",
#             "peers": peer_list,
#             "count": len(peer_list)
#         }
#         print(f"[SampleApp] Returning peer list with {len(peer_list)} peers")
#         return json.dumps(response)
#     except Exception as e:
#         print(f"[SampleApp] Error in get-list: {e}")
#         return json.dumps({
#             "status": "error",
#             "message": "An error occurred while retrieving the peer list."
#         })


# @app.route('/connect-peer', methods=['POST'])
# def connect_peer(headers="guest", body="anonymous"):
#     """
#     Handle request to connect to a specific peer via POST request.

#     This route simulates connecting to a specified peer.

#     :param headers (str): The request headers or user identifier.
#     :param body (str): The request body containing the peer ID to connect to.
#     """
#     try:
#         data = json.loads(body) if body else {}
#         from_peer = data.get("from_peer")
#         to_peer = data.get("to_peer")

#         if from_peer in active_peers and to_peer in active_peers:
#             target_info = active_peers[to_peer]
#             response = {
                
#             }

       

# if __name__ == "__main__":

#     parser = argparse.ArgumentParser(prog='Backend', description='', epilog='Beckend daemon')
#     parser.add_argument('--server-ip', default='127.0.0.1')
#     parser.add_argument('--server-port', type=int, default=PORT)
#     args = parser.parse_args()
#     ip = args.server_ip
#     port = args.server_port
#     app.prepare_address(ip, port)
#     app.run()

import json
import time
import argparse
from daemon.weaprous import WeApRous

app = WeApRous()

peers = {}
# peers = {
#     "127.0.0.1:5001": {
#         'ip': '127.0.0.1',
#         'port': 5001,
#         'peer_id': '127.0.0.1:5001',
#         'last_seen': 169xxxxxxx.x   # timestamp (float)
#     },
#     "127.0.0.1:5002": {
#         'ip': '127.0.0.1',
#         'port': 5002,
#         'peer_id': '127.0.0.1:5002',
#         'last_seen': 169xxxxxxx.x
#     }
# }


@app.route('/submit-info', methods=['POST'])
def submit_peer_info(headers="", body=""):
    try:
        data = json.loads(body) if body else {}
        peer_ip = data.get("ip")
        peer_port = data.get("port")
        peer_name = data.get("name", "unknown")
        timestamp = time.time()
        peer_id = f"{peer_ip}:{peer_port}"
        if not peer_id or not peer_ip or not peer_port:
            return_body = json.dumps({
                "status": "error",
                "message": "Missing peer information."
            })
            print(f"[SampleApp] Missing peer information: {return_body}")
            return (
                "HTTP/1.1 400 Bad Request\r\n"
                "Content-Type: application/json\r\n"
                "\r\n"
                "{}".format(len(return_body), return_body)
            )
        if peer_id and peer_ip and peer_port:
            peers[peer_id] = {
                "ip": peer_ip,
                "port": peer_port,
                "name": peer_name,
                "last_seen": timestamp
            }
            print(f"[SampleApp] Registered peer {peer_id} at {peer_ip}:{peer_port}")

            response = json.dumps({
                "status": "success",
                "message": f"Peer {peer_id} registered successfully.",
                "peer_id": peer_id
            })
            print(f"[SampleApp] Registered peer successfully: {response}")
            return(
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: application/json\r\n"
                "\r\n"
                "{}".format(len(response), response)
            )
        else:
            response = json.dumps({
                "status": "error",
                "message": "Missing peer information."
            })
            print(f"[SampleApp] Missing peer information: {response}")
            return(
                "HTTP/1.1 400 Bad Request\r\n"
                "Content-Type: application/json\r\n"
                "\r\n"
                "{}".format(len(response), response)
            )
    except Exception as e:
        print(f"[SampleApp] Error in submit-info: {e}")
        return json.dumps({
            "status": "error",
            "message": "An error occurred while submitting peer information."
        })

@app.route('/get-list', methods=['GET'])
def get_peer_list(headers="", body=""):
    try:
        current_time = time.time()
        expired_peers = [peer for peer, info in peers.items() if current_time - info["last_seen"] > 30000]
        for peer in expired_peers:
            del peers[peer]
            print(f"[SampleApp] Removed expired peer {peer}")
        peer_list = []
        for peer_id, info in peers.items():
            peer_list.append({
                "peer_id": peer_id,
                "ip": info["ip"],
                "port": info["port"],
                "name": info["name"]
            })
        
        response = json.dumps({
            "status": "success",
            "peers": peer_list,
            "count": len(peer_list)
        })
        print(f"[SampleApp] Returning peer list with {len(peer_list)} peers")
        return(
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: application/json\r\n"
            "Content-Length: {}\r\n"
            "\r\n"
            "{}".format(len(response), response)
        )
    except Exception as e:
        print(f"[SampleApp] Error in get-list: {e}")
        response = json.dumps({
            "status": "error",
            "message": "An error occurred while retrieving the peer list."
        })
        return(
            "HTTP/1.1 500 Internal Server Error\r\n"
            "Content-Type: application/json\r\n"
            "\r\n"
            "{}".format(len(response), response)
        )
    
@app.route('/remove-peer', methods=['POST'])
def remove_peer(headers="", body=""):
    try:
        data = json.loads(body) if body else {}
        peer_id = data.get("peer_id")
        if peer_id is None:
            response = json.dumps({
                "status": "error",
                "message": "peer_id is required."
            })
            return(
                "HTTP/1.1 400 Bad Request\r\n"
                "Content-Type: application/json\r\n"
                "\r\n"
                "{}".format(len(response), response)
            )
        
        if peer_id in peers:
            del peers[peer_id]
            print(f"[SampleApp] Removed peer {peer_id}")

            response = json.dumps({
                "status": "success",
                "message": f"Peer {peer_id} removed successfully."
            })
            return(
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: application/json\r\n"
                "\r\n"
                "{}".format(len(response), response)
            )
        else:
            response = json.dumps({
                "status": "error",
                "message": f"Peer {peer_id} not found."
            })
            
            return(
                "HTTP/1.1 404 Not Found\r\n"
                "Content-Type: application/json\r\n"
                "\r\n"
                "{}".format(len(response), response)
            )
    except Exception as e:
        print(f"[SampleApp] Error in remove-peer: {e}")
        response = json.dumps({
            "status": "error",
            "message": "An error occurred while removing the peer."
        })
        return(
            "HTTP/1.1 500 Internal Server Error\r\n"
            "Content-Type: application/json\r\n"
            "\r\n"
            "{}".format(len(response), response)
        )


@app.route('/ping', methods=['POST'])
def ping(headers="", body=""):
    try:
        data = json.loads(body) if body else {}
        peer_id = data.get("peer_id")
        print(f"[SampleApp] Received ping from {peer_id}")
        timestamp = time.time()
        if peer_id in peers:
            peers[peer_id]['last_seen'] = timestamp
            response = json.dumps({
                "status": "success",
                "message": f"Keep alive for {peer_id}."
            })
            return(
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: application/json\r\n"
                "\r\n"
                "{}".format(len(response), response)
            )
        else:
            response = json.dumps({
                "status": "error",
                "message": f"Peer {peer_id} not found."
            })
            return(
                "HTTP/1.1 404 Not Found\r\n"
                "Content-Type: application/json\r\n"
                "\r\n"
                "{}".format(len(response), response)
            )
    except Exception as e:
        print(f"[SampleApp] Error in ping: {e}")
        response = json.dumps({
            "status": "error",
            "message": "An error occurred while processing the ping."
        })
        return(
            "HTTP/1.1 500 Internal Server Error\r\n"
            "Content-Type: application/json\r\n"
            "\r\n"
            "{}".format(len(response), response)
        )
if __name__ == "__main__":

    parser = argparse.ArgumentParser(prog='Tracker server', description='', epilog='Beckend daemon')
    parser.add_argument('--server-ip', default='0.0.0.0')
    parser.add_argument('--server-port', type=int, default=8000)
    args = parser.parse_args()

    app.prepare_address(args.server_ip, args.server_port)
    app.run()