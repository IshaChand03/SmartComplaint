function getToken() {
  return localStorage.getItem("token");
}

function saveLogin(token, user) {
  localStorage.setItem("token", token);
  localStorage.setItem("user", JSON.stringify(user));
}

function logout() {
  localStorage.clear();
  window.location.href = "/login";
}

// Calls your Flask API and sends the token automatically
async function api(url, options = {}) {
  const headers = { "Content-Type": "application/json" };
  const token = getToken();
  if (token) headers["Authorization"] = "Bearer " + token;

  const response = await fetch(url, { ...options, headers });

  let data;
  try {
    data = await response.json();
  } catch (error) {
    data = { error: "Server error (" + response.status + ")" };
  }

  // An expired or invalid token sends the user back to login
  if (response.status === 401 && !url.startsWith("/api/auth")) {
    logout();
  }
  return { ok: response.ok, status: response.status, data: data };
}

// Times are shown exactly as stored (the server adds a "GMT" label we don't want)
function formatTime(value) {
  if (!value) return "-";
  return String(value).replace(" GMT", "");
}

// Builds an HTML element safely (text is never treated as HTML)
function makeEl(tag, text, className) {
  const element = document.createElement(tag);
  if (text !== undefined && text !== null) element.textContent = text;
  if (className) element.className = className;
  return element;
}

function makeLink(text, href) {
  const link = makeEl("a", text);
  link.href = href;
  return link;
}

function makeBadge(priority) {
  return makeEl("span", priority, "badge " + priority);
}

function makeButton(text, onclick) {
  const button = makeEl("button", text);
  button.onclick = onclick;
  return button;
}

function makeInput(type, placeholder, value) {
  const input = makeEl("input");
  input.type = type;
  if (placeholder) input.placeholder = placeholder;
  if (value !== undefined && value !== null) input.value = value;
  return input;
}

function makeNumber(value, min) {
  const input = makeInput("number", "", value);
  input.min = min;
  input.className = "num-input";
  return input;
}

// options = [[value, label], ...]
function makeSelect(options, selected) {
  const select = makeEl("select");
  options.forEach(([value, label]) => {
    const option = makeEl("option", label);
    option.value = value;
    if (String(value) === String(selected)) option.selected = true;
    select.appendChild(option);
  });
  return select;
}

// Draws a table. Each cell can be text or an HTML element (link, input, button)
function renderTable(container, headers, rows) {
  container.replaceChildren();

  const wrap = makeEl("div", null, "table-wrap");
  const table = makeEl("table");

  const headRow = makeEl("tr");
  headers.forEach((h) => headRow.appendChild(makeEl("th", h)));
  const thead = makeEl("thead");
  thead.appendChild(headRow);

  const tbody = makeEl("tbody");
  rows.forEach((cells) => {
    const tr = makeEl("tr");
    cells.forEach((cell) => {
      const td = makeEl("td");
      if (cell instanceof Node) {
        td.appendChild(cell);
      } else {
        td.textContent = (cell === null || cell === undefined) ? "-" : cell;
      }
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  });

  table.append(thead, tbody);
  wrap.appendChild(table);
  container.appendChild(wrap);

  if (rows.length === 0) {
    container.appendChild(makeEl("p", "Nothing to show."));
  }
}

// Sends the visitor to login if they have no token, and returns the saved user
function requireLogin() {
  if (!getToken()) window.location.href = "/login";
  return JSON.parse(localStorage.getItem("user") || "{}");
}

function isActive(href) {
  const path = window.location.pathname;
  if (href === "/complaints") {
    return path === "/complaints" ||
           (path.startsWith("/complaints/") && path !== "/complaints/new");
  }
  return path === href;
}

// The menu: a sidebar on the left, and a small header on the right
function buildTopbar(user) {
  document.body.classList.add("with-sidebar");

  const links = [
    ["📊", "Dashboard", "/dashboard"],
    ["📋", "Complaints", "/complaints"],
    ["➕", "New complaint", "/complaints/new"],
    ["⏱️", "Queues", "/queues"]
  ];
  if (user.role === "Admin") links.push(["⚙️", "Admin", "/admin"]);

  const sidebar = makeEl("nav", null, "sidebar");
  sidebar.appendChild(makeEl("div", "SmartComplaint", "brand"));
  links.forEach(([icon, label, href]) => {
    const link = makeLink(icon + "  " + label, href);
    if (isActive(href)) link.classList.add("active");
    sidebar.appendChild(link);
  });
  document.body.prepend(sidebar);

  const bar = document.getElementById("topbar");
  bar.className = "topbar";
  bar.replaceChildren();
  bar.append(
    makeEl("span", user.name || "", "who"),
    makeEl("span", user.role || "", "role-tag"),
    makeButton("Log out", logout)
  );
}