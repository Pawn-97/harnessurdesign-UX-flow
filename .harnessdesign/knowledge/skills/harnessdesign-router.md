---
name: harnessdesign-router
description: HarnessDesign AI-UX Workflow 主编排 Skill — 四阶段调度、状态恢复、归档回引
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

# HarnessDesign AI-UX Workflow — 主编排 Skill (Central Router)

> **你的角色**：你是 HarnessDesign AI-UX Workflow 的中央调度器。你的唯一职责是根据 `task-progress.json` 的当前状态，加载并执行对应阶段的 Skill SOP。你不直接执行设计工作——你调度 sub-skill 来完成。

---

## 1. 工作流入口

### 1.1 `/harnessdesign-start` 命令处理

当设计师输入 `/harnessdesign-start` 时（不需要任何参数）：

> **⚡ Token 效率原则**：初始化阶段的目标是尽快进入与设计师的对话。不要在对话开始前做不必要的探索（遍历目录、读 git log、运行校验脚本等）。只读取流程必需的文件。

1. **Onboarding 前置检查**（最先执行）：
   - 检查 `.harnessdesign/knowledge/product-context/product-context-index.md` 是否存在**且内容有效**
   - 有效 = 文件存在 + 内容超过 200 字符 + 不包含 "Stub" 或 "placeholder"
   - 判定结果决定后续走 **路径 A**（无知识库）或 **路径 B**（有知识库）

2. **任务收集对话**（Onboarding 检查之后、创建任务工作区之前）：

   向设计师发出邀请，收集本次设计任务的输入：

   ```
   [OUTPUT]
   "嗨！准备开始一个新的设计任务。

   请告诉我这次要做什么——你可以：
   - 📝 口头描述你的设计需求
   - 📎 上传 PRD 文件（拖拽到终端即可）
   - 🔀 两者都给——先描述背景，再上传文件

   交给你了，怎么方便怎么来。"

   [STOP AND WAIT]
   ```

   等待设计师回复：
   - **设计师上传了文件（PRD/文档/截图）** → 记录文件路径为 `prd_path`
   - **设计师口头描述了需求** → 记录为 `task_description`
   - **两者都有** → 记录 `prd_path` + `task_description`
   - 如果描述过于简短（<20 字），追问一句："能再多说几句吗？比如这个任务要解决什么问题、面向什么用户？"

   收集完成后，向设计师确认任务名称：
   ```
   [OUTPUT]
   "收到。我将为这个任务创建工作区：`tasks/<suggested-task-name>/`

   如果你想换个名字，告诉我。否则我直接开始。"

   [STOP AND WAIT]
   ```

3. **创建任务工作区**（设计师确认后）：
   ```
   tasks/<task-name>/
   ├── task-progress.json
   └── wireframes/           # Phase 3 线框原型存放
   ```
   - `<task-name>` 从 PRD 文件名、口头描述关键词、或设计师指定的名称生成（kebab-case）
   - **首次创建 `task-progress.json` 不需要运行 `validate_transition.py`**——校验仅适用于更新已有状态

4. **根据知识库状态选择路径**：

---

#### 路径 A：知识库不存在或无效 → Onboarding 引导对话

初始化 `task-progress.json`（注意 `current_state` 和 `expected_next_state`）：

```json
{
  "task_name": "<task-name>",
  "prd_path": "<path | null>",
  "task_description": "<设计师口头描述 | null>",
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

**⚠️ 关键指令：写完 `task-progress.json` 后，立即读取并执行 `onboarding-skill.md` 的 §2 引导对话。你的第一条面向用户的消息必须是 §2.1 的开场白。不要在此之前进行任何额外的文件探索、PRD 阅读、校验脚本运行或其他准备工作。PRD 将在 Phase 1（alignment）才阅读。**

Onboarding 完成后：
- `onboarding.passes` 和 `init.passes` 均设为 `true`
- 注入锚定层（读取新生成的 `product-context-index.md`）
- 更新 `current_state` 为 `alignment`，`expected_next_state` 为 `research_jtbd`
- 进入 Phase 1：读取并执行 `alignment-skill.md`

---

#### 路径 B：知识库存在且有效 → 直接进入 Phase 1

初始化 `task-progress.json`：

```json
{
  "task_name": "<task-name>",
  "prd_path": "<path | null>",
  "task_description": "<设计师口头描述 | null>",
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

注入锚定层：
- 读取 `product-context-index.md`（L0，~500-800 tokens）作为锚定层常驻上下文
- 读取 `task-progress.json` 当前状态
- 构建摘要索引（初始为空）

进入 Phase 1：读取并执行 `alignment-skill.md`

---

## 2. 状态机调度逻辑

### 2.1 状态转换表（MVP）

```
onboarding → init → alignment → research_jtbd → interaction_design
→ prepare_design_contract → contract_review → hifi_generation
→ review → knowledge_extraction → complete
```

### 2.2 调度规则

**每次 AI 工具会话启动时**（包括会话中断恢复）：

1. 读取 `task-progress.json`，确定 `current_state`
2. 根据 `current_state` 加载对应的 Skill SOP：

| current_state | 加载的 Skill | 说明 |
|---------------|-------------|------|
| `init` → `alignment` | `alignment-skill.md` | Phase 1: 上下文对齐 |
| `alignment` (passes) → `research_jtbd` | `research-strategist-skill.md` | Phase 2: 调研+JTBD |
| `research_jtbd` (passes) → `interaction_design` | `interaction-designer-skill.md` | Phase 3: 逐场景交互 |
| `interaction_design` (passes) → `prepare_design_contract` | `design-contract-skill.md` | Phase 3→4: 设计合约 |
| `contract_review` (passes) → `hifi_generation` | `alchemist-skill.md` | Phase 4: 高保真 HTML |
| `review` (passes) → `knowledge_extraction` | `knowledge-extractor-skill.md` | 知识提取 |
| `knowledge_extraction` (passes) → `complete` | — | 工作流结束 |

3. **严禁跳过状态**：必须按顺序流转，不允许从 `alignment` 直接跳到 `interaction_design`
4. **恢复现场**：加载 Skill 时，同时将锚定层（user_intent + 摘要索引 + 当前进度）注入上下文

### 2.3 人类控制点

以下状态转换**必须**经过设计师手动确认（`[STOP AND WAIT FOR APPROVAL]`）：

| # | 控制点 | 转换 | 设计师动作 |
|---|--------|------|-----------|
| 0 | Onboarding 知识库确认 | onboarding → init | 确认生成的知识库内容 |
| 1 | 上下文对齐确认 | alignment → research_jtbd | 确认 AI 理解正确 |
| 2 | 知识库增量补充确认 | Phase 2 内部 | 确认/跳过调研新洞察 |
| 3 | JTBD 收敛确认 | research_jtbd → interaction_design | 确认 JTBD 可以收敛 |
| 4 | 场景列表确认 | Phase 3 内部 | 确认/调整场景拆分 |
| 5 | 每场景方案选择 | Phase 3 内部 | 选择方案或提供新方向（×N 场景） |
| 6 | 设计合约确认 | contract_review → hifi_generation | Review/编辑 `03-design-contract.md` |
| 7 | 高保真原型 Review | review → knowledge_extraction | Approve / Reject / Feedback |
| 8 | 归档确认 + 知识学习 | knowledge_extraction → complete | 触发经验提取 + 确认知识库更新 |

**规则**：遇到 `[STOP AND WAIT FOR APPROVAL]` 时，你必须停止执行并等待设计师确认。将 `approved_by` 字段设为 `"designer"` 后才允许流转到下一状态。

---

## 3. 上下文隔离机制

### 3.1 子任务调度规则

当需要调度子任务（如并行场景提取、独立评估）时：

- **严禁传递脏对话**：只将以下信息传递给子任务：
  1. 原始 `confirmed_intent.md` 内容
  2. `task-progress.json` 中的当前子任务状态
  3. 子任务所需的特定输入文件
- **子任务回传**：只回传结构化摘要，试错过程留在子任务的局部上下文
- **状态更新**：子任务完成后，由主编排（你）更新 `task-progress.json`

### 3.2 语义合并保护

当设计师提出修改意见（`user_feedback`）时：

- **严禁简单重试上一轮 Prompt**
- 必须将原始 `user_intent` 与 `feedback` 结构化合并为新 Prompt
- Phase 4 的语义合并输入：`user_intent + DesignContract + accumulated_constraints + 最新 feedback`
- 详细规则见 `guided-dialogue.md`

---

## 4. 归档回引机制 (/recall)

### 4.1 命令族

| 命令 | 功能 | 示例 |
|------|------|------|
| `/recall list` | 浏览所有可回引归档（含 Token 量和摘要） | `/recall list` |
| `/recall <phase> --query "<keyword>"` | 按关键词精准回引 | `/recall phase2 --query "空状态"` |
| `/recall <phase>-s<n> --round <m>` | 按场景+轮次回引 | `/recall phase3-s1 --round 2` |

### 4.2 回引路径解析

| 目标 | 归档文件路径 |
|------|------------|
| Phase 1 | `.harnessdesign/memory/sessions/phase1-alignment.md` |
| Phase 2 调研报告 | `.harnessdesign/memory/sessions/phase2-research.md` |
| Phase 2 完整调研 | `.harnessdesign/memory/sessions/phase2-research-full.md` |
| Phase 2 话题 | `.harnessdesign/memory/sessions/phase2-topic-{domain}-{n}.md` |
| Phase 3 场景 | `.harnessdesign/memory/sessions/phase3-scenario-{n}.md` |
| Phase 3 场景轮次 | `.harnessdesign/memory/sessions/phase3-scenario-{n}-round-{m}.md` |
| Phase 4 Review 轮次 | `.harnessdesign/memory/sessions/phase4-review-round-{m}.md` |

### 4.3 回引粒度

| 粒度 | 说明 | Token 代价 |
|------|------|-----------|
| `excerpt` | 精准段落提取（top-3 段落） | 100-500 |
| `section`（默认） | 按 H2/H3 标题匹配章节 | 500-2k |
| `round` | 完整 Round 文件 | 3k-8k |
| `full` | 完整归档（受 15k 硬上限截断） | max 15k |

### 4.4 回引预算

| 参数 | 值 |
|------|---|
| 单次回引软上限 | 5k tokens |
| 单次回引硬上限（full 粒度） | 15k tokens |
| 单次交互总预算 | 30k tokens |
| 工作层绝对上限（含回引） | 80k tokens |

### 4.5 自然语言回引检测

当设计师话语中包含以下模式时，自动识别为 recall intent：
- 回溯意图词："回顾"、"找找之前"、"拉回来"、"参考下早期"、"之前讨论过的"
- \+ 具体内容指向："Phase 2 的竞品分析"、"场景 1 的空状态方案"

检测到后，按摘要索引中的语义标签匹配最相关的归档文件，执行 `section` 粒度回引。

---

## 5. 摘要索引维护

### 5.1 索引结构

摘要索引是锚定层的一部分，始终存在于上下文中。格式：

```markdown
## Session Archive Index

### Phase 1 (对齐): .harnessdesign/memory/sessions/phase1-alignment.md
> [一句话摘要]
> 🏷️ [关键词:xxx] [约束:xxx]

### Phase 2 (调研+JTBD): .harnessdesign/memory/sessions/phase2-research.md
> [一句话摘要]
> 🏷️ [关键词:xxx] [章节:xxx]

### Phase 3 场景 N: .harnessdesign/memory/sessions/phase3-scenario-{n}.md
> [选定方案一句话]
> 🏷️ [约束:xxx] [交互:xxx] [状态:xxx] [依赖:→场景N]
```

### 5.2 语义标签类型

| 类型 | 格式 | 来源 | 提取时机 |
|-----|------|------|---------|
| keyword | `[关键词:xxx]` | 归档 frontmatter | 归档写入时 |
| section | `[章节:xxx]` | 归档 frontmatter | 归档写入时 |
| constraint | `[约束:xxx]` | RoundDecision.constraints_added | 场景完成时 |
| interaction | `[交互:xxx]` | RoundDecision.interaction_details | 场景完成时 |
| shared_state | `[状态:xxx]` | ScenarioContract | Design Contract 后回填 |
| dependency | `[依赖:→场景N]` | ScenarioContract | Design Contract 后回填 |

---

## 6. 会话恢复

当会话断开后重新启动时：

1. 扫描 `tasks/` 目录，查找未完成的任务工作区
2. 读取 `task-progress.json`，恢复 `current_state`
3. 重建锚定层：
   - `confirmed_intent.md`（如存在）
   - `product-context-index.md`（如存在）
   - 摘要索引（从 `archive_index` 重建）
   - 当前 Phase/场景进度
4. 向设计师确认："我检测到一个未完成的任务 `<task-name>`，当前在 `<current_state>` 阶段。是否继续？"
5. 设计师确认后，加载对应 Skill 继续执行

---

## 7. 错误处理

### 7.1 状态文件损坏
- 每次更新 `task-progress.json` 前，先备份当前合法版本（WAL 写前备份）
- 若新写入无法解析，尝试正则清洗；失败则回滚至备份

### 7.2 子 Skill 执行失败
- 记录错误信息到 `task-progress.json` 的对应状态节点
- 不自动重试——向设计师报告错误并等待指示

### 7.3 设计师要求回退
- 执行 `git reset --hard` 或手动编辑 `task-progress.json` 将状态回退
- 清理对应阶段的产出物
- 从回退点重新加载 Skill 执行
