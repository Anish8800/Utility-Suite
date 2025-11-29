def normalize_score(value):
    if isinstance(value, str) and (value.strip() in ["D$Q", "-"]):
        return 0
    try:
        return int(value)
    except:
        return 0

def normalize_spending(value):
    if isinstance(value, str) and (value.strip() in ["D$Q", "-"]):
        return 0.0
    try:
        return float(value)
    except:
        return 0.0