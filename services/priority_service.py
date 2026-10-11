HIGH_IMPACT_KEYWORDS = [
    "urgent", "immediately", "emergency", "fraud", "failed",
    "unauthorized", "hacked", "stolen", "money deducted", "not working",
]

PRIORITY_NAMES = {1: "Low", 2: "Medium", 3: "High", 4: "Critical"}


def calculate_priority(urgency, text, sentiment, category_is_critical):
    score = urgency
    reasons = [f"Urgency {urgency}"]

    lower_text = text.lower()
    found = [k for k in HIGH_IMPACT_KEYWORDS if k in lower_text]
    if found:
        score += 1
        reasons.append("High-impact words: " + ", ".join(found))

    if sentiment == "Negative":
        score += 1
        reasons.append("Negative sentiment")

    if category_is_critical:
        score += 1
        reasons.append("Critical category")

    score = min(score, 4)

    return {
        "score": score,
        "priority": PRIORITY_NAMES[score],
        "reasons": reasons,
    }