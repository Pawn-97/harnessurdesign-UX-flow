---
name: harnessdesign-extract
description: "Codex entrypoint for HarnessDesign knowledge extraction."
---

Read and follow the Skill SOP at `.harnessdesign/knowledge/skills/knowledge-extractor-skill.md`.

For Codex, route workflow-critical writes through `harnessdesign_runtime`, and map any `AskUserQuestion` step to `hd_ask_decision`.

Arguments: $ARGUMENTS
