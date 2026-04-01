#!/usr/bin/env python3
"""Shared helpers for the HarnessDesign Codex runtime."""

from __future__ import annotations

import copy
import importlib
import json
import os
import pathlib
import re
import tempfile
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPTS_DIR = ROOT / "scripts"
HD_SCRIPTS_DIR = ROOT / ".harnessdesign" / "scripts"
RUNTIME_DIR = ROOT / ".codex" / "runtime"
STATE_DIR = RUNTIME_DIR / "state"
TASKS_DIR = ROOT / "tasks"
SESSIONS_DIR = ROOT / ".harnessdesign" / "memory" / "sessions"

CRITICAL_FILES = {
    "task-progress.json",
    "confirmed_intent.md",
    "00-research.md",
    "01-jtbd.md",
    "02-structure.md",
    "03-design-contract.md",
    "index.html",
}

WORKFLOW_WRITE_PATTERNS = [
    re.compile(r"\.harnessdesign/memory/sessions/.+\.md$"),
]

ARCHIVE_PATTERNS = [
    (re.compile(r"phase1-alignment\.md$"), "phase1"),
    (re.compile(r"phase2-topic-.+\.md$"), "phase2-topic"),
    (re.compile(r"phase2-research-full\.md$"), "phase2-research"),
    (re.compile(r"phase3-scenario-\d+-round-\d+\.md$"), "phase3-round"),
    (re.compile(r"phase3-scenario-\d+\.md$"), "phase3-scenario"),
    (re.compile(r"phase4-review-round-\d+\.md$"), "phase4-review"),
    (re.compile(r"phase2-insight-cards\.md$"), "insight-cards"),
]

COMMAND_ALIASES = {
    "/harnessdesign-start": "harnessdesign-start",
    "/harnessdesign-resume": "harnessdesign-resume",
    "/harnessdesign-status": "harnessdesign-status",
    "/harnessdesign-update": "harnessdesign-update",
    "/harnessdesign-migrate": "harnessdesign-migrate",
    "/harnessdesign-onboarding": "harnessdesign-onboarding",
    "/harnessdesign-alignment": "harnessdesign-alignment",
    "/harnessdesign-research": "harnessdesign-research",
    "/harnessdesign-interaction": "harnessdesign-interaction",
    "/harnessdesign-contract": "harnessdesign-contract",
    "/harnessdesign-hifi": "harnessdesign-hifi",
    "/harnessdesign-extract": "harnessdesign-extract",
}

STATE_TO_SKILL = {
    "migration": "harnessdesign-migrate",
    "migration_complete": None,
    "onboarding": "harnessdesign-onboarding",
    "init": "harnessdesign-alignment",
    "alignment": "harnessdesign-alignment",
    "research_jtbd": "harnessdesign-research",
    "interaction_design": "harnessdesign-interaction",
    "prepare_design_contract": "harnessdesign-contract",
    "contract_review": "harnessdesign-contract",
    "hifi_generation": "harnessdesign-hifi",
    "review": "harnessdesign-hifi",
    "knowledge_extraction": "harnessdesign-extract",
    "complete": None,
}

DEFAULT_ARTIFACT_PATHS = {
    "confirmed_intent": "confirmed_intent.md",
    "research_report": "00-research.md",
    "jtbd": "01-jtbd.md",
    "structure": "02-structure.md",
    "design_contract": "03-design-contract.md",
    "hifi": "index.html",
}

TRUSTED_BASH_SUBSTRINGS = [
    "scripts/validate_transition.py",
    "scripts/verify_archive.py",
    ".harnessdesign/scripts/validate_html.py",
    ".harnessdesign/scripts/cognitive_load_audit.py",
    ".codex/runtime/server.py",
    ".codex/runtime/hooks/",
    ".codex/runtime/smoke_test.py",
]


def ensure_runtime_dirs() -> pathlib.Path:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    return STATE_DIR


def runtime_path(*parts: str) -> pathlib.Path:
    ensure_runtime_dirs()
    return STATE_DIR.joinpath(*parts)


def json_dump(data: Any) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True)


def load_json(path: pathlib.Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def save_json_atomic(path: pathlib.Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=str(path.parent), prefix=path.name, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def save_text_atomic(path: pathlib.Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=str(path.parent), prefix=path.name, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(content)
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def import_script_module(module_name: str):
    if str(SCRIPTS_DIR) not in os.sys.path:
        os.sys.path.insert(0, str(SCRIPTS_DIR))
    module = importlib.import_module(module_name)
    return importlib.reload(module)


def validate_module():
    return import_script_module("validate_transition")


def verify_module():
    return import_script_module("verify_archive")


def project_root() -> pathlib.Path:
    return ROOT


def find_task_dir(file_path: str) -> pathlib.Path | None:
    candidate = pathlib.Path(file_path).resolve()
    current = candidate if candidate.is_dir() else candidate.parent
    while current != current.parent:
        if (current / "task-progress.json").is_file():
            return current
        current = current.parent
    if TASKS_DIR.is_dir():
        for child in TASKS_DIR.iterdir():
            if (child / "task-progress.json").is_file():
                return child
    return None


def load_progress(task_dir: str | pathlib.Path) -> dict:
    task_path = pathlib.Path(task_dir).resolve()
    progress_path = task_path / "task-progress.json"
    with progress_path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def merge_patch(base: Any, patch: Any) -> Any:
    if not isinstance(base, dict) or not isinstance(patch, dict):
        return copy.deepcopy(patch)
    result = copy.deepcopy(base)
    for key, value in patch.items():
        if value is None:
            result.pop(key, None)
        elif isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = merge_patch(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def detect_archive_type(file_path: str | pathlib.Path) -> str | None:
    basename = pathlib.Path(file_path).name
    for pattern, archive_type in ARCHIVE_PATTERNS:
        if pattern.search(basename):
            return archive_type
    return None


def resolve_artifact_path(
    task_dir: str | pathlib.Path,
    artifact_kind: str,
    target_path: str | None = None,
) -> pathlib.Path:
    task_path = pathlib.Path(task_dir).resolve()
    if target_path:
        resolved = pathlib.Path(target_path)
        return resolved if resolved.is_absolute() else task_path / resolved
    if artifact_kind not in DEFAULT_ARTIFACT_PATHS:
        raise ValueError(f"Unknown artifact_kind '{artifact_kind}' without target_path")
    return task_path / DEFAULT_ARTIFACT_PATHS[artifact_kind]


def list_tasks() -> list[dict[str, Any]]:
    if not TASKS_DIR.is_dir():
        return []
    items: list[dict[str, Any]] = []
    for child in sorted(TASKS_DIR.iterdir()):
        progress_path = child / "task-progress.json"
        if not progress_path.is_file():
            continue
        try:
            progress = load_progress(child)
        except Exception as exc:  # pragma: no cover - defensive
            items.append(
                {
                    "task_name": child.name,
                    "task_dir": str(child),
                    "error": str(exc),
                }
            )
            continue
        items.append(
            {
                "task_name": progress.get("task_name", child.name),
                "task_dir": str(child),
                "current_state": progress.get("current_state"),
                "expected_next_state": progress.get("expected_next_state"),
                "updated_at": progress_path.stat().st_mtime,
            }
        )
    return items


def get_task_summary(task_dir: str | pathlib.Path) -> dict[str, Any]:
    vt = validate_module()
    summary = vt.generate_summary(str(pathlib.Path(task_dir).resolve()))
    summary["task_dir"] = str(pathlib.Path(task_dir).resolve())
    return summary


def get_resume_payload(task_dir: str | pathlib.Path) -> dict[str, Any]:
    progress = load_progress(task_dir)
    current_state = progress.get("current_state")
    return {
        "task_dir": str(pathlib.Path(task_dir).resolve()),
        "current_state": current_state,
        "recommended_skill": STATE_TO_SKILL.get(current_state),
        "summary": get_task_summary(task_dir),
        "progress": progress,
    }


def search_archives(query: Any) -> dict[str, Any]:
    payload = query if isinstance(query, dict) else {"query": str(query)}
    needle = payload.get("query", "").strip().lower()
    phase = payload.get("phase")
    scenario = payload.get("scenario")
    round_number = payload.get("round")
    matches: list[dict[str, Any]] = []
    if not SESSIONS_DIR.is_dir():
        return {"matches": matches}

    for archive_path in sorted(SESSIONS_DIR.glob("*.md")):
        text = archive_path.read_text(encoding="utf-8")
        haystack = text.lower()
        if needle and needle not in archive_path.name.lower() and needle not in haystack:
            continue
        if phase and f"phase: {phase}" not in haystack:
            continue
        if scenario and f"scenario: {scenario}" not in haystack:
            continue
        if round_number and f"round: {round_number}" not in haystack:
            continue
        snippet = text[:400].strip()
        matches.append(
            {
                "path": str(archive_path),
                "filename": archive_path.name,
                "snippet": snippet,
            }
        )
    return {"matches": matches[:20], "query": payload}


def _command_mentions_workflow_path(command: str) -> bool:
    normalized = command.replace("\\", "/")
    if any(basename in normalized for basename in CRITICAL_FILES):
        return True
    return any(pattern.search(normalized) for pattern in WORKFLOW_WRITE_PATTERNS)


def _looks_mutating(command: str) -> bool:
    tokens = [
        r"(^|\s)tee(\s|$)",
        r">>",
        r"(^|[^>])>([^>]|$)",
        r"sed\s+-i",
        r"perl\s+-pi",
        r"python3?\s+.*write",
        r"python3?\s+-c",
        r"node\s+-e",
        r"ruby\s+-e",
        r"mv\s+",
        r"cp\s+",
        r"rm\s+",
        r"touch\s+",
        r"truncate\s+",
        r"cat\s+<<",
    ]
    return any(re.search(pattern, command) for pattern in tokens)


def should_block_bash_command(command: str) -> tuple[bool, str | None]:
    if any(fragment in command for fragment in TRUSTED_BASH_SUBSTRINGS):
        return False, None
    if _command_mentions_workflow_path(command) and _looks_mutating(command):
        return (
            True,
            "HarnessDesign critical files must be modified via the "
            "`harnessdesign_runtime` MCP tools instead of Bash redirection or ad-hoc scripts.",
        )
    return False, None


def prompt_alias_context(prompt: str) -> str | None:
    stripped = prompt.strip()
    if not stripped.startswith("/"):
        return None
    head = stripped.split(maxsplit=1)[0]
    if head in COMMAND_ALIASES:
        skill_name = COMMAND_ALIASES[head]
        args = stripped[len(head):].strip()
        extra = f" Pass the trailing arguments `{args}` through." if args else ""
        return (
            f"The user invoked the HarnessDesign Codex alias `{head}`. "
            f"Treat this as an explicit request to invoke the repo skill `${skill_name}`.{extra} "
            "Use the `harnessdesign_runtime` MCP tools for workflow-critical writes and structured decisions."
        )
    if stripped.startswith("/recall"):
        return (
            "The user invoked a HarnessDesign recall command. Use the `hd_recall` runtime tool "
            "and the router guidance in `.harnessdesign/knowledge/skills/harnessdesign-router.md`."
        )
    return None


def session_context() -> str:
    tasks = list_tasks()
    lines = [
        "HarnessDesign Codex runtime is active.",
        "Use the `harnessdesign_runtime` MCP tools for workflow-critical writes, state transitions, archive verification, and structured decisions.",
        "Do not directly edit `task-progress.json`, stage artifacts, archive files, or `index.html` with generic edit tools.",
    ]
    if tasks:
        lines.append("Known tasks:")
        for item in tasks[:5]:
            state = item.get("current_state", "unknown")
            lines.append(f"- {item['task_name']}: {state} ({item['task_dir']})")
    else:
        lines.append("Known tasks: none yet.")
    return "\n".join(lines)


def pending_decision_snapshot() -> dict[str, Any]:
    path = runtime_path("pending_decisions.json")
    return load_json(path, default={"pending": []})

