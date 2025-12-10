import json
import time
import argparse
import threading
from daemon.weaprous import WeApRous
import urllib.request
import urllib.error
import socket
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
class peer2peer:

    def __init__(self, tracker_url, port, peer_name="anonymous"):
        self.tracker_url = tracker_url
        self.port = port
        self.peer_name = peer_name
        self.ip = self.get_local_ip()
        self.peer_id = f"{self.ip}:{self.port}"
        
        self.app = WeApRous()
        self.connected_peers = {"general": {}, "tech": {}, "random": {}}
        self.messages = []
        self.setup_own_routes()
        self.running = True 
        self.heartbeat_thread = None
        self.cookies = {}

        self.peers_lock = threading.Lock()
        self.messages_lock = threading.Lock()

    def get_local_ip(self):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                return s.getsockname()[0]
        except Exception as e:
            print(f"Falling back to localhost for IP: {e}")
            return "127.0.0.1"

    def register_tracker(self):
        try:
            print(f"Registering with tracker at {self.tracker_url}")
            payload = {
                "ip": self.ip,
                "port": self.port,
                "name": self.peer_name
            }
            print(f"Payload: {payload}")
            data = json.dumps(payload).encode('utf-8')
            if self.cookies and self.cookies.get("auth", "") == "true":
                print("Adding auth cookie to request headers")
                req_headers = {
                    "Content-Type": "application/json",
                    "Cookie": f"auth={self.cookies.get('auth', '')}"
                }
            req = urllib.request.Request(
                method="POST",
                url=f"{self.tracker_url}/submit-info",
                data=data,
                headers=req_headers if self.cookies and self.cookies.get("auth", "") == "true" else {"Content-Type": "application/json"}
            )
            print(f"Request: {req.full_url}, Data: {data}")

            with urllib.request.urlopen(req, timeout=5) as response:
                if response.getcode() == 200:
                    resp_data = response.read().decode('utf-8')
                    resp_json = json.loads(resp_data)
                    print(f"Registered with tracker: {resp_json}")
                    return True
        except Exception as e:
            print(f"Error registering with tracker: {e}") 


    def get_peers_list(self, channel="general"):
        try:
            if self.cookies and self.cookies.get("auth", "") == "true":
                req_headers = {
                    "Content-Type": "application/json",
                    "Cookie": f"auth={self.cookies.get('auth', '')}"
                }
            else:
                req_headers = {"Content-Type": "application/json"}
                
            if channel == "general":
                req = urllib.request.Request(
                    method="GET",
                    url=f"{self.tracker_url}/get-list",
                    headers=req_headers
                )
            else:
                req = urllib.request.Request(
                    method="POST",
                    url=f"{self.tracker_url}/get-list",
                    data=json.dumps({"channel": channel}).encode('utf-8'),
                    headers=req_headers
                )

            with urllib.request.urlopen(req, timeout=5) as response:
                if response.getcode() == 200:
                    resp_data = response.read().decode('utf-8')
                    resp_json = json.loads(resp_data)
                    
                    peers_list = resp_json.get("peers", [])

                    #peers_list = [{"peer_id": "127.0.0.1:9001", "ip": "127.0.0.1", "port": 9001, "name": "peer1"},
                    #              {"peer_id": "127.0.0.1:9002", "ip": "127.0.0.1", "port": 9002, "name": "peer2"}]
                    
                    # Update the specific channel's peer list
                    new_peers_dict = {}
                    for p in peers_list:
                        pid = p.get('peer_id')
                        if pid and pid != self.peer_id:
                            new_peers_dict[pid] = p
                    
                    # Update only the specific channel
                    with self.peers_lock:
                        self.connected_peers[channel] = new_peers_dict
                    print(f"Retrieved {len(new_peers_dict)} peers from channel '{channel}'")
                    
        except Exception as e:
            print(f"Error getting peers list from tracker: {e}")

    def unregister_from_tracker(self):
        try:
            payload = {
                "peer_id": self.peer_id
            }
            data = json.dumps(payload).encode('utf-8')
            if self.cookies and self.cookies.get("auth", "") == "true":
                print("Adding auth cookie to request headers for unregister")
                req_headers = {
                    "Content-Type": "application/json",
                    "Cookie": f"auth={self.cookies.get('auth', '')}"
                }
            req = urllib.request.Request(
                method="POST",
                url=f"{self.tracker_url}/remove-peer",
                data=data,
                headers=req_headers if self.cookies and self.cookies.get("auth", "") == "true" else {"Content-Type": "application/json"}
            )

            with urllib.request.urlopen(req, timeout=5) as response:
                if response.getcode() == 200:
                    resp_data = response.read().decode('utf-8')
                    resp_json = json.loads(resp_data)
                    print(f"Unregistered from tracker: {resp_json}")
        except Exception as e:
            print(f"Error unregistering from tracker: {e}")
    
    def check_alive(self):
        while self.running:
            # Refresh peers for all joined channels
            with self.peers_lock:
                channels = list(self.connected_peers.keys())
            for channel in channels:
                self.get_peers_list(channel)
            self.ping_tracker()
            time.sleep(5)


    def setup_own_routes(self):
        # Setup own routes for P2P communication
        @self.app.route('/connect-peer', methods=['POST'])
        def connect_peer(headers="", body=""):
            try:
                if body:
                    data=json.loads(body)
                else:
                    data={}
                peer_id = data.get("peer_id", "")
                peer_ip = data.get("ip", "")
                peer_port = data.get("port", 0)
                peer_name = data.get("name", "anonymous")
                channel = data.get("channel", "general")

                if peer_id and peer_ip and peer_port:
                    # Add peer to the specific channel
                    with self.peers_lock:
                        if channel not in self.connected_peers:
                            self.connected_peers[channel] = {}
                        
                        self.connected_peers[channel][peer_id] = {
                            "ip": peer_ip,
                            "port": peer_port,
                            "name": peer_name
                        }
                    response = {
                        "status": "success",
                        "message": f"Connected to peer {peer_id} in channel {channel}",
                        "peer_id": peer_id,
                        "name": peer_name,
                        "channel": channel
                    }
                    return(
                        "HTTP/1.1 200 OK\r\n"
                        "Content-Type: application/json\r\n"
                        "Content-Length: {}\r\n"
                        "\r\n"
                        "{}".format(
                            len(json.dumps(response)),
                            json.dumps(response)
                        )
                    )
            except Exception as e:
                print(f"Error connecting to peer: {e}")
                response = {
                    "status": "error",
                    "message": "Failed to connect to peer"
                }
                return(
                    "HTTP/1.1 500 Internal Server Error\r\n"
                    "Content-Type: application/json\r\n"
                    "Content-Length: {}\r\n"
                    "\r\n"
                    "{}".format(
                        len(json.dumps(response)),
                        json.dumps(response)
                    )
                )
            
        @self.app.route('/broadcast-peer', methods=['POST'])
        def broad_cast_received(headers="", body=""):
            try:
                if body:
                    data=json.loads(body)
                    print(data)
                else:
                    data={}
                from_peer = data.get("from_peer", "")
                from_name = data.get("from_name", "anonymous")
                message = data.get("message", "")
                timestamp = data.get("timestamp", time.time())
                channel = data.get("channel", "general")

                if from_peer and message:
                    with self.messages_lock:
                        self.messages.append({
                            "type": "broadcast",
                            "from": from_peer,
                            "from_name": from_name,
                            "message": message,
                            "timestamp": timestamp,
                            "channel": channel
                        })
                    response = {
                        "status": "success",
                        "message": f"Message received from {from_peer}"
                    }
                    print(f"{channel} message received from {from_peer}: {message}")
                    return(
                        "HTTP/1.1 200 OK\r\n"
                        "Content-Type: application/json\r\n"
                        "Content-Length: {}\r\n"
                        "\r\n"
                        "{}".format(
                            len(json.dumps(response)),
                            json.dumps(response)
                        )
                    )
            except Exception as e:
                print(f"Error receiving broadcast message: {e}")
                response = {
                    "status": "error",
                    "message": "Failed to receive message"
                }
                return(
                    "HTTP/1.1 500 Internal Server Error\r\n"
                    "Content-Type: application/json\r\n"
                    "Content-Length: {}\r\n"
                    "\r\n"
                    "{}".format(
                        len(json.dumps(response)),
                        json.dumps(response)
                    )
                )
            
        @self.app.route('/send-peer', methods=['POST'])
        def received_direct_messages(headers="", body=""):
            try:
                data = {}
                if body:
                    data=json.loads(body)
                    print("this is the " + str(data))
                else:
                    data={}

                from_peer = data.get("from_peer", "")
                from_name = data.get("from_name", "anonymous")
                message = data.get("message", "")
                timestamp = data.get("timestamp", time.time())

                print(f"Direct message received from {from_peer}: {message}")
                
                with self.messages_lock:
                    self.messages.append({
                                "type": "direct",
                                "from": from_peer,
                                "from_name": from_name,
                                "message": message,
                                "timestamp": timestamp
                            })
                        
                response = {
                        "status": "success",
                        "message": f"Direct message received from {from_peer}"
                }

                return(
                    "HTTP/1.1 200 OK\r\n"
                    "Content-Type: application/json\r\n"
                    "Content-Length: {}\r\n"
                    "\r\n"
                    "{}".format(
                        len(json.dumps(response)),
                        json.dumps(response)
                    )
                )
            except Exception as e:
                print(f"Error retrieving direct messages: {e}")
                response = {
                    "status": "error",
                    "message": "Failed to retrieve messages"
                }
                return(
                    "HTTP/1.1 500 Internal Server Error\r\n"
                    "Content-Type: application/json\r\n"
                    "Content-Length: {}\r\n"
                    "\r\n"
                    "{}".format(
                        len(json.dumps(response)),
                        json.dumps(response)
                    )
                )


    

    def connect_to_peers(self, peer_ip, peer_port, peer_id, channel="general"):
        try:
            payload = {
                "peer_id": self.peer_id,
                "ip": self.ip,
                "port": self.port,
                "name": self.peer_name,
                "channel": channel
            }
            if self.cookies and self.cookies.get("auth", "") == "true":
                req_headers = {
                    "Content-Type": "application/json",
                    "Cookie": f"auth={self.cookies.get('auth', '')}"
                }
            else:
                req_headers = {"Content-Type": "application/json"}  
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(
                method="POST",
                url=f"http://{peer_ip}:{peer_port}/connect-peer",
                data=data,
                headers=req_headers
            )

            with urllib.request.urlopen(req, timeout=5) as response:
                if response.getcode() == 200:
                    resp_data = response.read().decode('utf-8')
                    resp_json = json.loads(resp_data)
                    print(f"Connected to peer {peer_id} in channel '{channel}': {resp_json}")
        except Exception as e:
            pass  # Silently ignore connection errors - peer might not be ready
    
    def send_broadcast_message(self, message, channel="general"):
        timestamp = time.time()
        
        # Get peers from the specific channel
        with self.peers_lock:
            channel_peers = self.connected_peers.get(channel, {}).copy()
        
        if not channel_peers:
            print(f"No connected peers in channel '{channel}' to send the broadcast message.")
            return
            
        for peer_id, peer_info in channel_peers.items():
            try:
                payload = {
                    "from_peer": self.peer_id,
                    "from_name": self.peer_name,
                    "message": message,
                    "timestamp": timestamp,
                    "channel": channel
                }
                if self.cookies and self.cookies.get("auth", "") == "true":
                    req_headers = {
                        "Content-Type": "application/json",
                        "Cookie": f"auth={self.cookies.get('auth', '')}"
                    }
                else:
                    req_headers = {"Content-Type": "application/json"}
                data = json.dumps(payload).encode('utf-8')
                req = urllib.request.Request(
                    method="POST",
                    url=f"http://{peer_info['ip']}:{peer_info['port']}/broadcast-peer",
                    data=data,
                    headers=req_headers
                )

                with urllib.request.urlopen(req, timeout=5) as response:
                    if response.getcode() == 200:
                        resp_data = response.read().decode('utf-8')
                        resp_json = json.loads(resp_data)
                        print(f"[{channel}] Broadcast message sent to {peer_id}: {resp_json}")
            except Exception as e:
                print(f"Error sending broadcast message to {peer_id} in channel '{channel}': {e}")

    def send_direct_message(self, peer_id, message):
        timestamp = time.time()
        
        # Search for peer in general channel only
        with self.peers_lock:
            peer_info = self.connected_peers["general"].get(peer_id, None)
        
        if not peer_info:
            print(f"Peer {peer_id} not found in general channel.")
            return
            
        try:
            payload = {
                "from_peer": self.peer_id,
                "from_name": self.peer_name,
                "message": message,
                "timestamp": timestamp
            }
            if self.cookies and self.cookies.get("auth", "") == "true":
                req_headers = {
                    "Content-Type": "application/json",
                    "Cookie": f"auth={self.cookies.get('auth', '')}"
                }
            else:
                req_headers = {"Content-Type": "application/json"}
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(
                method="POST",
                url=f"http://{peer_info['ip']}:{peer_info['port']}/send-peer",
                data=data,
                headers=req_headers
            )

            with urllib.request.urlopen(req, timeout=5) as response:
                if response.getcode() == 200:
                    resp_data = response.read().decode('utf-8')
                    resp_json = json.loads(resp_data)
                    print(f"Direct message sent to {peer_id}: {resp_json}")
        except Exception as e:
            print(f"Error sending direct message to {peer_id}: {e}")

    def find_all_peers_and_connect(self, channel="general"):
        self.get_peers_list(channel)
        with self.peers_lock:
            channel_peers = self.connected_peers.get(channel, {}).copy()
        
        if not channel_peers:
            print(f"No peers found in channel '{channel}' from tracker.")
            return
            
        for peer_id, peer_info in channel_peers.items():
            peer_ip = peer_info.get("ip", "")
            peer_port = peer_info.get("port", 0)
            if peer_id != self.peer_id:
                self.connect_to_peers(peer_ip, peer_port, peer_id, channel)
    
    def join_channel(self, channel_name):
        """Join a specific channel"""
        try:
            payload = {
                "peer_id": self.peer_id,
                "channel_name": channel_name
            }
            data = json.dumps(payload).encode('utf-8')
            
            req_headers = {"Content-Type": "application/json"}
            if self.cookies and self.cookies.get("auth", "") == "true":
                req_headers["Cookie"] = f"auth={self.cookies.get('auth', '')}"
            
            req = urllib.request.Request(
                method="POST",
                url=f"{self.tracker_url}/add-peer-to-channel",
                data=data,
                headers=req_headers
            )
            
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.getcode() == 200:
                    resp_data = response.read().decode('utf-8')
                    resp_json = json.loads(resp_data)
                    
                    if resp_json.get("status") == "success":
                        print(f"Joined channel: {channel_name}")
                        # Discover and connect to peers in this channel
                        self.find_all_peers_and_connect(channel_name)
                        return True
                    else:
                        print(f"Failed to join channel: {resp_json.get('message')}")
                        return False
        except Exception as e:
            print(f"Error joining channel {channel_name}: {e}")
            return False

    def find_some_peers_and_connect(self, peer_name=""):
        """Connect to specific peer(s) by name"""
        self.connected_peers = {}
        all_peers = self.get_peers_list()
        if not all_peers:
            print("No peers found from tracker.")
            return

        found_any = False
        with self.peers_lock:
            peers_copy = self.connected_peers.copy()
        for peer_id, peer_info in peers_copy.items():
            # Check if this peer matches the requested name
            if peer_info.get("name", "") == peer_name:
                peer_ip = peer_info.get("ip", "")
                peer_port = peer_info.get("port", 0)
                
                # Don't connect to ourselves
                if peer_id != self.peer_id:
                    print(f"Connecting to peer '{peer_name}' at {peer_id}")
                    self.connect_to_peers(peer_ip, peer_port, peer_id)
                found_any = True
    
        if not found_any:
            print(f"No peer found with name '{peer_name}'")

    def list_peers(self, channel="general"):
        """List connected peers in a specific channel"""
        with self.peers_lock:
            channel_peers = self.connected_peers.get(channel, {}).copy()
        
        if not channel_peers:
            print(f"\nNo connected peers in channel '{channel}'.")
        else:
            print(f"\nConnected peers in '{channel}' ({len(channel_peers)}):")
            for peer_id, info in channel_peers.items():
                print(f"  - {info.get('name', 'Unknown')} ({peer_id})")
        

    def run_console(self):
        """Run interactive console for user input"""
        print("\n" + "=" * 60)
        print("Peer Console - Type /help for commands")
        print("=" * 60)
        
        while self.running:
            try:
                user_input = input(">>")
                
                if not user_input.strip():
                    continue
                
                # if user_input == '/help':
                #     self.print_help()
                
                elif user_input == '/peers':
                    self.list_peers()
                
                elif user_input == '/discover':
                    print("Discovering peers...")
                    self.find_all_peers_and_connect()
                
                elif user_input.startswith('/direct '):
                    parts = user_input.split(' ', 2)
                    if len(parts) >= 3:
                        peer_id = parts[1]
                        message = parts[2]
                        print(f"Sending direct message to {peer_id}: {message}")
                        self.send_direct_message(peer_id, message)
                    else:
                        print("Usage: /direct <peer_id> <message>")
                
                elif user_input == '/quit':
                    print("Shutting down...")
                    self.running = False
                    break
                
                else:
                    # Broadcast message
                    self.send_broadcast_message(user_input)
                
            except KeyboardInterrupt:
                print("\n\nShutting down...")
                self.running = False
                break
            except EOFError:
                self.running = False
                break
                
    def ping_tracker(self):
        try:
            body = json.dumps({"peer_id": self.peer_id}).encode('utf-8')
            if self.cookies and self.cookies.get("auth", "") == "true":
                req_headers = {
                    "Content-Type": "application/json",
                    "Cookie": f"auth={self.cookies.get('auth', '')}"
                }
            else:
                req_headers = {"Content-Type": "application/json"}
                
            req = urllib.request.Request(
                method="POST",
                url=f"{self.tracker_url}/ping",
                headers=req_headers,
                data=body
            )

            self.find_all_peers_and_connect()

            with urllib.request.urlopen(req, timeout=5) as response:
                if response.getcode() == 200:
                    pass
        except Exception as e:
            print(f"Error pinging tracker: {e}")

    def start(self):
        if not self.register_tracker():
            print("Failed to register with tracker. Exiting.")
            return

        self.check_alive_thread = threading.Thread(target=self.check_alive)
        self.check_alive_thread.daemon = True
        self.check_alive_thread.start()
        
        self.find_all_peers_and_connect()

        def run_app():
            self.app.prepare_address('0.0.0.0', self.port)
            self.app.run()

        self.app_thread = threading.Thread(target=run_app)
        self.app_thread.daemon = True
        self.app_thread.start()

        time.sleep(1)

        try:
            self.run_console()
        finally:
            self.unregister_from_tracker()
            self.running = False
            print("Peer shut down.")
            time.sleep(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="P2P Peer")
    parser.add_argument('--tracker-url', type=str, required=True, help='Tracker server URL')
    parser.add_argument('--port', type=int, required=True, help='Port to run the peer server on')
    parser.add_argument('--peer-name', type=str, default='anonymous', help='Name of the peer')

    args = parser.parse_args()

    peer = peer2peer(tracker_url=args.tracker_url, port=args.port, peer_name=args.peer_name)
    peer.start()