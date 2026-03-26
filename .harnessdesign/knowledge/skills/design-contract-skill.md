---
name: design-contract-skill
description: Phase 3→4 Transition — Extract ScenarioContracts from scenario archives, synthesize DesignContract, bidirectional completeness validation, anti-context-starvation
user_invocable: false
allowed_tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
  - Agent
  - AskUserQuestion
---

# Phase 3→4 Transition: Design Contract Generator Skill

> **Your Role**: You are a **cross-scenario information extractor**, responsible for directionally extracting navigation topology, interaction commitments, and global constraints from all Phase 3 scenario archives, then synthesizing them into a structured design contract. Your output serves as the blueprint for Phase 4 high-fidelity generation.
>
> **Why This Step Is Needed**: Phase 3's scenario-level compression (~200 tokens summary per scenario) loses cross-scenario navigation topology, specific interaction commitments, and global design constraints. The Design Contract mechanism directionally extracts this critical information before entering Phase 4, ensuring Alchemist has all the context needed to generate a cross-scenario consistent prototype.
>
> **Protocol Reference**: This Skill follows the dialogue protocol defined in `guided-dialogue.md` during the designer Review phase.

---

## 0. Internal Stage Overview

```
[Load Context] → [Concurrent Scenario Extraction ScenarioContract]
                     ↓
              [Global Contract Synthesis DesignContract]
                     ↓
              [Bidirectional Validation + GAP Annotation]
                     ↓
              [Write to 03-design-contract.md]
                     ↓
              [Summary Index Backfill]
                     ↓
              [STOP: Designer Review/Edit Contract]
                     ↓
              [Transition to hifi_generation]
```

---

## 1. Prerequisites and Context Loading

### 1.1 State Validation

```
[PREREQUISITE] Read tasks/<task-name>/task-progress.json
Assert: current_state === "prepare_design_contract"
Assert: states.interaction_design.passes === true
Assert: All scenarios have status "archived" or "skipped"
If not satisfied → Stop execution, report state inconsistency
```

### 1.2 Load Anchor Layer

```
[ACTION] Read the following files into the anchor layer (always present in context):
1. tasks/<task-name>/confirmed_intent.md (~500 tokens, Phase 1 output)
2. .harnessdesign/knowledge/product-context/product-context-index.md (L0, if exists)
3. Summary index (reconstructed from task-progress.json.archive_index)
```

### 1.3 Load Working Layer

```
[ACTION] Read the following files into the working layer:
1. tasks/<task-name>/02-structure.md (interaction plan summary table, Phase 3 output)
2. scenarios field from task-progress.json (get scenario list and archive paths)
```

---

## 2. Concurrent Scenario Extraction — ScenarioContract

### 2.1 Extraction Process

For each scenario with `status === "archived"` in `task-progress.json.states.interaction_design.scenarios`, perform extraction:

```
[ACTION] For each completed scenario, read:
1. .harnessdesign/memory/sessions/phase3-scenario-{n}.md (scenario archive, containing RoundDecision summary)
2. .harnessdesign/memory/sessions/phase3-scenario-{n}-round-{m}.md (per-round Recall Buffer, as needed)

Extract ScenarioContract from the archive.
```

> **Parallel Capability**: Extraction of N scenarios is mutually independent and can leverage AI tool Agent parallelism for concurrent execution. Each scenario independently produces a ScenarioContract, following the Assembler Pattern principle.

### 2.2 ScenarioContract Structure

Extract the following structure for each scenario:

```yaml
# ScenarioContract (design contract for a single scenario)

scenario_id: "scenario-1"
scenario_name: "Pre-meeting Preparation"
selected_option_summary: "Timeline view with drag-to-reorder agenda items"  # ~100 tokens

# Entry Conditions
entry_conditions:
  - source_scenario: "scenario-0"       # or "external" (first scenario)
    trigger: "User clicks 'Prepare Meeting'"
    shared_state_changes:
      - "current_flow → prep"

# Exit Actions
exit_actions:
  - target_scenario: "scenario-2"
    trigger: "User clicks 'Finish Preparation'"
    shared_state_changes:
      - "meeting_status → prepared"

# Shared State Dependencies
shared_state_dependencies:
  consumed_from:
    - "current_user (from login flow)"
    - "meeting_info (from meeting list)"
  produced_for:
    - "agenda_items (consumed by scenario 2)"
    - "meeting_status (checked by scenario 3)"

# Interaction Commitments (extracted from RoundDecision.interaction_details, max 5 items)
interaction_commitments:
  - "List items support drag-to-reorder; a dashed placeholder frame appears during drag"
  - "Empty state uses illustration + guidance copy + CTA button"
  - "Timeline view supports collapse/expand"
  # ... max 5 most critical interaction decisions

# Global Constraints (extracted from RoundDecision.constraints_added)
global_constraints:
  - "First screen has no more than 5 interaction modules"
  - "No plain-text empty states"

# Edge Cases Checklist
edge_cases_to_handle:
  - "0 agenda items → empty state"
  - "Insufficient permissions → error prompt + redirect"
  - "Network interruption → retry button"
```

### 2.3 Extraction Quality Check

Perform the following checks on each ScenarioContract:

```
[CHECK] ScenarioContract completeness check:
- [ ] entry_conditions has at least 1 entry (first scenario may be "external")
- [ ] exit_actions has at least 1 entry (final scenario may be "task_complete")
- [ ] interaction_commitments ≤ 5 items, each sourced from RoundDecision.interaction_details
- [ ] edge_cases_to_handle includes at minimum: empty state, error state
- [ ] selected_option_summary does not exceed 100 tokens
```

Missing items are annotated with `[⚠️ GAP]` and supplemented with reasonable inferences (marked `[auto-inferred]`).

---

## 3. Global Contract Synthesis — DesignContract

### 3.1 Synthesis Inputs

```
[ACTION] Synthesize the following into a DesignContract:
1. All ScenarioContracts (N total)
2. 02-structure.md (interaction plan summary table)
3. confirmed_intent.md (core problem, constraints, success criteria)
```

### 3.2 DesignContract Structure

```yaml
# DesignContract (complete design contract for Phase 4 high-fidelity generation)

# Navigation Topology Map
navigation_topology:
  entry_point: "scenario-1"             # First scenario the user enters
  adjacency:                            # Inter-scenario connections
    scenario-1: ["scenario-2"]
    scenario-2: ["scenario-3", "scenario-1"]
    scenario-3: []                      # Terminal scenario

# Shared State Model
shared_state_model:
  - name: "current_user"
    type: "User object"
    produced_by: ["auth_flow"]
    consumed_by: ["scenario-1", "scenario-2", "scenario-3"]
  - name: "agenda_items"
    type: "Agenda[]"
    produced_by: ["scenario-1"]
    consumed_by: ["scenario-2"]

# Global Design Constraints (deduplicated and merged from all ScenarioContracts)
global_constraints:
  - "First screen interaction modules ≤ 5"
  - "No plain-text empty states"
  - "Animation duration ≤ 300ms"
  # ... complete deduplicated constraint list

# Visual Consistency Rules (derived from constraints)
visual_consistency_rules:
  - "All scenarios use a unified sidebar navigation"
  - "Button border-radius uniformly 8px"
  - "Information density control: ≤ 12 interactive elements per screen"
  # ... derived from confirmed_intent and constraints

# Per-Scenario Contracts
scenarios:
  - scenario_id: "scenario-1"
    scenario_name: "Pre-meeting Preparation"
    selected_option_summary: "..."
    entry_conditions: [...]
    exit_actions: [...]
    interaction_commitments: [...]
    edge_cases_to_handle: [...]
  # ... complete ScenarioContract list

# Aggregated Edge Cases Checklist
edge_cases_to_handle:
  - category: "Empty State"
    scenarios: ["scenario-1", "scenario-3"]
    pattern: "[ZDS:zds-empty-state] illustration + guidance copy"
  - category: "Network Error"
    scenarios: ["all"]
    pattern: "Toast notification + retry button"
  - category: "Missing Permissions"
    scenarios: ["scenario-1"]
    pattern: "Error page + redirect suggestion"
```

### 3.3 Constraint Deduplication and Merge Rules

```
[RULE] When merging global_constraints:
1. Exact match → deduplicate and keep one
2. Same-dimension conflict (e.g., "≤ 5 modules" vs "≤ 7 modules") → keep the stricter constraint, annotate source scenario
3. Implicit duplication (e.g., "no popups" and "avoid modals") → unify into one entry, note coverage scope
```

---

## 4. Bidirectional Validation

### 4.1 Forward Validation (Commitment Completeness)

```
[CHECK] For each ScenarioContract's interaction_commitments:
- Trace back to original RoundDecision in phase3-scenario-{n}.md archive
- Confirm each commitment has supporting RoundDecision.interaction_details
- Unsupported commitments → annotate [⚠️ GAP: no original basis]
```

### 4.2 Reverse Validation (Structural Completeness)

```
[CHECK] Structural completeness check:
- [ ] Each scenario has at least 1 entry_condition (first scenario may be external)
- [ ] Each scenario has at least 1 exit_action (terminal scenario may be task_complete)
- [ ] navigation_topology.adjacency has no isolated scenarios (all scenarios reachable)
- [ ] navigation_topology has no dead ends (except explicitly terminal scenarios)
- [ ] Each state in shared_state_model has non-empty produced_by and consumed_by
- [ ] shared_state_model has no unconsumed states (produced but not consumed → annotate [⚠️ GAP])
- [ ] shared_state_model has no unproduced dependencies (consumed but not produced → annotate [⚠️ GAP])
```

### 4.3 GAP Handling

- All `[⚠️ GAP]` items are highlighted in the output
- AI provides reasonable inferences for each GAP, marked `[auto-inferred]`
- Designer confirms/modifies/deletes each during Review

---

## 5. Output and Write

### 5.1 Write 03-design-contract.md

```
[ACTION] Write to tasks/<task-name>/03-design-contract.md

Document format is plain Markdown (designer can edit directly in IDE), structured as follows:
```

```markdown
# Design Contract

> This document is the blueprint for Phase 4 high-fidelity generation. Modifying this file will directly affect the generated prototype.
> Items annotated with [⚠️ GAP] require designer confirmation. Items annotated with [auto-inferred] were supplemented by AI inference.

## Navigation Topology

**Entry Scenario**: [scenario name]

**Inter-Scenario Connections**:
| From | To | Trigger Condition |
|------|----|-------------------|
| Scenario 1 | Scenario 2 | [trigger description] |
| ... | ... | ... |

## Shared State Model

| State Name | Type | Producing Scenario | Consuming Scenario |
|-----------|------|-------------------|-------------------|
| current_user | User | auth_flow | Scenario 1, 2, 3 |
| ... | ... | ... | ... |

## Global Design Constraints

1. [Constraint content] (Source: Scenario N)
2. [Constraint content] (Source: Scenario M, N)
...

## Visual Consistency Rules

1. [Rule content]
2. [Rule content]
...

## Per-Scenario Contracts

### Scenario 1: [Scenario Name]

**Selected Option**: [option summary]

**Entry Conditions**:
- From [scenario/external], trigger: [condition]

**Exit Actions**:
- Navigate to [scenario], trigger: [condition]

**Interaction Commitments**:
1. [specific interaction decision]
2. [specific interaction decision]
... (max 5 items)

**Edge Case Handling**:
- [edge case] → [handling approach]
...

### Scenario 2: [Scenario Name]
...

## Aggregated Edge Cases Checklist

| Category | Affected Scenarios | Unified Handling Pattern |
|----------|-------------------|------------------------|
| Empty State | Scenario 1, 3 | [ZDS:zds-empty-state] illustration + guidance copy |
| Network Error | All | Toast notification + retry button |
| ... | ... | ... |

## GAP Checklist (Requires Designer Confirmation)

- [ ] [⚠️ GAP] [GAP description] ([auto-inferred]: [AI inference content])
...
```

### 5.2 Summary Index Backfill

```
[ACTION] Extract semantic tags from all ScenarioContracts and backfill into the summary index:

From shared_state_dependencies extract:
- [state:xxx] tags (e.g., [state:current_user], [state:agenda_items])

From exit_actions extract:
- [dependency:→scenarioN] tags (e.g., [dependency:→scenario2], [dependency:→scenario3])

Backfill into existing scenario entries in the anchor layer summary index.
This step completes the cross-scenario dimension tags that could not be deterministically extracted at scenario completion time.
```

---

## 6. Update task-progress.json

```
[ACTION] Use Edit tool to update task-progress.json:

1. states.prepare_design_contract.passes = true
2. states.prepare_design_contract.approved_by = null (pending designer confirmation)
3. states.prepare_design_contract.artifacts = ["03-design-contract.md"]
4. current_state = "contract_review"

Append to archive_index:
{
  "file": "03-design-contract.md",
  "type": "design_contract",
  "phase": "3→4",
  "digest": "Design contract: navigation topology, interaction commitments, and global constraints for N scenarios"
}
```

---

## 7. Designer Review

### 7.1 Present the Contract

```
[OUTPUT]

"The design contract has been generated and saved to 03-design-contract.md.

**Overview**:
- {N} scenarios in total, entry scenario: {scenario name}
- Shared state: {M} cross-scenario state variables
- Global constraints: {K} items
- Interaction commitments: {J} items total (across all scenarios)

**GAPs Requiring Attention**:
{List all [⚠️ GAP] items with [auto-inferred] content}

Please open 03-design-contract.md in your IDE for Review.
You can edit the file content directly, or share your revision feedback in the conversation."
```

### 7.2 Wait for Confirmation

```
[STOP AND WAIT FOR APPROVAL]

Wait for the designer's confirmation on the design contract.

Possible responses:
- Approve → §7.3 Transition
- Revision feedback → Follow guided-dialogue.md §3 semantic merge:
  Merge designer feedback with current contract, update 03-design-contract.md
  Never simply regenerate from scratch
- Direct file edit → Re-read the file to confirm changes, update summary index
```

### 7.3 Post-Confirmation Transition

```
[ACTION] After designer confirms:

1. Update task-progress.json:
   - states.contract_review.passes = true
   - states.contract_review.approved_by = "designer"
   - states.contract_review.approved_at = "<ISO 8601>"
   - current_state = "hifi_generation"

2. Output transition prompt:
```

```
[OUTPUT]

"Design contract confirmed.

Proceeding to → Phase 4 High-Fidelity Prototype Generation.
Alchemist will use the design contract as its blueprint, integrate ZDS design specifications,
and generate a complete high-fidelity interactive HTML covering all {N} interaction scenarios.

[Continue]"
```

---

## Appendix A: Token Budget Analysis

### Extraction Stage Working Layer

| Component | Token Budget | Notes |
|-----------|-------------|-------|
| Anchor layer | ~5-6k | confirmed_intent + L0 + summary index |
| 02-structure.md | ~1-2k | Plan summary table |
| Single scenario archive (during extraction) | ~3-5k | phase3-scenario-{n}.md |
| ScenarioContract output | ~500 | Single scenario extraction result |
| **Single scenario extraction peak** | **~10-13k** | |

### Synthesis Stage Working Layer

| Component | Token Budget | Notes |
|-----------|-------------|-------|
| Anchor layer | ~5-6k | Always resident |
| All ScenarioContracts | ~500 × N | Extraction results for N scenarios |
| 02-structure.md | ~1-2k | Reference |
| DesignContract output | ~3-5k | Final contract |
| **Synthesis peak** | **~12-18k** | Depends on number of scenarios |

---

## Appendix B: Error Handling

### B.1 Missing Scenario Archive File

```
→ Check task-progress.json.states.interaction_design.scenarios[n].archived_to
→ If path is invalid → report: "Scenario {n} archive file is missing, please verify Phase 3 archiving completed"
→ Can perform degraded extraction from that scenario's entry in 02-structure.md (reduced information, annotate [⚠️ degraded extraction])
```

### B.2 Missing or Incomplete RoundDecision

```
→ Extract from the "RoundDecision Summary" section in the scenario archive
→ If summary section is also missing → search round-by-round from round Recall Buffer
→ Still missing → annotate that scenario's interaction_commitments with [⚠️ GAP: RoundDecision unavailable]
```

### B.3 Skipped Scenarios

```
→ Scenarios with status === "skipped" do not get ScenarioContract extraction
→ Annotate the scenario as [skipped] in the DesignContract
→ If other scenarios have entry/exit dependencies on the skipped scenario → annotate [⚠️ GAP: skipped scenario has dependencies]
```

### B.4 03-design-contract.md Write Failure

```
→ Output the DesignContract content into the conversation
→ Ask the designer to manually save as 03-design-contract.md
→ Retry the write
```
