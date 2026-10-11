from datetime import datetime, timedelta
from database import get_connection
from services.notification_service import send_notification
from services.audit_service import log_action

SYSTEM_EMAIL = "system@smartresolve.local"


def escalate_overdue_complaints():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # The System user is the "actor" for automatic actions
    cursor.execute("SELECT id FROM users WHERE email = %s", (SYSTEM_EMAIL,))
    system_user = cursor.fetchone()
    if not system_user:
        cursor.close()
        conn.close()
        print("Escalation skipped: System user not found")
        return 0
    system_id = system_user["id"]

    # Grace period and level for each priority
    cursor.execute(
        "SELECT priority, grace_hours, escalation_level FROM escalation_rules WHERE active = TRUE"
    )
    rules = {r["priority"]: r for r in cursor.fetchall()}

    # Only unresolved complaints that are not already escalated
    cursor.execute(
        """SELECT id, priority, status, due_at, department_id
           FROM complaints
           WHERE status IN ('Open', 'Assigned', 'In Progress') AND due_at IS NOT NULL"""
    )
    candidates = cursor.fetchall()

    now = datetime.now()
    escalated_count = 0

    for c in candidates:
        rule = rules.get(c["priority"])
        if not rule:
            continue

        # Deadline = due date + grace period
        deadline = c["due_at"] + timedelta(hours=rule["grace_hours"])
        if now <= deadline:
            continue   # not late enough yet

        # Find a manager in the complaint's department
        cursor.execute(
            "SELECT id, name FROM users WHERE role = 'Manager' AND department_id = %s ORDER BY id LIMIT 1",
            (c["department_id"],),
        )
        manager = cursor.fetchone()
        manager_id = manager["id"] if manager else None
        manager_name = manager["name"] if manager else "no manager found"

        reason = (
            f"SLA breached ({c['priority']} priority) and the "
            f"{rule['grace_hours']}-hour grace period has passed"
        )

        cursor.execute("UPDATE complaints SET status = 'Escalated' WHERE id = %s", (c["id"],))
        cursor.execute(
            "INSERT INTO complaint_escalations (complaint_id, level, manager_id, reason) VALUES (%s, %s, %s, %s)",
            (c["id"], rule["escalation_level"], manager_id, reason),
        )
        cursor.execute(
            """INSERT INTO complaint_history (complaint_id, action, old_value, new_value, changed_by)
               VALUES (%s, 'Status changed', %s, 'Escalated', %s)""",
            (c["id"], c["status"], system_id),
        )
        cursor.execute(
            "INSERT INTO comments (complaint_id, user_id, comment_text, is_system) VALUES (%s, %s, %s, TRUE)",
            (c["id"], system_id, f"SLA breached. Escalated to {manager_name}."),
        )
        if manager_id:
            send_notification(cursor, c["id"], manager_id, "Escalated",
                              f"Complaint #{c['id']} was escalated to you. {reason}.")
        log_action(cursor, "COMPLAINT_ESCALATED", "complaint", c["id"], reason, system_id)
        escalated_count += 1

    conn.commit()
    cursor.close()
    conn.close()
    return escalated_count