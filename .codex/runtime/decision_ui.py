#!/usr/bin/env python3
"""Local browser sidecar for HarnessDesign structured decisions."""

from __future__ import annotations

import json
import subprocess
import sys
import threading
import time
import uuid
from dataclasses import dataclass, field
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import parse_qs, urlparse

from common import json_dump, runtime_path, save_json_atomic


HTML_TEMPLATE = """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>HarnessDesign Decision</title>
  <style>
    :root {
      --bg: #f7f3eb;
      --fg: #1d1a16;
      --muted: #6e6356;
      --panel: #fffdf8;
      --line: #d8c9b6;
      --accent: #174b63;
      --accent-2: #d96b3b;
      --success: #236d4e;
      --shadow: 0 20px 60px rgba(29, 26, 22, 0.12);
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: "SF Pro Display", "PingFang SC", "Hiragino Sans GB", sans-serif;
      background:
        radial-gradient(circle at top right, rgba(217, 107, 59, 0.16), transparent 34%),
        radial-gradient(circle at bottom left, rgba(23, 75, 99, 0.18), transparent 28%),
        var(--bg);
      color: var(--fg);
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 24px;
    }
    .shell {
      width: min(760px, 100%);
      background: rgba(255, 253, 248, 0.92);
      border: 1px solid rgba(216, 201, 182, 0.9);
      border-radius: 28px;
      box-shadow: var(--shadow);
      backdrop-filter: blur(14px);
      overflow: hidden;
    }
    .hero {
      padding: 24px 28px 10px;
      background:
        linear-gradient(135deg, rgba(23, 75, 99, 0.08), transparent 56%),
        linear-gradient(180deg, rgba(217, 107, 59, 0.1), transparent 100%);
      border-bottom: 1px solid rgba(216, 201, 182, 0.7);
    }
    .eyebrow {
      font-size: 12px;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      color: var(--accent);
      margin-bottom: 10px;
    }
    .title {
      font-size: clamp(24px, 4vw, 34px);
      margin: 0 0 8px;
      line-height: 1.1;
    }
    .subtitle {
      margin: 0;
      color: var(--muted);
      line-height: 1.5;
      font-size: 15px;
    }
    .content {
      padding: 24px 28px 28px;
      display: grid;
      gap: 18px;
    }
    .option {
      display: grid;
      gap: 10px;
      padding: 18px;
      border: 1px solid var(--line);
      background: var(--panel);
      border-radius: 20px;
      transition: transform 120ms ease, border-color 120ms ease, box-shadow 120ms ease;
    }
    .option:hover {
      transform: translateY(-1px);
      border-color: rgba(23, 75, 99, 0.45);
      box-shadow: 0 14px 30px rgba(23, 75, 99, 0.08);
    }
    .option-head {
      display: flex;
      gap: 14px;
      align-items: flex-start;
    }
    .option input {
      margin-top: 4px;
      accent-color: var(--accent);
    }
    .option strong {
      display: block;
      font-size: 16px;
      margin-bottom: 4px;
    }
    .option p {
      margin: 0;
      color: var(--muted);
      line-height: 1.5;
      font-size: 14px;
    }
    textarea {
      width: 100%;
      min-height: 118px;
      resize: vertical;
      border-radius: 18px;
      border: 1px solid var(--line);
      padding: 14px 16px;
      font: inherit;
      background: rgba(255, 255, 255, 0.72);
      color: var(--fg);
    }
    .meta {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      color: var(--muted);
      font-size: 13px;
    }
    .badge {
      border: 1px solid rgba(23, 75, 99, 0.18);
      padding: 6px 10px;
      border-radius: 999px;
      background: rgba(23, 75, 99, 0.06);
    }
    .actions {
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
    }
    button {
      border: none;
      background: linear-gradient(135deg, var(--accent), #225b76);
      color: white;
      padding: 14px 18px;
      border-radius: 999px;
      cursor: pointer;
      font: inherit;
      font-weight: 600;
      min-width: 180px;
      box-shadow: 0 16px 28px rgba(23, 75, 99, 0.2);
    }
    button:disabled {
      cursor: wait;
      opacity: 0.7;
      box-shadow: none;
    }
    .status {
      min-height: 24px;
      font-size: 14px;
      color: var(--muted);
    }
    .status.ok {
      color: var(--success);
    }
    .status.error {
      color: var(--accent-2);
    }
  </style>
</head>
<body>
  <main class="shell">
    <section class="hero">
      <div class="eyebrow">HarnessDesign Decision</div>
      <h1 class="title" id="header">加载中</h1>
      <p class="subtitle" id="question">正在同步当前决策点。</p>
    </section>
    <section class="content">
      <div class="meta">
        <span class="badge" id="decision-id">ID</span>
        <span class="badge" id="followup-mode">Follow-up</span>
      </div>
      <form id="decision-form">
        <div id="options"></div>
        <div>
          <textarea id="free-text" placeholder="可选补充：修改说明、原因、额外约束、Other 内容。"></textarea>
        </div>
        <div class="actions">
          <button type="submit" id="submit">提交决策</button>
          <div class="status" id="status"></div>
        </div>
      </form>
    </section>
  </main>
  <script>
    const params = new URLSearchParams(window.location.search);
    const decisionId = params.get("decision_id");
    const statusEl = document.getElementById("status");
    const formEl = document.getElementById("decision-form");
    const optionsEl = document.getElementById("options");
    const freeTextEl = document.getElementById("free-text");
    const submitEl = document.getElementById("submit");
    let spec = null;

    function setStatus(message, cls = "") {
      statusEl.className = `status ${cls}`.trim();
      statusEl.textContent = message;
    }

    function renderOption(option) {
      const wrapper = document.createElement("label");
      wrapper.className = "option";
      const inputType = spec.multiSelect ? "checkbox" : "radio";
      wrapper.innerHTML = `
        <div class="option-head">
          <input type="${inputType}" name="selected" value="${option.id}">
          <div>
            <strong>${option.label}</strong>
            <p>${option.description || ""}</p>
          </div>
        </div>
      `;
      return wrapper;
    }

    function selectedValues() {
      return Array.from(document.querySelectorAll("input[name='selected']:checked")).map((node) => node.value);
    }

    async function loadSpec() {
      const res = await fetch(`/api/pending?decision_id=${encodeURIComponent(decisionId)}`);
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }
      spec = await res.json();
      document.getElementById("header").textContent = spec.header || "决策选择";
      document.getElementById("question").textContent = spec.question;
      document.getElementById("decision-id").textContent = spec.decision_id;
      document.getElementById("followup-mode").textContent = spec.followup_policy || "none";
      optionsEl.innerHTML = "";
      spec.options.forEach((option) => optionsEl.appendChild(renderOption(option)));
      if (!spec.allow_other) {
        freeTextEl.placeholder = "如有补充说明，可填写在这里。";
      }
    }

    formEl.addEventListener("submit", async (event) => {
      event.preventDefault();
      submitEl.disabled = true;
      setStatus("正在提交…");
      const selected = selectedValues();
      const payload = {
        decision_id: decisionId,
        selected_option: spec.multiSelect ? selected : (selected[0] || null),
        free_text: freeTextEl.value.trim()
      };
      try {
        const res = await fetch("/api/submit", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        if (!res.ok) {
          throw new Error(`HTTP ${res.status}`);
        }
        const body = await res.json();
        setStatus("已提交，Codex 会继续执行。", "ok");
        submitEl.textContent = "已提交";
        submitEl.disabled = true;
        formEl.querySelectorAll("input, textarea").forEach((node) => node.disabled = true);
        console.log(body);
      } catch (error) {
        setStatus(`提交失败：${error.message}`, "error");
        submitEl.disabled = false;
      }
    });

    loadSpec().catch((error) => {
      setStatus(`加载失败：${error.message}`, "error");
      submitEl.disabled = true;
    });
  </script>
</body>
</html>
"""


@dataclass
class PendingDecision:
    decision_id: str
    spec: dict[str, Any]
    created_at: float = field(default_factory=time.time)
    event: threading.Event = field(default_factory=threading.Event)
    result: dict[str, Any] | None = None

    def public_spec(self) -> dict[str, Any]:
        payload = dict(self.spec)
        payload.setdefault("decision_id", self.decision_id)
        return payload


class DecisionManager:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._pending: dict[str, PendingDecision] = {}
        self._httpd: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None
        self._base_url: str | None = None

    @property
    def base_url(self) -> str:
        self.ensure_server()
        assert self._base_url is not None
        return self._base_url

    def ensure_server(self) -> None:
        with self._lock:
            if self._httpd is not None:
                return

            manager = self

            class Handler(BaseHTTPRequestHandler):
                def _json(self, status: int, payload: dict[str, Any]) -> None:
                    raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
                    self.send_response(status)
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    self.send_header("Content-Length", str(len(raw)))
                    self.end_headers()
                    self.wfile.write(raw)

                def do_GET(self) -> None:  # noqa: N802
                    parsed = urlparse(self.path)
                    if parsed.path == "/":
                        raw = HTML_TEMPLATE.encode("utf-8")
                        self.send_response(HTTPStatus.OK)
                        self.send_header("Content-Type", "text/html; charset=utf-8")
                        self.send_header("Content-Length", str(len(raw)))
                        self.end_headers()
                        self.wfile.write(raw)
                        return
                    if parsed.path == "/api/pending":
                        decision_id = parse_qs(parsed.query).get("decision_id", [None])[0]
                        pending = manager.get(decision_id)
                        if not pending:
                            self._json(HTTPStatus.NOT_FOUND, {"error": "decision_not_found"})
                            return
                        self._json(HTTPStatus.OK, pending.public_spec())
                        return
                    self._json(HTTPStatus.NOT_FOUND, {"error": "not_found"})

                def do_POST(self) -> None:  # noqa: N802
                    if self.path != "/api/submit":
                        self._json(HTTPStatus.NOT_FOUND, {"error": "not_found"})
                        return
                    length = int(self.headers.get("Content-Length", "0"))
                    body = self.rfile.read(length or 0)
                    try:
                        payload = json.loads(body.decode("utf-8"))
                    except json.JSONDecodeError:
                        self._json(HTTPStatus.BAD_REQUEST, {"error": "invalid_json"})
                        return
                    result = manager.submit(payload)
                    if not result:
                        self._json(HTTPStatus.NOT_FOUND, {"error": "decision_not_found"})
                        return
                    self._json(HTTPStatus.OK, result)

                def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
                    return

            self._httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
            self._base_url = f"http://127.0.0.1:{self._httpd.server_port}"
            self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)
            self._thread.start()

    def _persist_pending(self) -> None:
        snapshot = []
        for item in self._pending.values():
            snapshot.append(
                {
                    "decision_id": item.decision_id,
                    "header": item.spec.get("header"),
                    "question": item.spec.get("question"),
                    "created_at": item.created_at,
                }
            )
        save_json_atomic(runtime_path("pending_decisions.json"), {"pending": snapshot})

    def create(self, spec: dict[str, Any]) -> PendingDecision:
        decision_id = spec.get("decision_id") or str(uuid.uuid4())
        payload = dict(spec)
        payload["decision_id"] = decision_id
        with self._lock:
            pending = PendingDecision(decision_id=decision_id, spec=payload)
            self._pending[decision_id] = pending
            self._persist_pending()
            return pending

    def get(self, decision_id: str | None) -> PendingDecision | None:
        if not decision_id:
            return None
        with self._lock:
            return self._pending.get(decision_id)

    def submit(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        decision_id = payload.get("decision_id")
        with self._lock:
            pending = self._pending.get(decision_id)
            if pending is None:
                return None
            selected = payload.get("selected_option")
            free_text = (payload.get("free_text") or "").strip()
            if pending.spec.get("multiSelect") and not isinstance(selected, list):
                selected = [selected] if selected else []
            requires_followup = bool(free_text)
            if isinstance(selected, list):
                for option_id in selected:
                    option = next((item for item in pending.spec["options"] if item["id"] == option_id), None)
                    requires_followup = requires_followup or bool(option and option.get("requires_followup"))
            else:
                option = next(
                    (item for item in pending.spec["options"] if item["id"] == selected),
                    None,
                )
                requires_followup = requires_followup or bool(option and option.get("requires_followup"))
            pending.result = {
                "decision_id": decision_id,
                "selected_option": selected,
                "free_text": free_text,
                "requires_followup": requires_followup,
                "raw_payload": payload,
            }
            pending.event.set()
            del self._pending[decision_id]
            self._persist_pending()
            return pending.result

    def open_browser(self, decision_id: str) -> tuple[str, bool]:
        url = f"{self.base_url}/?decision_id={decision_id}"
        opened = False
        commands = []
        if sys.platform == "darwin":
            commands.append(["open", url])
        elif sys.platform.startswith("linux"):
            commands.append(["xdg-open", url])
        elif sys.platform.startswith("win"):
            commands.append(["cmd", "/c", "start", "", url])
        for command in commands:
            try:
                subprocess.Popen(command)
                opened = True
                break
            except OSError:
                continue
        return url, opened

    def ask(self, spec: dict[str, Any], timeout_seconds: int = 1800, open_browser: bool = True) -> dict[str, Any]:
        self.ensure_server()
        pending = self.create(spec)
        url = None
        opened = False
        if open_browser:
            url, opened = self.open_browser(pending.decision_id)
        completed = pending.event.wait(timeout_seconds)
        if not completed:
            with self._lock:
                self._pending.pop(pending.decision_id, None)
                self._persist_pending()
            return {
                "decision_id": pending.decision_id,
                "selected_option": None,
                "free_text": "",
                "requires_followup": True,
                "raw_payload": {
                    "timeout": True,
                    "decision_url": url or f"{self.base_url}/?decision_id={pending.decision_id}",
                    "opened_in_browser": opened,
                },
            }
        result = pending.result or {}
        result["raw_payload"] = {
            **result.get("raw_payload", {}),
            "decision_url": url or f"{self.base_url}/?decision_id={pending.decision_id}",
            "opened_in_browser": opened,
        }
        return result
