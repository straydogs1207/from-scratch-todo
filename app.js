// ========================================================
// PILLAR 1: CUSTOM VIRTUAL DOM & RECONCILER (FROM SCRATCH)
// References:
// - Rodrigo Pombo: "Build your own React" (https://pomb.us/build-your-own-react/)
// - Gleb Bielieiakou: "How to write your own Virtual DOM"
// ========================================================

// 1. Virtual Node Creator
function h(type, props, ...children) {
  return {
    type,
    props: {
      ...(props || {}),
      children: children.flat().map(child =>
        typeof child === "object" && child !== null
          ? child
          : createTextElement(child)
      ),
    },
  };
}

function createTextElement(text) {
  return {
    type: "TEXT_ELEMENT",
    props: {
      nodeValue: text ?? "",
      children: [],
    },
  };
}

// 2. Materialize Real DOM Node from Virtual Node
function createRealDOM(vnode) {
  const dom =
    vnode.type === "TEXT_ELEMENT"
      ? document.createTextNode("")
      : document.createElement(vnode.type);

  updateProps(dom, {}, vnode.props);

  vnode.props.children.forEach(child => {
    dom.appendChild(createRealDOM(child));
  });

  return dom;
}

// 3. Diff and Patch Properties (Attributes & Event Listeners)
function updateProps(dom, oldProps = {}, newProps = {}) {
  // Remove old or removed event listeners and attributes
  for (const name in oldProps) {
    if (name === "children") continue;
    if (name.startsWith("on")) {
      const eventType = name.toLowerCase().substring(2);
      dom.removeEventListener(eventType, oldProps[name]);
    } else if (!(name in newProps)) {
      dom.removeAttribute(name);
    }
  }

  // Set new or changed attributes and event listeners
  for (const name in newProps) {
    if (name === "children") continue;
    if (oldProps[name] !== newProps[name]) {
      if (name.startsWith("on")) {
        const eventType = name.toLowerCase().substring(2);
        dom.addEventListener(eventType, newProps[name]);
      } else if (name === "nodeValue") {
        dom.nodeValue = newProps[name];
      } else if (name === "checked" || name === "value") {
        dom[name] = newProps[name];
      } else {
        dom.setAttribute(name, newProps[name]);
      }
    }
  }
}

// 4. The Core Reconciler (Diff Algorithm)
function diff(parentDOM, oldVNode, newVNode, index = 0) {
  const currentDOM = parentDOM.childNodes[index];

  // 1. Node was removed
  if (!newVNode) {
    if (currentDOM) parentDOM.removeChild(currentDOM);
    return;
  }

  // 2. Node was added
  if (!oldVNode) {
    parentDOM.appendChild(createRealDOM(newVNode));
    return;
  }

  // 3. Node type changed (replace node completely)
  if (oldVNode.type !== newVNode.type) {
    parentDOM.replaceChild(createRealDOM(newVNode), currentDOM);
    return;
  }

  // 4. Same node type: update props & reconcile children
  if (newVNode.type === "TEXT_ELEMENT") {
    if (oldVNode.props.nodeValue !== newVNode.props.nodeValue) {
      currentDOM.nodeValue = newVNode.props.nodeValue;
    }
  } else {
    updateProps(currentDOM, oldVNode.props, newVNode.props);
  }

  const oldChildren = oldVNode.props.children;
  const newChildren = newVNode.props.children;
  const maxLen = Math.max(oldChildren.length, newChildren.length);

  for (let i = 0; i < maxLen; i++) {
    diff(currentDOM, oldChildren[i], newChildren[i], i);
  }
}

// ========================================================
// APPLICATION STATE & UI LOGIC
// ========================================================

let state = {
  todos: [],
  inputValue: ""
};

let oldVNode = null;
const root = document.getElementById("root");

function fetchTodos() {
  fetch("/api/todos")
    .then(res => res.json())
    .then(data => {
      state.todos = data;
      renderApp();
    })
    .catch(err => console.error("Error fetching todos:", err));
}

function addTodo() {
  const title = state.inputValue.trim();
  if (!title) return;

  fetch("/api/todos", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title: title })
  }).then(() => {
    state.inputValue = "";
    fetchTodos();
  });
}

function toggleTodo(id, currentStatus) {
  fetch(`/api/todos/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ completed: !currentStatus })
  }).then(fetchTodos);
}

function deleteTodo(id) {
  fetch(`/api/todos/${id}`, { method: "DELETE" }).then(fetchTodos);
}

// Declarative UI View
function view(state) {
  return h("div", { class: "todo-app" },
    h("h1", null, "From-Scratch Todo"),
    h("div", { class: "subtitle" }, "Custom Reconciler • Callback Sockets • SQLite Clone"),
    h("div", { class: "input-group" },
      h("input", {
        type: "text",
        placeholder: "What needs to be done?",
        value: state.inputValue,
        onInput: (e) => {
          state.inputValue = e.target.value;
        },
        onKeydown: (e) => {
          if (e.key === "Enter") addTodo();
        }
      }),
      h("button", { class: "add-btn", onClick: addTodo }, "Add")
    ),
    h("ul", { class: "todo-list" },
      ...state.todos.map(todo =>
        h("li", { class: todo.completed ? "completed" : "" },
          h("input", {
            type: "checkbox",
            checked: todo.completed,
            onClick: () => toggleTodo(todo.id, todo.completed)
          }),
          h("span", null, todo.title),
          h("button", { class: "del-btn", onClick: () => deleteTodo(todo.id) }, "×")
        )
      )
    )
  );
}

function renderApp() {
  const newVNode = view(state);
  diff(root, oldVNode, newVNode);
  oldVNode = newVNode;
}

// Initial fetch
fetchTodos();
