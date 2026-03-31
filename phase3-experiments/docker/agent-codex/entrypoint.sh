#!/bin/bash
set -e

PROMPT="${TASK_PROMPT:-Say hello}"
TIMEOUT="${AGENT_TIMEOUT:-300}"
MODEL="${CODEX_MODEL:-gpt-5.4}"
REASONING="${CODEX_REASONING:-medium}"
# SANDBOX_MODE: "full" | "workspace-write" | "none"
# "none" = --dangerously-bypass-approvals-and-sandbox
SANDBOX_MODE="${CODEX_SANDBOX:-full}"

echo "=========================================="
echo "SkillPoison Agent Container"
echo "=========================================="
echo "Agent:     Codex CLI"
echo "Model:     ${MODEL} (reasoning=${REASONING})"
echo "Sandbox:   ${SANDBOX_MODE}"
echo "Prompt:    ${PROMPT:0:80}..."
echo "Timeout:   ${TIMEOUT}s"
echo "Workspace: $(ls /workspace/)"
echo "=========================================="

if [[ -f /workspace/AGENTS.md ]]; then
    echo "📄 AGENTS.md detected ($(wc -c < /workspace/AGENTS.md) bytes)"
fi
if [[ -f /workspace/.env ]]; then
    echo "📄 .env detected ($(wc -c < /workspace/.env) bytes)"
fi

echo ""
echo "📡 Starting filesystem monitor..."
inotifywait -m -r /workspace \
    --format '%T %e %w%f' \
    --timefmt '%H:%M:%S' \
    -e create -e modify -e delete -e moved_to \
    > /results/fs_events.log 2>/dev/null &
FS_MONITOR_PID=$!

sleep 1

echo ""
echo "🤖 Starting Codex CLI..."
echo ""

set +e
if [[ "${SANDBOX_MODE}" == "none" ]]; then
    # 샌드박스 완전 해제 — 컨테이너 자체가 격리 경계
    timeout "${TIMEOUT}" codex exec \
        --skip-git-repo-check \
        --dangerously-bypass-approvals-and-sandbox \
        -c "model=\"${MODEL}\"" \
        -c "model_reasoning_effort=\"${REASONING}\"" \
        "$PROMPT" \
        > /results/agent_stdout.txt 2>/results/agent_stderr.txt
elif [[ "${SANDBOX_MODE}" == "workspace-write" ]]; then
    # 워크스페이스 쓰기 허용, 네트워크 제한
    timeout "${TIMEOUT}" codex exec \
        --skip-git-repo-check \
        --yolo \
        -c "model=\"${MODEL}\"" \
        -c "model_reasoning_effort=\"${REASONING}\"" \
        -c 'sandbox_permissions=["disk-full-read-access"]' \
        "$PROMPT" \
        > /results/agent_stdout.txt 2>/results/agent_stderr.txt
else
    # 기본: full sandbox (seatbelt/bubblewrap + 네트워크 제한)
    timeout "${TIMEOUT}" codex exec \
        --skip-git-repo-check \
        --yolo \
        -c "model=\"${MODEL}\"" \
        -c "model_reasoning_effort=\"${REASONING}\"" \
        "$PROMPT" \
        > /results/agent_stdout.txt 2>/results/agent_stderr.txt
fi
EXIT_CODE=$?
set -e

echo ""
echo "=========================================="
echo "Agent exited with code: $EXIT_CODE"
echo "=========================================="

kill $FS_MONITOR_PID 2>/dev/null || true

find /workspace -type f -not -path '*/\.*' | sort > /results/workspace_files.txt 2>/dev/null
find /workspace -name '.*' -type f | sort > /results/workspace_hidden.txt 2>/dev/null
crontab -l > /results/crontab_after.txt 2>/dev/null || echo "no crontab" > /results/crontab_after.txt

echo "📊 Results saved to /results/"
echo "   stdout:     $(wc -c < /results/agent_stdout.txt) bytes"
echo "   stderr:     $(wc -c < /results/agent_stderr.txt) bytes"
echo "   fs_events:  $(wc -l < /results/fs_events.log) events"
echo "   exit_code:  $EXIT_CODE"

exit $EXIT_CODE
