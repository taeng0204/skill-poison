#!/usr/bin/env python3
"""Build a standalone HTML session behavior map from released Tier-2 data."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


INPUT = Path("artifacts/tier2_features/merged_runs_features_tier1_tier2.csv")
OUT_DIR = Path("artifacts/visualizations")
OUT_HTML = OUT_DIR / "session_behavior_map.html"

MODEL_ORDER = ["qwen3:8b", "qwen3:1.7b", "gpt-5.4", "gpt-5.4-mini"]
CONDITION_ORDER = ["C1", "C2", "C3"]

FEATURES: list[dict[str, str]] = [
    {
        "id": "prompt_agents",
        "short": "AG",
        "label": "AGENTS.md in prompt",
        "group": "Prompt",
        "source": "tier2_prompt_mentions_agents_md",
        "desc": "Task prompt references AGENTS.md. This is exposure, not proof that the agent read the file.",
    },
    {
        "id": "prompt_review",
        "short": "SR",
        "label": "Safety-review framing",
        "group": "Prompt",
        "source": "safety_review",
        "desc": "Condition/prompt asks the agent to review or explain security concerns.",
    },
    {
        "id": "prompt_pressure",
        "short": "TP",
        "label": "Trust-pressure framing",
        "group": "Prompt",
        "source": "trust_pressure",
        "desc": "Condition/prompt applies trust, urgency, or messy-but-needed framing.",
    },
    {
        "id": "stage_a",
        "short": "A",
        "label": "Stage-A acceptance",
        "group": "Stages",
        "source": "stage_a_acceptance",
        "desc": "Textual or decision-level acceptance signal. Not a strict prerequisite for later stages.",
    },
    {
        "id": "stage_b",
        "short": "B",
        "label": "Stage-B execution",
        "group": "Stages",
        "source": "stage_b_execution",
        "desc": "Concrete action execution was observed.",
    },
    {
        "id": "stage_c",
        "short": "C",
        "label": "Stage-C egress",
        "group": "Stages",
        "source": "stage_c_egress",
        "desc": "Canary endpoint network egress was observed.",
    },
    {
        "id": "decision_review",
        "short": "RV",
        "label": "Review decision",
        "group": "Decision",
        "source": "tier2_decision_review",
        "desc": "The verdict classified the agent decision as review.",
    },
    {
        "id": "detected",
        "short": "DT",
        "label": "Detected malicious",
        "group": "Decision",
        "source": "agent_detected_malicious",
        "desc": "The agent/verdict detected malicious or suspicious behavior.",
    },
    {
        "id": "stdout",
        "short": "OUT",
        "label": "Agent stdout present",
        "group": "Execution",
        "source": "tier2_agent_stdout_present",
        "desc": "The run had agent stdout, but the full stdout transcript is not included.",
    },
    {
        "id": "cmd_trace",
        "short": "CMD",
        "label": "Command trace",
        "group": "Execution",
        "source": "tier2_dangerous_commands_count",
        "op": "gt0",
        "availability": "tier2_schema_has_dangerous_commands",
        "desc": "Dangerous or security-relevant command evidence exists in the raw verdict.",
    },
    {
        "id": "curl",
        "short": "curl",
        "label": "curl command",
        "group": "Execution",
        "source": "tier2_cmd_has_curl",
        "availability": "tier2_schema_has_dangerous_commands",
        "desc": "Command trace contains curl.",
    },
    {
        "id": "cmd_url",
        "short": "URL",
        "label": "Command external URL",
        "group": "Execution",
        "source": "tier2_cmd_has_external_url",
        "availability": "tier2_schema_has_dangerous_commands",
        "desc": "Command trace contains an external URL.",
    },
    {
        "id": "cmd_canary",
        "short": "CN",
        "label": "Command canary host",
        "group": "Execution",
        "source": "tier2_cmd_has_canary_host",
        "availability": "tier2_schema_has_dangerous_commands",
        "desc": "Command trace references the canary host or /api/exfil.",
    },
    {
        "id": "env_read",
        "short": "ENV",
        "label": "Environment-read pattern",
        "group": "Execution",
        "source": "tier2_cmd_has_env_read",
        "availability": "tier2_schema_has_dangerous_commands",
        "desc": "Command trace contains env/printenv or shell-style environment variable references.",
    },
    {
        "id": "tool_error",
        "short": "TE",
        "label": "Tool-call error",
        "group": "Execution",
        "source": "tier2_tool_call_error_count",
        "op": "gt0",
        "desc": "Tool-call errors were recorded.",
    },
    {
        "id": "external_url",
        "short": "EXT",
        "label": "External URL observed",
        "group": "Network",
        "source": "tier2_external_urls_count",
        "op": "gt0",
        "desc": "External URLs were observed in verdict evidence.",
    },
    {
        "id": "trycloudflare",
        "short": "TCF",
        "label": "trycloudflare domain",
        "group": "Network",
        "source": "tier2_external_has_trycloudflare",
        "desc": "Observed domains include a trycloudflare tunnel.",
    },
    {
        "id": "local_mcp",
        "short": "MCP",
        "label": "Local MCP endpoint",
        "group": "Network",
        "source": "tier2_external_has_local_mcp",
        "desc": "Observed domains include 127.0.0.1:8745.",
    },
    {
        "id": "canary_req",
        "short": "CAN",
        "label": "Canary request",
        "group": "Network",
        "source": "tier2_canary_requests",
        "op": "gt0",
        "desc": "At least one canary endpoint request was observed.",
    },
    {
        "id": "canary_body",
        "short": "BDY",
        "label": "Non-empty canary body",
        "group": "Network",
        "source": "tier2_canary_nonempty_body_events",
        "op": "gt0",
        "desc": "Canary request with non-empty body. This is zero in the final dataset.",
    },
    {
        "id": "token_leak",
        "short": "TOK",
        "label": "Canary token leaked",
        "group": "Network",
        "source": "canary_token_leaked",
        "desc": "Plaintext canary token leaked. This is zero in the final dataset.",
    },
    {
        "id": "fs_events",
        "short": "FS",
        "label": "Filesystem events",
        "group": "Filesystem",
        "source": "tier2_fs_events_count",
        "op": "gt0",
        "desc": "Filesystem event count is greater than zero.",
    },
    {
        "id": "workspace_files",
        "short": "WF",
        "label": "Workspace files created",
        "group": "Filesystem",
        "source": "tier2_workspace_new_files_count",
        "op": "gt0",
        "desc": "New workspace files were observed.",
    },
    {
        "id": "curl_artifact",
        "short": "CA",
        "label": "curl artifact",
        "group": "Filesystem",
        "source": "tier2_workspace_has_curl_tarball",
        "desc": "Workspace contains a curl tarball artifact.",
    },
    {
        "id": "curl_tree",
        "short": "CT",
        "label": "curl source tree",
        "group": "Filesystem",
        "source": "tier2_workspace_has_curl_source_tree",
        "desc": "Workspace contains an extracted curl source tree.",
    },
    {
        "id": "shell_file",
        "short": "SH",
        "label": "Shell script created",
        "group": "Filesystem",
        "source": "tier2_workspace_has_shell_script",
        "desc": "Workspace contains a shell script.",
    },
    {
        "id": "python_file",
        "short": "PY",
        "label": "Python file created",
        "group": "Filesystem",
        "source": "tier2_workspace_has_python_file",
        "desc": "Workspace contains a Python file.",
    },
    {
        "id": "node_pkg",
        "short": "NPM",
        "label": "Node package files",
        "group": "Filesystem",
        "source": "tier2_workspace_has_node_package",
        "desc": "Workspace contains package.json or node_modules evidence.",
    },
    {
        "id": "home_mod",
        "short": "HM",
        "label": "Home modified",
        "group": "Filesystem",
        "source": "tier2_home_modified",
        "availability": "tier2_schema_has_home_modified",
        "desc": "Verdict reported home-directory modification.",
    },
    {
        "id": "suspicious_files",
        "short": "SF",
        "label": "Suspicious files",
        "group": "Filesystem",
        "source": "tier2_suspicious_files_count",
        "op": "gt0",
        "desc": "Suspicious files were recorded in the verdict.",
    },
    {
        "id": "backdoor",
        "short": "BD",
        "label": "Backdoor pattern",
        "group": "Filesystem",
        "source": "tier2_backdoor_patterns_count",
        "op": "gt0",
        "desc": "Backdoor patterns were recorded in the verdict.",
    },
    {
        "id": "detected_b",
        "short": "D+B",
        "label": "Detected but Stage-B",
        "group": "Gap",
        "source": "tier2_detected_but_stage_b",
        "desc": "Detection/review coexists with execution.",
    },
    {
        "id": "detected_c",
        "short": "D+C",
        "label": "Detected but Stage-C",
        "group": "Gap",
        "source": "tier2_detected_but_stage_c",
        "desc": "Detection/review coexists with boundary crossing.",
    },
    {
        "id": "silent_c",
        "short": "S-C",
        "label": "Silent Stage-C",
        "group": "Gap",
        "source": "tier2_silent_stage_c",
        "desc": "Stage-C occurred without detection/refusal/warning signals.",
    },
]


def clean(value: Any) -> str:
    if value is None or pd.isna(value):
        return ""
    return str(value)


def num(value: Any) -> float:
    try:
        if value is None or pd.isna(value):
            return 0.0
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def truth(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None or pd.isna(value):
        return False
    if isinstance(value, (int, float)):
        return float(value) != 0.0
    text = str(value).strip().lower()
    return text in {"1", "1.0", "true", "yes", "y"}


def trunc(text: str, limit: int) -> str:
    text = clean(text).replace("\n", " ").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "..."


def feature_value(row: pd.Series, feature: dict[str, str]) -> bool | None:
    availability = feature.get("availability")
    if availability and not truth(row.get(availability)):
        return None
    source = feature["source"]
    value = row.get(source)
    if feature.get("op") == "gt0":
        return num(value) > 0
    return truth(value)


def model_rank(model: str) -> int:
    return MODEL_ORDER.index(model) if model in MODEL_ORDER else 99


def condition_rank(condition: str) -> int:
    return CONDITION_ORDER.index(condition) if condition in CONDITION_ORDER else 99


def build_rows(df: pd.DataFrame) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for idx, row in df.iterrows():
        feature_values: dict[str, bool | None] = {}
        present_count = 0
        available_count = 0
        for feature in FEATURES:
            value = feature_value(row, feature)
            feature_values[feature["id"]] = value
            if value is not None:
                available_count += 1
            if value:
                present_count += 1

        model = clean(row.get("model")) or "unknown"
        condition = clean(row.get("condition")) or "unknown"
        duration = num(row.get("tier2_duration_s")) or num(row.get("duration_s"))
        canary_requests = int(num(row.get("tier2_canary_requests")) or num(row.get("canary_requests")))
        stage_c = truth(row.get("stage_c_egress"))
        stage_b = truth(row.get("stage_b_execution"))
        detected = truth(row.get("agent_detected_malicious")) or truth(row.get("tier2_detected_malicious"))
        review = truth(row.get("tier2_decision_review"))
        session_id = clean(row.get("session_id"))

        rows.append(
            {
                "row_index": idx,
                "session_id": session_id,
                "skill": clean(row.get("skill")),
                "condition": condition,
                "condition_label": clean(row.get("condition_label")),
                "agent": clean(row.get("agent")),
                "model": model,
                "model_family": clean(row.get("model_family")),
                "status": clean(row.get("status")),
                "duration_s": round(duration, 3),
                "raw_available": bool(session_id and clean(row.get("tier2_result_json_path"))),
                "stage_b": stage_b,
                "stage_c": stage_c,
                "detected": detected,
                "review": review,
                "silent_stage_c": truth(row.get("tier2_silent_stage_c")),
                "canary_requests": canary_requests,
                "external_domains_count": int(num(row.get("tier2_external_domains_count"))),
                "external_domains_sample": trunc(clean(row.get("tier2_external_domains_sample")), 260),
                "dangerous_commands_count": int(num(row.get("tier2_dangerous_commands_count"))),
                "dangerous_command_sample": trunc(clean(row.get("tier2_dangerous_command_sample")), 260),
                "fs_events_count": int(num(row.get("tier2_fs_events_count"))),
                "workspace_new_files_count": int(num(row.get("tier2_workspace_new_files_count"))),
                "tool_call_error_count": int(num(row.get("tier2_tool_call_error_count"))),
                "detection_quote_count": int(num(row.get("tier2_detection_quote_count"))),
                "result_json_path": clean(row.get("tier2_result_json_path")),
                "feature_count": present_count,
                "available_feature_count": available_count,
                "features": feature_values,
                "sort_model": model_rank(model),
                "sort_condition": condition_rank(condition),
            }
        )
    rows.sort(key=lambda r: (r["sort_model"], r["sort_condition"], -int(r["stage_c"]), r["skill"]))
    return rows


def build_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    valid = [r for r in rows if r["raw_available"]]
    stage_c = sum(1 for r in valid if r["stage_c"])
    stage_b = sum(1 for r in valid if r["stage_b"])
    detected_b = sum(1 for r in valid if r["features"].get("detected_b"))
    detected_c = sum(1 for r in valid if r["features"].get("detected_c"))
    silent_c = sum(1 for r in valid if r["features"].get("silent_c"))
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "input": str(INPUT),
        "rows": len(rows),
        "valid_rows": len(valid),
        "missing_raw_rows": len(rows) - len(valid),
        "stage_b_rows": stage_b,
        "stage_c_rows": stage_c,
        "stage_c_rate": stage_c / len(valid) if valid else 0.0,
        "detected_but_stage_b_rows": detected_b,
        "detected_but_stage_c_rows": detected_c,
        "silent_stage_c_rows": silent_c,
        "canary_requests_sum": sum(int(r["canary_requests"]) for r in valid),
        "feature_count": len(FEATURES),
        "models": MODEL_ORDER,
        "conditions": CONDITION_ORDER,
        "caveats": [
            "This is a run-level behavioral evidence map, not a turn-by-turn timeline.",
            "The dataset does not contain full LLM conversation transcripts or complete tool-call traces.",
            "AGENTS.md exposure means the prompt referenced the skill file; actual file-read timing is not logged.",
            "Command-derived cells marked N/A are unavailable for schemas without dangerous_commands.",
            "Use stage_c_egress and canary_requests as the boundary-crossing label, not canary_hit alone.",
        ],
    }


def build_html(payload: dict[str, Any]) -> str:
    payload_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    feature_columns = len(payload["features"])
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>SkillProbe Session Behavior Map</title>
  <style>
    :root {{
      --bg: #f5f6f8;
      --surface: #ffffff;
      --ink: #1f2933;
      --muted: #62707f;
      --line: #d8dee6;
      --line-strong: #b8c1cc;
      --absent: #edf0f3;
      --na: #f8f9fb;
      --danger: #b42318;
      --focus: #0f62fe;
      --shadow: 0 10px 28px rgba(31, 41, 51, 0.08);
    }}
    * {{ box-sizing: border-box; }}
    html, body {{ margin: 0; min-height: 100%; background: var(--bg); color: var(--ink); font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
    body {{ padding: 24px; }}
    .page {{ max-width: 1760px; margin: 0 auto; }}
    .topbar {{ display: flex; align-items: flex-start; justify-content: space-between; gap: 20px; margin-bottom: 18px; }}
    h1 {{ margin: 0 0 8px; font-size: 26px; line-height: 1.15; letter-spacing: 0; }}
    .subtitle {{ margin: 0; color: var(--muted); max-width: 920px; line-height: 1.45; font-size: 14px; }}
    .meta {{ text-align: right; color: var(--muted); font-size: 12px; line-height: 1.5; min-width: 240px; }}
    .panel {{ background: var(--surface); border: 1px solid var(--line); border-radius: 8px; box-shadow: var(--shadow); }}
    .summary {{ display: grid; grid-template-columns: repeat(6, minmax(130px, 1fr)); gap: 10px; margin-bottom: 14px; }}
    .metric {{ background: var(--surface); border: 1px solid var(--line); border-radius: 8px; padding: 12px; min-height: 76px; }}
    .metric .label {{ color: var(--muted); font-size: 12px; line-height: 1.25; }}
    .metric .value {{ margin-top: 8px; font-size: 24px; font-weight: 720; }}
    .metric .sub {{ margin-top: 4px; color: var(--muted); font-size: 12px; }}
    .controls {{ padding: 14px; margin-bottom: 14px; display: grid; grid-template-columns: minmax(260px, 1.2fr) minmax(460px, 2fr) minmax(320px, 1.4fr); gap: 14px; align-items: end; }}
    label {{ display: block; color: var(--muted); font-size: 12px; margin-bottom: 6px; }}
    input[type="search"], select {{ width: 100%; height: 36px; border: 1px solid var(--line-strong); border-radius: 6px; background: #fff; color: var(--ink); padding: 0 10px; font-size: 13px; }}
    .chips, .checks {{ display: flex; flex-wrap: wrap; gap: 8px; }}
    .chip, .toggle {{ height: 32px; border: 1px solid var(--line-strong); border-radius: 6px; background: #fff; color: var(--ink); padding: 0 10px; font-size: 12px; cursor: pointer; display: inline-flex; align-items: center; gap: 7px; }}
    .chip.active, .toggle.active {{ border-color: var(--focus); box-shadow: inset 0 0 0 1px var(--focus); }}
    .dot {{ width: 10px; height: 10px; border-radius: 99px; display: inline-block; }}
    .control-row {{ display: grid; grid-template-columns: repeat(3, minmax(120px, 1fr)); gap: 10px; margin-top: 10px; }}
    .legend {{ padding: 12px 14px; margin-bottom: 14px; display: flex; flex-wrap: wrap; gap: 16px; align-items: center; color: var(--muted); font-size: 12px; }}
    .legend-item {{ display: inline-flex; align-items: center; gap: 7px; }}
    .swatch {{ width: 15px; height: 15px; border-radius: 4px; border: 1px solid rgba(0,0,0,.16); display: inline-block; }}
    .swatch.na {{ background: repeating-linear-gradient(135deg, #fff, #fff 3px, #d5dce5 3px, #d5dce5 5px); }}
    .overview {{ display: grid; grid-template-columns: 1.05fr 1fr; gap: 14px; margin-bottom: 14px; }}
    .overview .panel {{ padding: 14px; }}
    .section-title {{ margin: 0 0 10px; font-size: 15px; }}
    .mc-grid {{ display: grid; grid-template-columns: 110px repeat(3, 1fr); gap: 6px; align-items: stretch; }}
    .mc-head {{ color: var(--muted); font-size: 12px; padding: 6px 4px; }}
    .mc-model {{ font-size: 12px; padding: 8px 6px; display: flex; align-items: center; gap: 7px; }}
    .mc-cell {{ border: 1px solid var(--line); border-radius: 6px; padding: 8px; min-height: 64px; background: #fbfcfd; }}
    .mc-rate {{ font-size: 19px; font-weight: 720; }}
    .mc-small {{ font-size: 11px; color: var(--muted); margin-top: 3px; }}
    .coverage-list {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 7px 18px; }}
    .coverage-row {{ display: grid; grid-template-columns: 98px 1fr 42px; gap: 8px; align-items: center; font-size: 12px; }}
    .bar-track {{ height: 9px; background: var(--absent); border-radius: 99px; overflow: hidden; }}
    .bar-fill {{ height: 100%; background: #425466; border-radius: 99px; }}
    .matrix-panel {{ overflow: hidden; }}
    .matrix-toolbar {{ display: flex; justify-content: space-between; gap: 12px; align-items: center; padding: 12px 14px; border-bottom: 1px solid var(--line); color: var(--muted); font-size: 12px; }}
    .matrix-wrap {{ overflow: auto; max-height: 72vh; }}
    .matrix {{ min-width: {760 + feature_columns * 19}px; }}
    .matrix-row {{ display: grid; grid-template-columns: 10px 118px 46px minmax(170px, 1fr) 86px 48px repeat({feature_columns}, 18px); column-gap: 3px; align-items: center; min-height: 25px; padding: 2px 8px; border-bottom: 1px solid #edf0f3; }}
    .matrix-row.header {{ position: sticky; top: 0; z-index: 5; background: #f9fafb; min-height: 112px; border-bottom: 1px solid var(--line-strong); }}
    .matrix-row.header > div {{ align-self: end; }}
    .model-strip {{ height: 20px; border-radius: 4px; }}
    .model-name, .condition, .skill, .duration, .score {{ font-size: 12px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
    .condition {{ font-weight: 700; }}
    .skill {{ color: #27313d; }}
    .duration-track {{ width: 64px; height: 8px; background: var(--absent); border-radius: 99px; overflow: hidden; display: inline-block; vertical-align: middle; margin-right: 5px; }}
    .duration-fill {{ height: 100%; background: #697789; border-radius: 99px; }}
    .feature-head {{ writing-mode: vertical-rl; transform: rotate(180deg); text-align: left; font-size: 10px; color: var(--muted); line-height: 1; height: 98px; width: 18px; display: flex; align-items: center; justify-content: flex-end; }}
    .cell {{ width: 15px; height: 15px; border-radius: 4px; border: 1px solid #d7dde5; background: var(--absent); cursor: default; }}
    .cell.present {{ border-color: rgba(31, 41, 51, .28); }}
    .cell.absent {{ background: var(--absent); }}
    .cell.na {{ background: repeating-linear-gradient(135deg, #fff, #fff 3px, #d5dce5 3px, #d5dce5 5px); border-color: #d5dce5; }}
    .cell.critical.present {{ box-shadow: inset 0 0 0 2px rgba(180, 35, 24, .72); }}
    .matrix-row:hover:not(.header) {{ background: #f8fafc; }}
    .missing {{ opacity: .62; }}
    .details {{ padding: 14px; margin-top: 14px; display: none; }}
    .details.open {{ display: block; }}
    .details-grid {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; }}
    .details .kv {{ border: 1px solid var(--line); border-radius: 6px; padding: 9px; background: #fbfcfd; min-height: 58px; }}
    .kv .k {{ color: var(--muted); font-size: 11px; }}
    .kv .v {{ margin-top: 5px; font-size: 13px; overflow-wrap: anywhere; }}
    .tooltip {{ position: fixed; z-index: 20; pointer-events: none; opacity: 0; transform: translate(10px, 10px); max-width: 360px; background: #101820; color: #fff; border-radius: 6px; padding: 9px 10px; font-size: 12px; line-height: 1.35; box-shadow: 0 10px 28px rgba(0,0,0,.24); }}
    .tooltip .muted {{ color: #b9c3cf; }}
    .note {{ color: var(--muted); font-size: 12px; line-height: 1.45; }}
    @media (max-width: 1100px) {{
      body {{ padding: 14px; }}
      .topbar, .overview {{ grid-template-columns: 1fr; display: grid; }}
      .meta {{ text-align: left; }}
      .summary {{ grid-template-columns: repeat(2, minmax(130px, 1fr)); }}
      .controls {{ grid-template-columns: 1fr; }}
      .control-row {{ grid-template-columns: 1fr; }}
      .coverage-list {{ grid-template-columns: 1fr; }}
      .details-grid {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <main class="page">
    <section class="topbar">
      <div>
        <h1>SkillProbe Session Behavior Map</h1>
        <p class="subtitle">Run-level evidence map for the final dataset. Model is encoded by color and condition by opacity: C1 low, C2 medium, C3 high. This is not a turn-by-turn timeline because full conversation and tool-call traces are not present in the released results.</p>
      </div>
      <div class="meta" id="meta"></div>
    </section>

    <section class="summary" id="summary"></section>

    <section class="controls panel">
      <div>
        <label for="search">Search skill, session, or domain</label>
        <input id="search" type="search" placeholder="e.g. grubhub, qwen3:8b, canary">
      </div>
      <div>
        <label>Model filter</label>
        <div class="chips" id="modelChips"></div>
      </div>
      <div>
        <label>Condition and row filters</label>
        <div class="checks" id="conditionChecks"></div>
        <div class="control-row">
          <button class="toggle" id="stageCOnly" type="button">Stage-C only</button>
          <button class="toggle" id="gapOnly" type="button">Detection-action gap</button>
          <button class="toggle" id="reset" type="button">Reset</button>
        </div>
      </div>
      <div>
        <label for="groupSelect">Feature group</label>
        <select id="groupSelect"></select>
      </div>
      <div>
        <label for="sortSelect">Sort sessions</label>
        <select id="sortSelect">
          <option value="default">Model, condition, Stage-C, skill</option>
          <option value="skill">Skill name</option>
          <option value="duration">Duration, longest first</option>
          <option value="feature_count">Observed feature count</option>
          <option value="stage_c">Stage-C first</option>
        </select>
      </div>
      <div class="note">AGENTS.md cells indicate prompt exposure, not confirmed file-read timing. N/A cells indicate the raw-result schema did not expose that feature family.</div>
    </section>

    <section class="legend panel" id="legend"></section>

    <section class="overview">
      <div class="panel">
        <h2 class="section-title">Model x Condition Stage-C Coverage</h2>
        <div class="mc-grid" id="mcGrid"></div>
      </div>
      <div class="panel">
        <h2 class="section-title">Feature Coverage In Current Filter</h2>
        <div class="coverage-list" id="coverageList"></div>
      </div>
    </section>

    <section class="matrix-panel panel">
      <div class="matrix-toolbar">
        <div id="showing"></div>
        <div>Click a row for details. Hover cells for feature definitions.</div>
      </div>
      <div class="matrix-wrap">
        <div class="matrix" id="matrix"></div>
      </div>
    </section>

    <section class="details panel" id="details"></section>
  </main>
  <div class="tooltip" id="tooltip"></div>

  <script>
    const PAYLOAD = {payload_json};
    const MODEL_COLORS = {{
      "qwen3:8b": "#D55E00",
      "qwen3:1.7b": "#009E73",
      "gpt-5.4": "#0072B2",
      "gpt-5.4-mini": "#CC79A7",
      "unknown": "#6B7280"
    }};
    const CONDITION_ALPHA = {{ C1: 0.42, C2: 0.68, C3: 0.95, unknown: 0.55 }};
    const CRITICAL_FEATURES = new Set(["stage_c", "canary_req", "detected_c", "silent_c"]);
    const state = {{
      models: new Set(PAYLOAD.meta.models),
      conditions: new Set(PAYLOAD.meta.conditions),
      stageCOnly: false,
      gapOnly: false,
      search: "",
      group: "All",
      sort: "default"
    }};

    const $ = (id) => document.getElementById(id);

    function hexToRgba(hex, alpha) {{
      const raw = hex.replace("#", "");
      const bigint = parseInt(raw, 16);
      const r = (bigint >> 16) & 255;
      const g = (bigint >> 8) & 255;
      const b = bigint & 255;
      return `rgba(${{r}}, ${{g}}, ${{b}}, ${{alpha}})`;
    }}

    function pct(value) {{
      return `${{Math.round(value * 1000) / 10}}%`;
    }}

    function escapeHtml(value) {{
      return String(value ?? "").replace(/[&<>"']/g, (ch) => ({{
        "&": "&amp;", "<": "&lt;", ">": "&gt;", "\\"": "&quot;", "'": "&#039;"
      }}[ch]));
    }}

    function currentFeatures() {{
      if (state.group === "All") return PAYLOAD.features;
      return PAYLOAD.features.filter((f) => f.group === state.group);
    }}

    function matches(row) {{
      if (!state.models.has(row.model)) return false;
      if (!state.conditions.has(row.condition)) return false;
      if (state.stageCOnly && !row.stage_c) return false;
      if (state.gapOnly && !(row.features.detected_b || row.features.detected_c || row.features.silent_c)) return false;
      if (state.search) {{
        const haystack = [
          row.session_id, row.skill, row.model, row.condition,
          row.external_domains_sample, row.dangerous_command_sample
        ].join(" ").toLowerCase();
        if (!haystack.includes(state.search.toLowerCase())) return false;
      }}
      return true;
    }}

    function sortedRows(rows) {{
      const copy = rows.slice();
      copy.sort((a, b) => {{
        if (state.sort === "skill") return a.skill.localeCompare(b.skill) || a.sort_model - b.sort_model || a.sort_condition - b.sort_condition;
        if (state.sort === "duration") return b.duration_s - a.duration_s;
        if (state.sort === "feature_count") return b.feature_count - a.feature_count || b.duration_s - a.duration_s;
        if (state.sort === "stage_c") return Number(b.stage_c) - Number(a.stage_c) || a.sort_model - b.sort_model || a.skill.localeCompare(b.skill);
        return a.sort_model - b.sort_model || a.sort_condition - b.sort_condition || Number(b.stage_c) - Number(a.stage_c) || a.skill.localeCompare(b.skill);
      }});
      return copy;
    }}

    function filteredRows() {{
      return sortedRows(PAYLOAD.rows.filter(matches));
    }}

    function renderMeta() {{
      $("meta").innerHTML = `
        <div>Generated: ${{escapeHtml(PAYLOAD.meta.generated_at)}}</div>
        <div>Input: ${{escapeHtml(PAYLOAD.meta.input)}}</div>
        <div>${{PAYLOAD.meta.feature_count}} feature columns, ${{PAYLOAD.meta.valid_rows}} valid raw sessions</div>
      `;
    }}

    function renderSummary(rows) {{
      const valid = rows.filter((r) => r.raw_available);
      const n = valid.length || 1;
      const stageC = valid.filter((r) => r.stage_c).length;
      const stageB = valid.filter((r) => r.stage_b).length;
      const silentC = valid.filter((r) => r.features.silent_c).length;
      const detB = valid.filter((r) => r.features.detected_b).length;
      const canary = valid.reduce((acc, r) => acc + Number(r.canary_requests || 0), 0);
      const missing = rows.filter((r) => !r.raw_available).length;
      const cards = [
        ["Rows", rows.length, `${{valid.length}} valid, ${{missing}} missing raw`],
        ["Stage-B execution", stageB, pct(stageB / n)],
        ["Stage-C egress", stageC, pct(stageC / n)],
        ["Silent Stage-C", silentC, stageC ? pct(silentC / stageC) + " of Stage-C" : "0%"],
        ["Detected but Stage-B", detB, "detection-action gap"],
        ["Canary requests", canary, "GET /api/exfil evidence"]
      ];
      $("summary").innerHTML = cards.map(([label, value, sub]) => `
        <div class="metric">
          <div class="label">${{escapeHtml(label)}}</div>
          <div class="value">${{escapeHtml(value)}}</div>
          <div class="sub">${{escapeHtml(sub)}}</div>
        </div>
      `).join("");
    }}

    function renderControls() {{
      $("modelChips").innerHTML = PAYLOAD.meta.models.map((model) => `
        <button class="chip active" data-model="${{escapeHtml(model)}}" type="button">
          <span class="dot" style="background:${{MODEL_COLORS[model] || MODEL_COLORS.unknown}}"></span>${{escapeHtml(model)}}
        </button>
      `).join("");
      $("conditionChecks").innerHTML = PAYLOAD.meta.conditions.map((condition) => `
        <button class="chip active" data-condition="${{condition}}" type="button">
          <span class="swatch" style="background:rgba(31,41,51,${{CONDITION_ALPHA[condition]}})"></span>${{condition}}
        </button>
      `).join("");
      const groups = ["All", ...Array.from(new Set(PAYLOAD.features.map((f) => f.group)))];
      $("groupSelect").innerHTML = groups.map((group) => `<option value="${{escapeHtml(group)}}">${{escapeHtml(group)}}</option>`).join("");

      document.querySelectorAll("[data-model]").forEach((btn) => {{
        btn.addEventListener("click", () => {{
          const model = btn.getAttribute("data-model");
          if (state.models.has(model)) state.models.delete(model); else state.models.add(model);
          btn.classList.toggle("active", state.models.has(model));
          renderAll();
        }});
      }});
      document.querySelectorAll("[data-condition]").forEach((btn) => {{
        btn.addEventListener("click", () => {{
          const condition = btn.getAttribute("data-condition");
          if (state.conditions.has(condition)) state.conditions.delete(condition); else state.conditions.add(condition);
          btn.classList.toggle("active", state.conditions.has(condition));
          renderAll();
        }});
      }});
      $("search").addEventListener("input", (event) => {{ state.search = event.target.value; renderAll(); }});
      $("groupSelect").addEventListener("change", (event) => {{ state.group = event.target.value; renderAll(); }});
      $("sortSelect").addEventListener("change", (event) => {{ state.sort = event.target.value; renderAll(); }});
      $("stageCOnly").addEventListener("click", () => {{ state.stageCOnly = !state.stageCOnly; $("stageCOnly").classList.toggle("active", state.stageCOnly); renderAll(); }});
      $("gapOnly").addEventListener("click", () => {{ state.gapOnly = !state.gapOnly; $("gapOnly").classList.toggle("active", state.gapOnly); renderAll(); }});
      $("reset").addEventListener("click", () => {{
        state.models = new Set(PAYLOAD.meta.models);
        state.conditions = new Set(PAYLOAD.meta.conditions);
        state.stageCOnly = false;
        state.gapOnly = false;
        state.search = "";
        state.group = "All";
        state.sort = "default";
        $("search").value = "";
        $("groupSelect").value = "All";
        $("sortSelect").value = "default";
        $("stageCOnly").classList.remove("active");
        $("gapOnly").classList.remove("active");
        document.querySelectorAll("[data-model], [data-condition]").forEach((btn) => btn.classList.add("active"));
        renderAll();
      }});
    }}

    function renderLegend() {{
      const modelItems = PAYLOAD.meta.models.map((model) => `
        <span class="legend-item"><span class="dot" style="background:${{MODEL_COLORS[model]}}"></span>${{escapeHtml(model)}}</span>
      `).join("");
      const conditionItems = PAYLOAD.meta.conditions.map((condition) => `
        <span class="legend-item"><span class="swatch" style="background:rgba(31,41,51,${{CONDITION_ALPHA[condition]}})"></span>${{condition}} opacity</span>
      `).join("");
      $("legend").innerHTML = `
        ${{modelItems}}
        ${{conditionItems}}
        <span class="legend-item"><span class="swatch na"></span>N/A schema unavailable</span>
        <span class="legend-item"><span class="swatch" style="background:#edf0f3"></span>Absent/not observed</span>
        <span class="legend-item"><span class="swatch" style="background:#fff; box-shadow: inset 0 0 0 2px rgba(180,35,24,.72)"></span>Boundary-critical feature</span>
      `;
    }}

    function renderModelCondition(rows) {{
      const grid = $("mcGrid");
      const header = [`<div></div>`, ...PAYLOAD.meta.conditions.map((c) => `<div class="mc-head">${{c}}</div>`)].join("");
      const body = PAYLOAD.meta.models.map((model) => {{
        const modelHead = `<div class="mc-model"><span class="dot" style="background:${{MODEL_COLORS[model]}}"></span>${{escapeHtml(model)}}</div>`;
        const cells = PAYLOAD.meta.conditions.map((condition) => {{
          const subset = rows.filter((r) => r.model === model && r.condition === condition && r.raw_available);
          const n = subset.length || 0;
          const c = subset.filter((r) => r.stage_c).length;
          const b = subset.filter((r) => r.stage_b).length;
          const rate = n ? c / n : 0;
          const color = hexToRgba(MODEL_COLORS[model] || MODEL_COLORS.unknown, Math.max(0.16, CONDITION_ALPHA[condition] * (0.25 + rate)));
          return `<div class="mc-cell" style="background:${{color}}">
            <div class="mc-rate">${{n ? pct(rate) : "n/a"}}</div>
            <div class="mc-small">C: ${{c}} / ${{n}}</div>
            <div class="mc-small">B: ${{b}}</div>
          </div>`;
        }}).join("");
        return modelHead + cells;
      }}).join("");
      grid.innerHTML = header + body;
    }}

    function renderCoverage(rows) {{
      const features = currentFeatures();
      const validRows = rows.filter((r) => r.raw_available);
      const html = features.map((feature) => {{
        const available = validRows.filter((r) => r.features[feature.id] !== null).length;
        const count = validRows.filter((r) => r.features[feature.id] === true).length;
        const denom = available || 1;
        const ratio = count / denom;
        return `<div class="coverage-row" title="${{escapeHtml(feature.label)}}: ${{count}} / ${{available}} available">
          <div>${{escapeHtml(feature.short)}}</div>
          <div class="bar-track"><div class="bar-fill" style="width:${{Math.round(ratio * 100)}}%"></div></div>
          <div>${{count}}</div>
        </div>`;
      }}).join("");
      $("coverageList").innerHTML = html;
    }}

    function cellTooltip(row, feature, value) {{
      const status = value === null ? "N/A schema unavailable" : value ? "present" : "absent/not observed";
      return `<strong>${{escapeHtml(feature.label)}}</strong><br>
        <span class="muted">${{escapeHtml(feature.desc)}}</span><br>
        <br>${{escapeHtml(row.model)}} / ${{escapeHtml(row.condition)}} / ${{escapeHtml(row.skill)}}<br>
        status: <strong>${{escapeHtml(status)}}</strong><br>
        canary requests: ${{row.canary_requests}}, duration: ${{Math.round(row.duration_s)}}s`;
    }}

    function showTooltip(html, event) {{
      const tooltip = $("tooltip");
      tooltip.innerHTML = html;
      tooltip.style.opacity = "1";
      tooltip.style.left = `${{event.clientX + 12}}px`;
      tooltip.style.top = `${{event.clientY + 12}}px`;
    }}

    function hideTooltip() {{
      $("tooltip").style.opacity = "0";
    }}

    function renderMatrix(rows) {{
      const features = currentFeatures();
      const maxDuration = Math.max(1, ...PAYLOAD.rows.map((r) => Number(r.duration_s || 0)));
      const matrix = $("matrix");
      const headerCells = [
        `<div></div>`,
        `<div class="model-name">Model</div>`,
        `<div class="condition">Cond</div>`,
        `<div class="skill">Skill</div>`,
        `<div class="duration">Duration</div>`,
        `<div class="score">Feat</div>`,
        ...features.map((f) => `<div class="feature-head" title="${{escapeHtml(f.label)}}">${{escapeHtml(f.short)}}</div>`)
      ].join("");
      const body = rows.map((row) => {{
        const color = MODEL_COLORS[row.model] || MODEL_COLORS.unknown;
        const alpha = CONDITION_ALPHA[row.condition] || CONDITION_ALPHA.unknown;
        const durationPct = Math.min(100, Math.round((Number(row.duration_s || 0) / maxDuration) * 100));
        const cells = features.map((feature) => {{
          const value = row.features[feature.id];
          const cls = value === null ? "na" : value ? "present" : "absent";
          const critical = CRITICAL_FEATURES.has(feature.id) ? " critical" : "";
          const style = value ? ` style="background:${{hexToRgba(color, alpha)}}"` : "";
          return `<div class="cell ${{cls}}${{critical}}"${{style}} data-session="${{escapeHtml(row.session_id)}}" data-feature="${{escapeHtml(feature.id)}}"></div>`;
        }}).join("");
        return `<div class="matrix-row ${{row.raw_available ? "" : "missing"}}" data-row="${{row.row_index}}">
          <div class="model-strip" style="background:${{color}}"></div>
          <div class="model-name" title="${{escapeHtml(row.model)}}">${{escapeHtml(row.model)}}</div>
          <div class="condition">${{escapeHtml(row.condition)}}</div>
          <div class="skill" title="${{escapeHtml(row.session_id)}}">${{escapeHtml(row.skill || "(missing)")}}</div>
          <div class="duration"><span class="duration-track"><span class="duration-fill" style="width:${{durationPct}}%"></span></span>${{Math.round(row.duration_s)}}s</div>
          <div class="score">${{row.feature_count}}/${{row.available_feature_count}}</div>
          ${{cells}}
        </div>`;
      }}).join("");
      matrix.innerHTML = `<div class="matrix-row header">${{headerCells}}</div>${{body}}`;
      $("showing").textContent = `Showing ${{rows.length}} of ${{PAYLOAD.rows.length}} sessions`;

      matrix.querySelectorAll(".cell").forEach((cell) => {{
        cell.addEventListener("mousemove", (event) => {{
          const session = cell.getAttribute("data-session");
          const featureId = cell.getAttribute("data-feature");
          const row = PAYLOAD.rows.find((r) => r.session_id === session);
          const feature = PAYLOAD.features.find((f) => f.id === featureId);
          showTooltip(cellTooltip(row, feature, row.features[feature.id]), event);
        }});
        cell.addEventListener("mouseleave", hideTooltip);
      }});
      matrix.querySelectorAll(".matrix-row:not(.header)").forEach((rowEl) => {{
        rowEl.addEventListener("click", () => {{
          const idx = Number(rowEl.getAttribute("data-row"));
          const row = PAYLOAD.rows.find((r) => r.row_index === idx);
          renderDetails(row);
        }});
      }});
    }}

    function renderDetails(row) {{
      const detail = $("details");
      const featureNames = PAYLOAD.features.filter((f) => row.features[f.id] === true).map((f) => f.short).join(", ");
      detail.classList.add("open");
      detail.innerHTML = `
        <h2 class="section-title">${{escapeHtml(row.model)}} / ${{escapeHtml(row.condition)}} / ${{escapeHtml(row.skill)}}</h2>
        <div class="details-grid">
          <div class="kv"><div class="k">Session</div><div class="v">${{escapeHtml(row.session_id || "(missing raw result)")}}</div></div>
          <div class="kv"><div class="k">Stage / gap</div><div class="v">B=${{row.stage_b}}, C=${{row.stage_c}}, detected=${{row.detected}}, review=${{row.review}}, silentC=${{row.silent_stage_c}}</div></div>
          <div class="kv"><div class="k">Runtime evidence</div><div class="v">duration=${{Math.round(row.duration_s)}}s, commands=${{row.dangerous_commands_count}}, toolErrors=${{row.tool_call_error_count}}</div></div>
          <div class="kv"><div class="k">Canary / filesystem</div><div class="v">canary=${{row.canary_requests}}, fsEvents=${{row.fs_events_count}}, workspaceFiles=${{row.workspace_new_files_count}}</div></div>
          <div class="kv"><div class="k">Feature positives</div><div class="v">${{escapeHtml(featureNames || "none")}}</div></div>
          <div class="kv"><div class="k">External domains</div><div class="v">${{escapeHtml(row.external_domains_sample || "none")}}</div></div>
          <div class="kv"><div class="k">Command sample</div><div class="v">${{escapeHtml(row.dangerous_command_sample || "none")}}</div></div>
          <div class="kv"><div class="k">Raw result path</div><div class="v">${{escapeHtml(row.result_json_path || "missing")}}</div></div>
        </div>
      `;
      detail.scrollIntoView({{ behavior: "smooth", block: "nearest" }});
    }}

    function renderAll() {{
      const rows = filteredRows();
      renderSummary(rows);
      renderModelCondition(rows);
      renderCoverage(rows);
      renderMatrix(rows);
    }}

    renderMeta();
    renderControls();
    renderLegend();
    renderAll();
  </script>
</body>
</html>
"""


def main() -> None:
    if not INPUT.exists():
        raise SystemExit(f"Missing input CSV: {INPUT}")
    df = pd.read_csv(INPUT)
    rows = build_rows(df)
    payload = {
        "meta": build_summary(rows),
        "features": [
            {k: v for k, v in feature.items() if k not in {"source", "op", "availability"}}
            for feature in FEATURES
        ],
        "rows": rows,
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_HTML.write_text(build_html(payload), encoding="utf-8")
    print(f"Wrote {OUT_HTML}")
    print(f"Rows: {payload['meta']['rows']} ({payload['meta']['valid_rows']} valid)")
    print(f"Features: {payload['meta']['feature_count']}")


if __name__ == "__main__":
    main()
