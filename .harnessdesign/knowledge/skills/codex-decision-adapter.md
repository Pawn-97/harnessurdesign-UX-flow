---
name: codex-decision-adapter
description: Codex adapter for HarnessDesign structured decisions and workflow-critical writes
user_invocable: false
---

# HarnessDesign Codex Decision Adapter

> This file defines how Codex should preserve the **same workflow semantics** as Claude Code without changing the shared Skill SOP business logic.

## 1. Purpose

Claude Code can execute `AskUserQuestion` directly inside the chat UI. Codex currently cannot provide the same transport in the general execution path, so Codex must route structured decisions through the local `harnessdesign_runtime` MCP server.

The business semantics stay the same:
- `[STOP AND WAIT]` still pauses execution
- `[STOP AND WAIT FOR APPROVAL]` still requires designer confirmation before state transition
- `[DECISION POINT — STRUCTURED]` still means a structured, enumerable choice rather than free-form dialogue

Only the transport changes:
- Claude Code: `AskUserQuestion`
- Codex: `hd_ask_decision`

## 2. Mapping Rule

Whenever a shared Skill SOP says:

```text
[DECISION POINT — STRUCTURED]
Use AskUserQuestion:
  question: ...
  header: ...
  options: ...
```

Codex must call `hd_ask_decision` with the equivalent payload:

```json
{
  "question": "...",
  "header": "...",
  "options": [
    {
      "id": "option-1",
      "label": "...",
      "description": "...",
      "requires_followup": false
    }
  ],
  "allow_other": true,
  "multiSelect": false,
  "followup_policy": "optional"
}
```

## 3. Follow-up Rule

If the chosen option requires designer elaboration, set `requires_followup: true` on that option. After `hd_ask_decision` returns:

- `requires_followup = false` → continue the workflow immediately
- `requires_followup = true` → switch back to normal natural-language dialogue to collect the extra detail

This preserves the Rule 3 behavior from `guided-dialogue.md`:
- structured first
- open follow-up second

## 4. Workflow-Critical Writes

In Codex, the following files must be written through `harnessdesign_runtime` instead of generic edit tools:

- `task-progress.json`
- `confirmed_intent.md`
- `00-research.md`
- `01-jtbd.md`
- `02-structure.md`
- `03-design-contract.md`
- `index.html`
- archives under `.harnessdesign/memory/sessions/`

Tool mapping:
- `task-progress.json` → `hd_update_progress`
- stage artifacts / archives / HTML → `hd_write_artifact`
- archive-only recheck → `hd_verify_archive`

## 5. Command Aliases

Codex should treat these slash-style prompts as skill aliases:

- `/harnessdesign-start` → `$harnessdesign-start`
- `/harnessdesign-resume` → `$harnessdesign-resume`
- `/harnessdesign-status` → `$harnessdesign-status`
- `/harnessdesign-update` → `$harnessdesign-update`
- `/harnessdesign-migrate` → `$harnessdesign-migrate`

Phase skills may also be invoked directly when needed:
- `$harnessdesign-onboarding`
- `$harnessdesign-alignment`
- `$harnessdesign-research`
- `$harnessdesign-interaction`
- `$harnessdesign-contract`
- `$harnessdesign-hifi`
- `$harnessdesign-extract`

## 6. Non-Goals

This adapter does **not** change:
- the shared phase/state machine
- the meaning of approval gates
- archive quality rules
- validation scripts
- Claude Code behavior
