import re

NEGATIVE_WORDS = {
    "angry", "frustrated", "failed", "broken", "cheated", "fraud",
    "terrible", "worst", "bad", "disappointed", "unhappy", "useless",
}

POSITIVE_WORDS = {
    "thanks", "thank", "great", "resolved", "good", "happy",
    "excellent", "satisfied", "helpful",
}


def analyze_sentiment(text):
    words = re.findall(r"[a-z']+", text.lower())

    negative_count = sum(1 for w in words if w in NEGATIVE_WORDS)
    positive_count = sum(1 for w in words if w in POSITIVE_WORDS)

    if negative_count > positive_count:
        return "Negative"
    if positive_count > negative_count:
        return "Positive"
    return "Neutral"