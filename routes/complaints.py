from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from database import get_connection
from services.sentiment_service import analyze_sentiment
from services.priority_service import calculate_priority
from services.sla_service import load_sla_rules, calculate_due_at, get_sla_state
from services.notification_service import send_notification

complaints_bp = Blueprint("complaints", __name__)


# ---------- Raise a complaint ----------

@complaints_bp.route("/api/complaints", methods=["POST"])
@jwt_required()
def create_complaint():
    user_id = int(get_jwt_identity())
    data = request.get_json() or {}

    title = data.get("title", "").strip()
    description = data.get("description", "").strip()
    category_id = data.get("category_id")
    urgency = data.get("urgency")

    # Validation
    if not title or not description or not category_id or urgency is None:
        return jsonify({"error": "title, description, category_id and urgency are required"}), 400
    if not isinstance(urgency, int) or urgency not in (1, 2, 3, 4):
        return jsonify({"error": "urgency must be a number from 1 to 4"}), 400

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Find the category, its department and whether it is critical
    cursor.execute(
        "SELECT id, department_id, is_critical FROM categories WHERE id = %s",
        (category_id,),
    )
    category = cursor.fetchone()
    if not category:
        cursor.close()
        conn.close()
        return jsonify({"error": "Category not found"}), 404

    # Run the engines
    full_text = f"{title} {description}"
    sentiment = analyze_sentiment(full_text)
    result = calculate_priority(urgency, full_text, sentiment, bool(category["is_critical"]))
    priority = result["priority"]

    rules = load_sla_rules(cursor)
    due_at = calculate_due_at(rules, priority)

    cursor.execute(
        """INSERT INTO complaints
           (title, description, category_id, department_id, urgency, sentiment, priority, due_at, raised_by)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
        (title, description, category["id"], category["department_id"],
         urgency, sentiment, priority, due_at, user_id),
    )
    new_id = cursor.lastrowid

    # Build the reference number: CMP-YYYYMMDD-XXXXXX
    reference_no = f"CMP-{datetime.now().strftime('%Y%m%d')}-{new_id:06d}"
    cursor.execute("UPDATE complaints SET reference_no = %s WHERE id = %s", (reference_no, new_id))
    add_history(cursor, new_id, "Created", None, "Open", user_id)
    send_notification(cursor, new_id, user_id, "Created",
                      f"Your complaint {reference_no} has been received. Priority: {priority}.")

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({
        "message": "Complaint raised successfully",
        "id": new_id,
        "reference_no": reference_no,
        "sentiment": sentiment,
        "priority": priority,
        "priority_score": result["score"],
        "reasons": result["reasons"],
        "due_at": due_at.strftime("%Y-%m-%d %H:%M:%S"),
        "status": "Open",
    }), 201


# ---------- List complaints (search, filters, pagination) ----------

VALID_STATUSES = ["Open", "Assigned", "In Progress", "Resolved", "Closed", "Escalated"]
VALID_PRIORITIES = ["Low", "Medium", "High", "Critical"]


@complaints_bp.route("/api/complaints", methods=["GET"])
@jwt_required()
def list_complaints():
    user_id = int(get_jwt_identity())

    # Read the options from the URL: ?search=...&status=...&priority=...&page=...
    search = request.args.get("search", "").strip()
    status = request.args.get("status", "").strip()
    priority = request.args.get("priority", "").strip()

    try:
        page = max(int(request.args.get("page", 1)), 1)
        page_size = min(max(int(request.args.get("page_size", 10)), 1), 50)
    except ValueError:
        return jsonify({"error": "page and page_size must be numbers"}), 400

    if status and status not in VALID_STATUSES:
        return jsonify({"error": f"status must be one of: {', '.join(VALID_STATUSES)}"}), 400
    if priority and priority not in VALID_PRIORITIES:
        return jsonify({"error": f"priority must be one of: {', '.join(VALID_PRIORITIES)}"}), 400

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    user = get_user(cursor, user_id)

    conditions = []
    params = []

    # 1. Role scope: who may see which complaints
    role = user["role"]
    if role == "Manager":
        conditions.append("c.department_id = %s")
        params.append(user["department_id"])
    elif role == "Support Agent":
        conditions.append("c.assigned_to = %s")
        params.append(user["id"])
    elif role == "Customer":
        conditions.append("c.raised_by = %s")
        params.append(user["id"])
    # Admin: no condition, sees everything

    # 2. Search and filters
    if search:
        like = f"%{search}%"
        conditions.append("(c.title LIKE %s OR c.description LIKE %s OR c.reference_no LIKE %s)")
        params.extend([like, like, like])
    if status:
        conditions.append("c.status = %s")
        params.append(status)
    if priority:
        conditions.append("c.priority = %s")
        params.append(priority)

    where = (" WHERE " + " AND ".join(conditions)) if conditions else ""

    base = """
        FROM complaints c
        JOIN categories cat ON cat.id = c.category_id
        JOIN departments d ON d.id = c.department_id
    """

    # 3. Count all matching complaints (needed for the page numbers)
    cursor.execute("SELECT COUNT(*) AS total " + base + where, tuple(params))
    total = cursor.fetchone()["total"]

    # 4. Fetch only the requested page
    offset = (page - 1) * page_size
    cursor.execute(
        """SELECT c.id, c.reference_no, c.title, c.priority, c.status, c.sentiment, c.due_at,
                  cat.name AS category, d.name AS department, c.created_at """
        + base + where +
        " ORDER BY c.created_at DESC, c.id DESC LIMIT %s OFFSET %s",
        tuple(params + [page_size, offset]),
    )
    rows = cursor.fetchall()

    rules = load_sla_rules(cursor)
    for row in rows:
        row["sla_state"] = get_sla_state(row, rules)

    cursor.close()
    conn.close()

    return jsonify({
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": (total + page_size - 1) // page_size,
        "complaints": rows,
    })


# ---------- Helper functions ----------

def get_user(cursor, user_id):
    cursor.execute("SELECT id, name, role, department_id FROM users WHERE id = %s", (user_id,))
    return cursor.fetchone()


def add_history(cursor, complaint_id, action, old_value, new_value, user_id):
    cursor.execute(
        """INSERT INTO complaint_history (complaint_id, action, old_value, new_value, changed_by)
           VALUES (%s, %s, %s, %s, %s)""",
        (complaint_id, action, old_value, new_value, user_id),
    )


def can_view(user, complaint):
    if user["role"] == "Admin":
        return True
    if user["role"] == "Manager":
        return complaint["department_id"] == user["department_id"]
    if user["role"] == "Support Agent":
        return complaint["assigned_to"] == user["id"]
    if user["role"] == "Customer":
        return complaint["raised_by"] == user["id"]
    return False


# Allowed status moves: current status -> list of next statuses
TRANSITIONS = {
    "Assigned": ["In Progress"],
    "In Progress": ["Resolved"],
    "Resolved": ["Closed"],
    "Escalated": ["In Progress"],
}


# ---------- Complaint details ----------

@complaints_bp.route("/api/complaints/<int:complaint_id>", methods=["GET"])
@jwt_required()
def get_complaint(complaint_id):
    user_id = int(get_jwt_identity())
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    user = get_user(cursor, user_id)
    cursor.execute(
        """SELECT c.*, cat.name AS category, d.name AS department,
                  r.name AS raised_by_name, a.name AS assigned_to_name
           FROM complaints c
           JOIN categories cat ON cat.id = c.category_id
           JOIN departments d ON d.id = c.department_id
           JOIN users r ON r.id = c.raised_by
           LEFT JOIN users a ON a.id = c.assigned_to
           WHERE c.id = %s""",
        (complaint_id,),
    )
    complaint = cursor.fetchone()

    if not complaint:
        cursor.close()
        conn.close()
        return jsonify({"error": "Complaint not found"}), 404
    if not can_view(user, complaint):
        cursor.close()
        conn.close()
        return jsonify({"error": "You do not have permission to view this complaint"}), 403

    cursor.execute(
        """SELECT h.action, h.old_value, h.new_value, u.name AS changed_by, h.created_at
           FROM complaint_history h
           JOIN users u ON u.id = h.changed_by
           WHERE h.complaint_id = %s
           ORDER BY h.created_at, h.id""",
        (complaint_id,),
    )
    complaint["history"] = cursor.fetchall()

    rules = load_sla_rules(cursor)
    complaint["sla_state"] = get_sla_state(complaint, rules)

    cursor.close()
    conn.close()
    return jsonify(complaint)


# ---------- Assign an agent ----------

@complaints_bp.route("/api/complaints/<int:complaint_id>/assign", methods=["PUT"])
@jwt_required()
def assign_complaint(complaint_id):
    user_id = int(get_jwt_identity())
    data = request.get_json() or {}
    agent_id = data.get("agent_id")

    if not agent_id:
        return jsonify({"error": "agent_id is required"}), 400

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    user = get_user(cursor, user_id)
    if user["role"] not in ("Admin", "Manager"):
        cursor.close()
        conn.close()
        return jsonify({"error": "Only Admin or Manager can assign complaints"}), 403

    cursor.execute("SELECT * FROM complaints WHERE id = %s", (complaint_id,))
    complaint = cursor.fetchone()
    if not complaint:
        cursor.close()
        conn.close()
        return jsonify({"error": "Complaint not found"}), 404

    if user["role"] == "Manager" and complaint["department_id"] != user["department_id"]:
        cursor.close()
        conn.close()
        return jsonify({"error": "This complaint belongs to another department"}), 403

    if complaint["status"] in ("Resolved", "Closed"):
        cursor.close()
        conn.close()
        return jsonify({"error": "Cannot assign a resolved or closed complaint"}), 400

    # The agent must be a Support Agent in the complaint's department
    agent = get_user(cursor, agent_id)
    if (not agent or agent["role"] != "Support Agent"
            or agent["department_id"] != complaint["department_id"]):
        cursor.close()
        conn.close()
        return jsonify({"error": "Agent must be a Support Agent in the complaint's department"}), 400

    old_agent = None
    if complaint["assigned_to"]:
        old_agent = get_user(cursor, complaint["assigned_to"])["name"]

    # Open becomes Assigned. Other statuses (like In Progress) stay as they are.
    new_status = "Assigned" if complaint["status"] == "Open" else complaint["status"]

    cursor.execute(
        "UPDATE complaints SET assigned_to = %s, status = %s WHERE id = %s",
        (agent_id, new_status, complaint_id),
    )
    add_history(cursor, complaint_id, "Assigned", old_agent, agent["name"], user_id)
    if new_status != complaint["status"]:
        add_history(cursor, complaint_id, "Status changed", complaint["status"], new_status, user_id)

    send_notification(cursor, complaint_id, agent_id, "Assigned",
                      f"Complaint {complaint['reference_no']} has been assigned to you.")

    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": f"Assigned to {agent['name']}", "status": new_status})


# ---------- Update status ----------

@complaints_bp.route("/api/complaints/<int:complaint_id>/status", methods=["PUT"])
@jwt_required()
def update_status(complaint_id):
    user_id = int(get_jwt_identity())
    data = request.get_json() or {}
    new_status = data.get("status", "").strip()

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    user = get_user(cursor, user_id)
    cursor.execute("SELECT * FROM complaints WHERE id = %s", (complaint_id,))
    complaint = cursor.fetchone()

    if not complaint:
        cursor.close()
        conn.close()
        return jsonify({"error": "Complaint not found"}), 404

    # Who is allowed to change this complaint?
    role = user["role"]
    allowed = (
        role == "Admin"
        or (role == "Manager" and complaint["department_id"] == user["department_id"])
        or (role == "Support Agent" and complaint["assigned_to"] == user["id"])
        or (role == "Customer" and complaint["raised_by"] == user["id"]
            and complaint["status"] == "Resolved" and new_status == "Closed")
    )
    if not allowed:
        cursor.close()
        conn.close()
        return jsonify({"error": "You do not have permission to change this status"}), 403

    # Is this move allowed by the lifecycle?
    current = complaint["status"]
    if new_status not in TRANSITIONS.get(current, []):
        cursor.close()
        conn.close()
        return jsonify({"error": f"Cannot move from {current} to {new_status}"}), 400

    cursor.execute("UPDATE complaints SET status = %s WHERE id = %s", (new_status, complaint_id))
    add_history(cursor, complaint_id, "Status changed", current, new_status, user_id)
    if new_status == "Resolved":
        send_notification(cursor, complaint_id, complaint["raised_by"], "Resolved",
                          f"Your complaint {complaint['reference_no']} has been marked as resolved.")

    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Status updated", "status": new_status})


# ---------- Comments ----------

@complaints_bp.route("/api/complaints/<int:complaint_id>/comments", methods=["POST"])
@jwt_required()
def add_comment(complaint_id):
    user_id = int(get_jwt_identity())
    data = request.get_json() or {}
    text = data.get("comment", "").strip()

    if not text:
        return jsonify({"error": "Comment cannot be empty"}), 400
    if len(text) > 1000:
        return jsonify({"error": "Comment is too long (maximum 1000 characters)"}), 400

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    user = get_user(cursor, user_id)
    cursor.execute("SELECT * FROM complaints WHERE id = %s", (complaint_id,))
    complaint = cursor.fetchone()

    if not complaint:
        cursor.close()
        conn.close()
        return jsonify({"error": "Complaint not found"}), 404
    if not can_view(user, complaint):
        cursor.close()
        conn.close()
        return jsonify({"error": "You do not have permission to comment on this complaint"}), 403
    if complaint["status"] == "Closed":
        cursor.close()
        conn.close()
        return jsonify({"error": "This complaint is closed. No new comments allowed"}), 400

    cursor.execute(
        "INSERT INTO comments (complaint_id, user_id, comment_text) VALUES (%s, %s, %s)",
        (complaint_id, user_id, text),
    )
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Comment added"}), 201


# ---------- Unified activity feed ----------

@complaints_bp.route("/api/complaints/<int:complaint_id>/history", methods=["GET"])
@jwt_required()
def get_activity_feed(complaint_id):
    user_id = int(get_jwt_identity())
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    user = get_user(cursor, user_id)
    cursor.execute("SELECT * FROM complaints WHERE id = %s", (complaint_id,))
    complaint = cursor.fetchone()

    if not complaint:
        cursor.close()
        conn.close()
        return jsonify({"error": "Complaint not found"}), 404
    if not can_view(user, complaint):
        cursor.close()
        conn.close()
        return jsonify({"error": "You do not have permission to view this complaint"}), 403

    feed = []

    # 1. System events (created, assigned, status changes)
    cursor.execute(
        """SELECT h.action, h.old_value, h.new_value, u.name AS actor, h.created_at
           FROM complaint_history h
           JOIN users u ON u.id = h.changed_by
           WHERE h.complaint_id = %s""",
        (complaint_id,),
    )
    for h in cursor.fetchall():
        if h["action"] == "Created":
            text = "Complaint created"
        elif h["action"] == "Assigned":
            if h["old_value"]:
                text = f"Reassigned from {h['old_value']} to {h['new_value']}"
            else:
                text = f"Assigned to {h['new_value']}"
        else:
            text = f"Status changed: {h['old_value']} -> {h['new_value']}"
        feed.append({"type": "system", "actor": h["actor"], "text": text, "time": h["created_at"]})

    # 2. Human comments
    cursor.execute(
        """SELECT c.comment_text, u.name AS actor, u.role, c.created_at
           FROM comments c
           JOIN users u ON u.id = c.user_id
           WHERE c.complaint_id = %s""",
        (complaint_id,),
    )
    for c in cursor.fetchall():
        feed.append({
            "type": "comment",
            "actor": c["actor"],
            "role": c["role"],
            "text": c["comment_text"],
            "time": c["created_at"],
        })

    cursor.close()
    conn.close()

    # Mix both lists and sort oldest to newest
    feed.sort(key=lambda item: item["time"])
    return jsonify(feed)