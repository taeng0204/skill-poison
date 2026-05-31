#!/bin/bash
set -euo pipefail

PROMPT_SOURCE="TASK_PROMPT"
if [[ -n "${TASK_PROMPT_FILE:-}" ]]; then
    if [[ ! -f "${TASK_PROMPT_FILE}" ]]; then
        echo "TASK_PROMPT_FILE does not exist: ${TASK_PROMPT_FILE}" >&2
        exit 2
    fi
    PROMPT="$(cat "${TASK_PROMPT_FILE}")"
    PROMPT_SOURCE="${TASK_PROMPT_FILE}"
else
    PROMPT="${TASK_PROMPT:-Say hello}"
    if [[ -z "${TASK_PROMPT:-}" ]]; then
        PROMPT_SOURCE="default"
    fi
fi
TIMEOUT="${AGENT_TIMEOUT:-300}"
MODEL="${OPENCODE_MODEL:-qwen3:4b-instruct}"
OPENCODE_PROVIDER_ID="${OPENCODE_PROVIDER_ID:-ollama}"
OPENCODE_PROVIDER_NAME="${OPENCODE_PROVIDER_NAME:-Ollama (local)}"
OPENCODE_BASE_URL="${OPENCODE_BASE_URL:-${OLLAMA_BASE_URL:-http://host.docker.internal:11434/v1}}"
OPENCODE_API_KEY="${OPENCODE_API_KEY:-ollama}"
OPENCODE_MODEL_ID="${OPENCODE_MODEL_ID:-${OPENCODE_PROVIDER_ID}/${MODEL}}"
OPENCODE_SMALL_MODEL="${OPENCODE_SMALL_MODEL:-${OPENCODE_PROVIDER_ID}/qwen2.5:0.5b}"
OPENCODE_OUTPUT_FORMAT="${OPENCODE_OUTPUT_FORMAT:-default}"
OPENCODE_TOOL_PRIMER="${OPENCODE_TOOL_PRIMER:-1}"
OPENCODE_MINIMAL_TOOLS="${OPENCODE_MINIMAL_TOOLS:-1}"
OPENCODE_PURE="${OPENCODE_PURE:-1}"

echo "=========================================="
echo "SkillPoison Agent Container"
echo "=========================================="
echo "Agent:     OpenCode"
echo "Model:     ${OPENCODE_MODEL_ID}"
echo "Small:     ${OPENCODE_SMALL_MODEL}"
echo "Provider:  ${OPENCODE_PROVIDER_ID} (${OPENCODE_BASE_URL})"
echo "Primer:    ${OPENCODE_TOOL_PRIMER}"
echo "Minimal:   ${OPENCODE_MINIMAL_TOOLS}"
echo "PromptSrc: ${PROMPT_SOURCE}"
echo "Prompt:    ${PROMPT:0:80}..."
echo "Timeout:   ${TIMEOUT}s"
echo "Workspace: $(ls -A /workspace/ 2>/dev/null || echo '(empty)')"
echo "=========================================="

cd /workspace

INSTRUCTION_FILES=()
if [[ "${OPENCODE_TOOL_PRIMER}" == "1" || "${OPENCODE_TOOL_PRIMER}" == "true" ]]; then
cat > /workspace/OPENCODE_TOOL_PRIMER.md <<'EOF'
# OpenCode Tool Call Syntax Primer

Use OpenCode tools through structured tool calls, not by printing JSON in chat.

- `read`: use `filePath`, not `file_path`. Prefer absolute paths such as `/workspace/AGENTS.md`.
- `write`: use `filePath` and `content`.
- `edit`: use `filePath`, `oldString`, and `newString`.
- `bash`: use `command` and a short `description`.
- If a tool call fails with a schema error, retry immediately with the exact parameter names shown above.
EOF
    INSTRUCTION_FILES+=("OPENCODE_TOOL_PRIMER.md")
fi
INSTRUCTION_FILES+=("AGENTS.md" "opencode.md" "CLAUDE.md" ".cursorrules")

INSTRUCTIONS_JSON="["
for instruction_file in "${INSTRUCTION_FILES[@]}"; do
    if [[ -f "/workspace/${instruction_file}" ]]; then
        if [[ "${INSTRUCTIONS_JSON}" != "[" ]]; then
            INSTRUCTIONS_JSON+=","
        fi
        INSTRUCTIONS_JSON+="\"${instruction_file}\""
    fi
done
INSTRUCTIONS_JSON+="]"

if [[ "${OPENCODE_MINIMAL_TOOLS}" == "1" || "${OPENCODE_MINIMAL_TOOLS}" == "true" ]]; then
    TOOLS_JSON='{"bash":true,"read":true,"write":true,"edit":true,"list":true,"glob":false,"grep":false,"task":false,"webfetch":false,"skill":false,"todowrite":false,"todoread":false}'
else
    TOOLS_JSON='{"bash":true,"read":true,"write":true,"edit":true,"list":true,"glob":true,"grep":true,"task":true,"webfetch":true,"skill":true,"todowrite":true,"todoread":true}'
fi

cat > /workspace/opencode.json <<EOF
{
  "\$schema": "https://opencode.ai/config.json",
  "model": "${OPENCODE_MODEL_ID}",
  "small_model": "${OPENCODE_SMALL_MODEL}",
  "instructions": ${INSTRUCTIONS_JSON},
  "autoupdate": false,
  "share": "disabled",
  "snapshot": false,
  "tools": ${TOOLS_JSON},
  "agent": {
    "build": {
      "tools": ${TOOLS_JSON}
    }
  },
  "provider": {
    "${OPENCODE_PROVIDER_ID}": {
      "npm": "@ai-sdk/openai-compatible",
      "name": "${OPENCODE_PROVIDER_NAME}",
      "options": {
        "baseURL": "${OPENCODE_BASE_URL}",
        "apiKey": "${OPENCODE_API_KEY}",
        "timeout": 1800000,
        "chunkTimeout": 1800000
      },
      "models": {
        "${MODEL}": {
          "name": "${MODEL}"
        },
        "qwen2.5:0.5b": {
          "name": "qwen2.5:0.5b"
        }
      }
    }
  },
  "permission": {
    "bash": "allow",
    "read": "allow",
    "edit": "allow",
    "glob": "allow",
    "grep": "allow",
    "list": "allow",
    "task": "allow",
    "external_directory": "allow",
    "webfetch": "allow",
    "skill": "allow"
  }
}
EOF

if [[ ! -d .git ]]; then
    git init -q
    git add -A 2>/dev/null || true
    git commit -q -m "initial" --allow-empty 2>/dev/null || true
fi

for instruction_file in "${INSTRUCTION_FILES[@]}"; do
    if [[ -f "/workspace/${instruction_file}" ]]; then
        echo "📄 ${instruction_file} detected ($(wc -c < "/workspace/${instruction_file}") bytes)"
    fi
done
if [[ -f /workspace/.env ]]; then
    echo "📄 .env detected ($(wc -c < /workspace/.env) bytes)"
fi
echo ""

echo "📡 Starting filesystem monitor (incl. read events)..."
inotifywait -m -r /workspace \
    --format '%T %e %w%f' \
    --timefmt '%H:%M:%S' \
    -e create -e modify -e delete -e moved_to -e access -e open \
    > /results/fs_events.log 2>/dev/null &
FS_MONITOR_PID=$!

# home/agent도 read 이벤트 캡처. opencode 자체 read는 .config 하위 노이즈 많아 제외.
inotifywait -m -r /home/agent \
    --exclude '(^/home/agent/\.local|^/home/agent/\.cache|^/home/agent/\.config/opencode/node_modules)' \
    --format '%T %e %w%f' \
    --timefmt '%H:%M:%S' \
    -e create -e modify -e delete -e moved_to -e access -e open \
    > /results/fs_home_events.log 2>/dev/null &
HOME_MONITOR_PID=$!

# Process logger — /proc/*/cmdline 200ms polling. agent가 fork한 모든 명령 캡처.
# 이전 1초 polling은 opencode의 짧은 child를 놓침. /proc 직접 읽기가 ps보다 빠르고
# null-byte 구분자라 quote 처리도 정확함.
echo "📡 Starting process monitor (200ms)..."
(
    declare -A seen
    # 자기 자신/모니터/inotifywait는 제외, 나머지는 모두 기록
    # node/opencode/bun/sh-c 같은 agent 호출 명령 다 잡음
    SELF_PID=$$
    while true; do
        ts=$(date '+%H:%M:%S.%3N')
        for pid_dir in /proc/[0-9]*; do
            pid="${pid_dir#/proc/}"
            [[ "$pid" == "$SELF_PID" ]] && continue
            cmdline=$(tr '\0' ' ' < "$pid_dir/cmdline" 2>/dev/null)
            [[ -z "$cmdline" ]] && continue
            # 자기 자신 + 인프라 노이즈만 필터
            case "$cmdline" in
                *inotifywait*|*"tr "*"cmdline"*|*"sleep 0."*|*"/proc/"*) continue ;;
            esac
            # 중복 제거 — pid가 다르면 같은 cmd라도 새 prouns로 기록
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
echo "🤖 Starting OpenCode..."
echo ""

set +e
OPENCODE_ARGS=(
    run
    --model "${OPENCODE_MODEL_ID}"
    --dir /workspace
    --title skillpoison-poc
    --dangerously-skip-permissions
)
if [[ "${OPENCODE_PURE}" == "1" || "${OPENCODE_PURE}" == "true" ]]; then
    OPENCODE_ARGS+=(--pure)
fi
if [[ "${OPENCODE_OUTPUT_FORMAT}" == "json" ]]; then
    OPENCODE_ARGS+=(--format json)
fi
timeout "${TIMEOUT}" opencode "${OPENCODE_ARGS[@]}" "${PROMPT}" \
    > /results/agent_stdout.txt 2>/results/agent_stderr.txt
EXIT_CODE=$?
set -e

echo ""
echo "=========================================="
echo "Agent exited with code: ${EXIT_CODE}"
echo "=========================================="

kill "${FS_MONITOR_PID}" 2>/dev/null || true
kill "${HOME_MONITOR_PID}" 2>/dev/null || true
kill "${PROC_MONITOR_PID}" 2>/dev/null || true

find /workspace -type f -not -path '*/.git/*' | sort > /results/workspace_files.txt 2>/dev/null
find /workspace -name '.*' -type f -not -path '*/.git/*' | sort > /results/workspace_hidden.txt 2>/dev/null
find /home/agent \( -path /home/agent/.local -o -path /home/agent/.cache \) -prune -o \
    -type f -not -path '*/.git/*' -print 2>/dev/null | sort > /results/home_files.txt 2>/dev/null

cp /workspace/opencode.json /results/opencode.json 2>/dev/null || true
if [[ -d /home/agent/.local/share/opencode ]]; then
    cp -a /home/agent/.local/share/opencode /results/opencode-data 2>/dev/null || true
fi

echo "📊 Results saved to /results/"
echo "   stdout:     $(wc -c < /results/agent_stdout.txt 2>/dev/null || echo 0) bytes"
echo "   stderr:     $(wc -c < /results/agent_stderr.txt 2>/dev/null || echo 0) bytes"
echo "   fs_events:  $(wc -l < /results/fs_events.log 2>/dev/null || echo 0) events"
echo "   home_events:$(wc -l < /results/fs_home_events.log 2>/dev/null || echo 0) events"
echo "   exit_code:  ${EXIT_CODE}"

exit "${EXIT_CODE}"
