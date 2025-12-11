Task 1
    Run and Test.
    1. Open many backend:
    python start_backend.py –server-ip 127.0.0.1 –server-port 9000
    python start_backend.py –server-ip 127.0.0.1 –server-port 9001
    python start_backend.py –server-ip 127.0.0.1 –server-port 9002

    2. Start Proxy Server:
    python start_proxy.py
    3. Accessing http://localhost:8080/ many times; then log Proxy to see that request have been sent
    through all the backend 9000-9001-9002 (round-robin).

    4. Login POST /login through proxy; Check Set-Cookie in response.

    5. Reloading /: Will be serve with index.html if cookie is correct; remove cookie and client will be
    faced with unauthorized error.


Task 2:
    1. Run ChatApp server.
    python start_chatapp.py

    2. Run Peer side app.
    python peer_ui.py

    3. Input the server trakcer url and port.
    Default is at port 8000

    4. Login with these credentials.
    Username    Password
    admin       admin
    alice       alice
    tom         tom
    charlie     charlie
    bob         bob

    5. CLick connect to submit-info to tracker server
    
    6. Click on channel to connect and only talk to peers in the same channel.

    7. Choose a peer to send direct message to them.

    8. Test True Peer-2-peer.
    Turn off Chatapp server and see if peers can still chatting.

