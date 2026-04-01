#!/usr/bin/env python3
"""Minimal MCP server for the HarnessDesign Codex runtime."""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import traceback
from datetime import datetime
from typing import Any

from common import (
    CRITICAL_FILES,
    HD_SCRIPTS_DIR,
    ROOT,
    STATE_TO_SKILL,
    detect_archive_type,
    get_resume_payload,
    get_task_summary,
    json_dump,
    list_tasks,
    load_progress,
    merge_patch,
    resolve_artifact_path,
    save_json_atomic,
    save_text_atomic,
    search_archives,
    validate_module,
    verify_module,
)
from decision_ui import DecisionManager


SERVER_INFO = {
    "name": "harnessdesign_runtime",
    "version": "0.1.0",
}


class RuntimeErrorWithPayload(Exception):
    def __init__(self, message: str, payload: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.payload = payload or {"error": message}


class HarnessDesignRuntime:
    def __init__(self) -> None:
        self.decision_manager = DecisionManager()

    def tool_definitions(self) -> list[dict[str, Any]]:
        return [
            {
                "name": "hd_list_tasks",
                "description": "List HarnessDesign task workspaces and their current states.",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "additionalProperties": False,
                },
            },
            {
                "name": "hd_get_task_state",
                "description": "Load task-progress.json plus a generated summary for a specific task.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "task_dir": {"type": "string"},
                    },
                    "required": ["task_dir"],
                    "additionalProperties": False,
                },
            },
            {
                "name": "hd_resume_task",
                "description": "Return the current state, summary, and recommended skill for an existing task.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "task_dir": {"type": "string"},
                    },
                    "required": ["task_dir"],
                    "additionalProperties": False,
                },
            },
            {
                "name": "hd_update_progress",
                "description": "Safely patch task-progress.json and optionally perform a validated state transition.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "task_dir": {"type": "string"},
                        "patch": {"type": "object"},
                        "target_state": {"type": "string"},
                        "approval_actor": {"type": "string"},
                    },
                    "required": ["task_dir", "patch"],
                    "additionalProperties": False,
                },
            },
            {
                "name": "hd_write_artifact",
                "description": "Safely write a workflow artifact or archive file and run required validations.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "task_dir": {"type": "string"},
                        "artifact_kind": {"type": "string"},
                        "target_path": {"type": "string"},
                        "content": {"type": "string"},
                        "requires_state": {"type": "string"},
                    },
                    "required": ["task_dir", "artifact_kind", "content"],
                    "additionalProperties": False,
                },
            },
            {
                "name": "hd_verify_archive",
                "description": "Run deterministic archive verification for a written archive file.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string"},
                        "archive_type": {"type": "string"},
                    },
                    "required": ["file_path", "archive_type"],
                    "additionalProperties": False,
                },
            },
            {
                "name": "hd_recall",
                "description": "Search HarnessDesign archive files by phase, filename, or keyword.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {},
                    },
                    "required": ["query"],
                    "additionalProperties": False,
                },
            },
            {
                "name": "hd_ask_decision",
                "description": "Open the local HarnessDesign decision UI, wait for the designer's selection, and return a structured result.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "decision_id": {"type": "string"},
                        "question": {"type": "string"},
                        "header": {"type": "string"},
                        "options": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "string"},
                                    "label": {"type": "string"},
                                    "description": {"type": "string"},
                                    "requires_followup": {"type": "boolean"},
                                },
                                "required": ["label"],
                                "additionalProperties": False,
                            },
                        },
                        "allow_other": {"type": "boolean"},
                        "multiSelect": {"type": "boolean"},
                        "followup_policy": {"type": "string"},
                        "timeout_seconds": {"type": "integer", "minimum": 1},
                        "open_browser": {"type": "boolean"},
                    },
                    "required": ["question", "header", "options"],
                    "additionalProperties": False,
                },
            },
        ]

    def tool_call(self, name: str, args: dict[str, Any]) -> dict[str, Any]:
        if name == "hd_list_tasks":
            return {"tasks": list_tasks()}
        if name == "hd_get_task_state":
            task_dir = pathlib.Path(args["task_dir"]).resolve()
            return {
                "task_dir": str(task_dir),
                "progress": load_progress(task_dir),
                "summary": get_task_summary(task_dir),
            }
        if name == "hd_resume_task":
            return get_resume_payload(args["task_dir"])
        if name == "hd_update_progress":
            return self._update_progress(args)
        if name == "hd_write_artifact":
            return self._write_artifact(args)
        if name == "hd_verify_archive":
            verifier = verify_module()
            result = verifier.verify_archive(args["file_path"], args["archive_type"])
            return {
                "file_path": str(pathlib.Path(args["file_path"]).resolve()),
                "archive_type": args["archive_type"],
                "result": result,
            }
        if name == "hd_recall":
            return search_archives(args["query"])
        if name == "hd_ask_decision":
            return self._ask_decision(args)
        raise RuntimeErrorWithPayload(f"Unknown tool '{name}'")

    def _update_progress(self, args: dict[str, Any]) -> dict[str, Any]:
        vt = validate_module()
        task_dir = pathlib.Path(args["task_dir"]).resolve()
        progress_path = task_dir / "task-progress.json"
        progress = load_progress(task_dir)
        patch = args.get("patch") or {}
        if "current_state" in patch and not args.get("target_state"):
            raise RuntimeErrorWithPayload(
                "Directly patching current_state is not allowed. Use target_state for validated transitions."
            )
        updated = merge_patch(progress, patch)

        current_state = progress.get("current_state")
        approval_actor = args.get("approval_actor")
        if approval_actor and current_state:
            states = updated.setdefault("states", {})
            gate = states.setdefault(current_state, {})
            gate["approved_by"] = approval_actor
            gate["approved_at"] = datetime.now().isoformat()

        target_state = args.get("target_state")
        validation = None
        if target_state:
            updated["current_state"] = current_state
            save_json_atomic(progress_path, updated)
            validation = vt.validate_transition(str(task_dir), target_state)
            if not validation["valid"]:
                save_json_atomic(progress_path, progress)
                raise RuntimeErrorWithPayload(
                    "State transition validation failed.",
                    {"validation": validation},
                )
            updated["current_state"] = target_state
            updated["expected_next_state"] = vt.TRANSITIONS.get(target_state, {}).get("next")

        save_json_atomic(progress_path, updated)
        return {
            "task_dir": str(task_dir),
            "progress_path": str(progress_path),
            "validation": validation,
            "progress": updated,
        }

    def _write_artifact(self, args: dict[str, Any]) -> dict[str, Any]:
        vt = validate_module()
        task_dir = pathlib.Path(args["task_dir"]).resolve()
        requires_state = args.get("requires_state")
        progress = load_progress(task_dir)
        current_state = progress.get("current_state")
        if requires_state and current_state != requires_state:
            raise RuntimeErrorWithPayload(
                f"Artifact requires state '{requires_state}', but current state is '{current_state}'."
            )

        target_path = resolve_artifact_path(task_dir, args["artifact_kind"], args.get("target_path"))
        preflight = vt.check_write_allowed(str(target_path), str(task_dir))
        if not preflight["allowed"]:
            raise RuntimeErrorWithPayload(
                "Write blocked by workflow guard.",
                {"preflight": preflight, "target_path": str(target_path)},
            )

        target_path.parent.mkdir(parents=True, exist_ok=True)
        save_text_atomic(target_path, args["content"])

        post_write: dict[str, Any] = {"preflight": preflight}
        archive_type = detect_archive_type(target_path)
        if archive_type:
            verifier = verify_module()
            post_write["archive_validation"] = verifier.verify_archive(str(target_path), archive_type)

        if target_path.name == "index.html":
            post_write["html_validation"] = self._run_command(
                ["python3", str(HD_SCRIPTS_DIR / "validate_html.py"), str(target_path)]
            )
            post_write["cognitive_load_audit"] = self._run_command(
                ["python3", str(HD_SCRIPTS_DIR / "cognitive_load_audit.py"), str(target_path)]
            )

        return {
            "task_dir": str(task_dir),
            "artifact_kind": args["artifact_kind"],
            "target_path": str(target_path),
            "current_state": current_state,
            "post_write": post_write,
        }

    def _ask_decision(self, args: dict[str, Any]) -> dict[str, Any]:
        options = []
        for index, option in enumerate(args["options"], start=1):
            option_id = option.get("id") or f"option-{index}"
            options.append(
                {
                    "id": option_id,
                    "label": option["label"],
                    "description": option.get("description", ""),
                    "requires_followup": option.get("requires_followup", False),
                }
            )
        if args.get("allow_other"):
            options.append(
                {
                    "id": "other",
                    "label": "Other",
                    "description": "Provide a custom response.",
                    "requires_followup": True,
                }
            )
        spec = {
            "decision_id": args.get("decision_id"),
            "question": args["question"],
            "header": args["header"],
            "options": options,
            "allow_other": bool(args.get("allow_other", True)),
            "multiSelect": bool(args.get("multiSelect", False)),
            "followup_policy": args.get("followup_policy", "optional"),
        }
        return self.decision_manager.ask(
            spec,
            timeout_seconds=int(args.get("timeout_seconds", 1800)),
            open_browser=bool(args.get("open_browser", True)),
        )

    def _run_command(self, command: list[str]) -> dict[str, Any]:
        proc = subprocess.run(command, capture_output=True, text=True)
        return {
            "command": command,
            "returncode": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
        }


def encode_result(result: Any, is_error: bool = False) -> dict[str, Any]:
    if isinstance(result, dict):
        structured = result
        text = json_dump(result)
    else:
        structured = {"result": result}
        text = str(result)
    payload = {
        "content": [{"type": "text", "text": text}],
        "structuredContent": structured,
    }
    if is_error:
        payload["isError"] = True
    return payload


def read_message() -> dict[str, Any] | None:
    headers: dict[str, str] = {}
    while True:
        line = sys.stdin.buffer.readline()
        if not line:
            return None
        if line in (b"\r\n", b"\n"):
            break
        name, value = line.decode("utf-8").split(":", 1)
        headers[name.strip().lower()] = value.strip()
    length = int(headers.get("content-length", "0"))
    body = sys.stdin.buffer.read(length)
    if not body:
        return None
    return json.loads(body.decode("utf-8"))


def write_message(message: dict[str, Any]) -> None:
    raw = json.dumps(message, ensure_ascii=False).encode("utf-8")
    sys.stdout.buffer.write(f"Content-Length: {len(raw)}\r\n\r\n".encode("utf-8"))
    sys.stdout.buffer.write(raw)
    sys.stdout.buffer.flush()


def success_response(request_id: Any, result: Any) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def error_response(request_id: Any, code: int, message: str, data: Any = None) -> dict[str, Any]:
    payload = {"code": code, "message": message}
    if data is not None:
        payload["data"] = data
    return {"jsonrpc": "2.0", "id": request_id, "error": payload}


def main() -> int:
    runtime = HarnessDesignRuntime()

    while True:
        request = read_message()
        if request is None:
            return 0

        method = request.get("method")
        request_id = request.get("id")
        params = request.get("params", {})

        try:
            if method == "initialize":
                result = {
                    "protocolVersion": params.get("protocolVersion", "2024-11-05"),
                    "capabilities": {"tools": {}},
                    "serverInfo": SERVER_INFO,
                }
                write_message(success_response(request_id, result))
                continue

            if method == "notifications/initialized":
                continue

            if method == "tools/list":
                write_message(
                    success_response(
                        request_id,
                        {
                            "tools": runtime.tool_definitions(),
                        },
                    )
                )
                continue

            if method == "tools/call":
                name = params.get("name")
                arguments = params.get("arguments", {})
                result = runtime.tool_call(name, arguments)
                write_message(success_response(request_id, encode_result(result)))
                continue

            write_message(error_response(request_id, -32601, f"Method not found: {method}"))
        except RuntimeErrorWithPayload as exc:
            write_message(
                success_response(
                    request_id,
                    encode_result(exc.payload, is_error=True),
                )
            )
        except Exception as exc:  # pragma: no cover - defensive
            payload = {
                "error": str(exc),
                "traceback": traceback.format_exc(),
            }
            write_message(success_response(request_id, encode_result(payload, is_error=True)))


if __name__ == "__main__":
    raise SystemExit(main())
