from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from auth_utils import role_required
from database import get_connection
from services.audit_service import log_action

admin_bp = Blueprint("admin", __name__)

PRIORITIES = ["Low", "Medium", "High", "Critical"]
ROLES = ["Admin", "Manager", "Support Agent", "Customer"]


# ---------- Small helpers ----------

def fail(cursor, conn, message, code):
    """Close the database and return an error. Saves repeating 4 lines."""
    cursor.close()
    conn.close()
    return jsonify({"error": message}), code


def is_positive_int(value, allow_zero=False):
    if isinstance(value, bool) or not isinstance(value, int):
        return False
    return value >= 0 if allow_zero else value > 0


# ---------- Departments ----------

@admin_bp.route("/api/departments")
@jwt_required()
def list_departments():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, name FROM departments ORDER BY name")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(rows)


@admin_bp.route("/api/admin/departments", methods=["POST"])
@role_required("Admin")
def create_department():
    admin_id = int(get_jwt_identity())
    data = request.get_json() or {}
    name = str(data.get("name", "")).strip()
    if not name:
        return jsonify({"error": "Name is required"}), 400

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT id FROM departments WHERE name = %s", (name,))
    if cursor.fetchone():
        return fail(cursor, conn, "Department already exists", 409)

    cursor.execute("INSERT INTO departments (name) VALUES (%s)", (name,))
    new_id = cursor.lastrowid
    log_action(cursor, "DEPARTMENT_CREATED", "department", new_id, f"Created department '{name}'", admin_id)

    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Department created", "id": new_id}), 201


@admin_bp.route("/api/admin/departments/<int:department_id>", methods=["PUT"])
@role_required("Admin")
def update_department(department_id):
    admin_id = int(get_jwt_identity())
    data = request.get_json() or {}
    name = str(data.get("name", "")).strip()
    if not name:
        return jsonify({"error": "Name is required"}), 400

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT name FROM departments WHERE id = %s", (department_id,))
    department = cursor.fetchone()
    if not department:
        return fail(cursor, conn, "Department not found", 404)

    cursor.execute("SELECT id FROM departments WHERE name = %s AND id <> %s", (name, department_id))
    if cursor.fetchone():
        return fail(cursor, conn, "Another department already has this name", 409)

    cursor.execute("UPDATE departments SET name = %s WHERE id = %s", (name, department_id))
    log_action(cursor, "DEPARTMENT_UPDATED", "department", department_id,
               f"Renamed '{department['name']}' to '{name}'", admin_id)

    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Department updated"})


# ---------- Categories ----------

@admin_bp.route("/api/categories")
@jwt_required()
def list_categories():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT c.id, c.name, c.is_critical, d.name AS department
        FROM categories c
        JOIN departments d ON d.id = c.department_id
        ORDER BY c.name
    """)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    for r in rows:
        r["is_critical"] = bool(r["is_critical"])
    return jsonify(rows)


@admin_bp.route("/api/admin/categories", methods=["POST"])
@role_required("Admin")
def create_category():
    admin_id = int(get_jwt_identity())
    data = request.get_json() or {}
    name = str(data.get("name", "")).strip()
    department_id = data.get("department_id")
    is_critical = bool(data.get("is_critical", False))

    if not name or not department_id:
        return jsonify({"error": "Name and department_id are required"}), 400

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT id FROM departments WHERE id = %s", (department_id,))
    if not cursor.fetchone():
        return fail(cursor, conn, "Department not found", 404)

    cursor.execute("SELECT id FROM categories WHERE name = %s", (name,))
    if cursor.fetchone():
        return fail(cursor, conn, "Category already exists", 409)

    cursor.execute(
        "INSERT INTO categories (name, department_id, is_critical) VALUES (%s, %s, %s)",
        (name, department_id, is_critical),
    )
    new_id = cursor.lastrowid
    log_action(cursor, "CATEGORY_CREATED", "category", new_id,
               f"Created category '{name}' (department {department_id}, critical={is_critical})", admin_id)

    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Category created", "id": new_id}), 201


@admin_bp.route("/api/admin/categories/<int:category_id>", methods=["PUT"])
@role_required("Admin")
def update_category(category_id):
    admin_id = int(get_jwt_identity())
    data = request.get_json() or {}

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM categories WHERE id = %s", (category_id,))
    category = cursor.fetchone()
    if not category:
        return fail(cursor, conn, "Category not found", 404)

    # Anything not sent keeps its current value
    name = str(data.get("name", category["name"])).strip()
    department_id = data.get("department_id", category["department_id"])
    is_critical = bool(data.get("is_critical", category["is_critical"]))

    if not name:
        return fail(cursor, conn, "Name cannot be empty", 400)

    cursor.execute("SELECT id FROM departments WHERE id = %s", (department_id,))
    if not cursor.fetchone():
        return fail(cursor, conn, "Department not found", 404)

    cursor.execute("SELECT id FROM categories WHERE name = %s AND id <> %s", (name, category_id))
    if cursor.fetchone():
        return fail(cursor, conn, "Another category already has this name", 409)

    cursor.execute(
        "UPDATE categories SET name = %s, department_id = %s, is_critical = %s WHERE id = %s",
        (name, department_id, is_critical, category_id),
    )
    log_action(cursor, "CATEGORY_UPDATED", "category", category_id,
               f"'{category['name']}' -> '{name}', department {category['department_id']} -> {department_id}, "
               f"critical {bool(category['is_critical'])} -> {is_critical}", admin_id)

    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Category updated"})


# ---------- SLA rules ----------

@admin_bp.route("/api/admin/sla-rules")
@role_required("Admin")
def list_sla_rules():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT priority, resolution_hours, near_breach_hours, active FROM sla_rules ORDER BY resolution_hours"
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    for r in rows:
        r["active"] = bool(r["active"])
    return jsonify(rows)


@admin_bp.route("/api/admin/sla-rules/<priority>", methods=["PUT"])
@role_required("Admin")
def update_sla_rule(priority):
    admin_id = int(get_jwt_identity())
    data = request.get_json() or {}

    if priority not in PRIORITIES:
        return jsonify({"error": f"Priority must be one of: {', '.join(PRIORITIES)}"}), 404

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM sla_rules WHERE priority = %s", (priority,))
    rule = cursor.fetchone()
    if not rule:
        return fail(cursor, conn, "SLA rule not found", 404)

    resolution = data.get("resolution_hours", rule["resolution_hours"])
    near = data.get("near_breach_hours", rule["near_breach_hours"])

    if not is_positive_int(resolution) or not is_positive_int(near):
        return fail(cursor, conn, "Hours must be whole numbers greater than 0", 400)
    if near >= resolution:
        return fail(cursor, conn, "near_breach_hours must be smaller than resolution_hours", 400)

    cursor.execute(
        "UPDATE sla_rules SET resolution_hours = %s, near_breach_hours = %s WHERE priority = %s",
        (resolution, near, priority),
    )
    log_action(cursor, "SLA_RULE_UPDATED", "sla_rule", rule["id"],
               f"{priority}: resolution {rule['resolution_hours']}h -> {resolution}h, "
               f"near {rule['near_breach_hours']}h -> {near}h", admin_id)

    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "SLA rule updated"})


# ---------- Escalation rules ----------

@admin_bp.route("/api/admin/escalation-rules")
@role_required("Admin")
def list_escalation_rules():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT priority, grace_hours, escalation_level, target_role, active FROM escalation_rules ORDER BY id"
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    for r in rows:
        r["active"] = bool(r["active"])
    return jsonify(rows)


@admin_bp.route("/api/admin/escalation-rules/<priority>", methods=["PUT"])
@role_required("Admin")
def update_escalation_rule(priority):
    admin_id = int(get_jwt_identity())
    data = request.get_json() or {}

    if priority not in PRIORITIES:
        return jsonify({"error": f"Priority must be one of: {', '.join(PRIORITIES)}"}), 404

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM escalation_rules WHERE priority = %s", (priority,))
    rule = cursor.fetchone()
    if not rule:
        return fail(cursor, conn, "Escalation rule not found", 404)

    grace = data.get("grace_hours", rule["grace_hours"])
    level = data.get("escalation_level", rule["escalation_level"])
    target_role = data.get("target_role", rule["target_role"])

    if not is_positive_int(grace, allow_zero=True):
        return fail(cursor, conn, "grace_hours must be 0 or a positive whole number", 400)
    if not is_positive_int(level):
        return fail(cursor, conn, "escalation_level must be a whole number greater than 0", 400)
    if target_role not in ("Manager", "Admin"):
        return fail(cursor, conn, "target_role must be Manager or Admin", 400)

    cursor.execute(
        """UPDATE escalation_rules
           SET grace_hours = %s, escalation_level = %s, target_role = %s
           WHERE priority = %s""",
        (grace, level, target_role, priority),
    )
    log_action(cursor, "ESCALATION_RULE_UPDATED", "escalation_rule", rule["id"],
               f"{priority}: grace {rule['grace_hours']}h -> {grace}h, level {rule['escalation_level']} -> {level}, "
               f"target {rule['target_role']} -> {target_role}", admin_id)

    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Escalation rule updated"})


# ---------- Users and agents ----------

@admin_bp.route("/api/admin/users")
@role_required("Admin")
def list_users():
    role = request.args.get("role", "").strip()
    department_id = request.args.get("department_id", "").strip()

    conditions = []
    params = []
    if role:
        if role not in ROLES:
            return jsonify({"error": f"role must be one of: {', '.join(ROLES)}"}), 400
        conditions.append("u.role = %s")
        params.append(role)
    if department_id:
        if not department_id.isdigit():
            return jsonify({"error": "department_id must be a number"}), 400
        conditions.append("u.department_id = %s")
        params.append(int(department_id))

    where = (" WHERE " + " AND ".join(conditions)) if conditions else ""

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """SELECT u.id, u.name, u.email, u.role, u.department_id,
                  d.name AS department, u.created_at
           FROM users u
           LEFT JOIN departments d ON d.id = u.department_id""" + where + " ORDER BY u.id",
        tuple(params),
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(rows)


@admin_bp.route("/api/admin/users/<int:user_id>", methods=["PUT"])
@role_required("Admin")
def update_user(user_id):
    admin_id = int(get_jwt_identity())
    data = request.get_json() or {}

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT id, name, role, department_id FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    if not user:
        return fail(cursor, conn, "User not found", 404)

    new_role = data.get("role", user["role"])
    new_department = data["department_id"] if "department_id" in data else user["department_id"]

    if new_role not in ROLES:
        return fail(cursor, conn, f"role must be one of: {', '.join(ROLES)}", 400)

    # Stop the Admin from locking themselves out
    if user_id == admin_id and new_role != "Admin":
        return fail(cursor, conn, "You cannot remove your own Admin role", 400)

    # Managers and agents must belong to a department
    if new_role in ("Manager", "Support Agent") and not new_department:
        return fail(cursor, conn, f"A {new_role} needs a department_id", 400)

    if new_department:
        cursor.execute("SELECT id FROM departments WHERE id = %s", (new_department,))
        if not cursor.fetchone():
            return fail(cursor, conn, "Department not found", 404)

    cursor.execute(
        "UPDATE users SET role = %s, department_id = %s WHERE id = %s",
        (new_role, new_department, user_id),
    )
    log_action(cursor, "USER_UPDATED", "user", user_id,
               f"{user['name']}: role {user['role']} -> {new_role}, "
               f"department {user['department_id']} -> {new_department}", admin_id)

    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "User updated. They must log in again to get the new role."})


@admin_bp.route("/api/agents")
@jwt_required()
def list_agents():
    user_id = int(get_jwt_identity())
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT role, department_id FROM users WHERE id = %s", (user_id,))
    me = cursor.fetchone()
    if me["role"] not in ("Admin", "Manager"):
        return fail(cursor, conn, "Only Admin or Manager can list agents", 403)

    department_id = request.args.get("department_id", "").strip()
    if me["role"] == "Manager":
        department_id = me["department_id"]     # a Manager only sees their own department
    elif department_id and not department_id.isdigit():
        return fail(cursor, conn, "department_id must be a number", 400)

    conditions = ["u.role = 'Support Agent'"]
    params = []
    if department_id:
        conditions.append("u.department_id = %s")
        params.append(int(department_id))

    cursor.execute(
        """SELECT u.id, u.name, u.email, d.name AS department
           FROM users u
           LEFT JOIN departments d ON d.id = u.department_id
           WHERE """ + " AND ".join(conditions) + " ORDER BY u.name",
        tuple(params),
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(rows)


# ---------- Audit log ----------

@admin_bp.route("/api/admin/audit-logs")
@role_required("Admin")
def list_audit_logs():
    action = request.args.get("action", "").strip()
    try:
        page = max(int(request.args.get("page", 1)), 1)
        page_size = min(max(int(request.args.get("page_size", 20)), 1), 100)
    except ValueError:
        return jsonify({"error": "page and page_size must be numbers"}), 400

    where = ""
    params = []
    if action:
        where = " WHERE a.action_name = %s"
        params.append(action)

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT COUNT(*) AS total FROM audit_logs a" + where, tuple(params))
    total = cursor.fetchone()["total"]

    cursor.execute(
        """SELECT a.id, a.action_name, a.entity_type, a.entity_id, a.details,
                  u.name AS done_by, a.created_at
           FROM audit_logs a
           JOIN users u ON u.id = a.user_id""" + where +
        " ORDER BY a.id DESC LIMIT %s OFFSET %s",
        tuple(params + [page_size, (page - 1) * page_size]),
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    return jsonify({
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": (total + page_size - 1) // page_size,
        "logs": rows,
    })


# ---------- Tools you already had ----------

@admin_bp.route("/api/admin/run-escalation", methods=["POST"])
@role_required("Admin")
def run_escalation():
    from services.escalation_service import escalate_overdue_complaints
    count = escalate_overdue_complaints()
    return jsonify({"escalated": count})


@admin_bp.route("/api/admin/notifications")
@role_required("Admin")
def list_notifications():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """SELECT n.id, n.complaint_id, u.name AS recipient, n.channel,
                  n.event, n.status, n.message, n.created_at
           FROM notifications n
           JOIN users u ON u.id = n.recipient_id
           ORDER BY n.id DESC
           LIMIT 50"""
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(rows)