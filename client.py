import socket
import threading
import os

SERVER_IP = "192.168.1.231"  # Cambia a tu IP del servidor
SERVER_PORT = 9000

def recvall(sock, n):
    data = b""
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            return None
        data += packet
    return data

def receive(client_socket):
    while True:
        try:
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
                length = int(parts[2])
                msg = recvall(client_socket, length).decode()
                print(f"{sender_name}: {msg}")

            elif parts[0] == "FILE":
                sender_name = parts[1]
                filename = parts[2]
                filesize = int(parts[3])
                print(f"[Archivo de {sender_name}] Recibiendo {filename} ({filesize} bytes)")
                with open(f"recibido_{filename}", "wb") as f:
                    remaining = filesize
                    while remaining > 0:
                        chunk = client_socket.recv(min(4096, remaining))
                        if not chunk:
                            break
                        f.write(chunk)
                        remaining -= len(chunk)
                print(f"[Archivo recibido de {sender_name}] Guardado como recibido_{filename}")

        except ConnectionResetError:
            print("[Servidor cerró la conexión]")
            break
        except Exception as e:
            print(f"[Error] {e}")
            break

def send_message(client_socket, name):
    while True:
        msg = input("Escribe '@Nombre mensaje' para unicast o 'all mensaje' para broadcast:\n")
        if msg.startswith("/file "):
            filepath = msg[6:].strip()
            if not os.path.isfile(filepath):
                print("Archivo no encontrado")
                continue
            filesize = os.path.getsize(filepath)
            filename = os.path.basename(filepath)
            # Preguntar destinatario
            recipient = input("Enviar a (nombre o 'all'): ").strip()
            client_socket.sendall(f"FILE|{name}|{recipient}|{filename}|{filesize}\n".encode())
            with open(filepath, "rb") as f:
                while chunk := f.read(4096):
                    client_socket.sendall(chunk)
            print(f"[Archivo enviado] {filename} a {recipient}")
        else:
            # Detectar destinatario en texto
            if msg.startswith("@"):
                try:
                    recipient, text = msg[1:].split(" ", 1)
                except ValueError:
                    print("Formato inválido. Usa '@Nombre mensaje'")
                    continue
            else:
                recipient = "all"
                text = msg
            data = text.encode()
            header = f"MSG|{name}|{recipient}|{len(data)}|\n".encode()
            client_socket.sendall(header + data)

def main():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((SERVER_IP, SERVER_PORT))

    while True:
        name = input("Ingresa tu nombre: ").strip()
        if name and "|" not in name:
            break
        print("Nombre inválido. No puede estar vacío ni contener '|'")
    client_socket.sendall(f"{name}\n".encode())
    print(f"[Conectado como {name}]")

    thread = threading.Thread(target=receive, args=(client_socket,), daemon=True)
    thread.start()

    send_message(client_socket, name)

if __name__ == "__main__":
    main()