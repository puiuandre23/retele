import json
import os
import socket
from pathlib import Path

HOST = "127.0.0.1"
PORT = 5000
LOCAL_DIR = Path("client_files")


class ClientFTP:
    def __init__(self):
        self.sock = None
        self.connected_user = None
        LOCAL_DIR.mkdir(exist_ok=True)

    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((HOST, PORT))
        print(f"Conectat la serverul {HOST}:{PORT}")

    def request(self, **payload):
        self.sock.sendall((json.dumps(payload) + "\n").encode("utf-8"))
        buffer = b""
        while b"\n" not in buffer:
            part = self.sock.recv(1024)
            if not part:
                raise ConnectionError("Serverul a inchis conexiunea.")
            buffer += part
        line, _ = buffer.split(b"\n", 1)
        return json.loads(line.decode("utf-8"))

    def choose_server_file(self):
        response = self.request(command="list_files")
        if not response.get("ok"):
            print(response.get("message"))
            return None
        files = response.get("files", [])
        if not files:
            print("Nu exista fisiere pe server.")
            return None
        for index, filename in enumerate(files, 1):
            print(f"{index}. {filename}")
        choice = input("Alege numarul fisierului sau scrie numele: ").strip()
        if choice.isdigit():
            index = int(choice) - 1
            if 0 <= index < len(files):
                return files[index]
            print("Numar invalid.")
            return None
        return choice

    def show_result(self, response):
        symbol = "OK" if response.get("ok") else "EROARE"
        print(f"[{symbol}] {response.get('message', '')}")

    def login(self):
        username = input("Utilizator: ").strip()
        password = input("Parola: ").strip()
        response = self.request(command="login", username=username, password=password)
        self.show_result(response)
        if response.get("ok"):
            self.connected_user = username

    def create_file(self):
        name = input("Nume fisier local: ").strip()
        if not name:
            print("Nume invalid.")
            return
        print("Scrie continutul. Linie goala pentru final:")
        rows = []
        while True:
            row = input()
            if row == "":
                break
            rows.append(row)
        path = LOCAL_DIR / Path(name).name
        path.write_text("\n".join(rows), encoding="utf-8")
        print(f"Fisier creat local: {path}")

    def upload(self):
        files = sorted([p.name for p in LOCAL_DIR.iterdir() if p.is_file()])
        if not files:
            print("Nu ai fisiere locale in client_files.")
            return
        for index, filename in enumerate(files, 1):
            print(f"{index}. {filename}")
        choice = input("Alege fisierul de incarcat: ").strip()
        try:
            filename = files[int(choice) - 1]
        except Exception:
            filename = choice
        path = LOCAL_DIR / Path(filename).name
        if not path.exists():
            print("Fisier local inexistent.")
            return
        response = self.request(command="upload", filename=path.name, content=path.read_text(encoding="utf-8"))
        self.show_result(response)

    def rename_file(self):
        old_name = self.choose_server_file()
        if old_name is None:
            return
        new_name = input("Noul nume: ").strip()
        response = self.request(command="rename_file", old_name=old_name, new_name=new_name)
        self.show_result(response)

    def read_file(self):
        filename = self.choose_server_file()
        if filename is None:
            return
        response = self.request(command="read_file", filename=filename)
        if response.get("ok"):
            print(f"\n--- {response['filename']} ---")
            print(response.get("content", ""))
            print("--- sfarsit fisier ---")
        else:
            self.show_result(response)

    def download(self):
        filename = self.choose_server_file()
        if filename is None:
            return
        response = self.request(command="download", filename=filename)
        if response.get("ok"):
            path = LOCAL_DIR / Path(response["filename"]).name
            path.write_text(response.get("content", ""), encoding="utf-8")
            print(f"Fisier descarcat local: {path}")
        else:
            self.show_result(response)

    def edit_file(self):
        filename = self.choose_server_file()
        if filename is None:
            return
        print("Scrie noul continut. Linie goala pentru final:")
        rows = []
        while True:
            row = input()
            if row == "":
                break
            rows.append(row)
        response = self.request(command="edit_file", filename=filename, content="\n".join(rows))
        self.show_result(response)

    def file_history(self):
        filename = self.choose_server_file()
        if filename is None:
            return
        response = self.request(command="see_file_operation_history", filename=filename)
        if not response.get("ok"):
            self.show_result(response)
            return
        events = response.get("history", [])
        if not events:
            print("Nu exista istoric pentru acest fisier.")
            return
        print(f"Istoric pentru {filename}:")
        for event in events:
            print(f"- {event['time']} | {event['user']} | {event['action']}")

    def list_files(self):
        response = self.request(command="list_files")
        if not response.get("ok"):
            self.show_result(response)
            return
        files = response.get("files", [])
        print("Fisiere server:")
        for filename in files:
            print(f"- {filename}")
        if not files:
            print("(lista goala)")

    def logout(self):
        response = self.request(command="logout")
        self.show_result(response)
        if response.get("ok"):
            self.connected_user = None

    def close(self):
        if self.sock:
            self.sock.close()

    def menu(self):
        actions = {
            "1": self.login,
            "2": self.create_file,
            "3": self.upload,
            "4": self.rename_file,
            "5": self.read_file,
            "6": self.download,
            "7": self.edit_file,
            "8": self.file_history,
            "9": self.list_files,
            "10": self.logout,
        }
        while True:
            print("\n=== MENIU CLIENT FTP ===")
            print("1. Login")
            print("2. Creeaza fisier local")
            print("3. Upload fisier")
            print("4. Redenumeste fisier pe server")
            print("5. Citeste fisier de pe server")
            print("6. Download fisier")
            print("7. Editeaza fisier pe server")
            print("8. Istoric operatii fisier")
            print("9. Lista fisiere server")
            print("10. Logout")
            print("0. Iesire")
            choice = input("Optiune: ").strip()
            if choice == "0":
                self.close()
                print("Client inchis.")
                break
            action = actions.get(choice)
            if action:
                action()
            else:
                print("Optiune invalida.")


def main():
    client = ClientFTP()
    try:
        client.connect()
        client.menu()
    except Exception as exc:
        print(f"Eroare client: {exc}")
    finally:
        client.close()


if __name__ == "__main__":
    main()
