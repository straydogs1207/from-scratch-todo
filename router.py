import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def route_request(method, path, body, db):
    if method == "OPTIONS":
        return "204 No Content", "text/plain", b""

    # API: List all todos
    if method == "GET" and path == "/api/todos":
        todos = db.select_all()
        return "200 OK", "application/json", json.dumps(todos).encode("utf-8")

    # API: Create new todo
    if method == "POST" and path == "/api/todos":
        data = json.loads(body.decode("utf-8"))
        todos = db.select_all()
        new_id = (max([t["id"] for t in todos], default=0) + 1)
        db.insert(new_id, data.get("title", ""), False)
        return (
            "201 Created",
            "application/json",
            json.dumps({"id": new_id, "title": data.get("title", ""), "completed": False}).encode("utf-8"),
        )

    # API: Toggle completed status
    if method == "PUT" and path.startswith("/api/todos/"):
        todo_id = int(path.split("/")[-1])
        data = json.loads(body.decode("utf-8"))
        success = db.update_completed(todo_id, data.get("completed", False))
        if success:
            return "200 OK", "application/json", b'{"status": "updated"}'
        return "404 Not Found", "application/json", b'{"error": "not found"}'

    # API: Delete todo
    if method == "DELETE" and path.startswith("/api/todos/"):
        todo_id = int(path.split("/")[-1])
        success = db.delete(todo_id)
        if success:
            return "200 OK", "application/json", b'{"status": "deleted"}'
        return "404 Not Found", "application/json", b'{"error": "not found"}'

    # Static file serving: index.html
    if path == "/" or path == "/index.html":
        file_path = os.path.join(BASE_DIR, "index.html")
        if os.path.exists(file_path):
            with open(file_path, "rb") as f:
                return "200 OK", "text/html", f.read()

    # Static file serving: app.js
    if path == "/app.js":
        file_path = os.path.join(BASE_DIR, "app.js")
        if os.path.exists(file_path):
            with open(file_path, "rb") as f:
                return "200 OK", "application/javascript", f.read()

    return "404 Not Found", "text/plain", b"Not Found"
