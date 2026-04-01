---
name: harnessdesign-update
description: "Codex entrypoint for updating the HarnessDesign workflow engine."
---

This skill mirrors `/harnessdesign-update` for Codex.

Follow `AGENTS.md` and the documented update flow:
1. `git pull origin main`
2. `pip3 install -r .harnessdesign/scripts/requirements.txt`
3. `python3 .harnessdesign/scripts/integration_test.py`

Report which files changed and whether validation passed.

Arguments: $ARGUMENTS
