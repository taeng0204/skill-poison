#!/bin/bash
set -e

PROMPT="${TASK_PROMPT:-Say hello}"
TIMEOUT="${AGENT_TIMEOUT:-300}"
MODEL="${AIDER_MODEL:-gpt-4o}"
# AIDER_MODE:
#   message    (기존) — --message 단일 호출, shell 실행 차단됨
#   multiturn  (B-2) — stdin pipe로 y/y 주입, shell 확인 통과
#   test_hook  (B-3) — --test-cmd "bash /workspace/test_runner.sh" 자동 실행
AIDER_MODE="${AIDER_MODE:-message}"

echo "=========================================="
echo "SkillPoison Agent Container"
echo "=========================================="
echo "Agent:     Aider"
echo "Model:     ${MODEL}"
echo "Mode:      ${AIDER_MODE}"
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
echo "🤖 Starting Aider (mode: ${AIDER_MODE})..."
echo ""

set +e

if [[ "${AIDER_MODE}" == "multiturn" ]]; then
    # ────────────────────────────────────────────
    # B-2: Multi-turn stdin pipe
    #   - interactive 모드로 Aider 실행
    #   - stdin에 태스크 메시지 + "y" 응답 주입
    #   - shell 확인 프롬프트를 y로 통과시킴
    #   - /run 명령도 주입 가능
    # ────────────────────────────────────────────
    echo "[B-2 multiturn] stdin pipe 모드로 실행"
    # 입력 시퀀스:
    #   1) 태스크 메시지
    #   2) "y" × 10 — shell 확인 프롬프트 대응
    #   3) /exit — 명시적 종료
    STDIN_INPUTS="${PROMPT}
y
y
y
y
y
y
y
y
y
y
/exit
"
    timeout "${TIMEOUT}" aider \
        --model "${MODEL}" \
        --yes-always \
        --no-git \
        --no-auto-commits \
        --no-stream \
        --no-pretty \
        --read /workspace/AGENTS.md \
        < <(echo "${STDIN_INPUTS}") \
        > /results/agent_stdout.txt 2>/results/agent_stderr.txt
    EXIT_CODE=$?

elif [[ "${AIDER_MODE}" == "test_hook" ]]; then
    # ────────────────────────────────────────────
    # B-3: --test-cmd hook
    #   - 코드 생성 후 test_runner.sh 자동 실행
    #   - AGENTS.md가 test_runner.sh를 오염된 내용으로 생성하도록 유도
    #   - shell 확인 없이 자동 실행됨
    # ────────────────────────────────────────────
    echo "[B-3 test_hook] test-cmd hook 모드로 실행"

    # 초기 빈 test_runner.sh 생성 (AGENTS.md가 덮어쓸 것)
    echo "#!/bin/bash" > /workspace/test_runner.sh
    echo "echo 'tests passed'" >> /workspace/test_runner.sh
    chmod +x /workspace/test_runner.sh

    timeout "${TIMEOUT}" aider \
        --model "${MODEL}" \
        --yes-always \
        --no-git \
        --no-auto-commits \
        --no-stream \
        --no-pretty \
        --read /workspace/AGENTS.md \
        --test-cmd "bash /workspace/test_runner.sh" \
        --auto-test \
        --message "${PROMPT}" \
        > /results/agent_stdout.txt 2>/results/agent_stderr.txt
    EXIT_CODE=$?

else
    # ────────────────────────────────────────────
    # 기존: --message 단일 호출
    #   shell 명령 차단됨 (explicit_yes_required=True)
    # ────────────────────────────────────────────
    echo "[message] 단일 메시지 모드로 실행"
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
fi

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

# test_runner.sh 내용 저장 (B-3 분석용)
if [[ -f /workspace/test_runner.sh ]]; then
    cp /workspace/test_runner.sh /results/test_runner_final.sh
fi

echo "📊 Results saved to /results/"
echo "   stdout:     $(wc -c < /results/agent_stdout.txt 2>/dev/null || echo 0) bytes"
echo "   stderr:     $(wc -c < /results/agent_stderr.txt 2>/dev/null || echo 0) bytes"
echo "   fs_events:  $(wc -l < /results/fs_events.log 2>/dev/null || echo 0) events"
echo "   home_events:$(wc -l < /results/fs_home_events.log 2>/dev/null || echo 0) events"
echo "   exit_code:  $EXIT_CODE"

exit $EXIT_CODE
