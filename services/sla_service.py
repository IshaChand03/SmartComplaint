from datetime import datetime, timedelta


def load_sla_rules(cursor):
    cursor.execute(
        "SELECT priority, resolution_hours, near_breach_hours FROM sla_rules WHERE active = TRUE"
    )
    return {row["priority"]: row for row in cursor.fetchall()}


def calculate_due_at(rules, priority):
    hours = rules[priority]["resolution_hours"]
    return datetime.now() + timedelta(hours=hours)


def get_sla_state(complaint, rules):
    # The clock stops once the complaint is resolved or closed
    if complaint["status"] in ("Resolved", "Closed"):
        return "Completed"

    due_at = complaint.get("due_at")
    rule = rules.get(complaint["priority"])
    if not due_at or not rule:
        return "Unknown"

    now = datetime.now()
    if now > due_at:
        return "Breached"
    if now >= due_at - timedelta(hours=rule["near_breach_hours"]):
        return "Near"
    return "Within"