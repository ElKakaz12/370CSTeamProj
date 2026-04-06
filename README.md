# Python TCP Chat Application

This is a simple client-server chat application in Python. Different devices can communicate over a network using TCP sockets, allowing multiple clients to send messages and files to each other through a central server.

## How It Works

1. **Server Side**:
   - Listens on a network IP and port for incoming client connections.
   - Receives the username from each client.
   - Receives messages or files from clients and forwards them to the intended recipient(s).
   - Handles multiple clients at the same time using threads.

2. **Client Side**:
   - Connects to the server using its IP and port.
   - Sends the username to the server.
   - Runs a thread to continuously listen for messages or files from other clients.
   - Reads user input to send messages or files to other clients.

3. **Communication Protocol**:
   - Messages and files are sent with a header indicating type, sender, recipient, and size.
   - The server reads the header to know how much data to expect and who should receive it.
   - Files are transmitted in chunks so large files can be sent safely.

---

## How To Run

### Server

1. Open the server script "server.py" and set the IP and port for your network:

SERVER_IP = "0.0.0.0"  # Listen on all network interfaces
SERVER_PORT = 9000      # Port to listen on

2. Run the server:
python server.py

The server will start listening for clients.

3. Run the client:
python client.py

Enter a username when prompted.

To send messages:
Broadcast messages are sent automatically.
Private message: @'User to send message' 'message'

Send a file: /file path-to-file/file.txt
Then specify the recipient name or all.
On name type the user name, for all will broadcast to everyone

## Notes

Usernames cannot contain the character | because it is used in communication headers.
Files are sent in chunks and received files are saved with a prefix like received_.
Multiple clients can communicate at the same time using threads.
