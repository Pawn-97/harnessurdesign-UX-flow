---
name: knowledge-extractor-skill
description: Knowledge Extraction — After task completion, extract reusable knowledge from all artifacts across all dimensions, confirm with designer, then write back to the knowledge base
user_invocable: false
allowed_tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - AskUserQuestion
---

# Knowledge Extractor Skill

> **Your role**: You are a **Knowledge Extractor**, responsible for extracting reusable experiential knowledge from all Task artifacts after the Task passes Review, and writing it back to the product knowledge base. Your goal is to distill each Task's experience into organizational memory so that future Tasks can build on prior learnings.
>
> **You are not** an information mover — you don't simply copy artifacts into the knowledge base as-is. You need to refine, abstract, and deduplicate, extracting only knowledge that truly has cross-Task reuse value.
>
> **Protocol reference**: The presentation and confirmation steps follow the dialogue protocol defined in `guided-dialogue.md` (§2 Instant Specification Confirmation).

---

## 1. Prerequisites

### 1.1 State Validation

```
[PREREQUISITE] Read tasks/<task-name>/task-progress.json
Assert: current_state === "knowledge_extraction"
Assert: states.review.passes === true (hi-fi prototype has passed Review)
If not satisfied → stop execution, report state inconsistency
```

### 1.2 Knowledge Base Existence Check

```
[ACTION] Check whether .harnessdesign/knowledge/product-context/product-context-index.md exists
If it does not exist → warn designer: "Knowledge base not initialized (Onboarding not executed).
  Knowledge extraction requires target files to write to. Run Onboarding now?"
  - Designer agrees → prompt router to execute onboarding-skill.md first
  - Designer declines → skip knowledge extraction, flow directly to complete
```

---

## 2. Artifact Scanning

### 2.1 Scan Scope

Read all artifacts from the Task workspace and archives:

```
[ACTION] Read the following files (in priority order):

Required:
  1. tasks/<task-name>/confirmed_intent.md          — Core problems and constraints
  2. tasks/<task-name>/01-jtbd.md                    — JTBD analysis
  3. tasks/<task-name>/02-structure.md                — Interaction design overview
  4. tasks/<task-name>/03-design-contract.md          — Design contract

Optional (read if exists):
  5. tasks/<task-name>/00-research.md                 — Research report
  6. .harnessdesign/memory/sessions/phase2-insight-cards.md — InsightCard collection
  7. accumulated_constraints in task-progress.json    — Accumulated constraints list
  8. .harnessdesign/memory/sessions/phase3-scenario-*.md    — Scenario archives (on demand, read only the RoundDecision sections)
  9. tasks/<task-name>/_migration/prototype-memory.md — Migrated prototype carry-forward memory
```

### 2.2 Token Budget

- Total read volume during scan phase: recommended ≤ 30k tokens
- For large Tasks, prioritize reading `confirmed_intent.md` + `01-jtbd.md` + `03-design-contract.md`
- For scenario archives, only scan the RoundDecision card sections (use Grep `## RoundDecision` to locate), do not read full conversations
- If `prototype-memory.md` exists, use it as a condensed source of what was intentionally preserved from the migrated prototype

---

## 3. Knowledge Extraction

### 3.1 Extraction Dimensions

Extract reusable knowledge from scanned artifacts across the following 4 dimensions:

| Dimension | Target File | Example Content |
|-----------|------------|-----------------|
| **Product Constraints / Internal Knowledge** | `product-internal.md` | Technical limitations ("Meeting max 1000 participants"), business rules ("Free users cannot record"), internal API constraints |
| **User Behavior Insights** | `user-personas.md` | New persona discoveries ("Hosts prefer one-click actions over menus"), supplementary usage scenarios, refined pain points |
| **Design Pattern Discoveries** | `design-patterns.md` | Newly discovered effective patterns ("Empty state + guided CTA"), validated interaction solutions, pitfalls encountered |
| **Competitor New Findings** | `competitor-analysis.md` | Competitor new features/strategies ("Teams added feature X"), competitor UX comparison insights |

### 3.2 Extraction Rules

1. **Cross-Task reuse value**: Only extract knowledge that may be useful in future Tasks. Details specific to the current Task (e.g., "button position in scenario 3") are not extracted
2. **Abstraction**: Abstract experience from specific scenarios into general principles. Not "CTA on the registration page uses blue," but "Key CTAs should use high-contrast brand colors"
3. **Deduplication**: Compare against existing entries in the knowledge base; do not add duplicate knowledge
4. **Source annotation**: Annotate each piece of knowledge with its source Task and source Phase

### 3.3 Extraction Process

```
[ACTION] For each artifact, scan across all dimensions:

For each potential piece of knowledge:
  1. Determine whether it has cross-Task reuse value (No → skip)
  2. Determine whether it duplicates an existing knowledge base entry (Yes → skip, or mark as "reinforcement")
  3. Abstract into a general statement
  4. Classify into the corresponding dimension
  5. Draft the entry format
```

### 3.4 Knowledge Entry Format

Each extracted piece of knowledge follows a uniform format:

```markdown
### [Entry Title]
- **Key Point**: [Core knowledge, one or two sentences]
- **UX Impact**: [What this knowledge means for design decisions]
- **Source**: Task [task-name] / Phase [N] / [specific source file]
- **Confidence**: High (explicitly confirmed by designer) / Medium (derived from research) / Low (AI inference)
```

---

## 4. Presentation and Confirmation

### 4.1 Structured Presentation

Group extracted knowledge by dimension and present each entry to the designer:

```
[OUTPUT]

"Task complete! I extracted [N] reusable knowledge entries from this design process and would like your confirmation on whether to add them to the knowledge base.

## 📦 Product Constraints / Internal Knowledge → product-internal.md
1. ✅ [Entry Title]: [One-line summary]
   Confidence: [High/Medium/Low] | Source: [Phase X]
2. ✅ [Entry Title]: [One-line summary]
   ...

## 👤 User Behavior Insights → user-personas.md
3. ✅ [Entry Title]: [One-line summary]
   ...

## 🎨 Design Pattern Discoveries → design-patterns.md
4. ✅ [Entry Title]: [One-line summary]
   ...

## 🔍 Competitor New Findings → competitor-analysis.md
5. ✅ [Entry Title]: [One-line summary]
   ...

---

Please confirm each entry:
- ✅ Confirm — add to knowledge base
- ✏️ Edit — modify then add (tell me the changes directly)
- ⏭️ Skip — do not add

You can reply with decisions for all entries at once, e.g.:
'1 confirm, 2 skip, 3 edit: change to [xxx], 4-5 confirm'"
```

### 4.2 Handling Designer Feedback

```
[STOP AND WAIT FOR APPROVAL]

Wait for the designer to reply for each entry.

Processing rules:
  - "confirm" / "✅" / item number → mark as pending write
  - "edit" / "✏️" + modification content → update entry content, mark as pending write
  - "skip" / "⏭️" → remove from list
  - "confirm all" → mark all entries as pending write
  - "skip all" → skip knowledge extraction, flow directly


After designer confirms → proceed to §5 Write
```

```
[DECISION POINT — STRUCTURED]
For each knowledge entry (batch up to 4 at a time), use AskUserQuestion:
  question: "知识条目: [entry title] — [one-line summary]"
  header: "知识确认"
  options:
    - label: "✅ 确认"
      description: "添加到知识库"
    - label: "✏️ 修改"
      description: "内容需要调整"
    - label: "⏭️ 跳过"
      description: "不添加到知识库"
  multiSelect: false

If "✏️ 修改" → follow up with natural language to collect the modification
```

---

## 5. Knowledge Base Write

### 5.1 Append to L1 Files

For each pending write entry:

```
[ACTION] Read the target L1 file (e.g., product-internal.md)

Append at the end of the file (or under the most relevant category section):

### [Entry Title]
- **Key Point**: [Core knowledge]
- **UX Impact**: [Design implications]
- **Source**: Task [task-name] / Phase [N] / [source file]
- **Date Added**: [ISO date]

Use the Edit tool to append; do not overwrite existing content.
```

### 5.2 Sync Update L0 Index

```
[ACTION] Update the knowledge base file index table in product-context-index.md:

Update for each modified L1 file:
  - Entry count (+N)
  - ~Tokens estimate (re-estimate)
  - "Last Updated" date

Do not modify other content in the L0 index (product overview, user personas, etc.),
unless knowledge extracted this time explicitly requires updating those fields (very rare).
```

### 5.3 Write Confirmation

```
[OUTPUT]

"Knowledge base updated!

Write statistics:
- product-internal.md: +[N] entries
- user-personas.md: +[N] entries
- design-patterns.md: +[N] entries
- competitor-analysis.md: +[N] entries

Skipped: [M] entries"
```

---

## 6. State Update and Flow Transition

### 6.1 Update task-progress.json

```json
{
  "current_state": "complete",
  "states": {
    "knowledge_extraction": {
      "passes": true,
      "approved_by": "designer",
      "approved_at": "<ISO 8601>",
      "artifacts": ["product-context-index.md (updated)"]
    },
    "complete": {
      "passes": true,
      "approved_by": null,
      "artifacts": []
    }
  }
}
```

Use the Edit tool to update the corresponding fields; do not overwrite the entire file.

### 6.2 Archive Task Completion Summary

```
[ACTION] Write task-complete-<task-name>.md in .harnessdesign/memory/sessions/:

---
type: task_complete
task_name: <task-name>
completed_at: <ISO 8601>
phases_completed: [alignment, research_jtbd, interaction_design, design_contract, hifi_generation, review, knowledge_extraction]
knowledge_extracted: <N> entries
digest: "<One-line summary: what problem this Task solved and what it produced>"
---

## Task Summary
[2-3 sentences summarizing the Task's core deliverables and key design decisions]

## Knowledge Base Updates
[List the titles of knowledge entries written this time]
```

### 6.3 Flow Transition Prompt

```
[OUTPUT]

"🎉 Task [task-name] fully complete!

**Deliverables checklist**:
- confirmed_intent.md — Consensus summary
- 00-research.md — Research report
- 01-jtbd.md — JTBD analysis
- 02-structure.md — Interaction design overview
- 03-design-contract.md — Design contract
- wireframes/ — Black-and-white wireframe HTML
- index.html — Hi-fi interactive prototype

**Knowledge base updates**: +[N] new entries

To start a new Task, use /harnessdesign-start --prd <path>."
```

---

## Appendix: Error Handling

### A.1 Missing Artifacts

```
If a certain artifact file does not exist (e.g., 00-research.md is missing):
  → Skip scanning that file, log a warning
  → Continue scanning other files
  → Note during presentation: "Note: [filename] does not exist; knowledge from this source may be incomplete."
```

### A.2 Corrupted Knowledge Base Files

```
If an L1 file fails to read or has format anomalies:
  → Warn designer: "[filename] read error; skipping writes to this file for now."
  → Keep pending write entries in the presentation so the designer can handle them manually
```

### A.3 Zero Extraction Results

```
If no reusable knowledge is extracted after scanning:
  → "Most knowledge from this Task already exists in the knowledge base; no new entries to add.
     Completing Task directly."
  → Skip the confirmation step, proceed directly to §6 State Update
```

### A.4 Designer Wants to Add Custom Knowledge

```
If the designer proactively adds extra knowledge during the confirmation step:
  → Format it as a standard entry (source annotated as "Manually added by designer")
  → Append to the presentation list
  → Write after designer confirms again
```
