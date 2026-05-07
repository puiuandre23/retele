import json
import os
import socket
import threading
from datetime import datetime
from pathlib import Path

HOST = "127.0.0.1"
PORT = 5000
SERVER_FILES = Path("server_files")
HISTORY_FILE = Path("history.json")
USER = "student"
PASSWORD = "1234"

history_lock = threading.Lock()


def setup_storage():
    SERVER_FILES.mkdir(exist_ok=True)
    if not HISTORY_FILE.exists():
        HISTORY_FILE.write_text("{}", encoding="utf-8")


def safe_name(filename):
    filename = Path(filename).name
    if not filename:
        raise ValueError("Numele fisierului este invalid.")
    return filename


def load_history():
    try:
        return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_history(data):
    HISTORY_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def add_history(filename, action, username):
    filename = safe_name(filename)
    event = {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "user": username,
        "action": action,
    }
    with history_lock:
        data = load_history()
        data.setdefault(filename, []).append(event)
        save_history(data)


def read_json_line(sock):
    buffer = b""
    while True:
        part = sock.recv(1024)
        if not part:
            return None
        buffer += part
        if b"\n" in buffer:
            line, _ = buffer.split(b"\n", 1)
            return json.loads(line.decode("utf-8"))


def send_response(sock, payload):
    sock.sendall((json.dumps(payload) + "\n").encode("utf-8"))


def list_server_files():
    return sorted([p.name for p in SERVER_FILES.iterdir() if p.is_file()])


def process_command(request, state):
    command = request.get("command")

    if command == "login":
        username = request.get("username", "")
        password = request.get("password", "")
        if username == USER and password == PASSWORD:
            state["logged_in"] = True
            state["user"] = username
            return {"ok": True, "message": f"Autentificare reusita pentru {username}."}
        return {"ok": False, "message": "Date de autentificare gresite."}

    if not state.get("logged_in"):
        return {"ok": False, "message": "Trebuie sa te autentifici mai intai."}

    username = state.get("user", "student")

    if command == "logout":
        state["logged_in"] = False
        state["user"] = None
        return {"ok": True, "message": "Logout efectuat."}

    if command == "list_files":
        return {"ok": True, "files": list_server_files()}

    if command in ("create_file", "upload"):
        filename = safe_name(request.get("filename", ""))
        content = request.get("content", "")
        (SERVER_FILES / filename).write_text(content, encoding="utf-8")
        add_history(filename, "create" if command == "create_file" else "upload", username)
        return {"ok": True, "message": f"Fisierul {filename} a fost salvat pe server."}

    if command == "rename_file":
        old_name = safe_name(request.get("old_name", ""))
        new_name = safe_name(request.get("new_name", ""))
        old_path = SERVER_FILES / old_name
        new_path = SERVER_FILES / new_name
        if not old_path.exists():
            return {"ok": False, "message": "Fisierul initial nu exista."}
        if new_path.exists():
            return {"ok": False, "message": "Exista deja un fisier cu numele nou."}
        old_path.rename(new_path)
        with history_lock:
            data = load_history()
            old_events = data.pop(old_name, [])
            data[new_name] = old_events
            save_history(data)
        add_history(new_name, f"rename from {old_name}", username)
        return {"ok": True, "message": f"Fisier redenumit: {old_name} -> {new_name}."}

    if command == "read_file":
        filename = safe_name(request.get("filename", ""))
        path = SERVER_FILES / filename
        if not path.exists():
            return {"ok": False, "message": "Fisierul nu exista."}
        add_history(filename, "read", username)
        return {"ok": True, "filename": filename, "content": path.read_text(encoding="utf-8")}

    if command == "download":
        filename = safe_name(request.get("filename", ""))
        path = SERVER_FILES / filename
        if not path.exists():
            return {"ok": False, "message": "Fisierul nu exista."}
        add_history(filename, "download", username)
        return {"ok": True, "filename": filename, "content": path.read_text(encoding="utf-8")}

    if command == "edit_file":
        filename = safe_name(request.get("filename", ""))
        path = SERVER_FILES / filename
        if not path.exists():
            return {"ok": False, "message": "Fisierul nu exista."}
        path.write_text(request.get("content", ""), encoding="utf-8")
        add_history(filename, "edit", username)
        return {"ok": True, "message": f"Fisierul {filename} a fost modificat."}

    if command == "see_file_operation_history":
        filename = safe_name(request.get("filename", ""))
        data = load_history()
        return {"ok": True, "filename": filename, "history": data.get(filename, [])}

    return {"ok": False, "message": f"Comanda necunoscuta: {command}"}


def client_worker(sock, address):
    state = {"logged_in": False, "user": None}
    print(f"Client conectat: {address}")
    try:
        while True:
            request = read_json_line(sock)
            if request is None:
                break
            try:
                response = process_command(request, state)
            except Exception as exc:
                response = {"ok": False, "message": str(exc)}
            send_response(sock, response)
    finally:
        sock.close()
        print(f"Client deconectat: {address}")


def main():
    setup_storage()
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen()
    print(f"Server pornit pe {HOST}:{PORT}")
    print(f"User: {USER} | Parola: {PASSWORD}")
    try:
        while True:
            sock, address = server.accept()
            threading.Thread(target=client_worker, args=(sock, address), daemon=True).start()
    except KeyboardInterrupt:
        print("Server oprit.")
    finally:
        server.close()


if __name__ == "__main__":
    main()
