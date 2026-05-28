# SkillPoison — Canary Server
# 악성 exfil 시도를 캡처하는 경량 HTTP 서버
FROM python:3.11-slim

WORKDIR /app
COPY server.py .

EXPOSE 18080

CMD ["python3", "server.py", "--port", "18080", "--log-dir", "/logs"]
