import socket
import threading

HOST = "127.0.0.1"
PORT = 3333
BUFFER_SIZE = 1024


class State:
    def __init__(self):
        self.data = {}
        self.lock = threading.Lock()

    def add(self, key, value):
        with self.lock:
            self.data[key] = value
        return "OK - record add"

    def get(self, key):
        with self.lock:
            if key in self.data:
                return f"DATA {self.data[key]}"
            return "ERROR invalid key"

    def remove(self, key):
        with self.lock:
            if key in self.data:
                del self.data[key]
                return "OK value deleted"
            return "ERROR invalid key"

    def list_all(self):
        with self.lock:
            if not self.data:
                return "DATA|"
            items = ",".join([f"{k}={v}" for k, v in self.data.items()])
            return f"DATA|{items}"

    def count(self):
        with self.lock:
            return f"DATA {len(self.data)}"

    def clear(self):
        with self.lock:
            self.data.clear()
        return "all data deleted"

    def update(self, key, value):
        with self.lock:
            if key in self.data:
                self.data[key] = value
                return "Data updated"
            return "ERROR invalid key"

    def pop_item(self, key):
        with self.lock:
            if key in self.data:
                value = self.data.pop(key)
                return f"Data {value}"
            return "ERROR invalid key"


state = State()


def encode_response(response: str) -> bytes:
    return f"{len(response)} {response}".encode("utf-8")


def process_command(command: str):
    parts = command.split(maxsplit=2)

    if not parts:
        return "ERROR empty command", False

    cmd = parts[0].upper()

    if cmd == "ADD":
        if len(parts) != 3:
            return "ERROR unknown command", False
        return state.add(parts[1], parts[2]), False

    if cmd == "GET":
        if len(parts) != 2:
            return "ERROR unknown command", False
        return state.get(parts[1]), False

    if cmd == "REMOVE":
        if len(parts) != 2:
            return "ERROR unknown command", False
        return state.remove(parts[1]), False

    if cmd == "LIST":
        if len(parts) != 1:
            return "ERROR unknown command", False
        return state.list_all(), False

    if cmd == "COUNT":
        if len(parts) != 1:
            return "ERROR unknown command", False
        return state.count(), False

    if cmd == "CLEAR":
        if len(parts) != 1:
            return "ERROR unknown command", False
        return state.clear(), False

    if cmd == "UPDATE":
        if len(parts) != 3:
            return "ERROR unknown command", False
        return state.update(parts[1], parts[2]), False

    if cmd == "POP":
        if len(parts) != 2:
            return "ERROR unknown command", False
        return state.pop_item(parts[1]), False

    if cmd == "QUIT":
        return "Quit", True

    return "ERROR unknown command", False


def handle_client(client_socket):
    with client_socket:
        while True:
            try:
                data = client_socket.recv(BUFFER_SIZE)
                if not data:
                    break

                command = data.decode("utf-8").strip()
                response, should_close = process_command(command)
                client_socket.sendall(encode_response(response))

                if should_close:
                    break

            except Exception:
                error_message = "ERROR unknown command"
                try:
                    client_socket.sendall(encode_response(error_message))
                except OSError:
                    pass
                break


def start_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((HOST, PORT))
        server_socket.listen()
        print(f"[SERVER] Listening on {HOST}:{PORT}")

        while True:
            client_socket, addr = server_socket.accept()
            print(f"[SERVER] Connection from {addr}")
            threading.Thread(
                target=handle_client,
                args=(client_socket,),
                daemon=True
            ).start()


if __name__ == "__main__":
    start_server()