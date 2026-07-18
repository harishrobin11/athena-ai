TIER_LIMITS = {
    "free": {
        "max_workspaces": 1,
        "max_documents": 5,
        "max_tokens_per_month": 10000
    },
    "pro": {
        "max_workspaces": 3,
        "max_documents": 50,
        "max_tokens_per_month": 50000
    },
    "business": {
        "max_workspaces": -1, # Unlimited
        "max_documents": 500,
        "max_tokens_per_month": 500000
    },
    "enterprise": {
        "max_workspaces": -1,
        "max_documents": -1,
        "max_tokens_per_month": -1
    }
}

def check_limit(current_value: int, limit: int) -> bool:
    """Returns True if the action is allowed (under limit), False if blocked."""
    if limit == -1:
        return True
    return current_value < limit
