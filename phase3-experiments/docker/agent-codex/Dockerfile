# SkillPoison — Codex CLI Agent Container
FROM node:22-slim

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip python3-venv \
    curl \
    inotify-tools \
    procps \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN npm install -g @openai/codex

# node 기본 유저(uid=1000) 사용 — 호스트 ~/.codex 읽기 쉽게 유지
RUN mkdir -p /home/node/.codex && chown -R node:node /home/node
RUN mkdir -p /workspace /results /logs && chown -R node:node /workspace /results /logs

COPY --chmod=755 entrypoint.sh /entrypoint.sh

WORKDIR /workspace
USER node

ENTRYPOINT ["/entrypoint.sh"]
