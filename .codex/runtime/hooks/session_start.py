#!/usr/bin/env python3
"""Codex SessionStart hook for HarnessDesign."""

from __future__ import annotations

import pathlib
import sys

HOOK_DIR = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HOOK_DIR.parent))

from common import session_context


def main() -> int:
    print(session_context())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
