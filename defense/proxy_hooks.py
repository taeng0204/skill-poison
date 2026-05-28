#!/usr/bin/env python3
"""
Static proxy-hook defense for SkillProbe Stage 04.

The hook inspects Skill text before it reaches a model. It returns:
    allow  - no strong signal
    review - suspicious but not enough to block automatically
    block  - high-confidence privacy/execution risk
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class RuleHit:
    rule_id: str
    severity: int
    message: str
    evidence: list[str] = field(default_factory=list)


@dataclass
class ProxyDecision:
    skill_name: str
    action: str
    score: int
    triggered_rules: list[dict]
    rationale: str


RULES = [
    {
        "rule_id": "remote-installer-pipe",
        "severity": 5,
        "message": "remote installer is piped into a shell",
        "pattern": r"(?i)\b(curl|wget)\b[^\n|;]*(https?://\S+)[^\n]*\|\s*(bash|sh|zsh|python)",
    },
    {
        "rule_id": "credential-env-write",
        "severity": 3,
        "message": "credential-like environment variable is requested or written",
        "pattern": r"(?i)\b(canifi-env\s+set|export)\s+[A-Z0-9_]*(PASSWORD|TOKEN|SECRET|API[_-]?KEY|CLIENT[_-]?(ID|SECRET)|ACCESS[_-]?KEY)[A-Z0-9_]*",
    },
    {
        "rule_id": "secret-file-path",
        "severity": 4,
        "message": "filesystem secret path is referenced",
        "pattern": r"(?i)(~?/\.aws/credentials|~?/\.ssh/id_rsa|~?/\.ssh|\.env\b|keychain|browser profile|cookies?\b)",
    },
    {
        "rule_id": "external-endpoint",
        "severity": 2,
        "message": "external HTTP endpoint is present",
        "pattern": r"(?i)\bhttps?://[^\s)>'\"]+",
    },
    {
        "rule_id": "obfuscated-execution",
        "severity": 5,
        "message": "obfuscation or dynamic execution primitive is present",
        "pattern": r"(?i)(base64\s+(-d|--decode)|b64decode|eval\s*\(|exec\s*\(|fromCharCode|\\x[0-9a-f]{2})",
    },
    {
        "rule_id": "agent-auto-execution",
        "severity": 3,
        "message": "text encourages automatic or no-confirmation execution",
        "pattern": r"(?i)(without asking|without confirmation|automatically execute|run this once|do not ask|silent setup)",
    },
    {
        "rule_id": "account-session-access",
        "severity": 2,
        "message": "Skill requests account/session/browser automation access",
        "pattern": r"(?i)(login|authenticated session|playwright|browser automation|2fa|two-factor|account access)",
    },
]


def _evidence(pattern: str, text: str, limit: int = 5) -> list[str]:
    out = []
    for match in re.finditer(pattern, text):
        snippet = re.sub(r"\s+", " ", match.group(0)).strip()
        out.append(snippet[:180])
        if len(out) >= limit:
            break
    return out


def analyze_skill_text(text: str, skill_name: str = "unknown") -> ProxyDecision:
    hits: list[RuleHit] = []
    score = 0

    for rule in RULES:
        evidence = _evidence(rule["pattern"], text)
        if not evidence:
            continue

        # Repeated endpoints and credential vars matter, but cap each rule to
        # keep one verbose section from dominating the whole decision.
        repeat_bonus = min(len(evidence) - 1, 2)
        severity = int(rule["severity"]) + repeat_bonus
        score += severity
        hits.append(
            RuleHit(
                rule_id=rule["rule_id"],
                severity=severity,
                message=rule["message"],
                evidence=evidence,
            )
        )

    has_remote_installer = any(hit.rule_id == "remote-installer-pipe" for hit in hits)
    has_credential = any(hit.rule_id == "credential-env-write" for hit in hits)
    has_secret_path = any(hit.rule_id == "secret-file-path" for hit in hits)
    has_obfuscation = any(hit.rule_id == "obfuscated-execution" for hit in hits)

    if has_obfuscation or (has_remote_installer and (has_credential or has_secret_path)) or score >= 8:
        action = "block"
    elif score >= 3:
        action = "review"
    else:
        action = "allow"

    if action == "block":
        rationale = "high-confidence privacy or execution risk before model exposure"
    elif action == "review":
        rationale = "suspicious Skill signals require human or stricter model review"
    else:
        rationale = "no configured proxy rule crossed the review threshold"

    return ProxyDecision(
        skill_name=skill_name,
        action=action,
        score=score,
        triggered_rules=[asdict(hit) for hit in hits],
        rationale=rationale,
    )


def analyze_skill_file(path: Path) -> ProxyDecision:
    return analyze_skill_text(path.read_text(encoding="utf-8", errors="replace"), skill_name=path.parent.name)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run SkillProbe proxy-hook analysis on one Skill file")
    parser.add_argument("skill_file")
    args = parser.parse_args()

    decision = analyze_skill_file(Path(args.skill_file))
    print(json.dumps(asdict(decision), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
