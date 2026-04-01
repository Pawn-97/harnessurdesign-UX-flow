#!/usr/bin/env python3
"""Smoke tests for the HarnessDesign Codex runtime helpers."""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from common import detect_archive_type, merge_patch, prompt_alias_context, should_block_bash_command


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    merged = merge_patch({"a": {"b": 1}, "c": 2}, {"a": {"d": 3}, "c": None})
    assert_true(merged == {"a": {"b": 1, "d": 3}}, "merge_patch failed")

    assert_true(
        detect_archive_type("phase3-scenario-1-round-2.md") == "phase3-round",
        "archive detection failed",
    )
    assert_true(
        prompt_alias_context("/harnessdesign-start --prd foo.md") is not None,
        "command alias context missing",
    )
    blocked, _ = should_block_bash_command("cat <<'EOF' > tasks/demo/index.html\nEOF")
    assert_true(blocked, "critical Bash write should be blocked")
    print("HarnessDesign Codex runtime smoke tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
