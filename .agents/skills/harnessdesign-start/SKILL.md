---
name: harnessdesign-start
description: "Codex entrypoint for starting a new HarnessDesign workflow task."
---

Read and follow the Skill SOP at `.harnessdesign/knowledge/skills/harnessdesign-router.md`.

This is the Codex entrypoint for `/harnessdesign-start`.

When running inside Codex:
- Use the `harnessdesign_runtime` MCP tools for workflow-critical writes.
- Use `hd_ask_decision` for any structured decision that would otherwise rely on Claude's `AskUserQuestion`.
- Keep the underlying HarnessDesign workflow logic in the shared Skill SOP files unchanged.

If the user provided arguments: $ARGUMENTS
