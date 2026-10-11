def log_action(cursor, action_name, entity_type, entity_id, details, user_id):
    cursor.execute(
        """INSERT INTO audit_logs (action_name, entity_type, entity_id, details, user_id)
           VALUES (%s, %s, %s, %s, %s)""",
        (action_name, entity_type, entity_id, details, user_id),
    )