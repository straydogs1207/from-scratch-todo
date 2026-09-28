import socket
import selectors
import os
from database import SimpleDB
from router import route_request

selector = selectors.DefaultSelector()


def on_accept(server_sock, mask, db):
    client_sock, client_addr = server_sock.accept()
    client_sock.setblocking(False)

    connection_state = {
        "buffer": bytearray(),
        "response": bytearray(),
        "db": db,
    }

    # Register callback for when the client socket has data to read
    selector.register(
        client_sock,
        selectors.EVENT_READ,
        data=lambda s, m: on_read(s, m, connection_state),
    )


def on_read(client_sock, mask, state):
    try:
        chunk = client_sock.recv(4096)
    except ConnectionResetError:
        chunk = b""

    if not chunk:
        # Client disconnected
        selector.unregister(client_sock)
        client_sock.close()
        return

    state["buffer"].extend(chunk)

    # Check if we have received complete HTTP headers (\r\n\r\n)
    header_end = state["buffer"].find(b"\r\n\r\n")
    if header_end != -1:
        headers_raw = state["buffer"][:header_end].decode("latin1")
        body_start = header_end + 4

        # Read Content-Length if present
        content_length = 0
        for line in headers_raw.split("\r\n"):
            if line.lower().startswith("content-length:"):
                content_length = int(line.split(":")[1].strip())

        # When the complete body has arrived, handle the request
        if len(state["buffer"]) >= body_start + content_length:
            body = state["buffer"][body_start : body_start + content_length]
            handle_http_request(client_sock, headers_raw, body, state)


def handle_http_request(client_sock, headers_raw, body, state):
    lines = headers_raw.split("\r\n")
    request_line = lines[0].split(" ")
    if len(request_line) < 2:
        selector.unregister(client_sock)
        client_sock.close()
        return

    method, path = request_line[0], request_line[1]

    # Process request using router and DB
    status, content_type, response_body = route_request(
        method, path, body, state["db"]
    )

    # Build raw HTTP response
    response = (
        f"HTTP/1.1 {status}\r\n"
        f"Content-Type: {content_type}\r\n"
        f"Content-Length: {len(response_body)}\r\n"
        f"Access-Control-Allow-Origin: *\r\n"
        f"Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS\r\n"
        f"Access-Control-Allow-Headers: Content-Type\r\n"
        f"Connection: close\r\n\r\n"
    ).encode("latin1") + response_body

    state["response"] = bytearray(response)

    # Transition socket to EVENT_WRITE callback
    selector.modify(
        client_sock,
        selectors.EVENT_WRITE,
        data=lambda s, m: on_write(s, m, state),
    )


def on_write(client_sock, mask, state):
    try:
        sent = client_sock.send(state["response"])
        state["response"] = state["response"][sent:]
    except (BrokenPipeError, ConnectionResetError):
        state["response"] = bytearray()

    # Once entire response is written, close connection cleanly
    if len(state["response"]) == 0:
        selector.unregister(client_sock)
        client_sock.close()


def main():
    host = "127.0.0.1"
    port = 8000

    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "todos.db")
    db = SimpleDB(db_path)

    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind((host, port))
    server_sock.listen(128)
    server_sock.setblocking(False)

    selector.register(
        server_sock,
        selectors.EVENT_READ,
        data=lambda s, m: on_accept(s, m, db),
    )

    print(f"🚀 Server running on http://{host}:{port}")
    print("📡 Pure callback event loop active (No coroutines / async-await)")
    print("Press Ctrl+C to stop.")

    try:
        while True:
            events = selector.select()
            for key, mask in events:
                callback = key.data
                callback(key.fileobj, mask)
    except KeyboardInterrupt:
        print("\nShutting down server.")
    finally:
        server_sock.close()
        selector.close()


if __name__ == "__main__":
    main()
