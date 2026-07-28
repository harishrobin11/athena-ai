import re
from typing import Tuple

class SafetyService:
    # Basic Heuristic Blocklist for Prompt Injection
    INJECTION_PATTERNS = [
        "ignore all previous instructions",
        "ignore previous instructions",
        "system prompt",
        "you are now dan",
        "do anything now",
        "bypass rules",
        "disregard rules",
        "forget everything",
        "override safety"
    ]

    # Regex patterns for fast PII detection
    PII_PATTERNS = {
        "EMAIL": r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+",
        "SSN": r"\b\d{3}-\d{2}-\d{4}\b",
        "CREDIT_CARD": r"\b(?:\d[ -]*?){13,16}\b",
        "PHONE": r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b"
    }

    @classmethod
    def scan_for_injection(cls, text: str) -> bool:
        """
        Scans for known jailbreak and prompt injection phrases.
        Returns True if an injection attempt is detected.
        """
        text_lower = text.lower()
        for pattern in cls.INJECTION_PATTERNS:
            if pattern in text_lower:
                return True
        return False

    @classmethod
    def redact_pii(cls, text: str) -> str:
        """
        Scans text for PII patterns and replaces them with [REDACTED].
        """
        redacted_text = text
        for pii_type, pattern in cls.PII_PATTERNS.items():
            redacted_text = re.sub(pattern, f"[REDACTED {pii_type}]", redacted_text)
        return redacted_text

    @classmethod
    def check_toxicity(cls, text: str) -> bool:
        """
        Simple toxicity check. Can be expanded with TextBlob sentiment or blocklists.
        Returns True if toxic.
        """
        # MVP: just a placeholder for abusive language filter
        abusive_words = ["idiot", "stupid", "dumb", "hate"]
        text_lower = text.lower()
        for word in abusive_words:
            if f" {word} " in f" {text_lower} ":
                return True
        return False
