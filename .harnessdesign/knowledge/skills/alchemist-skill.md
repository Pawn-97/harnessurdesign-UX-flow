---
name: alchemist-skill
description: Phase 4 Hi-Fi Generation — Integrates ZDS specifications based on DesignContract to generate a complete, interactive HTML prototype with cross-scenario consistency
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

# Phase 4: Hi-Fi Prototype Generation Skill (Alchemist)

> **Your Role**: You are the **Visual Alchemist**, responsible for transforming the Design Contract into a production-grade, high-fidelity interactive HTML prototype. You strictly follow ZDS design specifications and generate a complete single-page application covering all interaction scenarios.
>
> **You are not** a divergent explorer — the Design Contract is your blueprint, and your responsibility is faithful implementation.
>
> **Protocol Reference**: The Review loop follows the dialogue protocol defined in `guided-dialogue.md`.
>
> **Key Mechanisms**:
> - **DesignContract-Driven**: Uses the contract as a blueprint, ~3-5k tokens core input
> - **ZDS Strict Compliance**: Colors/spacing/fonts strictly use exact values defined in `Design.md`
> - **Self-Repair Loop**: Python validation + error reflection prompt + max 3 retries
> - **Review Feedback Boundary Compression**: `accumulated_constraints` append-only constraint list prevents regression

---

## 0. Internal Phase Overview

```
[Load Context + ZDS Specs] → [HTML Generation]
                              ↓
                        [Auto-Validation Loop]  ←── Max 3 retries
                              ↓ (pass)
                        [STOP: Designer Review]
                              ↓
                  ┌── Approve → [Transition to knowledge_extraction]
                  ├── Feedback → [Extract Constraints + Patch HTML + Archive Feedback]
                  │                    ↓
                  │              [Back to Auto-Validation]
                  └── Reject → [Designer Clarifies Direction → Regenerate]
```

---

## 1. Prerequisites and Context Loading

### 1.1 State Validation

```
[PREREQUISITE] Read tasks/<task-name>/task-progress.json
Assert: current_state === "hifi_generation"
Assert: states.contract_review.passes === true
If not satisfied → Stop execution, report state inconsistency
```

### 1.2 Load Anchor Layer

```
[ACTION] Read the following files into the anchor layer (always present in context):
1. tasks/<task-name>/confirmed_intent.md (~500 tokens, Phase 1 output)
2. .harnessdesign/knowledge/product-context/product-context-index.md (L0, if exists)
3. Summary index (rebuilt from task-progress.json.archive_index, with semantic tags)
```

### 1.3 Load Working Layer

```
[ACTION] Read the following files into the working layer:
1. tasks/<task-name>/03-design-contract.md (~3-5k tokens, core blueprint)
2. task-progress.json.accumulated_constraints (initially an empty array)
```

### 1.4 Load ZDS Specifications

```
[ACTION] Read ZDS design specifications:
1. .harnessdesign/knowledge/Design.md (global visual rules: colors, spacing, fonts, border-radius, shadows, layout)
2. .harnessdesign/knowledge/zds-index.md (component index L0)
3. Based on [ZDS:xxx] components referenced in 03-design-contract.md, read as needed:
   .harnessdesign/knowledge/zds/components/<component-name>.md (component detailed spec L2)
```

---

## 2. HTML Generation

### 2.1 HTML Template Structure

Generate a complete single-file `tasks/<task-name>/index.html` with the following structure:

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>[Task Name] - HarnessDesign AI-UX Prototype</title>

  <!-- SF Pro 字体（Prism 设计系统标准字体） -->
  <!-- SF Pro 为 Apple 系统字体，通过 system font stack 引用 -->

  <!-- Tailwind CDN（仅用 layout utility，颜色用 CSS 变量） -->
  <script src="https://cdn.tailwindcss.com"></script>

  <style>
    /* ===== Prism Design System CSS 变量声明（必须） ===== */
    :root {
      /* Background */
      --background\/bg-default: #FFFFFF;
      --background\/bg-darker-neutral: #F1F4F6;

      /* Fill */
      --fill\/fill-global-primary: #0D6BDE;
      --fill\/fill-primary: #0D6BDE;
      --fill\/fill-default: #FFFFFF;
      --fill\/fill-elevated-strongest: #FFFFFF;
      --fill\/fill-elevated-strong: rgba(255,255,255,0.8);
      --fill\/fill-subtle-neutral: #F1F4F6;
      --fill\/fill-subtler-neutral: #F7F9FA;
      --fill\/fill-subtler-primary: #F2F8FF;
      --fill\/fill-contrary-subtler-transparent: rgba(0,0,0,0.04);

      /* Text */
      --text\/text-stronger-neutral: #222325;
      --text\/text-neutral: #686F79;
      --text\/text-primary: #0D6BDE;
      --text\/text-strong-primary: #2057B1;
      --inverse\/inverse-global-default: #FFFFFF;

      /* Border */
      --border\/border-subtle-neutral: #DFE3E8;
      --border\/border-strong-neutral: #555B62;
      --border\/border-subtle-primary: #A8CCF8;
      --component\/input\/input-border: #C1C6CE;

      /* Semantic — Error/Warning/Success */
      --fill\/fill-error: #DA1639;
      --fill\/fill-success: #247F40;
      --fill\/fill-warning: #B36200;

      /* Shadow */
      --underlay\/dropshadow: rgba(0,0,0,0.08);

      /* Font */
      --font\/font-family: 'SF Pro', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
      --font\/font-weight-regular: 400;
      --font\/font-weight-medium: 500;
      --font\/font-weight-semibold: 590;
      --font\/font-weight-bold: 700;
      --font\/font-letterSpacing-14: -0.15px;
      --font\/font-letterSpacing-16: -0.31px;
      --font\/font-letterSpacing-20: -0.45px;
    }

    /* ===== 全局样式 ===== */
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: var(--font\/font-family);
      color: var(--text\/text-stronger-neutral);
      background: var(--background\/bg-default);
      font-size: 14px;
      line-height: 18px;
      letter-spacing: var(--font\/font-letterSpacing-14);
    }

    /* ===== Prism 组件样式（按 Design.md 规范） ===== */
    /* 所有颜色使用 CSS 变量，不使用 Tailwind 预设色板 */
    /* 间距使用 4px 基准网格：2, 4, 6, 8, 12, 14, 16, 24, 32px */

    /* 场景容器 */
    .scenario-container { display: none; }
    .scenario-container.active { display: block; }
  </style>
</head>
<body>
  <!-- ===== 场景导航（基于 navigation_topology） ===== -->

  <!-- 场景 1 -->
  <div id="scenario-1" class="scenario-container active">
    <!-- 基于 ScenarioContract 的交互承诺实现 -->
  </div>

  <!-- 场景 2 -->
  <div id="scenario-2" class="scenario-container">
    <!-- ... -->
  </div>

  <!-- ===== 跨场景导航 JS ===== -->
  <script>
    function navigateToScenario(scenarioId) {
      document.querySelectorAll('.scenario-container').forEach(el => {
        el.classList.remove('active');
      });
      const target = document.getElementById(scenarioId);
      if (target) {
        target.classList.add('active');
        window.scrollTo(0, 0);
      }
    }
  </script>
</body>
</html>
```

### 2.2 Prism Compliance Rules (Must Be Strictly Followed)

**Colors**:
- **Prohibited**: Tailwind preset color palette (e.g., `blue-500`, `gray-200`)
- **Prohibited**: Custom-invented color values
- **Required**: Use semantic CSS variables from Design.md Section 2.1
- CSS variable references preferred: `color: var(--text/text-stronger-neutral)` or `bg-[var(--fill/fill-global-primary)]`
- Fallback to exact hex values only when CSS variables are unavailable

**Spacing**:
- Based on 4px base grid: 2px, 4px, 6px, 8px, 12px, 14px, 16px, 24px, 32px
- Tailwind arbitrary value syntax: `p-[6px]`, `p-[12px]`, `p-[14px]`, `gap-[8px]`, etc.
- Refer to Design.md Section 2.3 for component-specific spacing values

**Fonts**:
- Font family: SF Pro (referenced via `var(--font/font-family)`)
- Font scale strictly per Design.md Section 2.2: 20px (title) / 14px (body) / 14px (paragraph)
- Font weights: Bold(700) / Semibold(590) / Medium(500) / Regular(400)
- Letter spacing: 14px → `-0.15px`, 16px → `-0.31px`, 20px → `-0.45px`

**Border Radius**: Per Design.md Section 2.4 — Dialog 32px, Notification 16px, Button/Input 12px, Pill 999px, Avatar 99px

**Shadows**: dropShadow-md (Notification/Dialog), dropShadow-sm (Segmented control)

**Layout** (Admin Portal):
- Viewport 1920x1080px
- Top Bar 64px
- 1st Nav 280px (expanded) / 56px (collapsed)
- 2nd Nav 220px
- Content area margin 32px
- See Design.md Section 10 for details

**Interactions** (5 states):
- Default / Hover / Pressed / Focused / Disabled
- Focus state: `var(--color/border/brand)` focus ring
- Disabled state: `opacity-[0.4-0.5] pointer-events-none`

### 2.3 Generation Principles

1. **DesignContract-Driven**: Each scenario's HTML implementation must cover all `interaction_commitments` from the corresponding ScenarioContract
2. **Navigation Topology Implementation**: Cross-scenario navigation strictly follows `navigation_topology.adjacency`
3. **Shared State Simulation**: Use JS variables to simulate states defined in `shared_state_model`
4. **Edge Case Handling**: Every `edge_cases_to_handle` listed in the DesignContract must have a corresponding HTML representation
5. **Complete Interaction States**: Every interactive element must cover hover, focus, disabled, and loading states
6. **Component References**: Prioritize component styles corresponding to `[ZDS:xxx]` tags (obtained from L2 component specs)
7. **Empty States Must Be Handled**: Every list/table uses the `[ZDS:zds-empty-state]` pattern

### 2.4 Write File

```
[ACTION] Use the Write tool to write to tasks/<task-name>/index.html
Ensure the file is a complete, runnable HTML file (can be previewed by opening directly in a browser)
```

---

## 3. Auto-Validation Loop

### 3.1 Validation Execution

```
[ACTION] Run validation scripts:

⚠️ Validation scripts pending Phase 6 implementation. Execute the following alternative validation for MVP:

Alternative Validation Checklist (manual check):
1. HTML syntax correctness — Is the file complete and renderable?
2. ZDS color compliance — Were Tailwind preset colors or custom-invented color values used?
3. Spacing compliance — Were non-4px grid spacing values used?
4. Scenario completeness — Do all scenario containers exist?
5. Navigation usability — Does navigateToScenario() cover all scenario connections?
6. Empty states — Do lists/tables have empty state handling?

TODO (activate in Phase 6):
- python3 .harnessdesign/scripts/validate_html.py tasks/<task-name>/index.html
- python3 .harnessdesign/scripts/cognitive_load_audit.py tasks/<task-name>/index.html
```

### 3.2 Self-Repair Loop

```
[RULE] Max Retries = 3

If validation fails:
1. Convert error messages into a reflection prompt:
   "Validation found the following issues: [error list]. Please analyze the causes and fix them."
2. Use the Edit tool to perform targeted fixes on index.html (do not rewrite the entire file)
3. Re-run validation
4. Repeat until passed or Max Retries reached

If Max Retries reached and still failing:
→ Report remaining issues to the designer:
  "After 3 repair attempts, auto-validation still has these unresolved issues: [issue list]
   These issues do not affect the prototype's core interactions but may have detail deviations.
   Continue to Review?"
```

---

## 4. State Update (After Validation)

```
[ACTION] After validation passes (or designer confirms to continue), update task-progress.json:

1. states.hifi_generation.passes = true
2. states.hifi_generation.artifacts = ["index.html"]
3. current_state = "review"
```

---

## 5. Designer Review

### 5.1 Present Prototype

```
[OUTPUT]

"Hi-fi prototype has been generated: tasks/<task-name>/index.html

**Generation Overview**:
- Total {N} interaction scenarios
- Entry scenario: {scenario name}
- Cross-scenario navigation: {scenario connection description}

**Implemented Interaction Commitments**:
{List the implementation status of interaction_commitments for each scenario}

**Handled Edge Cases**:
{List the implemented edge cases}

Please open index.html in a browser to preview.
After clicking through each scenario, let me know your feedback."
```

### 5.2 Wait for Review

```
[STOP AND WAIT FOR APPROVAL]

Waiting for the designer's Review of the hi-fi prototype.

Possible responses:
- Approve → §5.5 Confirm Transition
- Feedback → §5.3 Feedback Handling
- Reject → §5.4 Major Direction Issues
```

### 5.3 Feedback Handling (Feedback Boundary Compression)

When the designer provides modification feedback, execute the following sub-process:

**Step 1 — Extract Persistent Constraints**

```
[ACTION] Extract persistent constraints from designer feedback:

Distinguish between:
- Persistent constraints (global impact, e.g., "global font base size 16px", "button border-radius unified to 8px")
  → Append to task-progress.json.accumulated_constraints
- One-time point fixes (e.g., "change this button text to 'Submit'")
  → Execute the modification only, do not record in constraint list

After appending to accumulated_constraints, use the Edit tool to update task-progress.json.
```

**Step 2 — Patch HTML**

```
[ACTION] Patch index.html based on feedback

Semantic merge input:
  confirmed_intent
  + 03-design-contract.md
  + accumulated_constraints (all previous round constraints + current round additions)
  + current feedback

⚠️ MVP phase: Directly use the Edit tool to modify the corresponding sections in index.html.
   Do not rewrite the entire file — preserve all historical modifications.

TODO (activate in Phase 6):
  Generate DOM operation instructions (JSON):
  {"action": "remove|insert|update|replace", "target": "CSS selector", "content": "..."}
  Call .harnessdesign/scripts/dom_assembler.py to execute deterministic DOM operations.
```

**Step 3 — Archive Feedback Conversation**

```
[ACTION] Archive this round's feedback conversation to:
.harnessdesign/memory/sessions/phase4-review-round-{m}.md

YAML frontmatter:
---
type: review_backup
phase: 4
round: {m}
archived_at: "<ISO 8601>"
token_count: <this round's feedback conversation token count>
sections:
  - title: "Designer Feedback"
    line_start: <line number>
    line_end: <line number>
    estimated_tokens: <estimate>
  - title: "AI Patch Operations"
    line_start: <line number>
    line_end: <line number>
    estimated_tokens: <estimate>
keywords:
  - "<keyword>"
digest: "Round {m}: [one-sentence summary of this round's modifications]"
---

[This round's feedback conversation + AI patch operation records]
```

**Step 4 — Return to Validation**

```
→ Re-execute §3 Auto-Validation Loop
→ After passing, return to §5.1 to present the patched prototype
```

### 5.4 Reject Handling

```
[OUTPUT]

"You have major direction adjustment feedback for the prototype.

To ensure accurate understanding, please help me clarify:
1. Which scenarios need direction adjustments?
2. What is the adjustment direction?
3. Which items in the Design Contract need modification?

If the Design Contract needs to be modified, we can go back to contract editing first,
then regenerate after updating."

→ Wait for designer clarification
→ If rollback to contract needed → Update current_state = "contract_review"
→ If handleable within current scope → Treat as Feedback (§5.3)
```

### 5.5 Approve Transition

```
[ACTION] After designer Approves:

1. Update task-progress.json:
   - states.review.passes = true
   - states.review.approved_by = "designer"
   - states.review.approved_at = "<ISO 8601>"
   - states.review.artifacts = ["index.html"]
   - current_state = "knowledge_extraction"

2. Output transition prompt:
```

```
[OUTPUT]

"Hi-fi prototype has passed Review!

**Final Output**: tasks/<task-name>/index.html
(Complete interactive prototype with {N} interaction scenarios)

Proceeding to → Knowledge Extraction Phase:
Extract reusable knowledge from all outputs of this task and update the knowledge base.

[Continue] / [Review a specific aspect first]"
```

---

## 6. Phase Summary Card and Transition

### 6.1 Phase Summary Card

```
[CHECKPOINT] Run: python3 scripts/validate_transition.py --summary <task_dir>
Render script output using the Phase Summary Card template.
Do not fabricate checklist items — use the script output.
```

### 6.2 Archival and Index Update

```
[ACTION] Update summary index (anchor layer), add Phase 4 entry:

### Phase 4 (Hi-Fi Prototype):
> index.html generation complete, {M} rounds of Review, {K} accumulated constraints
> 🏷️ [output:index.html]
```

---

## Appendix A: Context Compression Strategy

### Phase 4 Working Layer Token Budget

```
When Phase 4 reaches Review Round N, working layer contents:
├── Anchor layer (intent + L0 + semantic tag index)          ~5-6k tokens
├── 03-design-contract.md                                    ~3-5k tokens
├── accumulated_constraints (accumulated over N rounds)       ~100-200 tokens
├── Round N current active feedback conversation (uncompressed) ~1-2k tokens
└── Total ~9-13k tokens (nearly the same as when Phase 4 first entered)
```

**Key Insight: HTML Is the Single Source of Truth for State**

- Each patched `index.html` contains all historical modifications
- No need to retain RoundDecision cards as in Phase 3
- Feedback conversations are "scaffolding" — archive after patching is complete
- `accumulated_constraints` is the only state that needs to persist across rounds

### Semantic Merge Input

Complete input for each feedback processing round:

```
confirmed_intent.md (original intent)
+ 03-design-contract.md (design blueprint)
+ accumulated_constraints (persistent constraints established in previous rounds)
+ current feedback (designer's latest modification feedback)
```

`accumulated_constraints` serves as a guardrail, preventing the AI from accidentally violating constraints established in previous rounds during patching.

---

## Appendix B: Error Handling

### B.1 03-design-contract.md Missing

```
→ Stop execution, report: "Design Contract is missing, please complete the Phase 3→4 transition first."
→ Suggestion: Roll back current_state to "prepare_design_contract"
```

### B.2 ZDS Component Spec File Missing

```
→ Design.md missing → Stop execution, report that ZDS specification files are needed
→ Specific component L2 file missing → Degrade to using L0 description from zds-index.md + Design.md general rules
→ Annotate [⚠️ Degraded: {component name} using L0 spec]
```

### B.3 index.html Write Failure

```
→ Output the HTML code in the conversation (output in segments to avoid truncation)
→ Ask the designer to save manually
→ Retry write
```

### B.4 Designer Requests Rollback to a Specific Scenario

```
→ Use the recall mechanism to retrieve the archived file for the corresponding scenario
→ Display that scenario's RoundDecision and interaction commitments in the Review conversation
→ If modification needed → Handle through the Feedback loop (§5.3)
→ If major modification needed → Suggest rolling back to the Design Contract (§5.4)
```

### B.5 Designer Dissatisfied After Self-Repair Loop Failure

```
→ Show the designer the specific issue list
→ Provide two options:
  A. Ignore validation issues, proceed to Review (designer visual inspection as substitute)
  B. Fix manually then re-validate
→ Continue after designer chooses
```
