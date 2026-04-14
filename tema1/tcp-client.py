import socket

HOST = "127.0.0.1"
PORT = 3333
BUFFER_SIZE = 1024


def receive_full_message(sock):
    try:
        data = sock.recv(BUFFER_SIZE)
        if not data:
            return None

        text = data.decode("utf-8")
        first_space = text.find(" ")

        if first_space == -1 or not text[:first_space].isdigit():
            return "ERROR invalid response format"

        message_length = int(text[:first_space])
        message = text[first_space + 1:]
        remaining = message_length - len(message)

        while remaining > 0:
            data = sock.recv(BUFFER_SIZE)
            if not data:
                return None
            chunk = data.decode("utf-8")
            message += chunk
            remaining -= len(chunk)

        return message
    except Exception as e:
        return f"ERROR {e}"


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((HOST, PORT))
        print("Connected to server.")
        print("Commands: ADD, GET, REMOVE, LIST, COUNT, CLEAR, UPDATE, POP, QUIT")

        while True:
            command = input("client> ").strip()
            if not command:
                continue

            sock.sendall(command.encode("utf-8"))
            response = receive_full_message(sock)

            if response is None:
                print("Connection closed by server.")
                break

            print(f"Server response: {response}")

            if command.upper() == "QUIT":
                break


if __name__ == "__main__":
    main()