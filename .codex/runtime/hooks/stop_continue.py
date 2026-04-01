#!/usr/bin/env python3
"""Codex Stop hook for pending HarnessDesign decisions."""

from __future__ import annotations

import json
import pathlib
import sys

HOOK_DIR = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HOOK_DIR.parent))

from common import pending_decision_snapshot


def main() -> int:
    payload = json.load(sys.stdin)
    if payload.get("stop_hook_active"):
        return 0
    pending = pending_decision_snapshot().get("pending", [])
    if not pending:
        return 0
    result = {
        "decision": "block",
        "reason": (
            "Resolve the pending HarnessDesign decision in the local browser chooser "
            "before ending this turn."
        ),
    }
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
