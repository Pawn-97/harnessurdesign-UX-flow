#!/usr/bin/env python3
"""Codex PreToolUse Bash policy for HarnessDesign."""

from __future__ import annotations

import json
import pathlib
import sys

HOOK_DIR = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HOOK_DIR.parent))

from common import should_block_bash_command


def main() -> int:
    payload = json.load(sys.stdin)
    command = payload.get("tool_input", {}).get("command", "")
    blocked, reason = should_block_bash_command(command)
    if not blocked:
        return 0
    result = {
        "decision": "block",
        "reason": reason,
    }
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
