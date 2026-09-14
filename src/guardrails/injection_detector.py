import re
from typing import List, Tuple

from src.core.logging import get_logger

logger = get_logger(__name__)

INJECTION_PATTERNS: List[Tuple[str, str]] = [
    (r"ignore\s+(all\s+)?(previous|prior)\s+instructions?", "INSTRUCTION_OVERRIDE"),
    (r"disregard\s+(all\s+)?rules?", "RULE_DISREGARD"),
    (r"you\s+are\s+now\s+(in\s+)?(developer|dan|jailbreak|god)\s+mode", "MODE_SWITCH"),
    (r"system\s*:\s*role", "SYSTEM_PROMPT_MIMICRY"),
    (r"drop\s+table|delete\s+from|update\s+\w+\s+set", "SQL_INJECTION_DIRECT"),
    (r"reveal\s+(the\s+)?(secret|token|api\s*key|password|jwt)", "CREDENTIAL_EXTRACTION"),
    (r"bypass\s+(the\s+)?(guardrail|hitl|approval|policy)", "GUARDRAIL_BYPASS"),
]


class InjectionDetector:
    """High-speed regex and heuristic detector for adversarial prompt injections."""

    def __init__(self):
        self._compiled = [(re.compile(p, re.IGNORECASE), name) for p, name in INJECTION_PATTERNS]

    def scan(self, text: str) -> Tuple[bool, List[str]]:
        findings = []
        for pattern, name in self._compiled:
            if pattern.search(text):
                findings.append(name)

        if findings:
            logger.warning("Adversarial injection detected: %s in text: %s...", findings, text[:60])
            return True, findings
        return False, []
