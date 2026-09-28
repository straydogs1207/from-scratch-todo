# From-Scratch Todo: Custom Reconciler, Callback Socket Server & SQLite Clone

An educational, dependency-free full-stack Todo application built completely from first principles.

---

## 📌 Project Overview

This project implements a web application without relying on web frameworks, UI libraries, or external database drivers:
1. **Frontend**: Custom Virtual DOM & Reconciler built in vanilla JavaScript (no React, Vue, etc.).
2. **Backend**: Custom HTTP/1.1 server built using raw TCP sockets and an event loop with non-blocking callbacks (no `async`/`await`, no coroutines, no Flask/Express).
3. **Database**: Custom SQLite-inspired database engine with a 4KB disk pager, binary row serialization, and B-Tree leaf node storage.

---

## 📚 Human-Written References & Reading List

This project is built directly by studying and referencing these human-written engineering guides:

### 1. Custom Virtual DOM & Reconciler (Frontend)
* [**Build your own React** by Rodrigo Pombo](https://pomb.us/build-your-own-react/)
  * Repository: [pomber/didact](https://github.com/pomber/didact)
  * *Concepts*: Element creation (`createElement`), Fiber architecture, render and commit phases, reconciliation diffing, hooks.
* [**How to write your own Virtual DOM** by Gleb Bielieiakou (deathmood)](https://github.com/deathmood)
  * *Concepts*: Virtual DOM representation, tree diffing (`diff(parent, oldVNode, newVNode)`), property patching, and event listeners.

### 2. Raw Socket Server with Callbacks (Backend)
* [**A Web Crawler With asyncio Coroutines — Section: "The Callback Approach"** by A. Jesse Jiryu Davis and Guido van Rossum](https://aosabook.org/en/500L/a-web-crawler-with-asyncio-coroutines.html#the-callback-approach) *(500 Lines or Less / Architecture of Open Source Applications)*
  * *Concepts*: Non-blocking sockets (`O_NONBLOCK`), OS I/O multiplexing (`selectors`), and event-driven callback chains without coroutines.
* [**Let's Build A Web Server (Parts 1-3)** by Ruslan Spivak](https://ruslanspivak.com/lsbaws-part1/)
  * *Concepts*: Berkeley sockets (`socket`, `bind`, `listen`, `accept`), byte buffers, manual HTTP/1.1 parsing.
* [**Beej's Guide to Network Programming** by Brian "Beej" Hall](https://beej.us/guide/bgnet/html/)
  * *Concepts*: Low-level socket APIs and `select()` multiplexing.

### 3. Custom SQLite Database Engine (Storage)
* [**Let's Build a Simple Database** by Connor Stack (cstack)](https://cstack.github.io/db_tutorial/)
  * *Concepts*: SQLite architecture, disk pager (4KB pages), binary serialization with `struct`, cursor traversal, and B-Tree leaf node layout.

---

## 🏗 Architecture

```
 ┌────────────────────────────────────────────────────────┐
 │   PILLAR 1: Browser Frontend (Custom Reconciler/VDOM)  │
 │   - Virtual DOM tree (h / createElement)               │
 │   - Diffing & patching real DOM nodes                  │
 └───────────────────────────▲────────────────────────────┘
                             │ HTTP / JSON (via fetch)
 ┌───────────────────────────▼────────────────────────────┐
 │   PILLAR 2: Backend (Raw Sockets + Callback Loop)      │
 │   - Non-blocking TCP sockets (O_NONBLOCK)              │
 │   - OS Event Demultiplexer (select / epoll / selectors)│
 │   - Pure Callback Chains (NO coroutines / async-await) │
 │   - Hand-rolled HTTP/1.1 parser & router               │
 └───────────────────────────▲────────────────────────────┘
                             │ Disk I/O & B-Tree queries
 ┌───────────────────────────▼────────────────────────────┐
 │   PILLAR 3: SQLite Clone Database (From Scratch)       │
 │   - 4KB Disk Pager (file persistence & caching)        │
 │   - Binary Row Serializer                              │
 │   - B-Tree Leaf Storage & Key Search                   │
 │   - SQL / Command Executor                             │
 └────────────────────────────────────────────────────────┘
```

---

## 📂 Project Structure

```
from-scratch-todo/
├── README.md        # Complete guide, references & documentation
├── database.py      # SQLite clone: 4KB Pager, binary packing, B-Tree leaf
├── router.py        # HTTP parser & routing to database
├── server.py        # Raw TCP socket server with callback event loop
├── index.html       # HTML entry point
└── app.js           # Custom Virtual DOM reconciler & Todo UI
```

---

## 🚀 How to Run Locally

1. Start the backend server:
   ```bash
   python3 server.py
   ```
2. Open your web browser and navigate to:
   ```
   http://127.0.0.1:8000
   ```
3. Test creating, toggling, and deleting todos. Check that `todos.db` is created in the directory to persist data across restarts.
