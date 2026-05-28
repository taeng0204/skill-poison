#!/bin/bash
set -e

# ─────────────────────────────────────────────
# SkillPoison Agent Entrypoint
# ─────────────────────────────────────────────
PROMPT="${TASK_PROMPT:-Say hello}"
TIMEOUT="${AGENT_TIMEOUT:-300}"

echo "=========================================="
echo "SkillPoison Agent Container"
echo "=========================================="
echo "Agent:     Claude Code"
echo "Prompt:    ${PROMPT:0:80}..."
echo "Timeout:   ${TIMEOUT}s"
echo "Workspace: $(ls /workspace/)"
echo "=========================================="

# CLAUDE.md 확인
if [[ -f /workspace/CLAUDE.md ]]; then
    echo "📄 CLAUDE.md detected ($(wc -c < /workspace/CLAUDE.md) bytes)"
fi
if [[ -f /workspace/.env ]]; then
    echo "📄 .env detected ($(wc -c < /workspace/.env) bytes)"
fi

# 파일시스템 모니터링 시작 (백그라운드)
echo ""
echo "📡 Starting filesystem monitor..."
inotifywait -m -r /workspace \
    --format '%T %e %w%f' \
    --timefmt '%H:%M:%S' \
    -e create -e modify -e delete -e moved_to \
    > /results/fs_events.log 2>/dev/null &
FS_MONITOR_PID=$!

# 잠시 대기 (모니터링 안정화)
sleep 1

# Claude Code 실행
echo ""
echo "🤖 Starting Claude Code..."
echo ""

set +e
timeout "${TIMEOUT}" claude \
    --print \
    --dangerously-skip-permissions \
    -p "$PROMPT" \
    > /results/agent_stdout.txt 2>/results/agent_stderr.txt
EXIT_CODE=$?
set -e

echo ""
echo "=========================================="
echo "Agent exited with code: $EXIT_CODE"
echo "=========================================="

# 모니터링 정지
kill $FS_MONITOR_PID 2>/dev/null || true

# 워크스페이스 파일 목록 저장
find /workspace -type f -not -path '*/\.*' | sort > /results/workspace_files.txt 2>/dev/null
# 숨김 파일도 별도 기록
find /workspace -name '.*' -type f | sort > /results/workspace_hidden.txt 2>/dev/null

# crontab 확인
crontab -l > /results/crontab_after.txt 2>/dev/null || echo "no crontab" > /results/crontab_after.txt

echo "📊 Results saved to /results/"
echo "   stdout:     $(wc -c < /results/agent_stdout.txt) bytes"
echo "   stderr:     $(wc -c < /results/agent_stderr.txt) bytes"
echo "   fs_events:  $(wc -l < /results/fs_events.log) events"
echo "   exit_code:  $EXIT_CODE"

exit $EXIT_CODE
