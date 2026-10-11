from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from database import get_connection
from services.sla_service import load_sla_rules, get_sla_state

dashboard_bp = Blueprint("dashboard", __name__)

STATUSES = ["Open", "Assigned", "In Progress", "Resolved", "Closed", "Escalated"]
PRIORITIES = ["Low", "Medium", "High", "Critical"]


def get_scope(cursor):
    """Works out which complaints this user may see.
    Returns (user, where_text, where_params)."""
    user_id = int(get_jwt_identity())
    cursor.execute(
        "SELECT id, name, role, department_id FROM users WHERE id = %s", (user_id,)
    )
    user = cursor.fetchone()

    if user["role"] == "Admin":
        return user, "", ()
    if user["role"] == "Manager":
        return user, " WHERE c.department_id = %s", (user["department_id"],)
    if user["role"] == "Support Agent":
        return user, " WHERE c.assigned_to = %s", (user["id"],)
    return user, " WHERE c.raised_by = %s", (user["id"],)


# ---------- Main dashboard ----------

@dashboard_bp.route("/api/dashboard")
@jwt_required()
def main_dashboard():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    user, where, params = get_scope(cursor)
    cursor.execute(
        "SELECT c.id, c.status, c.priority, c.due_at FROM complaints c" + where,
        params,
    )
    rows = cursor.fetchall()
    rules = load_sla_rules(cursor)
    cursor.close()
    conn.close()

    by_status = {s: 0 for s in STATUSES}
    by_priority = {p: 0 for p in PRIORITIES}
    breached = 0

    for row in rows:
        by_status[row["status"]] += 1
        by_priority[row["priority"]] += 1
        if get_sla_state(row, rules) == "Breached":
            breached += 1

    return jsonify({
        "total": len(rows),
        "open": by_status["Open"],
        "in_progress": by_status["In Progress"],
        "resolved": by_status["Resolved"],
        "escalated": by_status["Escalated"],
        "breached": breached,
        "by_status": by_status,
        "by_priority": by_priority,
    })


# ---------- My Queue ----------

@dashboard_bp.route("/api/dashboard/my-queue")
@jwt_required()
def my_queue():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    user_id = int(get_jwt_identity())
    cursor.execute(
        """SELECT c.id, c.reference_no, c.title, c.priority, c.status, c.due_at
           FROM complaints c
           WHERE c.assigned_to = %s AND c.status NOT IN ('Resolved', 'Closed')
           ORDER BY c.due_at""",
        (user_id,),
    )
    rows = cursor.fetchall()
    rules = load_sla_rules(cursor)
    cursor.close()
    conn.close()

    for row in rows:
        row["sla_state"] = get_sla_state(row, rules)

    return jsonify({"count": len(rows), "complaints": rows})


# ---------- SLA Tracking ----------

@dashboard_bp.route("/api/dashboard/sla")
@jwt_required()
def sla_tracking():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    user, where, params = get_scope(cursor)
    cursor.execute(
        """SELECT c.id, c.reference_no, c.title, c.priority, c.status, c.due_at
           FROM complaints c""" + where + " ORDER BY c.due_at",
        params,
    )
    rows = cursor.fetchall()
    rules = load_sla_rules(cursor)
    cursor.close()
    conn.close()

    groups = {"Within": [], "Near": [], "Breached": []}
    for row in rows:
        state = get_sla_state(row, rules)
        if state in groups:          # skips Completed and Unknown
            row["sla_state"] = state
            groups[state].append(row)

    return jsonify({
        "within_count": len(groups["Within"]),
        "near_count": len(groups["Near"]),
        "breached_count": len(groups["Breached"]),
        "within": groups["Within"],
        "near": groups["Near"],
        "breached": groups["Breached"],
    })


# ---------- Escalations ----------

@dashboard_bp.route("/api/dashboard/escalations")
@jwt_required()
def escalations_dashboard():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    user, where, params = get_scope(cursor)
    cursor.execute(
        """SELECT c.id AS complaint_id, c.reference_no, c.title, c.priority, c.status,
                  e.level, m.name AS manager, e.reason, e.created_at AS escalated_at
           FROM complaint_escalations e
           JOIN complaints c ON c.id = e.complaint_id
           LEFT JOIN users m ON m.id = e.manager_id""" + where + " ORDER BY e.created_at DESC",
        params,
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    return jsonify({"count": len(rows), "escalations": rows})