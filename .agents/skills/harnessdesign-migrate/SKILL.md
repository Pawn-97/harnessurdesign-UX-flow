---
name: harnessdesign-migrate
description: "Codex entrypoint for importing existing design artifacts into HarnessDesign."
---

Read and follow the Skill SOP at `.harnessdesign/knowledge/skills/harnessdesign-router.md`.

This is the Codex entrypoint for `/harnessdesign-migrate`.

When running inside Codex:
- Use the `harnessdesign_runtime` MCP tools for task-state changes, archive writes, and structured decisions.
- Keep the underlying migration logic in the shared Skill SOP files unchanged.

If the user provided arguments: $ARGUMENTS
