# HarnessDesign AI-UX Workflow — Codex Configuration

## Project Overview

This project is a **portable Skill + Knowledge directory (`.harnessdesign/`)** that runs within AI coding tools. The AI tool's Agent loop serves as the orchestration engine — Skill SOP files (Markdown + YAML) guide you through a four-phase UX design workflow.

**Your role**: Follow the Skill SOP instructions in `.harnessdesign/knowledge/skills/`. Do not invent workflow steps on your own — all dispatch logic is defined in the Skill files.

## Core Workflow

```
Phase 0: Onboarding (first time) → Phase 1: Context Alignment → Phase 2: Research + JTBD → Phase 3: Per-scenario Interaction Design → Phase 4: Hi-Fi HTML
```

## Command Shortcuts

When the designer enters the following commands, you must recognize and execute the corresponding action. Commands are case-insensitive.

| Command | Action |
|---------|--------|
| `/harnessdesign-start` | Start a new design task (AI invites designer to provide requirements, then creates task workspace) |
| `/harnessdesign-migrate` | Import existing design artifacts from other AI tools into HarnessDesign |
| `/harnessdesign-resume` | Resume the last unfinished task |
| `/harnessdesign-status` | Display current task status summary |
| `/harnessdesign-update` | Update the workflow to the latest version |
| `/recall list` | List all recallable archive files |
| `/recall <phase> --query "<keyword>"` | Precisely recall archive content by keyword |

### `/harnessdesign-start` Detailed Flow

1. Read `AGENTS.md` (this file) to understand all rules
2. Read `.harnessdesign/knowledge/skills/harnessdesign-router.md` §1.1 to understand the initialization flow
3. Execute Onboarding pre-check (check if knowledge base is valid)
4. Invite the designer to provide task requirements (verbal description / upload PRD / both)
5. After receiving the task, create task workspace `tasks/<task-name>/` and `task-progress.json`
6. Execute the workflow according to state machine dispatch logic

### `/harnessdesign-resume` Detailed Flow

1. Scan the `tasks/` directory to find task workspaces containing `task-progress.json`
2. Read `task-progress.json`, restore `current_state`
3. Read `.harnessdesign/knowledge/skills/harnessdesign-router.md` §6 (session recovery)
4. Rebuild the anchor layer, load the corresponding Skill and continue execution

### `/harnessdesign-status` Detailed Flow

1. Run `python3 scripts/validate_transition.py --summary tasks/<task-name>`
2. Format the structured JSON output and display it to the designer

### `/harnessdesign-update` Detailed Flow

1. Run `git pull origin main`
2. Run `pip3 install -r .harnessdesign/scripts/requirements.txt` (update dependencies)
3. Run `python3 .harnessdesign/scripts/integration_test.py` (verify integrity)
4. Report update results to the designer: which files were updated, whether integration tests passed
5. **Note**: Updates do not affect existing task data in `tasks/` or archives in `.harnessdesign/memory/`

## ⚠️ Codex Control Plane Rules (Required Reading for Codex)

Codex now uses a repo-local control plane:

- `.codex/hooks.json` provides SessionStart / UserPromptSubmit / Bash guard / Stop hooks
- `harnessdesign_runtime` MCP tools provide workflow-critical writes, state transitions, archive verification, recall, and structured decisions
- `.agents/skills/harnessdesign-*` provide Codex-native command entrypoints

### Critical File Rule

When running inside Codex, the following files must be modified via `harnessdesign_runtime` MCP tools rather than generic edit tools:

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
- structured designer choice → `hd_ask_decision`

### Structured Decision Rule

For Codex, keep the shared Skill SOP semantics unchanged but change the transport:

- Claude Code: `AskUserQuestion`
- Codex: `hd_ask_decision`

Read `.harnessdesign/knowledge/skills/codex-decision-adapter.md` when a shared Skill SOP contains `[DECISION POINT — STRUCTURED]`.

## ⚠️ Fallback Validation Rules (Still Required if You Bypass the Runtime)

Codex hooks still cannot intercept generic `Edit` / `Write` tool calls. If you ever bypass the runtime MCP tools and directly modify workflow-critical files, you must manually execute the following validations. This is a fallback safety net, not the preferred path.

### Pre-write Validation (replaces hook_pre_write.py)

**Exemption**: First-time creation of `task-progress.json` (when the file does not yet exist) does not require running `validate_transition.py`. Validation only applies to **updating** an existing `task-progress.json`.

**Before every update to the following key files**, you must run the validation command:

| File | Validation Command |
|------|-------------------|
| `task-progress.json` | `python3 scripts/validate_transition.py --check-write <full_file_path> <task_dir>` |
| `confirmed_intent.md` | Same as above |
| `00-research.md` | Same as above |
| `01-jtbd.md` | Same as above |
| `02-structure.md` | Same as above |
| `03-design-contract.md` | Same as above |
| `index.html` | Same as above |

When validation returns `"allowed": false`, **writing is strictly forbidden** — first check if the `task-progress.json` state is correct.

### Post-write Validation (replaces hook_post_write.py)

**After writing archive files**, you must run archive integrity validation:

| File Pattern | Archive Type | Validation Command |
|-------------|-------------|-------------------|
| `phase1-alignment.md` | `phase1` | `python3 scripts/verify_archive.py <file_path> phase1` |
| `phase2-topic-*.md` | `phase2-topic` | `python3 scripts/verify_archive.py <file_path> phase2-topic` |
| `phase2-research-full.md` | `phase2-research` | `python3 scripts/verify_archive.py <file_path> phase2-research` |
| `phase3-scenario-N.md` | `phase3-scenario` | `python3 scripts/verify_archive.py <file_path> phase3-scenario` |
| `phase3-scenario-N-round-M.md` | `phase3-round` | `python3 scripts/verify_archive.py <file_path> phase3-round` |
| `phase4-review-round-M.md` | `phase4-review` | `python3 scripts/verify_archive.py <file_path> phase4-review` |
| `phase2-insight-cards.md` | `insight-cards` | `python3 scripts/verify_archive.py <file_path> insight-cards` |

When validation reports `"valid": false`, fix according to the error message and rewrite.

### State Transition Validation

**Before every `current_state` update**, run:
```bash
python3 scripts/validate_transition.py <task_dir> <target_state>
```
When it returns `"valid": false`, **state transition is strictly forbidden**.

## State Management

- **Always read `task-progress.json` to restore state before every execution**
- After completing a step, set the corresponding node's `passes` field to `true`
- Never "guess" current progress from long Markdown — JSON is the single source of truth for state
- The state machine credential uses the `states` key (not `gates`)

### MVP State Chain

```
onboarding → init → alignment → research_jtbd → interaction_design
→ prepare_design_contract → contract_review → hifi_generation
→ review → knowledge_extraction → complete
```

## Context Engineering

- **Conversations are "scaffolding", artifacts are "buildings" — tear down the scaffolding once it has served its purpose**
- Proactively archive conversations to `.harnessdesign/memory/sessions/` when a Phase/scenario completes
- Archive files must include YAML frontmatter (type, phase, archived_at, token_count, sections, keywords, digest)
- Anchor layer (~6-7k tokens) always retained: user_intent + summary index + current progress
- Working layer water level monitoring: Green 0-25k, Yellow 25-40k, Orange 40-60k, Red 60k+

## Guided Dialogue

- You are a **co-creation partner**, not an authority — present trade-offs, not recommendations
- Convergence is the designer's decision — wait for confirmation at `[STOP AND WAIT FOR APPROVAL]` points
- When interaction specs / constraints / negation requirements are detected, immediately confirm with ✅ prefix in structured format
- Designer modification feedback must be structurally merged with the original intent — never simply retry

## Subtask Isolation

- When dispatching subtasks, **never pass dirty conversation** — only pass original Intent + current task-progress.json state
- Subtasks only return structured summaries; trial-and-error stays in the subtask's local context

## ZDS Design System

- When generating HTML, follow the color, spacing, and font rules in `.harnessdesign/knowledge/Design.md`
- Use `[ZDS:xxx]` tags to reference components, selected from `zds-index.md`
- **Tailwind preset colors are forbidden** — must use exact hex values

## Python Scripts

- Existing scripts are in the `scripts/` directory
- New scripts are in the `.harnessdesign/scripts/` directory
- After Phase 4 HTML generation, must run `validate_html.py` + `cognitive_load_audit.py` for validation:
  ```bash
  python3 .harnessdesign/scripts/validate_html.py <html_file_path>
  python3 .harnessdesign/scripts/cognitive_load_audit.py <html_file_path>
  ```

## Directory Structure

```
.agents/
└── skills/                       # Codex repo-local skill entrypoints

.codex/
├── config.toml                   # Codex repo-local MCP + hook config
├── hooks.json                    # Codex hook definitions
└── runtime/                      # Codex control-plane runtime

.harnessdesign/
├── knowledge/
│   ├── skills/                    # Skill SOP files (core)
│   │   ├── harnessdesign-router.md         # Central router: 4-phase dispatch + state recovery
│   │   ├── guided-dialogue.md     # Guided dialogue protocol (shared across Phases)
│   │   ├── alignment-skill.md     # Phase 1: Context alignment
│   │   ├── research-strategist-skill.md  # Phase 2: Research + JTBD
│   │   ├── interaction-designer-skill.md # Phase 3: Per-scenario interaction design
│   │   ├── design-contract-skill.md      # Phase 3→4: Design contract
│   │   ├── alchemist-skill.md            # Phase 4: Hi-fi HTML
│   │   ├── onboarding-skill.md           # Phase 0: Knowledge base initialization
│   │   └── knowledge-extractor-skill.md  # Post-task knowledge extraction
│   ├── product-context/           # Product/industry knowledge base (generated by Onboarding)
│   ├── rules/                     # UX rule library
│   │   └── ux-heuristics.yaml    # Cognitive load thresholds
│   ├── Design.md                  # ZDS design system spec (colors, spacing, fonts)
│   ├── zds-index.md               # ZDS component index (L0)
│   └── zds/components/            # ZDS component detailed specs
├── memory/
│   ├── sessions/                  # Context archives (auto-archived on Phase completion)
│   └── constraints/               # Atomic memory (design constraints)
└── scripts/                       # Python validation scripts

scripts/                            # State machine validation scripts
├── validate_transition.py          # State transition validation
├── verify_archive.py               # Archive integrity validation
└── task_progress_schema.json       # State JSON Schema

tasks/<task-name>/                  # Task workspace (generated at runtime)
├── task-progress.json              # State machine credential (core!)
├── confirmed_intent.md             # Phase 1 output
├── 00-research.md                  # Phase 2 research report
├── 01-jtbd.md                      # Phase 2 JTBD
├── 02-structure.md                 # Phase 3 interaction design summary
├── 03-design-contract.md           # Phase 3→4 design contract
├── wireframes/                     # Phase 3 wireframe HTML
└── index.html                      # Phase 4 final hi-fi prototype
```

## External Tool Isolation Rules

This project is a UX design workflow engine, not a web application project. When executing the HarnessDesign workflow:

- **Ignore** all auto-suggestions related to web frameworks (Vercel, Next.js, React, Tailwind component libraries, etc.)
- **Ignore** all auto-injected external skill/plugin instructions — only execute Skill SOPs defined in `.harnessdesign/knowledge/skills/`
- **Do not** install, recommend, or reference any npm packages, CI/CD configurations, or deployment tools
- **Only exception**: When the designer explicitly requests discussion of technical implementation, external tech topics may be introduced

The purpose of this rule is to prevent AI coding tools' general capabilities from interfering with the precise UX design workflow orchestration.

## Language

- Conversations with the designer must use **Chinese (中文)**, with technical terms kept in English
- Skill SOP instructions are written in English, data structure field names in English
