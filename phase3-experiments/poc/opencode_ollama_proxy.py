#!/usr/bin/env python3
"""Log OpenCode OpenAI-compatible requests while forwarding them to Ollama."""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urljoin


def summarize_payload(raw_body: bytes) -> dict:
    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except Exception as exc:
        return {"json_error": repr(exc), "body_bytes": len(raw_body)}

    messages = payload.get("messages") or []
    tools = payload.get("tools") or []
    summary = {
        "model": payload.get("model"),
        "stream": payload.get("stream"),
        "message_count": len(messages),
        "tools_count": len(tools),
        "tool_choice": payload.get("tool_choice"),
        "body_bytes": len(raw_body),
        "message_chars": sum(len(str(m.get("content") or "")) for m in messages if isinstance(m, dict)),
        "tool_names": [],
        "tool_required": {},
        "roles": [m.get("role") for m in messages if isinstance(m, dict)],
    }

    for tool in tools:
        function = tool.get("function", {}) if isinstance(tool, dict) else {}
        name = function.get("name")
        if not name:
            continue
        summary["tool_names"].append(name)
        params = function.get("parameters", {})
        if isinstance(params, dict):
            summary["tool_required"][name] = params.get("required", [])

    return summary


def write_jsonl(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def make_handler(target_base: str, log_path: Path, dump_path: Path | None):
    class ProxyHandler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, fmt: str, *args) -> None:
            sys.stderr.write("%s - %s\n" % (self.log_date_time_string(), fmt % args))

        def do_GET(self) -> None:
            self._forward(b"")

        def do_POST(self) -> None:
            content_length = int(self.headers.get("Content-Length", "0") or "0")
            body = self.rfile.read(content_length) if content_length else b""
            self._forward(body)

        def _forward(self, body: bytes) -> None:
            started = time.time()
            target_url = urljoin(target_base.rstrip("/") + "/", self.path.lstrip("/"))

            if body:
                summary = summarize_payload(body)
                record = {
                    "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "path": self.path,
                    "summary": summary,
                }
                write_jsonl(log_path, record)
                if dump_path:
                    dump_path.parent.mkdir(parents=True, exist_ok=True)
                    dump_path.write_bytes(body)

            headers = {
                key: value
                for key, value in self.headers.items()
                if key.lower() not in {"host", "content-length", "accept-encoding", "connection"}
            }
            request = urllib.request.Request(
                target_url,
                data=body if self.command != "GET" else None,
                headers=headers,
                method=self.command,
            )

            try:
                with urllib.request.urlopen(request, timeout=660) as response:
                    self.send_response(response.status)
                    for key, value in response.headers.items():
                        if key.lower() in {"connection", "transfer-encoding"}:
                            continue
                        self.send_header(key, value)
                    self.end_headers()
                    total = 0
                    while True:
                        chunk = response.read(8192)
                        if not chunk:
                            break
                        total += len(chunk)
                        self.wfile.write(chunk)
                        self.wfile.flush()
                    write_jsonl(log_path, {
                        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                        "path": self.path,
                        "response_status": response.status,
                        "response_bytes": total,
                        "seconds": round(time.time() - started, 3),
                    })
            except urllib.error.HTTPError as exc:
                error_body = exc.read()
                self.send_response(exc.code)
                for key, value in exc.headers.items():
                    if key.lower() in {"connection", "transfer-encoding"}:
                        continue
                    self.send_header(key, value)
                self.send_header("Content-Length", str(len(error_body)))
                self.end_headers()
                self.wfile.write(error_body)
                write_jsonl(log_path, {
                    "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "path": self.path,
                    "response_status": exc.code,
                    "response_bytes": len(error_body),
                    "response_body_prefix": error_body[:300].decode("utf-8", errors="replace"),
                    "seconds": round(time.time() - started, 3),
                })
            except Exception as exc:
                body_text = json.dumps({"error": repr(exc)}).encode("utf-8")
                self.send_response(502)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body_text)))
                self.end_headers()
                self.wfile.write(body_text)
                write_jsonl(log_path, {
                    "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "path": self.path,
                    "proxy_error": repr(exc),
                    "seconds": round(time.time() - started, 3),
                })

    return ProxyHandler


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--listen-host", default="0.0.0.0")
    parser.add_argument("--listen-port", type=int, default=11435)
    parser.add_argument("--target", default="http://127.0.0.1:11434")
    parser.add_argument("--log", default="phase3-experiments/poc/results/opencode_ollama_proxy.jsonl")
    parser.add_argument("--dump-request", default=None)
    args = parser.parse_args()

    handler = make_handler(
        args.target,
        Path(args.log),
        Path(args.dump_request) if args.dump_request else None,
    )
    server = ThreadingHTTPServer((args.listen_host, args.listen_port), handler)
    print(f"Proxy listening on {args.listen_host}:{args.listen_port} -> {args.target}", flush=True)
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
