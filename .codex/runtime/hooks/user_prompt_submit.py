#!/usr/bin/env python3
"""Codex UserPromptSubmit hook for HarnessDesign command aliases."""

from __future__ import annotations

import json
import pathlib
import sys

HOOK_DIR = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HOOK_DIR.parent))

from common import prompt_alias_context


def main() -> int:
    payload = json.load(sys.stdin)
    context = prompt_alias_context(payload.get("prompt", ""))
    if context:
        print(context)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
