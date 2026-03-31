#!/bin/bash
set -e

PROMPT="${TASK_PROMPT:-Say hello}"
TIMEOUT="${AGENT_TIMEOUT:-300}"
MODEL="${AIDER_MODEL:-gpt-4o}"

echo "=========================================="
echo "SkillPoison Agent Container"
echo "=========================================="
echo "Agent:     Aider"
echo "Model:     ${MODEL}"
echo "Prompt:    ${PROMPT:0:80}..."
echo "Timeout:   ${TIMEOUT}s"
echo "Workspace: $(ls /workspace/ 2>/dev/null || echo '(empty)')"
echo "=========================================="

# workspace에 AGENTS.md 있으면 출력
if [[ -f /workspace/AGENTS.md ]]; then
    echo "📄 AGENTS.md detected ($(wc -c < /workspace/AGENTS.md) bytes)"
fi
if [[ -f /workspace/.env ]]; then
    echo "📄 .env detected ($(wc -c < /workspace/.env) bytes)"
fi
echo ""

# git init (Aider 요구사항)
cd /workspace
if [[ ! -d .git ]]; then
    git init -q
    git add -A 2>/dev/null || true
    git commit -q -m "initial" --allow-empty 2>/dev/null || true
fi

# crontab before (변경 감지용)
crontab -l > /results/crontab_before.txt 2>/dev/null || echo "no crontab" > /results/crontab_before.txt

# 파일시스템 모니터링 시작
echo "📡 Starting filesystem monitor..."
inotifywait -m -r /workspace \
    --format '%T %e %w%f' \
    --timefmt '%H:%M:%S' \
    -e create -e modify -e delete -e moved_to \
    > /results/fs_events.log 2>/dev/null &
FS_MONITOR_PID=$!

# 홈디렉토리 변경 모니터링 (crontab, ~/.bashrc 등)
inotifywait -m -r /home/agent \
    --format '%T %e %w%f' \
    --timefmt '%H:%M:%S' \
    -e create -e modify -e delete -e moved_to \
    > /results/fs_home_events.log 2>/dev/null &
HOME_MONITOR_PID=$!

sleep 1

echo ""
echo "🤖 Starting Aider..."
echo ""

# Aider 실행:
#   --yes-always   : 모든 확인에 자동 동의 (shell 명령 포함)
#   --no-git       : git commit 비활성화 (결과 오염 방지)
#   --no-auto-commits : 자동 commit 방지
#   --read         : AGENTS.md를 read-only context로 주입
#   --message      : 비대화형 단일 메시지 실행
set +e
timeout "${TIMEOUT}" aider \
    --model "${MODEL}" \
    --yes-always \
    --no-git \
    --no-auto-commits \
    --no-stream \
    --no-pretty \
    --read /workspace/AGENTS.md \
    --message "${PROMPT}" \
    > /results/agent_stdout.txt 2>/results/agent_stderr.txt
EXIT_CODE=$?
set -e

echo ""
echo "=========================================="
echo "Agent exited with code: $EXIT_CODE"
echo "=========================================="

# 모니터링 정지
kill $FS_MONITOR_PID 2>/dev/null || true
kill $HOME_MONITOR_PID 2>/dev/null || true

# crontab after (변경 여부 확인)
crontab -l > /results/crontab_after.txt 2>/dev/null || echo "no crontab" > /results/crontab_after.txt

# 워크스페이스 파일 목록
find /workspace -type f -not -path '*/.git/*' | sort > /results/workspace_files.txt 2>/dev/null
find /workspace -name '.*' -type f -not -path '*/.git/*' | sort > /results/workspace_hidden.txt 2>/dev/null

# 홈 디렉토리 변경 파일 목록
find /home/agent -name '.*' -type f -not -path '*/.git/*' 2>/dev/null | sort > /results/home_files.txt 2>/dev/null

echo "📊 Results saved to /results/"
echo "   stdout:     $(wc -c < /results/agent_stdout.txt 2>/dev/null || echo 0) bytes"
echo "   stderr:     $(wc -c < /results/agent_stderr.txt 2>/dev/null || echo 0) bytes"
echo "   fs_events:  $(wc -l < /results/fs_events.log 2>/dev/null || echo 0) events"
echo "   home_events:$(wc -l < /results/fs_home_events.log 2>/dev/null || echo 0) events"
echo "   exit_code:  $EXIT_CODE"

exit $EXIT_CODE
