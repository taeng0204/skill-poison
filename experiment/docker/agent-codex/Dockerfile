# SkillPoison — Codex (OpenAI) Agent Container
#
# Runs `codex exec` non-interactively against the injected skill (AGENTS.md).
# Codex natively loads AGENTS.md as project context, so no instruction-injection
# layer is needed (unlike the opencode container). The Docker network + canary
# endpoint are the experiment boundary; codex runs with its sandbox bypassed.
FROM node:22-bookworm-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV NO_COLOR=1
# codex 설정/인증은 런타임에 /home/node/.codex 로 마운트됨
ENV CODEX_HOME=/home/node/.codex

RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    ca-certificates \
    curl \
    git \
    inotify-tools \
    jq \
    procps \
    python3 \
    python3-venv \
    ripgrep \
    && rm -rf /var/lib/apt/lists/*

# Codex CLI (로컬과 동일 계열 버전)
RUN npm install -g @openai/codex

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# root로 실행 — 마운트된 .codex(auth.json 600, host uid 소유)를 읽기 위해.
# 컨테이너 자체가 실험 격리 경계이므로 root 실행은 안전.
ENTRYPOINT ["/entrypoint.sh"]
