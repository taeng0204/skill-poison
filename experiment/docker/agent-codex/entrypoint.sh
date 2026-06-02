#!/bin/bash
set -euo pipefail

PROMPT="${TASK_PROMPT:-Say hello}"
PROMPT_SOURCE="TASK_PROMPT"
[[ -z "${TASK_PROMPT:-}" ]] && PROMPT_SOURCE="default"

TIMEOUT="${AGENT_TIMEOUT:-300}"
CODEX_MODEL="${CODEX_MODEL:-gpt-5.4}"
CODEX_REASONING="${CODEX_REASONING:-medium}"
export CODEX_HOME="${CODEX_HOME:-/home/node/.codex}"

echo "=========================================="
echo "SkillPoison Agent Container"
echo "=========================================="
echo "Agent:     Codex (OpenAI)"
echo "Model:     ${CODEX_MODEL}"
echo "Reasoning: ${CODEX_REASONING}"
echo "CODEX_HOME: ${CODEX_HOME}"
echo "PromptSrc: ${PROMPT_SOURCE}"
echo "Prompt:    ${PROMPT:0:80}..."
echo "Timeout:   ${TIMEOUT}s"
echo "Workspace: $(ls -A /workspace/ 2>/dev/null || echo '(empty)')"
echo "=========================================="

cd /workspace

# Codex는 AGENTS.md를 네이티브로 프로젝트 컨텍스트로 로드 — instruction 주입 불필요.
for f in AGENTS.md CLAUDE.md .env; do
    [[ -f "/workspace/${f}" ]] && echo "📄 ${f} detected ($(wc -c < "/workspace/${f}") bytes)"
done
echo ""

# git 저장소 (codex가 선호; --skip-git-repo-check로도 보강)
if [[ ! -d .git ]]; then
    git init -q 2>/dev/null || true
    git add -A 2>/dev/null || true
    git -c user.email=a@b.c -c user.name=a commit -q -m "initial" --allow-empty 2>/dev/null || true
fi

echo "📡 Starting filesystem monitor (incl. read events)..."
inotifywait -m -r /workspace \
    --format '%T %e %w%f' --timefmt '%H:%M:%S' \
    -e create -e modify -e delete -e moved_to -e access -e open \
    > /results/fs_events.log 2>/dev/null &
FS_MONITOR_PID=$!

echo "📡 Starting process monitor (200ms)..."
(
    declare -A seen
    SELF_PID=$$
    while true; do
        ts=$(date '+%H:%M:%S.%3N')
        for pid_dir in /proc/[0-9]*; do
            pid="${pid_dir#/proc/}"
            [[ "$pid" == "$SELF_PID" ]] && continue
            cmdline=$(tr '\0' ' ' < "$pid_dir/cmdline" 2>/dev/null)
            [[ -z "$cmdline" ]] && continue
            case "$cmdline" in
                *inotifywait*|*"tr "*"cmdline"*|*"sleep 0."*|*"/proc/"*) continue ;;
            esac
            fp="${pid}:${cmdline:0:200}"
            if [[ -z "${seen[$fp]:-}" ]]; then
                seen[$fp]=1
                ppid=$(awk '/^PPid:/ {print $2}' "$pid_dir/status" 2>/dev/null)
                printf '%s pid=%s ppid=%s cmd=%s\n' "$ts" "$pid" "${ppid:-?}" "$cmdline" >> /results/process_log.txt
            fi
        done
        sleep 0.2
    done
) &
PROC_MONITOR_PID=$!

sleep 1

echo ""
echo "🤖 Starting Codex..."
echo ""

# reasoning effort 매핑 (codex 설정 오버라이드)
REASONING_ARGS=()
if [[ -n "${CODEX_REASONING}" ]]; then
    REASONING_ARGS+=(-c "model_reasoning_effort=\"${CODEX_REASONING}\"")
fi

set +e
timeout "${TIMEOUT}" codex exec \
    --dangerously-bypass-approvals-and-sandbox \
    --skip-git-repo-check \
    -m "${CODEX_MODEL}" \
    -C /workspace \
    "${REASONING_ARGS[@]}" \
    "${PROMPT}" \
    > /results/agent_stdout.txt 2>/results/agent_stderr.txt
EXIT_CODE=$?
set -e

echo ""
echo "=========================================="
echo "Agent exited with code: ${EXIT_CODE}"
echo "=========================================="

kill "${FS_MONITOR_PID}" 2>/dev/null || true
kill "${PROC_MONITOR_PID}" 2>/dev/null || true

find /workspace -type f -not -path '*/.git/*' | sort > /results/workspace_files.txt 2>/dev/null
find /workspace -name '.*' -type f -not -path '*/.git/*' | sort > /results/workspace_hidden.txt 2>/dev/null

# codex 세션 로그(있으면) 일부 보존
if [[ -d "${CODEX_HOME}/sessions" ]]; then
    mkdir -p /results/codex-sessions 2>/dev/null || true
    cp -a "${CODEX_HOME}/sessions/." /results/codex-sessions/ 2>/dev/null || true
fi

echo "📊 Results saved to /results/"
echo "   stdout:     $(wc -c < /results/agent_stdout.txt 2>/dev/null || echo 0) bytes"
echo "   stderr:     $(wc -c < /results/agent_stderr.txt 2>/dev/null || echo 0) bytes"
echo "   fs_events:  $(wc -l < /results/fs_events.log 2>/dev/null || echo 0) events"
echo "   exit_code:  ${EXIT_CODE}"

exit "${EXIT_CODE}"
