import socket
import threading
import os

SERVER_IP = "0.0.0.0"
SERVER_PORT = 9000

clients = {}  # {socket: nombre}

def recvall(sock, n):
    data = b""
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            return None
        data += packet
    return data

def send_to(name_target, data, sender_socket):
    """Envía solo al cliente con nombre name_target"""
    if name_target == "all":
        # Broadcast
        for client, _ in clients.items():
            if client != sender_socket:
                try:
                    client.sendall(data)
                except:
                    clients.pop(client, None)
    else:
        for client, name in clients.items():
            if name == name_target and client != sender_socket:
                try:
                    client.sendall(data)
                except:
                    clients.pop(client, None)
                break

def handle_client(client_socket, addr):
    try:
        # Recibir nombre
        name_bytes = b""
        while b"\n" not in name_bytes:
            chunk = client_socket.recv(1)
            if not chunk:
                return
            name_bytes += chunk
        name = name_bytes.decode().strip()
        clients[client_socket] = name
        print(f"[Conexión] {addr} se unió como '{name}'")

        while True:
            header = b""
            while b"\n" not in header:
                chunk = client_socket.recv(1)
                if not chunk:
                    raise ConnectionResetError()
                header += chunk
            header = header.decode().strip()
            parts = header.split("|")

            if parts[0] == "MSG":
                sender_name = parts[1]
                recipient = parts[2]
                length = int(parts[3])
                message = recvall(client_socket, length).decode()
                if recipient != "all":
                    send_to(recipient, f"MSG|{sender_name}|{length}|\n{message}".encode(), client_socket)
                    print(f"[{sender_name} -> {recipient}] {message}")
                else:
                    send_to("all", f"MSG|{sender_name}|{length}|\n{message}".encode(), client_socket)
                    print(f"[{sender_name} -> todos] {message}")

            elif parts[0] == "FILE":
                sender_name = parts[1]
                recipient = parts[2]
                filename = parts[3]
                filesize = int(parts[4])
                print(f"[Archivo {sender_name} -> {recipient}] Recibiendo {filename} ({filesize} bytes)")
                filepath = f"tmp_{filename}"
                with open(filepath, "wb") as f:
                    remaining = filesize
                    while remaining > 0:
                        chunk = client_socket.recv(min(4096, remaining))
                        if not chunk:
                            break
                        f.write(chunk)
                        remaining -= len(chunk)
                # Enviar archivo al destinatario(s)
                with open(filepath, "rb") as f:
                    send_to(recipient, f"FILE|{sender_name}|{filename}|{filesize}\n".encode(), client_socket)
                    while chunk := f.read(4096):
                        send_to(recipient, chunk, client_socket)
                os.remove(filepath)
                print(f"[Archivo {filename}] enviado a {recipient}")

    except ConnectionResetError:
        print(f"[Desconectado inesperado] {clients.get(client_socket, addr)}")
    except Exception as e:
        print(f"[Error {clients.get(client_socket, addr)}] {e}")
    finally:
        if client_socket in clients:
            print(f"[Desconectado] {clients[client_socket]}")
            clients.pop(client_socket)
        client_socket.close()

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((SERVER_IP, SERVER_PORT))
    server.listen()
    print(f"[Servidor] Escuchando en {SERVER_IP}:{SERVER_PORT}")

    while True:
        client_socket, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(client_socket, addr), daemon=True)
        thread.start()

if __name__ == "__main__":
    main()