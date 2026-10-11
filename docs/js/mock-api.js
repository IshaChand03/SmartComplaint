(function () {
  "use strict";

  const H = 3600000;
  const KEY = "smartresolve_demo_v1";
  const STATUSES = ["Open", "Assigned", "In Progress", "Resolved", "Closed", "Escalated"];
  const PRIORITIES = ["Low", "Medium", "High", "Critical"];
  const ROLES = ["Admin", "Manager", "Support Agent", "Customer"];
  const PRIORITY_NAMES = { 1: "Low", 2: "Medium", 3: "High", 4: "Critical" };
  const TRANSITIONS = {
    "Assigned": ["In Progress"],
    "In Progress": ["Resolved"],
    "Resolved": ["Closed"],
    "Escalated": ["In Progress"]
  };
  const NEGATIVE = ["angry", "frustrated", "failed", "broken", "cheated", "fraud", "terrible", "worst", "bad", "disappointed", "unhappy", "useless"];
  const POSITIVE = ["thanks", "thank", "great", "resolved", "good", "happy", "excellent", "satisfied", "helpful"];
  const HIGH_IMPACT = ["urgent", "immediately", "emergency", "fraud", "failed", "unauthorized", "hacked", "stolen", "money deducted", "not working"];

  let db = null;

  /* ---------- small helpers ---------- */

  function pad(n) { return String(n).padStart(2, "0"); }
  function fmt(ms) {
    if (!ms) return null;
    const d = new Date(ms);
    return d.getFullYear() + "-" + pad(d.getMonth() + 1) + "-" + pad(d.getDate()) + " " +
      pad(d.getHours()) + ":" + pad(d.getMinutes()) + ":" + pad(d.getSeconds());
  }
  function nextId(list) { return list.reduce(function (m, x) { return Math.max(m, x.id); }, 0) + 1; }
  function fail(status, error) { return { status: status, data: { error: error } }; }
  function ok(data, status) { return { status: status || 200, data: data }; }
  function isPosInt(v) { return Number.isInteger(v) && v > 0; }
  function refNo(ms, id) {
    const d = new Date(ms);
    return "CMP-" + d.getFullYear() + pad(d.getMonth() + 1) + pad(d.getDate()) + "-" + String(id).padStart(6, "0");
  }
  function byName(a, b) { return a.name.localeCompare(b.name); }

  function getUser(id) { return db.users.find(function (u) { return u.id === id; }); }
  function userName(id) { const u = getUser(id); return u ? u.name : "Unknown"; }
  function getComplaint(id) { return db.complaints.find(function (c) { return c.id === id; }); }
  function deptName(id) {
    const d = db.departments.find(function (x) { return x.id === id; });
    return d ? d.name : null;
  }
  function catName(id) {
    const c = db.categories.find(function (x) { return x.id === id; });
    return c ? c.name : null;
  }
  function save() {
    try { localStorage.setItem(KEY, JSON.stringify(db)); } catch (e) {}
  }

  function addHistory(cid, action, oldV, newV, by, time) {
    db.history.push({ id: nextId(db.history), complaint_id: cid, action: action, old_value: oldV, new_value: newV, changed_by: by, created_at: time || Date.now() });
  }
  function addComment(cid, uid, text, system, time) {
    db.comments.push({ id: nextId(db.comments), complaint_id: cid, user_id: uid, comment_text: text, is_system: !!system, created_at: time || Date.now() });
  }
  function addAudit(action, type, id, details, by, time) {
    db.audit.push({ id: nextId(db.audit), action_name: action, entity_type: type, entity_id: id, details: details, user_id: by, created_at: time || Date.now() });
  }

  /* ---------- the three engines ---------- */

  function analyzeSentiment(text) {
    const words = text.toLowerCase().match(/[a-z']+/g) || [];
    let neg = 0, pos = 0;
    words.forEach(function (w) {
      if (NEGATIVE.indexOf(w) >= 0) neg++;
      if (POSITIVE.indexOf(w) >= 0) pos++;
    });
    if (neg > pos) return "Negative";
    if (pos > neg) return "Positive";
    return "Neutral";
  }

  function calculatePriority(urgency, text, sentiment, critical) {
    let score = urgency;
    const reasons = ["Urgency " + urgency];
    const lower = text.toLowerCase();
    const found = HIGH_IMPACT.filter(function (k) { return lower.indexOf(k) >= 0; });
    if (found.length) { score += 1; reasons.push("High-impact words: " + found.join(", ")); }
    if (sentiment === "Negative") { score += 1; reasons.push("Negative sentiment"); }
    if (critical) { score += 1; reasons.push("Critical category"); }
    score = Math.min(score, 4);
    return { score: score, priority: PRIORITY_NAMES[score], reasons: reasons };
  }

  function slaMap() {
    const m = {};
    db.sla_rules.forEach(function (r) { m[r.priority] = r; });
    return m;
  }

  function slaState(c, rules) {
    if (c.status === "Resolved" || c.status === "Closed") return "Completed";
    const rule = rules[c.priority];
    if (!c.due_at || !rule) return "Unknown";
    const now = Date.now();
    if (now > c.due_at) return "Breached";
    if (now >= c.due_at - rule.near_breach_hours * H) return "Near";
    return "Within";
  }

  /* ---------- automatic escalation (runs on every request) ---------- */

  function runEscalation() {
    const rules = {};
    db.escalation_rules.forEach(function (r) { rules[r.priority] = r; });
    const now = Date.now();
    let changed = false;

    db.complaints.forEach(function (c) {
      if (["Open", "Assigned", "In Progress"].indexOf(c.status) < 0 || !c.due_at) return;
      if (db.escalations.some(function (e) { return e.complaint_id === c.id; })) return;
      const rule = rules[c.priority];
      if (!rule) return;
      if (now <= c.due_at + rule.grace_hours * H) return;

      const manager = db.users.find(function (u) { return u.role === "Manager" && u.department_id === c.department_id; });
      const reason = "SLA breached (" + c.priority + " priority) and the " + rule.grace_hours + "-hour grace period has passed";
      const oldStatus = c.status;
      c.status = "Escalated";
      db.escalations.push({ id: nextId(db.escalations), complaint_id: c.id, level: rule.escalation_level, manager_id: manager ? manager.id : null, reason: reason, created_at: now });
      addHistory(c.id, "Status changed", oldStatus, "Escalated", 0, now);
      addComment(c.id, 0, "SLA breached. Escalated to " + (manager ? manager.name : "no manager found") + ".", true, now);
      addAudit("COMPLAINT_ESCALATED", "complaint", c.id, reason, 0, now);
      changed = true;
    });
    if (changed) save();
  }

  /* ---------- sample data ---------- */

  function seed() {
    const now = Date.now();
    const old = now - 40 * 24 * H;
    db = {
      users: [
        { id: 1, name: "Isha", email: "isha@test.com", password: "123456", role: "Admin", department_id: null, created_at: old },
        { id: 2, name: "Agent One", email: "agent@test.com", password: "123456", role: "Support Agent", department_id: 1, created_at: old },
        { id: 3, name: "Manager One", email: "manager@test.com", password: "123456", role: "Manager", department_id: 1, created_at: old },
        { id: 4, name: "Customer One", email: "customer@test.com", password: "123456", role: "Customer", department_id: null, created_at: old },
        { id: 5, name: "Agent Two", email: "agent2@test.com", password: "123456", role: "Support Agent", department_id: 2, created_at: old },
        { id: 6, name: "Customer Two", email: "customer2@test.com", password: "123456", role: "Customer", department_id: null, created_at: old },
        { id: 0, name: "System", email: "system@smartresolve.local", password: "!", role: "Admin", department_id: null, created_at: old, system: true }
      ],
      departments: [
        { id: 1, name: "Finance & Accounts" },
        { id: 2, name: "IT / Technical Support" },
        { id: 3, name: "Customer Support" },
        { id: 4, name: "Security / Risk" }
      ],
      categories: [
        { id: 1, name: "Billing & Payments", department_id: 1, is_critical: true },
        { id: 2, name: "Technical Issue", department_id: 2, is_critical: false },
        { id: 3, name: "Account & Login", department_id: 3, is_critical: false },
        { id: 4, name: "Security / Fraud", department_id: 4, is_critical: true }
      ],
      sla_rules: [
        { id: 1, priority: "Critical", resolution_hours: 4, near_breach_hours: 1 },
        { id: 2, priority: "High", resolution_hours: 8, near_breach_hours: 1 },
        { id: 3, priority: "Medium", resolution_hours: 24, near_breach_hours: 2 },
        { id: 4, priority: "Low", resolution_hours: 48, near_breach_hours: 4 }
      ],
      escalation_rules: [
        { id: 1, priority: "Critical", grace_hours: 0, escalation_level: 1, target_role: "Manager" },
        { id: 2, priority: "High", grace_hours: 1, escalation_level: 1, target_role: "Manager" },
        { id: 3, priority: "Medium", grace_hours: 2, escalation_level: 1, target_role: "Manager" },
        { id: 4, priority: "Low", grace_hours: 4, escalation_level: 1, target_role: "Manager" }
      ],
      complaints: [], history: [], comments: [], escalations: [], audit: []
    };

    function create(o) {
      const created = now - o.ageH * H;
      const cat = db.categories.find(function (c) { return c.id === o.cat; });
      const rule = db.sla_rules.find(function (r) { return r.priority === o.priority; });
      const id = nextId(db.complaints);
      db.complaints.push({
        id: id, reference_no: refNo(created, id), title: o.title, description: o.text,
        category_id: cat.id, department_id: cat.department_id, urgency: o.urgency,
        sentiment: o.sentiment, priority: o.priority, status: "Open",
        due_at: created + rule.resolution_hours * H, raised_by: o.by, assigned_to: null, created_at: created
      });
      addHistory(id, "Created", null, "Open", o.by, created);
      return id;
    }
    function assign(id, agentId, byId, ageH) {
      const c = getComplaint(id);
      c.assigned_to = agentId;
      c.status = "Assigned";
      addHistory(id, "Assigned", null, userName(agentId), byId, now - ageH * H);
      addHistory(id, "Status changed", "Open", "Assigned", byId, now - ageH * H);
    }
    function move(id, to, byId, ageH) {
      const c = getComplaint(id);
      addHistory(id, "Status changed", c.status, to, byId, now - ageH * H);
      c.status = to;
    }
    function say(id, uid, text, ageH) { addComment(id, uid, text, false, now - ageH * H); }

    const c1 = create({ title: "Payment failed three times", text: "My payment failed three times. I am frustrated and this is urgent.", cat: 1, urgency: 4, sentiment: "Negative", priority: "Critical", by: 4, ageH: 30 });
    assign(c1, 2, 1, 29.5);
    move(c1, "In Progress", 2, 29);
    say(c1, 2, "Checking the payment gateway logs now.", 28.8);
    move(c1, "Resolved", 2, 27);
    say(c1, 2, "The gateway timeout is fixed. Please try again.", 26.9);
    move(c1, "Closed", 4, 26);

    const c2 = create({ title: "Refund not received", text: "I am frustrated. My refund has not arrived and I need it urgently.", cat: 1, urgency: 3, sentiment: "Negative", priority: "Critical", by: 4, ageH: 1 });
    assign(c2, 2, 3, 0.9);
    move(c2, "In Progress", 2, 0.8);
    say(c2, 4, "Any update, please?", 0.7);
    say(c2, 2, "Looking into this now.", 0.6);

    const c3 = create({ title: "App crashes on startup", text: "The mobile app crashes every time I open it.", cat: 2, urgency: 3, sentiment: "Neutral", priority: "High", by: 6, ageH: 7.3 });
    assign(c3, 5, 1, 7.2);

    const c4 = create({ title: "Charged twice on invoice", text: "I was charged twice and this is an emergency. I am angry.", cat: 1, urgency: 3, sentiment: "Negative", priority: "Critical", by: 4, ageH: 10 });
    assign(c4, 2, 1, 9.9);
    move(c4, "Escalated", 0, 6);
    const reason = "SLA breached (Critical priority) and the 0-hour grace period has passed";
    db.escalations.push({ id: 1, complaint_id: c4, level: 1, manager_id: 3, reason: reason, created_at: now - 6 * H });
    addComment(c4, 0, "SLA breached. Escalated to Manager One.", true, now - 6 * H);
    addAudit("COMPLAINT_ESCALATED", "complaint", c4, reason, 0, now - 6 * H);

    create({ title: "Update my phone number", text: "I would like to update the phone number on my account.", cat: 3, urgency: 2, sentiment: "Neutral", priority: "Medium", by: 6, ageH: 2 });
    create({ title: "How do I change my display name?", text: "Thanks for the great app. How do I change my display name?", cat: 3, urgency: 1, sentiment: "Positive", priority: "Low", by: 4, ageH: 5 });

    addAudit("CATEGORY_UPDATED", "category", 1, "'Billing & Payments': critical false -> true", 1, now - 20 * H);
    addAudit("SLA_RULE_UPDATED", "sla_rule", 1, "Critical: resolution 6h -> 4h, near 2h -> 1h", 1, now - 19 * H);
  }

  function load() {
    try {
      const raw = localStorage.getItem(KEY);
      if (raw) { db = JSON.parse(raw); return; }
    } catch (e) {}
    seed();
    save();
  }

  /* ---------- who is logged in, and what they may see ---------- */

  function currentUser() {
    const token = localStorage.getItem("token") || "";
    const m = token.match(/^demo-token-(\d+)$/);
    if (!m) return null;
    const u = getUser(Number(m[1]));
    return u && !u.system ? u : null;
  }

  function canView(user, c) {
    if (user.role === "Admin") return true;
    if (user.role === "Manager") return c.department_id === user.department_id;
    if (user.role === "Support Agent") return c.assigned_to === user.id;
    return c.raised_by === user.id;
  }
  function scoped(user) { return db.complaints.filter(function (c) { return canView(user, c); }); }

  function brief(c, rules) {
    return {
      id: c.id, reference_no: c.reference_no, title: c.title, priority: c.priority,
      status: c.status, sentiment: c.sentiment, due_at: fmt(c.due_at),
      category: catName(c.category_id), department: deptName(c.department_id),
      created_at: fmt(c.created_at), sla_state: slaState(c, rules)
    };
  }

  /* ---------- login and register ---------- */

  function register(body) {
    const name = String(body.name || "").trim();
    const email = String(body.email || "").trim().toLowerCase();
    const password = String(body.password || "");
    if (!name || !email || !password) return fail(400, "Name, email and password are required");
    if (password.length < 6) return fail(400, "Password must be at least 6 characters");
    if (db.users.some(function (u) { return u.email === email; })) return fail(409, "Email already registered");
    db.users.push({ id: nextId(db.users), name: name, email: email, password: password, role: "Customer", department_id: null, created_at: Date.now() });
    save();
    return ok({ message: "Registration successful" }, 201);
  }

  function login(body) {
    const email = String(body.email || "").trim().toLowerCase();
    const password = String(body.password || "");
    if (!email || !password) return fail(400, "Email and password are required");
    const user = db.users.find(function (u) { return u.email === email && !u.system; });
    if (!user || user.password !== password) return fail(401, "Invalid email or password");
    return ok({ token: "demo-token-" + user.id, user: { id: user.id, name: user.name, role: user.role } });
  }

  /* ---------- dashboards ---------- */

  function dashboard(user) {
    const rows = scoped(user);
    const rules = slaMap();
    const byStatus = {}, byPriority = {};
    STATUSES.forEach(function (s) { byStatus[s] = 0; });
    PRIORITIES.forEach(function (p) { byPriority[p] = 0; });
    let breached = 0;
    rows.forEach(function (c) {
      byStatus[c.status]++;
      byPriority[c.priority]++;
      if (slaState(c, rules) === "Breached") breached++;
    });
    return ok({
      total: rows.length, open: byStatus["Open"], in_progress: byStatus["In Progress"],
      resolved: byStatus["Resolved"], escalated: byStatus["Escalated"], breached: breached,
      by_status: byStatus, by_priority: byPriority
    });
  }

  function myQueue(user) {
    const rules = slaMap();
    const rows = db.complaints
      .filter(function (c) { return c.assigned_to === user.id && c.status !== "Resolved" && c.status !== "Closed"; })
      .sort(function (a, b) { return a.due_at - b.due_at; })
      .map(function (c) { return brief(c, rules); });
    return ok({ count: rows.length, complaints: rows });
  }

  function slaTracking(user) {
    const rules = slaMap();
    const groups = { Within: [], Near: [], Breached: [] };
    scoped(user).slice().sort(function (a, b) { return a.due_at - b.due_at; }).forEach(function (c) {
      const s = slaState(c, rules);
      if (groups[s]) groups[s].push(brief(c, rules));
    });
    return ok({
      within_count: groups.Within.length, near_count: groups.Near.length, breached_count: groups.Breached.length,
      within: groups.Within, near: groups.Near, breached: groups.Breached
    });
  }

  function escalationsView(user) {
    const ids = scoped(user).map(function (c) { return c.id; });
    const rows = db.escalations
      .filter(function (e) { return ids.indexOf(e.complaint_id) >= 0; })
      .sort(function (a, b) { return b.created_at - a.created_at; })
      .map(function (e) {
        const c = getComplaint(e.complaint_id);
        return {
          complaint_id: c.id, reference_no: c.reference_no, title: c.title, priority: c.priority,
          status: c.status, level: e.level, manager: e.manager_id ? userName(e.manager_id) : null,
          reason: e.reason, escalated_at: fmt(e.created_at)
        };
      });
    return ok({ count: rows.length, escalations: rows });
  }

  /* ---------- reference data ---------- */

  function categoriesList() {
    return ok(db.categories.slice().sort(byName).map(function (c) {
      return { id: c.id, name: c.name, is_critical: c.is_critical, department: deptName(c.department_id) };
    }));
  }
  function departmentsList() {
    return ok(db.departments.slice().sort(byName).map(function (d) { return { id: d.id, name: d.name }; }));
  }
  function agentsList(user, q) {
    if (user.role !== "Admin" && user.role !== "Manager") return fail(403, "Only Admin or Manager can list agents");
    let dept = q.get("department_id") || "";
    if (user.role === "Manager") dept = String(user.department_id);
    else if (dept && !/^\d+$/.test(dept)) return fail(400, "department_id must be a number");
    const rows = db.users
      .filter(function (u) { return !u.system && u.role === "Support Agent" && (!dept || u.department_id === Number(dept)); })
      .sort(byName)
      .map(function (u) { return { id: u.id, name: u.name, email: u.email, department: deptName(u.department_id) }; });
    return ok(rows);
  }

  /* ---------- complaints ---------- */

  function listComplaints(user, q) {
    const search = (q.get("search") || "").trim().toLowerCase();
    const status = (q.get("status") || "").trim();
    const priority = (q.get("priority") || "").trim();
    let page = parseInt(q.get("page") || "1", 10);
    let size = parseInt(q.get("page_size") || "10", 10);
    if (isNaN(page) || isNaN(size)) return fail(400, "page and page_size must be numbers");
    page = Math.max(page, 1);
    size = Math.min(Math.max(size, 1), 50);
    if (status && STATUSES.indexOf(status) < 0) return fail(400, "status must be one of: " + STATUSES.join(", "));
    if (priority && PRIORITIES.indexOf(priority) < 0) return fail(400, "priority must be one of: " + PRIORITIES.join(", "));

    const rules = slaMap();
    const rows = scoped(user).filter(function (c) {
      const hit = !search || [c.title, c.description, c.reference_no].some(function (f) { return f.toLowerCase().indexOf(search) >= 0; });
      return hit && (!status || c.status === status) && (!priority || c.priority === priority);
    }).sort(function (a, b) { return (b.created_at - a.created_at) || (b.id - a.id); });

    const total = rows.length;
    const pageRows = rows.slice((page - 1) * size, page * size).map(function (c) { return brief(c, rules); });
    return ok({ page: page, page_size: size, total: total, total_pages: Math.ceil(total / size), complaints: pageRows });
  }

  function createComplaint(user, body) {
    const title = String(body.title || "").trim();
    const description = String(body.description || "").trim();
    const categoryId = body.category_id;
    const urgency = body.urgency;
    if (!title || !description || !categoryId || urgency === undefined || urgency === null) {
      return fail(400, "title, description, category_id and urgency are required");
    }
    if (!Number.isInteger(urgency) || [1, 2, 3, 4].indexOf(urgency) < 0) return fail(400, "urgency must be a number from 1 to 4");
    const cat = db.categories.find(function (c) { return c.id === categoryId; });
    if (!cat) return fail(404, "Category not found");

    const text = title + " " + description;
    const sentiment = analyzeSentiment(text);
    const result = calculatePriority(urgency, text, sentiment, cat.is_critical);
    const rule = db.sla_rules.find(function (r) { return r.priority === result.priority; });
    const created = Date.now();
    const due = created + rule.resolution_hours * H;
    const id = nextId(db.complaints);
    const reference = refNo(created, id);

    db.complaints.push({
      id: id, reference_no: reference, title: title, description: description,
      category_id: cat.id, department_id: cat.department_id, urgency: urgency,
      sentiment: sentiment, priority: result.priority, status: "Open",
      due_at: due, raised_by: user.id, assigned_to: null, created_at: created
    });
    addHistory(id, "Created", null, "Open", user.id);
    save();
    return ok({
      message: "Complaint raised successfully", id: id, reference_no: reference,
      sentiment: sentiment, priority: result.priority, priority_score: result.score,
      reasons: result.reasons, due_at: fmt(due), status: "Open"
    }, 201);
  }

  function complaintDetails(user, id) {
    const c = getComplaint(id);
    if (!c) return fail(404, "Complaint not found");
    if (!canView(user, c)) return fail(403, "You do not have permission to view this complaint");
    const out = brief(c, slaMap());
    out.description = c.description;
    out.urgency = c.urgency;
    out.department_id = c.department_id;
    out.raised_by_name = userName(c.raised_by);
    out.assigned_to_name = c.assigned_to ? userName(c.assigned_to) : null;
    out.history = db.history.filter(function (h) { return h.complaint_id === id; }).map(function (h) {
      return { action: h.action, old_value: h.old_value, new_value: h.new_value, changed_by: userName(h.changed_by), created_at: fmt(h.created_at) };
    });
    return ok(out);
  }

  function assignComplaint(user, id, body) {
    const agentId = body.agent_id;
    if (!agentId) return fail(400, "agent_id is required");
    if (user.role !== "Admin" && user.role !== "Manager") return fail(403, "Only Admin or Manager can assign complaints");
    const c = getComplaint(id);
    if (!c) return fail(404, "Complaint not found");
    if (user.role === "Manager" && c.department_id !== user.department_id) return fail(403, "This complaint belongs to another department");
    if (c.status === "Resolved" || c.status === "Closed") return fail(400, "Cannot assign a resolved or closed complaint");
    const agent = getUser(agentId);
    if (!agent || agent.system || agent.role !== "Support Agent" || agent.department_id !== c.department_id) {
      return fail(400, "Agent must be a Support Agent in the complaint's department");
    }
    const oldAgent = c.assigned_to ? userName(c.assigned_to) : null;
    const oldStatus = c.status;
    const newStatus = oldStatus === "Open" ? "Assigned" : oldStatus;
    c.assigned_to = agent.id;
    c.status = newStatus;
    addHistory(id, "Assigned", oldAgent, agent.name, user.id);
    if (newStatus !== oldStatus) addHistory(id, "Status changed", oldStatus, newStatus, user.id);
    save();
    return ok({ message: "Assigned to " + agent.name, status: newStatus });
  }

  function changeStatus(user, id, body) {
    const newStatus = String(body.status || "").trim();
    const c = getComplaint(id);
    if (!c) return fail(404, "Complaint not found");
    const role = user.role;
    const allowed = role === "Admin" ||
      (role === "Manager" && c.department_id === user.department_id) ||
      (role === "Support Agent" && c.assigned_to === user.id) ||
      (role === "Customer" && c.raised_by === user.id && c.status === "Resolved" && newStatus === "Closed");
    if (!allowed) return fail(403, "You do not have permission to change this status");
    if ((TRANSITIONS[c.status] || []).indexOf(newStatus) < 0) return fail(400, "Cannot move from " + c.status + " to " + newStatus);
    const old = c.status;
    c.status = newStatus;
    addHistory(id, "Status changed", old, newStatus, user.id);
    save();
    return ok({ message: "Status updated", status: newStatus });
  }

  function postComment(user, id, body) {
    const text = String(body.comment || "").trim();
    if (!text) return fail(400, "Comment cannot be empty");
    if (text.length > 1000) return fail(400, "Comment is too long (maximum 1000 characters)");
    const c = getComplaint(id);
    if (!c) return fail(404, "Complaint not found");
    if (!canView(user, c)) return fail(403, "You do not have permission to comment on this complaint");
    if (c.status === "Closed") return fail(400, "This complaint is closed. No new comments allowed");
    addComment(id, user.id, text, false);
    save();
    return ok({ message: "Comment added" }, 201);
  }

  function activityFeed(user, id) {
    const c = getComplaint(id);
    if (!c) return fail(404, "Complaint not found");
    if (!canView(user, c)) return fail(403, "You do not have permission to view this complaint");
    const feed = [];
    db.history.filter(function (h) { return h.complaint_id === id; }).forEach(function (h) {
      let text;
      if (h.action === "Created") text = "Complaint created";
      else if (h.action === "Assigned") text = h.old_value ? "Reassigned from " + h.old_value + " to " + h.new_value : "Assigned to " + h.new_value;
      else text = "Status changed: " + h.old_value + " -> " + h.new_value;
      feed.push({ type: "system", actor: userName(h.changed_by), text: text, time: h.created_at });
    });
    db.comments.filter(function (cm) { return cm.complaint_id === id; }).forEach(function (cm) {
      const u = getUser(cm.user_id);
      feed.push({ type: "comment", actor: u.name, role: u.role, text: cm.comment_text, time: cm.created_at });
    });
    feed.sort(function (a, b) { return a.time - b.time; });
    return ok(feed.map(function (f) { f.time = fmt(f.time); return f; }));
  }

  /* ---------- admin ---------- */

  function adminUsers(q) {
    const role = (q.get("role") || "").trim();
    const dept = (q.get("department_id") || "").trim();
    if (role && ROLES.indexOf(role) < 0) return fail(400, "role must be one of: " + ROLES.join(", "));
    if (dept && !/^\d+$/.test(dept)) return fail(400, "department_id must be a number");
    const rows = db.users
      .filter(function (u) { return !u.system && (!role || u.role === role) && (!dept || u.department_id === Number(dept)); })
      .sort(function (a, b) { return a.id - b.id; })
      .map(function (u) {
        return { id: u.id, name: u.name, email: u.email, role: u.role, department_id: u.department_id, department: u.department_id ? deptName(u.department_id) : null, created_at: fmt(u.created_at) };
      });
    return ok(rows);
  }

  function adminUpdateUser(admin, id, body) {
    const target = getUser(id);
    if (!target || target.system) return fail(404, "User not found");
    const newRole = body.role !== undefined ? body.role : target.role;
    const newDept = body.department_id !== undefined ? body.department_id : target.department_id;
    if (ROLES.indexOf(newRole) < 0) return fail(400, "role must be one of: " + ROLES.join(", "));
    if (target.id === admin.id && newRole !== "Admin") return fail(400, "You cannot remove your own Admin role");
    if ((newRole === "Manager" || newRole === "Support Agent") && !newDept) return fail(400, "A " + newRole + " needs a department_id");
    if (newDept && !db.departments.some(function (d) { return d.id === newDept; })) return fail(404, "Department not found");
    addAudit("USER_UPDATED", "user", id, target.name + ": role " + target.role + " -> " + newRole + ", department " + target.department_id + " -> " + newDept, admin.id);
    target.role = newRole;
    target.department_id = newDept || null;
    save();
    return ok({ message: "User updated." });
  }

  function adminCreateDepartment(admin, body) {
    const name = String(body.name || "").trim();
    if (!name) return fail(400, "Name is required");
    if (db.departments.some(function (d) { return d.name === name; })) return fail(409, "Department already exists");
    const id = nextId(db.departments);
    db.departments.push({ id: id, name: name });
    addAudit("DEPARTMENT_CREATED", "department", id, "Created department '" + name + "'", admin.id);
    save();
    return ok({ message: "Department created", id: id }, 201);
  }

  function adminUpdateDepartment(admin, id, body) {
    const name = String(body.name || "").trim();
    if (!name) return fail(400, "Name is required");
    const dep = db.departments.find(function (d) { return d.id === id; });
    if (!dep) return fail(404, "Department not found");
    if (db.departments.some(function (d) { return d.name === name && d.id !== id; })) return fail(409, "Another department already has this name");
    addAudit("DEPARTMENT_UPDATED", "department", id, "Renamed '" + dep.name + "' to '" + name + "'", admin.id);
    dep.name = name;
    save();
    return ok({ message: "Department updated" });
  }

  function adminCreateCategory(admin, body) {
    const name = String(body.name || "").trim();
    const deptId = body.department_id;
    const critical = !!body.is_critical;
    if (!name || !deptId) return fail(400, "Name and department_id are required");
    if (!db.departments.some(function (d) { return d.id === deptId; })) return fail(404, "Department not found");
    if (db.categories.some(function (c) { return c.name === name; })) return fail(409, "Category already exists");
    const id = nextId(db.categories);
    db.categories.push({ id: id, name: name, department_id: deptId, is_critical: critical });
    addAudit("CATEGORY_CREATED", "category", id, "Created category '" + name + "' (department " + deptId + ", critical=" + critical + ")", admin.id);
    save();
    return ok({ message: "Category created", id: id }, 201);
  }

  function adminUpdateCategory(admin, id, body) {
    const cat = db.categories.find(function (c) { return c.id === id; });
    if (!cat) return fail(404, "Category not found");
    const name = body.name !== undefined ? String(body.name).trim() : cat.name;
    const deptId = body.department_id !== undefined ? body.department_id : cat.department_id;
    const critical = body.is_critical !== undefined ? !!body.is_critical : cat.is_critical;
    if (!name) return fail(400, "Name cannot be empty");
    if (!db.departments.some(function (d) { return d.id === deptId; })) return fail(404, "Department not found");
    if (db.categories.some(function (c) { return c.name === name && c.id !== id; })) return fail(409, "Another category already has this name");
    addAudit("CATEGORY_UPDATED", "category", id, "'" + cat.name + "' -> '" + name + "', department " + cat.department_id + " -> " + deptId + ", critical " + cat.is_critical + " -> " + critical, admin.id);
    cat.name = name;
    cat.department_id = deptId;
    cat.is_critical = critical;
    save();
    return ok({ message: "Category updated" });
  }

  function adminSlaList() {
    return ok(db.sla_rules.slice().sort(function (a, b) { return a.resolution_hours - b.resolution_hours; }).map(function (r) {
      return { priority: r.priority, resolution_hours: r.resolution_hours, near_breach_hours: r.near_breach_hours, active: true };
    }));
  }

  function adminSlaUpdate(admin, priority, body) {
    const rule = db.sla_rules.find(function (r) { return r.priority === priority; });
    if (!rule) return fail(404, "Priority must be one of: " + PRIORITIES.join(", "));
    const res = body.resolution_hours !== undefined ? body.resolution_hours : rule.resolution_hours;
    const near = body.near_breach_hours !== undefined ? body.near_breach_hours : rule.near_breach_hours;
    if (!isPosInt(res) || !isPosInt(near)) return fail(400, "Hours must be whole numbers greater than 0");
    if (near >= res) return fail(400, "near_breach_hours must be smaller than resolution_hours");
    addAudit("SLA_RULE_UPDATED", "sla_rule", rule.id, priority + ": resolution " + rule.resolution_hours + "h -> " + res + "h, near " + rule.near_breach_hours + "h -> " + near + "h", admin.id);
    rule.resolution_hours = res;
    rule.near_breach_hours = near;
    save();
    return ok({ message: "SLA rule updated" });
  }

  function adminEscList() {
    return ok(db.escalation_rules.map(function (r) {
      return { priority: r.priority, grace_hours: r.grace_hours, escalation_level: r.escalation_level, target_role: r.target_role, active: true };
    }));
  }

  function adminEscUpdate(admin, priority, body) {
    const rule = db.escalation_rules.find(function (r) { return r.priority === priority; });
    if (!rule) return fail(404, "Priority must be one of: " + PRIORITIES.join(", "));
    const grace = body.grace_hours !== undefined ? body.grace_hours : rule.grace_hours;
    const level = body.escalation_level !== undefined ? body.escalation_level : rule.escalation_level;
    const target = body.target_role !== undefined ? body.target_role : rule.target_role;
    if (!Number.isInteger(grace) || grace < 0) return fail(400, "grace_hours must be 0 or a positive whole number");
    if (!isPosInt(level)) return fail(400, "escalation_level must be a whole number greater than 0");
    if (target !== "Manager" && target !== "Admin") return fail(400, "target_role must be Manager or Admin");
    addAudit("ESCALATION_RULE_UPDATED", "escalation_rule", rule.id, priority + ": grace " + rule.grace_hours + "h -> " + grace + "h, level " + rule.escalation_level + " -> " + level + ", target " + rule.target_role + " -> " + target, admin.id);
    rule.grace_hours = grace;
    rule.escalation_level = level;
    rule.target_role = target;
    save();
    return ok({ message: "Escalation rule updated" });
  }

  function adminAudit(q) {
    const action = (q.get("action") || "").trim();
    let page = parseInt(q.get("page") || "1", 10);
    let size = parseInt(q.get("page_size") || "20", 10);
    if (isNaN(page) || isNaN(size)) return fail(400, "page and page_size must be numbers");
    page = Math.max(page, 1);
    size = Math.min(Math.max(size, 1), 100);
    const rows = db.audit
      .filter(function (a) { return !action || a.action_name === action; })
      .sort(function (a, b) { return (b.created_at - a.created_at) || (b.id - a.id); });
    const logs = rows.slice((page - 1) * size, page * size).map(function (a) {
      return { id: a.id, action_name: a.action_name, entity_type: a.entity_type, entity_id: a.entity_id, details: a.details, done_by: userName(a.user_id), created_at: fmt(a.created_at) };
    });
    return ok({ page: page, page_size: size, total: rows.length, total_pages: Math.ceil(rows.length / size), logs: logs });
  }

  /* ---------- the router ---------- */

  function handle(method, rawUrl, body) {
    runEscalation();
    const url = new URL(rawUrl, "http://demo.local");
    const path = url.pathname;
    const q = url.searchParams;
    let m;

    if (path === "/api/auth/register" && method === "POST") return register(body);
    if (path === "/api/auth/login" && method === "POST") return login(body);

    const user = currentUser();
    if (!user) return { status: 401, data: { msg: "Missing Authorization Header" } };
    if (path.indexOf("/api/admin/") === 0 && user.role !== "Admin") return fail(403, "You do not have permission");

    if (path === "/api/dashboard") return dashboard(user);
    if (path === "/api/dashboard/my-queue") return myQueue(user);
    if (path === "/api/dashboard/sla") return slaTracking(user);
    if (path === "/api/dashboard/escalations") return escalationsView(user);

    if (path === "/api/categories") return categoriesList();
    if (path === "/api/departments") return departmentsList();
    if (path === "/api/agents") return agentsList(user, q);

    if (path === "/api/complaints" && method === "GET") return listComplaints(user, q);
    if (path === "/api/complaints" && method === "POST") return createComplaint(user, body);
    if ((m = path.match(/^\/api\/complaints\/(\d+)$/)) && method === "GET") return complaintDetails(user, Number(m[1]));
    if ((m = path.match(/^\/api\/complaints\/(\d+)\/assign$/)) && method === "PUT") return assignComplaint(user, Number(m[1]), body);
    if ((m = path.match(/^\/api\/complaints\/(\d+)\/status$/)) && method === "PUT") return changeStatus(user, Number(m[1]), body);
    if ((m = path.match(/^\/api\/complaints\/(\d+)\/comments$/)) && method === "POST") return postComment(user, Number(m[1]), body);
    if ((m = path.match(/^\/api\/complaints\/(\d+)\/history$/)) && method === "GET") return activityFeed(user, Number(m[1]));

    if (path === "/api/admin/users" && method === "GET") return adminUsers(q);
    if ((m = path.match(/^\/api\/admin\/users\/(\d+)$/)) && method === "PUT") return adminUpdateUser(user, Number(m[1]), body);
    if (path === "/api/admin/departments" && method === "POST") return adminCreateDepartment(user, body);
    if ((m = path.match(/^\/api\/admin\/departments\/(\d+)$/)) && method === "PUT") return adminUpdateDepartment(user, Number(m[1]), body);
    if (path === "/api/admin/categories" && method === "POST") return adminCreateCategory(user, body);
    if ((m = path.match(/^\/api\/admin\/categories\/(\d+)$/)) && method === "PUT") return adminUpdateCategory(user, Number(m[1]), body);
    if (path === "/api/admin/sla-rules" && method === "GET") return adminSlaList();
    if ((m = path.match(/^\/api\/admin\/sla-rules\/(\w+)$/)) && method === "PUT") return adminSlaUpdate(user, m[1], body);
    if (path === "/api/admin/escalation-rules" && method === "GET") return adminEscList();
    if ((m = path.match(/^\/api\/admin\/escalation-rules\/(\w+)$/)) && method === "PUT") return adminEscUpdate(user, m[1], body);
    if (path === "/api/admin/audit-logs") return adminAudit(q);

    return fail(404, "Not available in demo mode");
  }

  /* ---------- plug the mock into the pages ---------- */

  function pageUrl(path) {
    const pages = {
      "/login": "login.html", "/register": "register.html", "/dashboard": "dashboard.html",
      "/complaints": "complaints.html", "/complaints/new": "complaint-new.html",
      "/queues": "queues.html", "/admin": "admin.html"
    };
    if (pages[path]) return pages[path];
    const m = path.match(/^\/complaints\/(\d+)$/);
    if (m) return "complaint-details.html?id=" + m[1];
    return path;
  }

  window.makeLink = function (text, href) {
    const link = makeEl("a", text);
    link.href = pageUrl(href);
    return link;
  };

  window.isActive = function (href) {
    const file = window.location.pathname.split("/").pop() || "index.html";
    if (href === "/complaints") return file === "complaints.html" || file === "complaint-details.html";
    return file === pageUrl(href).split("?")[0];
  };

  window.logout = function () {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    window.location.href = "login.html";
  };

  window.requireLogin = function () {
    if (!getToken()) window.location.href = "login.html";
    return JSON.parse(localStorage.getItem("user") || "{}");
  };

  window.api = async function (url, options) {
    options = options || {};
    let body = {};
    if (options.body) {
      try { body = JSON.parse(options.body); } catch (e) {}
    }
    const res = handle((options.method || "GET").toUpperCase(), url, body);
    if (res.status === 401 && url.indexOf("/api/auth") !== 0) window.logout();
    return { ok: res.status < 400, status: res.status, data: res.data };
  };

  load();

  document.addEventListener("DOMContentLoaded", function () {
    const banner = document.createElement("div");
    banner.style.cssText = "background:#fef3c7;color:#92400e;padding:8px 16px;font-size:13px;text-align:center;";
    banner.textContent = "Demo mode: runs fully in your browser with sample data. Nothing is sent to a server. ";
    const reset = document.createElement("a");
    reset.href = "#";
    reset.textContent = "Reset demo data";
    reset.onclick = function (e) {
      e.preventDefault();
      localStorage.clear();
      window.location.href = "login.html";
    };
    banner.appendChild(reset);
    document.body.prepend(banner);
  });
})();