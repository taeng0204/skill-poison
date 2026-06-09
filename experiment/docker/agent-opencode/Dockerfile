# SkillPoison — OpenCode + Ollama Agent Container
#
# Runs opencode in non-interactive mode against an Ollama-compatible local
# provider. The container is intentionally allowed to execute tools; the Docker
# network and canary endpoint are the experiment boundary.
FROM node:22-bookworm-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV OPENCODE_DISABLE_AUTOUPDATE=true
ENV NO_COLOR=1

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

# opencode-ai 1.15.11에 핀 — 1.15.13은 ollama/qwen tool-call을 텍스트로 받아
# 실행하지 못하는 회귀가 있음(맥 빌드에서 확인). 1.15.11은 원격/팀 환경의 작동 버전.
RUN npm install -g opencode-ai@1.15.11 @ai-sdk/openai-compatible

RUN useradd -m -s /bin/bash agent && \
    mkdir -p /workspace /results /logs /home/agent/.config/opencode && \
    chown -R agent:agent /workspace /results /logs /home/agent

RUN git config --global user.email "agent@skillpoison" && \
    git config --global user.name "SkillPoison Agent" && \
    git config --global init.defaultBranch main

COPY --chmod=755 entrypoint.sh /entrypoint.sh

WORKDIR /workspace
USER agent

ENTRYPOINT ["/entrypoint.sh"]
