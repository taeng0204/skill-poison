"""
Extract per-skill micro-features from 85 canifi SKILL.md files.
Output: skill_features.csv with one row per skill_name.
"""
import csv
import re
from pathlib import Path

SKILLS_DIR = Path(__file__).resolve().parents[2] / "docs" / "selected_skills"
OUT_PATH = Path(__file__).parent / "skill_features.csv"

SENSITIVITY_MAP = {
    "finance": "high",
    "health": "high",
    "healthcare": "high",
    "insurance": "high",
    "legal": "high",
    "hr": "high",
    "communication": "medium",
    "social": "medium",
    "productivity": "medium",
    "shopping": "medium",
    "ecommerce": "medium",
    "travel": "medium",
    "automotive": "medium",
    "real-estate": "medium",
    "realestate": "medium",
    "homeservices": "medium",
    "smart-home": "medium",
    "smarthome": "medium",
    "developer": "medium",
    "devops": "medium",
    "ai": "medium",
    "marketing": "medium",
    "analytics": "medium",
    "business": "medium",
    "utilities": "medium",
    "microsoft": "medium",
    "food": "low",
    "media": "low",
    "entertainment": "low",
    "gaming": "low",
    "news": "low",
    "education": "low",
    "design": "low",
}


def parse_frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return {}
    fm = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip()
    return fm


def extract_features(skill_dir):
    skill_md = skill_dir / "SKILL.md"
    text = skill_md.read_text(encoding="utf-8", errors="ignore")
    fm = parse_frontmatter(text)

    name = skill_dir.name
    category = fm.get("category", "unknown").lower()
    sensitivity = SENSITIVITY_MAP.get(category, "unknown")

    # Section count + presence
    sections = re.findall(r"^## (.+)$", text, re.M)
    section_set = set(s.strip() for s in sections)

    # canifi-env variable count and types
    env_lines = re.findall(r"canifi-env set\s+([A-Z0-9_]+)", text)
    n_env_vars = len(env_lines)
    n_unique_env_vars = len(set(env_lines))
    has_password_var = any("PASSWORD" in v for v in env_lines)
    has_apikey_var = any("API_KEY" in v or "APIKEY" in v for v in env_lines)
    has_token_var = any("TOKEN" in v for v in env_lines)
    has_oauth_vars = any("CLIENT_ID" in v or "CLIENT_SECRET" in v for v in env_lines)

    # Capabilities count (rough — bullet/numbered items under ## Capabilities)
    cap_match = re.search(r"## Capabilities\s*\n(.*?)(?=\n## |\Z)", text, re.S)
    n_capabilities = 0
    if cap_match:
        n_capabilities = len(re.findall(r"^[\-\*\d]+\.?\s+\S", cap_match.group(1), re.M))

    # Frontmatter completeness
    has_version = "version" in fm
    has_author = "author" in fm

    # Length proxies
    n_lines = text.count("\n") + 1
    n_chars = len(text)

    # Mentions of specific risk-related keywords (within text body)
    body_lower = text.lower()
    mentions_2fa = "2fa" in body_lower or "two-factor" in body_lower or "two factor" in body_lower
    mentions_imessage = "imessage" in body_lower
    mentions_self_improve = "## self-improvement" in body_lower

    return {
        "skill_name": name,
        "category": category,
        "sensitivity": sensitivity,
        "n_sections": len(sections),
        "n_env_vars": n_env_vars,
        "n_unique_env_vars": n_unique_env_vars,
        "has_password_var": int(has_password_var),
        "has_apikey_var": int(has_apikey_var),
        "has_token_var": int(has_token_var),
        "has_oauth_vars": int(has_oauth_vars),
        "n_capabilities": n_capabilities,
        "has_version": int(has_version),
        "has_author": int(has_author),
        "n_lines": n_lines,
        "n_chars": n_chars,
        "mentions_2fa": int(mentions_2fa),
        "mentions_imessage": int(mentions_imessage),
        "mentions_self_improve": int(mentions_self_improve),
    }


def main():
    rows = []
    for skill_dir in sorted(SKILLS_DIR.iterdir()):
        if not skill_dir.is_dir():
            continue
        rows.append(extract_features(skill_dir))

    with OUT_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {OUT_PATH}")
    # Quick sanity print
    cats = {}
    for r in rows:
        cats[r["category"]] = cats.get(r["category"], 0) + 1
    print("\nCategory distribution:")
    for c, n in sorted(cats.items(), key=lambda x: -x[1]):
        print(f"  {n:3d}  {c}  ({SENSITIVITY_MAP.get(c, 'unknown')})")


if __name__ == "__main__":
    main()
