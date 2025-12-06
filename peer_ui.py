import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import json
import time
import urllib.request
import urllib.error
import http.cookiejar
from daemon.peer2peer import peer2peer

class PeerChatUI:
    def __init__(self, root):
        self.root = root
        self.root.title("P2P Chat Client")
        self.root.geometry("1000x1000")
        
        self.peer = None
        self.running = False
        self.authenticated = False
        self.username = None
        self.cookies = {}
        
        # Setup UI
        self.setup_login_frame()
        self.setup_connection_frame()
        self.setup_chat_frame()
        self.setup_peers_frame()
        
        # Initially hide connection/chat frames until logged in
        self.connection_frame.pack_forget()
        self.chat_frame.pack_forget()
        self.peers_frame.pack_forget()
        
    def setup_login_frame(self):
        """Login authentication frame"""
        self.login_frame = ttk.LabelFrame(self.root, text="Login", padding=20)
        self.login_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Tracker URL for login
        ttk.Label(self.login_frame, text="Tracker URL:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.login_tracker_url = tk.StringVar(value="http://127.0.0.1:8000")
        ttk.Entry(self.login_frame, textvariable=self.login_tracker_url, width=40).grid(row=0, column=1, padx=5, pady=5)
        
        # Username
        ttk.Label(self.login_frame, text="Username:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.login_username = tk.StringVar()
        ttk.Entry(self.login_frame, textvariable=self.login_username, width=40).grid(row=1, column=1, padx=5, pady=5)
        
        # Password
        ttk.Label(self.login_frame, text="Password:").grid(row=2, column=0, sticky='w', padx=5, pady=5)
        self.login_password = tk.StringVar()
        ttk.Entry(self.login_frame, textvariable=self.login_password, show='*', width=40).grid(row=2, column=1, padx=5, pady=5)
        
        # Login Button
        ttk.Button(self.login_frame, text="Login", command=self.authenticate).grid(row=3, column=0, columnspan=2, pady=20)
        
        # Status
        self.login_status = ttk.Label(self.login_frame, text="", foreground="red")
        self.login_status.grid(row=4, column=0, columnspan=2)
        
    def authenticate(self):
        """Authenticate with tracker server"""
        tracker_url = self.login_tracker_url.get()
        username = self.login_username.get().strip()
        password = self.login_password.get().strip()
        
        if not tracker_url or not username or not password:
            self.login_status.config(text="Please fill all fields", foreground="red")
            return
        
        try:
            # Call /login API
            payload = {
                "username": username,
                "password": password
            }
            data = json.dumps(payload).encode('utf-8')
            
            # Create cookie jar to store cookies
            cookie_jar = http.cookiejar.CookieJar()
            opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))
            
            req = urllib.request.Request(
                method="POST",
                url=f"{tracker_url}/login",
                data=data,
                headers={"Content-Type": "application/json"}
            )
            
            with opener.open(req, timeout=5) as response:
                if response.getcode() == 200:
                    resp_data = response.read().decode('utf-8')
                    resp_json = json.loads(resp_data)
                    
                    if resp_json.get("status") == "success" and resp_json.get("auth"):
                        self.authenticated = True
                        self.username = username
                        self.tracker_url.set(tracker_url)
                        self.peer_name.set(username)
                        
                        # Store cookies for future requests
                        for cookie in cookie_jar:
                            self.cookies[cookie.name] = cookie.value
                        
                        print(f"[PeerUI] Stored cookies: {self.cookies}")
                        
                        # Show success and switch to chat UI
                        self.login_status.config(text=f"Login successful! Welcome {username}", foreground="green")
                        self.root.after(1000, self.show_chat_ui)
                    else:
                        self.login_status.config(text="Invalid credentials", foreground="red")
                else:
                    self.login_status.config(text="Login failed", foreground="red")
                    
        except urllib.error.HTTPError as e:
            error_msg = e.read().decode('utf-8') if e.fp else str(e)
            self.login_status.config(text=f"HTTP Error: {e.code}", foreground="red")
            print(f"Login error: {error_msg}")
        except Exception as e:
            self.login_status.config(text=f"Connection error: {str(e)}", foreground="red")
            print(f"Login exception: {e}")
    
    def show_chat_ui(self):
        """Hide login frame and show chat interface"""
        self.login_frame.pack_forget()
        self.connection_frame.pack(fill='x', padx=10, pady=5)
        self.chat_frame.pack(fill='both', expand=True, padx=10, pady=5)
        self.peers_frame.pack(fill='x', padx=10, pady=5)
        self.root.title(f"P2P Chat Client - {self.username}")
        
    def setup_connection_frame(self):
        """Connection configuration frame"""
        self.connection_frame = ttk.LabelFrame(self.root, text="Connection Settings", padding=10)
        
        # Tracker URL
        ttk.Label(self.connection_frame, text="Tracker URL:").grid(row=0, column=0, sticky='w', padx=5)
        self.tracker_url = tk.StringVar(value="http://127.0.0.1:8000")
        ttk.Entry(self.connection_frame, textvariable=self.tracker_url, width=30, state='readonly').grid(row=0, column=1, padx=5)
        
        # Port
        ttk.Label(self.connection_frame, text="Port:").grid(row=0, column=2, sticky='w', padx=5)
        self.port = tk.StringVar(value="5001")
        ttk.Entry(self.connection_frame, textvariable=self.port, width=10).grid(row=0, column=3, padx=5)
        
        # Peer Name (auto-filled from login)
        ttk.Label(self.connection_frame, text="Name:").grid(row=1, column=0, sticky='w', padx=5)
        self.peer_name = tk.StringVar(value="User")
        ttk.Entry(self.connection_frame, textvariable=self.peer_name, width=20, state='readonly').grid(row=1, column=1, padx=5)
        
        # Connect/Disconnect Button
        self.connect_btn = ttk.Button(self.connection_frame, text="Connect", command=self.toggle_connection)
        self.connect_btn.grid(row=1, column=2, columnspan=2, padx=5, pady=5)
        
        # Status
        self.status_label = ttk.Label(self.connection_frame, text="Status: Disconnected", foreground="red")
        self.status_label.grid(row=2, column=0, columnspan=4, sticky='w', padx=5)
        
    def setup_chat_frame(self):
        """Chat messages frame"""
        self.chat_frame = ttk.LabelFrame(self.root, text="Messages", padding=10)
        
        # Messages display
        self.messages_text = scrolledtext.ScrolledText(self.chat_frame, height=20, state='disabled')
        self.messages_text.pack(fill='both', expand=True, pady=5)
        
        # Message input frame
        input_frame = ttk.Frame(self.chat_frame)
        input_frame.pack(fill='x', pady=5)
        
        self.message_input = ttk.Entry(input_frame)
        self.message_input.pack(side='left', fill='x', expand=True, padx=(0, 5))
        self.message_input.bind('<Return>', lambda e: self.send_message())
        
        ttk.Button(input_frame, text="Send Broadcast", command=self.send_message).pack(side='left', padx=2)
        ttk.Button(input_frame, text="Send Direct", command=self.send_direct).pack(side='left', padx=2)
        
    def setup_peers_frame(self):
        """Connected peers frame"""
        self.peers_frame = ttk.LabelFrame(self.root, text="Connected Peers", padding=10)
        
        self.peers_listbox = tk.Listbox(self.peers_frame, height=5)
        self.peers_listbox.pack(fill='both', expand=True)
        
        ttk.Button(self.peers_frame, text="Refresh Peers", command=self.refresh_peers).pack(pady=5)
        
    def toggle_connection(self):
        """Connect or disconnect from P2P network"""
        if not self.authenticated:
            messagebox.showerror("Error", "Please login first")
            return
            
        if not self.running:
            self.connect()
        else:
            self.disconnect()
            
    def connect(self):
        """Start P2P peer"""
        try:
            tracker = self.tracker_url.get()
            port = int(self.port.get())
            name = self.peer_name.get()
            
            if not tracker or not name:
                messagebox.showerror("Error", "Please fill all fields")
                return
            
            # Create peer instance
            self.peer = peer2peer(tracker_url=tracker, port=port, peer_name=name)
            self.peer.cookies = self.cookies  # Set cookies for tracker communication
            
            # Register with tracker
            if not self.peer.register_tracker():
                messagebox.showerror("Error", "Failed to register with tracker")
                return
            
            # Start background threads
            self.running = True
            
            # Start peer server
            def run_peer_server():
                self.peer.app.prepare_address('0.0.0.0', port)
                self.peer.app.run()
            
            self.server_thread = threading.Thread(target=run_peer_server, daemon=True)
            self.server_thread.start()
            
            # Start heartbeat/discovery
            self.heartbeat_thread = threading.Thread(target=self.heartbeat_loop, daemon=True)
            self.heartbeat_thread.start()
            
            # Start message polling
            self.message_thread = threading.Thread(target=self.message_loop, daemon=True)
            self.message_thread.start()
            
            # Discover initial peers
            self.peer.find_all_peers_and_connect()
            
            # Update UI
            self.status_label.config(text=f"Status: Connected as {name} on port {port}", foreground="green")
            self.connect_btn.config(text="Disconnect")
            self.add_message("System", f"Connected to P2P network as {name}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to connect: {e}")
            self.running = False
            
    def disconnect(self):
        """Stop P2P peer"""
        if self.peer:
            self.peer.unregister_from_tracker()
            self.peer.running = False
        
        self.running = False
        self.status_label.config(text="Status: Disconnected", foreground="red")
        self.connect_btn.config(text="Connect")
        self.add_message("System", "Disconnected from P2P network")
        
    def heartbeat_loop(self):
        """Background thread for peer discovery and heartbeat"""
        while self.running:
            try:
                self.peer.get_peers_list()
                self.peer.ping_tracker()
                self.root.after(0, self.update_peers_list)
            except Exception as e:
                print(f"Heartbeat error: {e}")
            time.sleep(5)
            
    def message_loop(self):
        """Background thread to poll for new messages"""
        while self.running:
            try:
                if self.peer and self.peer.messages:
                    for msg in self.peer.messages:
                        msg_type = msg.get('type', 'unknown')
                        from_name = msg.get('from_name', 'Unknown')
                        message = msg.get('message', '')
                        
                        prefix = "[Direct]" if msg_type == "direct" else "[Broadcast]"
                        self.root.after(0, self.add_message, f"{prefix} {from_name}", message)
                    
                    self.peer.messages.clear()
            except Exception as e:
                print(f"Message loop error: {e}")
            time.sleep(0.5)
            
    def send_message(self):
        """Send broadcast message"""
        if not self.running or not self.peer:
            messagebox.showwarning("Warning", "Not connected to P2P network")
            return
        
        message = self.message_input.get().strip()
        if not message:
            return
        
        try:
            self.peer.send_broadcast_message(message)
            self.add_message("You [Broadcast]", message)
            self.message_input.delete(0, tk.END)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to send message: {e}")
            
    def send_direct(self):
        """Send direct message to selected peer"""
        if not self.running or not self.peer:
            messagebox.showwarning("Warning", "Not connected to P2P network")
            return
        
        selection = self.peers_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a peer")
            return
        
        peer_id = self.peers_listbox.get(selection[0]).split(' - ')[1]
        message = self.message_input.get().strip()
        
        if not message:
            return
        
        try:
            self.peer.send_direct_message(peer_id, message)
            self.add_message(f"You [Direct to {peer_id}]", message)
            self.message_input.delete(0, tk.END)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to send direct message: {e}")
            
    def refresh_peers(self):
        """Manually refresh peers list"""
        if self.peer:
            self.peer.get_peers_list()
            self.update_peers_list()
            
    def update_peers_list(self):
        """Update peers listbox"""
        self.peers_listbox.delete(0, tk.END)
        if self.peer and self.peer.connected_peers:
            for peer_id, info in self.peer.connected_peers.items():
                name = info.get('name', 'Unknown')
                self.peers_listbox.insert(tk.END, f"{name} - {peer_id}")
                
    def add_message(self, sender, message):
        """Add message to chat display"""
        self.messages_text.config(state='normal')
        timestamp = time.strftime("%H:%M:%S")
        self.messages_text.insert(tk.END, f"[{timestamp}] {sender}: {message}\n")
        self.messages_text.see(tk.END)
        self.messages_text.config(state='disabled')
        
    def on_closing(self):
        """Handle window close"""
        if self.running:
            self.disconnect()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = PeerChatUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()