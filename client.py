import socket
import threading
import os

# Server IP and port configuration
#*********************************************************************************************************************************************
SERVER_IP = "#.#.#.#"  # Change this to your server's IP
#*********************************************************************************************************************************************
SERVER_PORT = 9000            # Port number the server is listening on

# Function to receive exactly 'n' bytes from a socket
def recvall(sock, n):
    data = b""  # Start with an empty byte string
    while len(data) < n:  # Keep receiving until we reach 'n' bytes
        packet = sock.recv(n - len(data))  # Receive remaining bytes
        if not packet:  # Connection closed or no data
            return None
        data += packet  # Append received bytes
    return data

# Function to continuously receive messages and files from the server
def receive(client_socket):
    while True:
        try:
            # Read header (terminated by newline '\n')
            header = b""
            while b"\n" not in header:
                chunk = client_socket.recv(1)  # Read one byte at a time
                if not chunk:
                    raise ConnectionResetError()  # Server disconnected unexpectedly
                header += chunk
            header = header.decode().strip()  # Convert bytes to string
            parts = header.split("|")  # Split header into parts

            # Check if it's a text message
            if parts[0] == "MSG":
                sender_name = parts[1]        # Who sent the message
                length = int(parts[2])        # Length of the message in bytes
                msg = recvall(client_socket, length).decode()  # Receive the full message
                print(f"{sender_name}: {msg}")  # Display the message

            # Check if it's a file
            elif parts[0] == "FILE":
                sender_name = parts[1]
                filename = parts[2]
                filesize = int(parts[3])
                print(f"[File from {sender_name}] Receiving {filename} ({filesize} bytes)")

                # Save the received file locally with prefix "received_"
                with open(f"received_{filename}", "wb") as f:
                    remaining = filesize
                    while remaining > 0:
                        chunk = client_socket.recv(min(4096, remaining))  # Receive in chunks
                        if not chunk:
                            break
                        f.write(chunk)
                        remaining -= len(chunk)

                print(f"[File from {sender_name}] Saved as received_{filename}")

        except ConnectionResetError:
            print("[Server closed the connection]")
            break
        except Exception as e:
            print(f"[Error] {e}")
            break

# Function to send messages or files to the server
def send_message(client_socket, name):
    while True:
        msg = input("Type '@Name message' for unicast or 'all message' for broadcast:\n")

        # File sending
        if msg.startswith("/file "):
            filepath = msg[6:].strip()
            if not os.path.isfile(filepath):
                print("File not found")
                continue
            filesize = os.path.getsize(filepath)
            filename = os.path.basename(filepath)

            # Ask for recipient
            recipient = input("Send to (name or 'all'): ").strip()
            # Send the file header
            client_socket.sendall(f"FILE|{name}|{recipient}|{filename}|{filesize}\n".encode())

            # Send the actual file in chunks
            with open(filepath, "rb") as f:
                while chunk := f.read(4096):
                    client_socket.sendall(chunk)

            print(f"[File sent] {filename} to {recipient}")

        else:
            # Detect recipient in text messages
            if msg.startswith("@"):
                try:
                    recipient, text = msg[1:].split(" ", 1)  # Split "@Name message"
                except ValueError:
                    print("Invalid format. Use '@Name message'")
                    continue
            else:
                recipient = "all"  # Broadcast to everyone
                text = msg

            data = text.encode()  # Convert message to bytes
            header = f"MSG|{name}|{recipient}|{len(data)}|\n".encode()  # Create header
            client_socket.sendall(header + data)  # Send header + message

# Main function
def main():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Create TCP socket
    client_socket.connect((SERVER_IP, SERVER_PORT))  # Connect to the server

    # Ask the user for a valid name
    while True:
        name = input("Enter your name: ").strip()
        if name and "|" not in name:  # Name cannot be empty or contain '|'
            break
        print("Invalid name. Cannot be empty or contain '|'")
    
    client_socket.sendall(f"{name}\n".encode())  # Send name to server
    print(f"[Connected as {name}]")

    # Start a thread to receive messages/files from the server
    thread = threading.Thread(target=receive, args=(client_socket,), daemon=True)
    thread.start()

    # Start sending messages/files
    send_message(client_socket, name)

if __name__ == "__main__":
    main()