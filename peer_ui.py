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
        self.root.geometry("1000x800")
        
        self.peer = None
        self.running = False
        self.authenticated = False
        self.username = None
        self.cookies = {}
        self.current_channel = "general"  # Default channel
        self.joined_channels = ["general"]  # Track joined channels
        
        # Store messages per channel
        self.channel_messages = {
            "general": [],
            "tech": [],
            "random": []
        }
        
        # Setup UI
        self.setup_login_frame()
        self.setup_connection_frame()
        self.setup_channel_frame()
        self.setup_chat_frame()
        self.setup_peers_frame()
        
        # Initially hide connection/chat frames until logged in
        self.connection_frame.pack_forget()
        self.channel_frame.pack_forget()
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
        self.channel_frame.pack(fill='x', padx=10, pady=5)
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
    
    def setup_channel_frame(self):
        """Channel selection frame"""
        self.channel_frame = ttk.LabelFrame(self.root, text="Channels", padding=10)
        
        ttk.Label(self.channel_frame, text="Active Channel:").grid(row=0, column=0, sticky='w', padx=5)
        self.channel_label = ttk.Label(self.channel_frame, text="general", foreground="green", font=('Arial', 10, 'bold'))
        self.channel_label.grid(row=0, column=1, sticky='w', padx=5)
        
        # Channel buttons
        btn_frame = ttk.Frame(self.channel_frame)
        btn_frame.grid(row=1, column=0, columnspan=4, pady=10)
        
        self.general_btn = ttk.Button(btn_frame, text="📢 General (Broadcast)", 
                                      command=lambda: self.switch_channel("general"), 
                                      state='disabled')
        self.general_btn.pack(side='left', padx=5)
        
        self.tech_btn = ttk.Button(btn_frame, text="💻 Tech", 
                                   command=lambda: self.join_channel("tech"))
        self.tech_btn.pack(side='left', padx=5)
        
        self.random_btn = ttk.Button(btn_frame, text="🎲 Random", 
                                     command=lambda: self.join_channel("random"))
        self.random_btn.pack(side='left', padx=5)
        
        # Channel status
        self.channel_status = ttk.Label(self.channel_frame, text="Joined: general", foreground="blue")
        self.channel_status.grid(row=2, column=0, columnspan=4, sticky='w', padx=5)
        
    def setup_chat_frame(self):
        """Chat messages frame"""
        self.chat_frame = ttk.LabelFrame(self.root, text="Messages", padding=10)
        
        # Messages display
        self.messages_text = scrolledtext.ScrolledText(self.chat_frame, height=15, state='disabled')
        self.messages_text.pack(fill='both', expand=True, pady=5)
        
        # Message input frame
        input_frame = ttk.Frame(self.chat_frame)
        input_frame.pack(fill='x', pady=5)
        
        self.message_input = ttk.Entry(input_frame)
        self.message_input.pack(side='left', fill='x', expand=True, padx=(0, 5))
        self.message_input.bind('<Return>', lambda e: self.send_message())
        
        ttk.Button(input_frame, text="Send to Channel", command=self.send_message).pack(side='left', padx=2)
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
            self.peer.cookies = self.cookies
            
            # Register with tracker (automatically joins general channel)
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
            
            # Wait for server to start
            time.sleep(2)
            
            # Start heartbeat/discovery
            self.heartbeat_thread = threading.Thread(target=self.heartbeat_loop, daemon=True)
            self.heartbeat_thread.start()
            
            # Start message polling
            self.message_thread = threading.Thread(target=self.message_loop, daemon=True)
            self.message_thread.start()
            
            # Discover initial peers in general channel
            self.peer.find_all_peers_and_connect("general")
            
            # Update UI
            self.status_label.config(text=f"Status: Connected as {name} on port {port}", foreground="green")
            self.connect_btn.config(text="Disconnect")
            self.add_message_to_channel("general", "System", f"Connected to P2P network as {name}")
            self.add_message_to_channel("general", "System", f"Joined channel: general (broadcast)")
            self.display_channel_messages()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to connect: {e}")
            self.running = False
    
    def join_channel(self, channel_name):
        """Join a specific channel"""
        if not self.running or not self.peer:
            messagebox.showwarning("Warning", "Not connected to P2P network")
            return
        
        if channel_name in self.joined_channels:
            self.switch_channel(channel_name)
            return
        
        try:
            # Use peer's join_channel method
            if self.peer.join_channel(channel_name):
                self.joined_channels.append(channel_name)
                self.add_message_to_channel(channel_name, "System", f"Joined channel: {channel_name}")
                self.switch_channel(channel_name)
                self.update_channel_status()
            else:
                messagebox.showerror("Error", f"Failed to join channel {channel_name}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to join channel: {e}")
            print(f"Join channel error: {e}")
    
    def switch_channel(self, channel_name):
        """Switch active viewing channel and load its messages"""
        if channel_name not in self.joined_channels:
            messagebox.showwarning("Warning", f"You haven't joined {channel_name} yet")
            return
        
        # Save current scroll position (optional)
        old_channel = self.current_channel
        
        # Switch channel
        self.current_channel = channel_name
        self.channel_label.config(text=channel_name)
        
        # Update button states
        self.general_btn.config(state='disabled' if channel_name == 'general' else 'normal')
        self.tech_btn.config(state='disabled' if channel_name == 'tech' else 'normal')
        self.random_btn.config(state='disabled' if channel_name == 'random' else 'normal')
        
        # Display messages for the new channel
        self.display_channel_messages()
        
        # Add system message about channel switch
        self.add_message_to_channel(channel_name, "System", f"Switched to channel: {channel_name}")
        self.display_channel_messages()
        
        # Refresh peers for this channel
        self.refresh_peers()
    
    def update_channel_status(self):
        """Update channel status label"""
        channels_str = ", ".join(self.joined_channels)
        self.channel_status.config(text=f"Joined: {channels_str}")
    
    def display_channel_messages(self):
        """Display all messages for the current channel"""
        self.messages_text.config(state='normal')
        self.messages_text.delete(1.0, tk.END)
        
        # Get messages for current channel
        messages = self.channel_messages.get(self.current_channel, [])
        
        for msg in messages:
            self.messages_text.insert(tk.END, msg + "\n")
        
        self.messages_text.see(tk.END)
        self.messages_text.config(state='disabled')
    
    def add_message_to_channel(self, channel, sender, message):
        """Add message to specific channel's message history"""
        timestamp = time.strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {sender}: {message}"
        
        # Initialize channel messages if not exists
        if channel not in self.channel_messages:
            self.channel_messages[channel] = []
        
        # Add message to channel history
        self.channel_messages[channel].append(formatted_message)
        
        # If this is the current channel, update display
        if channel == self.current_channel:
            self.display_channel_messages()
            
    def disconnect(self):
        """Stop P2P peer"""
        if self.peer:
            self.peer.unregister_from_tracker()
            self.peer.running = False
        
        self.running = False
        self.status_label.config(text="Status: Disconnected", foreground="red")
        self.connect_btn.config(text="Connect")
        self.add_message_to_channel("general", "System", "Disconnected from P2P network")
        
        # Reset channels
        self.joined_channels = ["general"]
        self.current_channel = "general"
        self.update_channel_status()
        self.display_channel_messages()
        
    def heartbeat_loop(self):
        """Background thread for peer discovery and heartbeat"""
        while self.running:
            try:
                # Refresh peers for all joined channels
                for channel in self.joined_channels:
                    self.peer.get_peers_list(channel)
                
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
                        msg_channel = msg.get('channel', 'general')
                        
                        # Filter messages based on type
                        if msg_type == "direct":
                            # Direct messages always go to general channel
                            self.root.after(0, self.add_message_to_channel, "general", f"[Direct] {from_name}", message)
                        elif msg_type == "broadcast":
                            # Broadcast messages go to their specific channel
                            self.root.after(0, self.add_message_to_channel, msg_channel, f"[{msg_channel}] {from_name}", message)
                    
                    self.peer.messages.clear()
            except Exception as e:
                print(f"Message loop error: {e}")
            time.sleep(0.5)
            
    def send_message(self):
        """Send message to current channel"""
        if not self.running or not self.peer:
            messagebox.showwarning("Warning", "Not connected to P2P network")
            return
        
        message = self.message_input.get().strip()
        if not message:
            return
        
        try:
            # Send broadcast to current channel
            self.peer.send_broadcast_message(message, self.current_channel)
            self.add_message_to_channel(self.current_channel, f"You [{self.current_channel}]", message)
            self.message_input.delete(0, tk.END)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to send message: {e}")
            
    def send_direct(self):
        """Send direct message to selected peer (only in general channel)"""
        if self.current_channel != "general":
            messagebox.showwarning("Warning", "Direct messages can only be sent from General channel")
            return
            
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
            self.add_message_to_channel("general", f"You [Direct to {peer_id}]", message)
            self.message_input.delete(0, tk.END)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to send direct message: {e}")
            
    def refresh_peers(self):
        """Manually refresh peers list for current channel"""
        if self.peer:
            self.peer.get_peers_list(self.current_channel)
            self.update_peers_list()
            
    def update_peers_list(self):
        """Update peers listbox for current channel"""
        self.peers_listbox.delete(0, tk.END)
        if self.peer and self.peer.connected_peers:
            # Get peers from current channel
            channel_peers = self.peer.connected_peers.get(self.current_channel, {})
            for peer_id, info in channel_peers.items():
                name = info.get('name', 'Unknown')
                self.peers_listbox.insert(tk.END, f"{name} - {peer_id}")
        
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