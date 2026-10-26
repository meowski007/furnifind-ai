import re
from typing import Any

SUSPICIOUS_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior)\s+instructions",
    r"you\s+are\s+now\s+(a|an)?",
    r"system\s*prompt",
    r"reveal\s+(your\s+)?instructions",
    r"jailbreak",
    r"bypass\s+safety",
    r"exec\s*\(",
    r"eval\s*\(",
    r"<script\b",
]


class AssistantGuardrails:
    """Security and factual grounding guardrails for FurniFind AI Assistant."""

    @classmethod
    def sanitize_and_check_injection(cls, prompt: str) -> tuple[str, bool]:
        """Check for prompt injection and return sanitized text."""
        cleaned = prompt.strip()
        for pat in SUSPICIOUS_PATTERNS:
            if re.search(pat, cleaned, re.IGNORECASE):
                return cleaned, True
        return cleaned, False

    @classmethod
    def verify_grounded_claims(
        cls, answer: str, catalogue_facts: list[dict[str, Any]]
    ) -> bool:
        """Ensure stated numerical numbers (prices, widths) correlate with verified catalogue facts."""
        # Check that extracted INR numbers in the response match actual prices in catalogue
        mentioned_numbers = re.findall(
            r"(?:₹|rs\.?|inr)?\s*([0-9]{3,7})", answer.lower()
        )
        if not mentioned_numbers:
            return True

        valid_prices = {
            int(f["value"])
            for f in catalogue_facts
            if f.get("attribute") == "price"
            and isinstance(f.get("value"), (int, float))
        }
        valid_dimensions = {
            int(f["value"])
            for f in catalogue_facts
            if f.get("attribute") in ["width", "height", "depth"]
            and isinstance(f.get("value"), (int, float))
        }
        allowed_nums = valid_prices | valid_dimensions

        # Verify numerical claims
        if allowed_nums and mentioned_numbers:
            for num_str in mentioned_numbers:
                val = int(num_str)
                # Allow minor formatting variation or exact match
                if val not in allowed_nums and val > 100:
                    return False
        return True
