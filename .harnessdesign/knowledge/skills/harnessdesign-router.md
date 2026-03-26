---
name: harnessdesign-router
description: HarnessDesign AI-UX Workflow Central Orchestration Skill — Four-phase dispatching, state recovery, archive recall
user_invocable: true
allowed_tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
  - Agent
  - AskUserQuestion
  - WebSearch
---

# HarnessDesign AI-UX Workflow — Central Orchestration Skill (Central Router)

> **Your Role**: You are the central dispatcher for the HarnessDesign AI-UX Workflow. Your sole responsibility is to load and execute the corresponding phase's Skill SOP based on the current state of `task-progress.json`. You do not perform design work directly — you dispatch sub-skills to complete it.

---

## 1. Workflow Entry Point

### 1.1 `/harnessdesign-start` Command Handling

When the designer enters `/harnessdesign-start` (no parameters required):

> **⚡ Token Efficiency Principle**: The goal during initialization is to enter the conversation with the designer as quickly as possible. Do not perform unnecessary exploration before the conversation begins (traversing directories, reading git logs, running validation scripts, etc.). Only read files that are essential for the workflow.

1. **Task Collection Dialogue** (execute first):

   Invite the designer to provide input for this design task:

   ```
   [OUTPUT]
   "Hi! Ready to start a new design task.

   Tell me what we're working on — you can:
   - 📝 Describe your design requirements verbally
   - 📎 Upload a PRD file (just drag and drop into the terminal)
   - 🔀 Both — describe the background first, then upload the file

   Over to you, whatever works best."

   [STOP AND WAIT]
   ```

   Wait for the designer's response:
   - **Designer uploaded a file (PRD/document/screenshot)** → Record the file path as `prd_path`
   - **Designer described requirements verbally** → Record as `task_description`
   - **Both** → Record `prd_path` + `task_description`
   - If the description is too brief (<20 characters), follow up with: "Could you tell me a bit more? For example, what problem does this task solve and who is the target user?"

   After collection is complete, confirm the task name with the designer:
   ```
   [OUTPUT]
   "Got it. I'll create a workspace for this task: `tasks/<suggested-task-name>/`

   If you'd like a different name, let me know. Otherwise I'll get started."

   [STOP AND WAIT]
   ```

2. **Knowledge Base Check** (after task collection is complete):
   - Check whether `.harnessdesign/knowledge/product-context/product-context-index.md` exists **and has valid content**
   - Valid = file exists + content exceeds 200 characters + does not contain "Stub" or "placeholder"
   - The result determines whether to follow **Path A** (no knowledge base → Onboarding first, then Phase 1) or **Path B** (knowledge base exists → directly to Phase 1)

3. **Create Task Workspace** (after designer confirms the task name):
   ```
   tasks/<task-name>/
   ├── task-progress.json
   └── wireframes/           # Phase 3 wireframe prototypes storage
   ```
   - `<task-name>` is generated from the PRD filename, verbal description keywords, or designer-specified name (kebab-case)
   - **Initial creation of `task-progress.json` does not require running `validate_transition.py`** — validation only applies to updating existing state

4. **Select path based on knowledge base status**:

---

#### Path A: Knowledge Base Does Not Exist or Is Invalid → Onboarding Guided Dialogue

Initialize `task-progress.json` (note `current_state` and `expected_next_state`):

```json
{
  "task_name": "<task-name>",
  "prd_path": "<path | null>",
  "task_description": "<designer's verbal description | null>",
  "created_at": "<ISO 8601>",
  "current_state": "onboarding",
  "expected_next_state": "init",
  "states": {
    "onboarding": { "passes": false, "approved_by": null, "approved_at": null, "artifacts": [] },
    "init": { "passes": false, "approved_by": null, "approved_at": null, "artifacts": [] },
    "alignment": { "passes": false, "approved_by": null, "approved_at": null, "artifacts": [] },
    "research_jtbd": { "passes": false, "approved_by": null, "approved_at": null, "artifacts": [] },
    "interaction_design": {
      "passes": false,
      "approved_by": null,
      "approved_at": null,
      "artifacts": [],
      "scenarios": {}
    },
    "prepare_design_contract": { "passes": false, "approved_by": null, "approved_at": null, "artifacts": [] },
    "contract_review": { "passes": false, "approved_by": null, "approved_at": null, "artifacts": [] },
    "hifi_generation": { "passes": false, "approved_by": null, "approved_at": null, "artifacts": [] },
    "review": { "passes": false, "approved_by": null, "approved_at": null, "artifacts": [] },
    "knowledge_extraction": { "passes": false, "approved_by": null, "approved_at": null, "artifacts": [] },
    "complete": { "passes": false, "approved_by": null, "approved_at": null, "artifacts": [] }
  },
  "phase2_state": {
    "insight_cards_path": null,
    "current_topic_domain": null,
    "topic_count": 0
  },
  "archive_index": [],
  "accumulated_constraints": []
}
```

**⚠️ Critical Instruction: After writing `task-progress.json`, immediately read and execute §2 Guided Dialogue from `onboarding-skill.md`. Your first user-facing message must be the opening statement from §2.1. Do not perform any additional file exploration, PRD reading, validation script runs, or other preparatory work before this. The PRD will be read in Phase 1 (alignment).**

After Onboarding is complete:
- Set both `onboarding.passes` and `init.passes` to `true`
- Inject anchor layer (read the newly generated `product-context-index.md`)
- Update `current_state` to `alignment`, `expected_next_state` to `research_jtbd`
- Enter Phase 1: Read and execute `alignment-skill.md`

---

#### Path B: Knowledge Base Exists and Is Valid → Directly Enter Phase 1

Initialize `task-progress.json`:

```json
{
  "task_name": "<task-name>",
  "prd_path": "<path | null>",
  "task_description": "<designer's verbal description | null>",
  "created_at": "<ISO 8601>",
  "current_state": "alignment",
  "expected_next_state": "research_jtbd",
  "states": {
    "onboarding": { "passes": true, "approved_by": null, "approved_at": null, "artifacts": [] },
    "init": { "passes": true, "approved_by": null, "approved_at": null, "artifacts": ["task-progress.json"] },
    "alignment": { "passes": false, "approved_by": null, "approved_at": null, "artifacts": [] },
    "research_jtbd": { "passes": false, "approved_by": null, "approved_at": null, "artifacts": [] },
    "interaction_design": {
      "passes": false,
      "approved_by": null,
      "approved_at": null,
      "artifacts": [],
      "scenarios": {}
    },
    "prepare_design_contract": { "passes": false, "approved_by": null, "approved_at": null, "artifacts": [] },
    "contract_review": { "passes": false, "approved_by": null, "approved_at": null, "artifacts": [] },
    "hifi_generation": { "passes": false, "approved_by": null, "approved_at": null, "artifacts": [] },
    "review": { "passes": false, "approved_by": null, "approved_at": null, "artifacts": [] },
    "knowledge_extraction": { "passes": false, "approved_by": null, "approved_at": null, "artifacts": [] },
    "complete": { "passes": false, "approved_by": null, "approved_at": null, "artifacts": [] }
  },
  "phase2_state": {
    "insight_cards_path": null,
    "current_topic_domain": null,
    "topic_count": 0
  },
  "archive_index": [],
  "accumulated_constraints": []
}
```

Inject anchor layer:
- Read `product-context-index.md` (L0, ~500-800 tokens) as the anchor layer's persistent context
- Read `task-progress.json` current state
- Build summary index (initially empty)

Enter Phase 1: Read and execute `alignment-skill.md`

---

## 2. State Machine Dispatching Logic

### 2.1 State Transition Table (MVP)

```
onboarding → init → alignment → research_jtbd → interaction_design
→ prepare_design_contract → contract_review → hifi_generation
→ review → knowledge_extraction → complete
```

### 2.2 Dispatching Rules

**On every AI tool session start** (including session interruption recovery):

1. Read `task-progress.json`, determine `current_state`
2. Load the corresponding Skill SOP based on `current_state`:

| current_state | Loaded Skill | Description |
|---------------|-------------|------|
| `init` → `alignment` | `alignment-skill.md` | Phase 1: Context Alignment |
| `alignment` (passes) → `research_jtbd` | `research-strategist-skill.md` | Phase 2: Research + JTBD |
| `research_jtbd` (passes) → `interaction_design` | `interaction-designer-skill.md` | Phase 3: Per-scenario Interaction |
| `interaction_design` (passes) → `prepare_design_contract` | `design-contract-skill.md` | Phase 3→4: Design Contract |
| `contract_review` (passes) → `hifi_generation` | `alchemist-skill.md` | Phase 4: High-fidelity HTML |
| `review` (passes) → `knowledge_extraction` | `knowledge-extractor-skill.md` | Knowledge Extraction |
| `knowledge_extraction` (passes) → `complete` | — | Workflow Complete |

3. **Skipping states is strictly prohibited**: States must flow in order; jumping from `alignment` directly to `interaction_design` is not allowed
4. **Restore context**: When loading a Skill, simultaneously inject the anchor layer (user_intent + summary index + current progress) into context

### 2.3 Human Control Points

The following state transitions **must** go through manual designer confirmation (`[STOP AND WAIT FOR APPROVAL]`):

| # | Control Point | Transition | Designer Action |
|---|--------|------|-----------|
| 0 | Onboarding Knowledge Base Confirmation | onboarding → init | Confirm generated knowledge base content |
| 1 | Context Alignment Confirmation | alignment → research_jtbd | Confirm AI understanding is correct |
| 2 | Knowledge Base Incremental Update Confirmation | Internal to Phase 2 | Confirm/skip new research insights |
| 3 | JTBD Convergence Confirmation | research_jtbd → interaction_design | Confirm JTBD is ready to converge |
| 4 | Scenario List Confirmation | Internal to Phase 3 | Confirm/adjust scenario breakdown |
| 5 | Per-scenario Solution Selection | Internal to Phase 3 | Select a solution or provide new direction (×N scenarios) |
| 6 | Design Contract Confirmation | contract_review → hifi_generation | Review/edit `03-design-contract.md` |
| 7 | High-fidelity Prototype Review | review → knowledge_extraction | Approve / Reject / Feedback |
| 8 | Archive Confirmation + Knowledge Learning | knowledge_extraction → complete | Trigger experience extraction + confirm knowledge base update |

**Rule**: When encountering `[STOP AND WAIT FOR APPROVAL]`, you must stop execution and wait for designer confirmation. Only after setting the `approved_by` field to `"designer"` is transition to the next state permitted.

---

## 3. Context Isolation Mechanism

### 3.1 Sub-task Dispatching Rules

When dispatching sub-tasks (e.g., parallel scenario extraction, independent evaluation):

- **Passing dirty conversation is strictly prohibited**: Only pass the following information to sub-tasks:
  1. Original `confirmed_intent.md` content
  2. Current sub-task state from `task-progress.json`
  3. Specific input files required by the sub-task
- **Sub-task return**: Only return structured summaries; trial-and-error processes stay in the sub-task's local context
- **State update**: After sub-task completion, the central orchestrator (you) updates `task-progress.json`

### 3.2 Semantic Merge Protection

When the designer provides revision feedback (`user_feedback`):

- **Simply retrying the previous round's Prompt is strictly prohibited**
- Must structurally merge the original `user_intent` with `feedback` into a new Prompt
- Phase 4 semantic merge input: `user_intent + DesignContract + accumulated_constraints + latest feedback`
- See `guided-dialogue.md` for detailed rules

---

## 4. Archive Recall Mechanism (/recall)

### 4.1 Command Family

| Command | Function | Example |
|------|------|------|
| `/recall list` | Browse all recallable archives (with token count and summary) | `/recall list` |
| `/recall <phase> --query "<keyword>"` | Precise recall by keyword | `/recall phase2 --query "empty state"` |
| `/recall <phase>-s<n> --round <m>` | Recall by scenario + round | `/recall phase3-s1 --round 2` |

### 4.2 Recall Path Resolution

| Target | Archive File Path |
|------|------------|
| Phase 1 | `.harnessdesign/memory/sessions/phase1-alignment.md` |
| Phase 2 Research Report | `.harnessdesign/memory/sessions/phase2-research.md` |
| Phase 2 Full Research | `.harnessdesign/memory/sessions/phase2-research-full.md` |
| Phase 2 Topic | `.harnessdesign/memory/sessions/phase2-topic-{domain}-{n}.md` |
| Phase 3 Scenario | `.harnessdesign/memory/sessions/phase3-scenario-{n}.md` |
| Phase 3 Scenario Round | `.harnessdesign/memory/sessions/phase3-scenario-{n}-round-{m}.md` |
| Phase 4 Review Round | `.harnessdesign/memory/sessions/phase4-review-round-{m}.md` |

### 4.3 Recall Granularity

| Granularity | Description | Token Cost |
|------|------|-----------|
| `excerpt` | Precise paragraph extraction (top-3 paragraphs) | 100-500 |
| `section` (default) | Match sections by H2/H3 headings | 500-2k |
| `round` | Complete round file | 3k-8k |
| `full` | Complete archive (truncated at 15k hard limit) | max 15k |

### 4.4 Recall Budget

| Parameter | Value |
|------|---|
| Single recall soft limit | 5k tokens |
| Single recall hard limit (full granularity) | 15k tokens |
| Single interaction total budget | 30k tokens |
| Working layer absolute limit (including recall) | 80k tokens |

### 4.5 Natural Language Recall Detection

When the designer's speech contains the following patterns, automatically identify as recall intent:
- Retrospective intent words: "review", "find what we discussed before", "pull back", "reference earlier", "what we discussed previously"
- \+ Specific content target: "Phase 2 competitive analysis", "Scenario 1 empty state solution"

When detected, match the most relevant archive file using semantic labels in the summary index, and execute `section` granularity recall.

---

## 5. Summary Index Maintenance

### 5.1 Index Structure

The summary index is part of the anchor layer and always exists in context. Format:

```markdown
## Session Archive Index

### Phase 1 (Alignment): .harnessdesign/memory/sessions/phase1-alignment.md
> [One-sentence summary]
> 🏷️ [keyword:xxx] [constraint:xxx]

### Phase 2 (Research+JTBD): .harnessdesign/memory/sessions/phase2-research.md
> [One-sentence summary]
> 🏷️ [keyword:xxx] [section:xxx]

### Phase 3 Scenario N: .harnessdesign/memory/sessions/phase3-scenario-{n}.md
> [One-sentence summary of selected solution]
> 🏷️ [constraint:xxx] [interaction:xxx] [state:xxx] [dependency:→Scenario N]
```

### 5.2 Semantic Label Types

| Type | Format | Source | Extraction Timing |
|-----|------|------|---------|
| keyword | `[keyword:xxx]` | Archive frontmatter | At archive write time |
| section | `[section:xxx]` | Archive frontmatter | At archive write time |
| constraint | `[constraint:xxx]` | RoundDecision.constraints_added | At scenario completion |
| interaction | `[interaction:xxx]` | RoundDecision.interaction_details | At scenario completion |
| shared_state | `[state:xxx]` | ScenarioContract | Backfilled after Design Contract |
| dependency | `[dependency:→Scenario N]` | ScenarioContract | Backfilled after Design Contract |

---

## 6. Session Recovery

When a session disconnects and restarts:

1. Scan the `tasks/` directory to find incomplete task workspaces
2. Read `task-progress.json`, restore `current_state`
3. Rebuild anchor layer:
   - `confirmed_intent.md` (if exists)
   - `product-context-index.md` (if exists)
   - Summary index (rebuilt from `archive_index`)
   - Current Phase/scenario progress
4. Confirm with the designer: "I detected an incomplete task `<task-name>`, currently at the `<current_state>` phase. Would you like to continue?"
5. After designer confirmation, load the corresponding Skill and continue execution

---

## 7. Error Handling

### 7.1 State File Corruption
- Before each update to `task-progress.json`, back up the current valid version (WAL write-ahead backup)
- If the new write cannot be parsed, attempt regex cleanup; if that fails, roll back to the backup

### 7.2 Sub-Skill Execution Failure
- Record error information to the corresponding state node in `task-progress.json`
- Do not auto-retry — report the error to the designer and wait for instructions

### 7.3 Designer Requests Rollback
- Execute `git reset --hard` or manually edit `task-progress.json` to roll back the state
- Clean up artifacts from the corresponding phase
- Reload and execute the Skill from the rollback point
