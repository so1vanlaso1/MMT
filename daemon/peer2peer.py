import json
import time
import argparse
import threading
from daemon.weaprous import WeApRous
import urllib.request
import urllib.error
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
class peer2peer:

    def __init__(self, tracker_url, port, peer_name="anonymous"):
        self.tracker_url = tracker_url
        self.port = port
        self.peer_name = peer_name
        self.ip = '127.0.0.1'
        self.peer_id = f"{self.ip}:{self.port}"\
        
        self.app = WeApRous()
        self.connected_peers = {}
        self.messages = []
        self.setup_own_routes()
        self.running = True 
        self.heartbeat_thread = None
        self.cookies = {}

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


        # Register with the tracker
    def get_peers_list(self):
        try:
            if self.cookies and self.cookies.get("auth", "") == "true":
                print("Adding auth cookie to request headers for get_peers_list")
                req_headers = {
                    "Content-Type": "application/json",
                    "Cookie": f"auth={self.cookies.get('auth', '')}"
                }
            req = urllib.request.Request(
                method="GET",
                url=f"{self.tracker_url}/get-list",
                headers=req_headers if self.cookies and self.cookies.get("auth", "") == "true" else {"Content-Type": "application/json"}
            )

            with urllib.request.urlopen(req, timeout=5) as response:
                if response.getcode() == 200:
                    #print("Getting peers list from tracker")

                    resp_data = response.read().decode('utf-8')
                    # print(f"Response data: {resp_data}") # Optional: Comment out to reduce noise
                    resp_json = json.loads(resp_data)
                    
                    # --- FIX START ---
                    peers_list = resp_json.get("peers", [])
                    
                    # Convert the list to a dictionary: { "peer_id": {data...} }
                    new_peers_dict = {}
                    for p in peers_list:
                        pid = p.get('peer_id')
                        # Ensure we don't add ourselves to our own connection list
                        if pid and pid != self.peer_id:
                            new_peers_dict[pid] = p
                            
                    self.connected_peers = new_peers_dict
                    # --- FIX END ---
                    
                    #print(f"Connected peers: {self.connected_peers}")
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
            self.get_peers_list()
            self.ping_tracker()
            time.sleep(5)  # Check every 30 seconds


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

                if peer_id and peer_ip and peer_port:
                    self.connected_peers[peer_id] = {
                        "ip": peer_ip,
                        "port": peer_port,
                        "name": peer_name
                    }
                    response = {
                        "status": "success",
                        "message": f"Connected to peer {peer_id}",
                        "peer_id": peer_id,
                        "name": peer_name
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

                if from_peer and message:
                    self.messages.append({
                        "type": "broadcast",
                        "from": from_peer,
                        "from_name": from_name,
                        "message": message,
                        "timestamp": timestamp
                    })
                    response = {
                        "status": "success",
                        "message": f"Message received from {from_peer}"
                    }
                    print(f"Broadcast message received from {from_peer}: {message}")
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


    def connect_to_peers(self, peer_ip, peer_port, peer_id):
        try:
            payload = {
                "peer_id": self.peer_id,
                "ip": self.ip,
                "port": self.port,
                "name": self.peer_name
            }
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(
                method="POST",
                url=f"http://{peer_ip}:{peer_port}/connect-peer",
                data=data,
                headers={"Content-Type": "application/json"}
            )

            with urllib.request.urlopen(req, timeout=5) as response:
                if response.getcode() == 200:
                    resp_data = response.read().decode('utf-8')
                    resp_json = json.loads(resp_data)
                    print(f"Connected to peer {peer_id}: {resp_json}")
        except Exception as e:
            print(f"Error connecting to peer {peer_id}: {e}")
    
    def send_broadcast_message(self, message):
        timestamp = time.time()
        if not self.connected_peers:
            print("No connected peers to send the broadcast message.")
            return
        for peer_id, peer_info in self.connected_peers.items():
            try:
                payload = {
                    "from_peer": self.peer_id,
                    "from_name": self.peer_name,
                    "message": message,
                    "timestamp": timestamp
                }
                data = json.dumps(payload).encode('utf-8')
                req = urllib.request.Request(
                    method="POST",
                    url=f"http://{peer_info['ip']}:{peer_info['port']}/broadcast-peer",
                    data=data,
                    headers={"Content-Type": "application/json"}
                )

                with urllib.request.urlopen(req, timeout=5) as response:
                    if response.getcode() == 200:
                        resp_data = response.read().decode('utf-8')
                        resp_json = json.loads(resp_data)
                        print(f"Broadcast message sent to {peer_id}: {resp_json}")
            except Exception as e:
                print(f"Error sending broadcast message to {peer_id}: {e}")

    def send_direct_message(self, peer_id, message):
        timestamp = time.time()
        peer_info = self.connected_peers.get(peer_id, None)
        if not peer_info:
            print(f"Peer {peer_id} not found in connected peers.")
            return
        try:
            payload = {
                "from_peer": self.peer_id,
                "from_name": self.peer_name,
                "message": message,
                "timestamp": timestamp
            }
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(
                method="POST",
                url=f"http://{peer_info['ip']}:{peer_info['port']}/send-peer",
                data=data,
                headers={"Content-Type": "application/json"}
            )

            with urllib.request.urlopen(req, timeout=5) as response:
                if response.getcode() == 200:
                    resp_data = response.read().decode('utf-8')
                    resp_json = json.loads(resp_data)
                    print(f"Direct message sent to {peer_id}: {resp_json}")
        except Exception as e:
            print(f"Error sending direct message to {peer_id}: {e}")

    def find_all_peers_and_connect(self):
        all_peers = self.get_peers_list()
        if not all_peers:
            print("No peers found from tracker.")
            return
        for peer in all_peers:
            peer_id = peer.get("peer_id", "")
            peer_ip = peer.get("ip", "")
            peer_port = peer.get("port", 0)
            if peer_id != self.peer_id:
                self.connect_to_peers(peer_ip, peer_port, peer_id)
    
    def find_some_peers_and_connect(self, peer_name=""):
        """Connect to specific peer(s) by name"""
        self.connected_peers = {}
        all_peers = self.get_peers_list()
        if not all_peers:
            print("No peers found from tracker.")
            return

        found_any = False
        for peer_id, peer_info in self.connected_peers.items():
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

    def list_peers(self):
        """List connected peers"""
        if not self.connected_peers:
            #print("\nNo connected peers.")
            pass
        else:
            pass
            #print("\nConnected peers ({})".format(len(self.connected_peers)))
            #for peer_id, info in self.connected_peers.items():
                #print("  - {} ({})".format(info.get('name', 'Unknown'), peer_id))
        
        

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
                print("Adding auth cookie to request headers for ping")
                req_headers = {
                    "Content-Type": "application/json",
                    "Cookie": f"auth={self.cookies.get('auth', '')}"
                }
            req = urllib.request.Request(
                method="POST",
                url=f"{self.tracker_url}/ping",
                headers=req_headers if self.cookies and self.cookies.get("auth", "") == "true" else {"Content-Type": "application/json"},
                data=body
            )
            print(req.data)

            self.find_all_peers_and_connect()

            with urllib.request.urlopen(req, timeout=5) as response:
                if response.getcode() == 200:
                    pass
                    #print("Pinged tracker successfully.")
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
          # Give some time for the server to start

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="P2P Peer")
    parser.add_argument('--tracker-url', type=str, required=True, help='Tracker server URL')
    parser.add_argument('--port', type=int, required=True, help='Port to run the peer server on')
    parser.add_argument('--peer-name', type=str, default='anonymous', help='Name of the peer')

    args = parser.parse_args()

    peer = peer2peer(tracker_url=args.tracker_url, port=args.port, peer_name=args.peer_name)
    peer.start()
