---
name: harnessdesign-alignment
description: "Codex entrypoint for the HarnessDesign alignment phase."
---

Read and follow the Skill SOP at `.harnessdesign/knowledge/skills/alignment-skill.md`.

For Codex, route workflow-critical writes through `harnessdesign_runtime`, and map any `AskUserQuestion` step to `hd_ask_decision`.

Arguments: $ARGUMENTS
