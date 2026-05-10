# flagging.py

from enum import Enum

class RiskLevel(Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

RISK_DEFINITIONS = {
    RiskLevel.HIGH: {
        "emoji": "🔴",
        "label": "HIGH",
        "description": "Could cause direct financial loss, loss of rights, or legal liability.",
    },
    RiskLevel.MEDIUM: {
        "emoji": "🟠",
        "label": "MEDIUM",
        "description": "Creates meaningful uncertainty or imbalance; warrants negotiation.",
    },
    RiskLevel.LOW: {
        "emoji": "🟡",
        "label": "LOW",
        "description": "Minor ambiguity or standard boilerplate that nonetheless deserves awareness.",
    },
}

def build_risk_scoring_prompt() -> str:
    """Returns the risk scoring instructions to inject into the system prompt."""
    lines = ["Assign each flagged clause a risk level:\n"]
    for level, meta in RISK_DEFINITIONS.items():
        lines.append(f"- {meta['emoji']} {meta['label']} — {meta['description']}")
    return "\n".join(lines)

def format_risk_badge(level: RiskLevel) -> str:
    """Returns a formatted badge string for a given risk level for the report output."""
    meta = RISK_DEFINITIONS[level]
    return f"{meta['emoji']} {meta['label']}"