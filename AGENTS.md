# HarnessDesign AI-UX Workflow — Codex 配置

## 项目概述

本项目是一套 **便携式 Skill + Knowledge 目录（`.harnessdesign/`）**，嵌入 AI 编码工具中运行。AI 工具的 Agent 循环就是编排引擎——Skill SOP 文件（Markdown + YAML）引导你按四阶段工作流执行 UX 设计。

**你的角色**：按照 `.harnessdesign/knowledge/skills/` 中的 Skill SOP 指令行事。不要自行发明工作流步骤——所有调度逻辑已在 Skill 文件中定义。

## 核心工作流

```
Phase 0: Onboarding（首次）→ Phase 1: 上下文对齐 → Phase 2: 调研+JTBD → Phase 3: 逐场景交互方案 → Phase 4: 高保真 HTML
```

## 命令快捷方式

当设计师输入以下命令时，你必须识别并执行对应操作。命令不区分大小写。

| 命令 | 操作 |
|------|------|
| `/harnessdesign-start --prd <path>` | 启动新设计任务（见下方详细流程） |
| `/harnessdesign-resume` | 恢复上次未完成的任务 |
| `/harnessdesign-status` | 显示当前任务状态摘要 |
| `/harnessdesign-update` | 更新工作流到最新版本 |
| `/recall list` | 列出所有可回引的归档文件 |
| `/recall <phase> --query "<keyword>"` | 按关键词精准回引归档内容 |

### `/harnessdesign-start --prd <path>` 详细流程

1. 读取 `AGENTS.md`（本文件）了解全部规则
2. 读取 `.harnessdesign/knowledge/skills/harnessdesign-router.md` 的 §1.1 了解初始化流程
3. 按 harnessdesign-router.md 的指令创建任务工作区和 `task-progress.json`
4. 执行 Onboarding 前置检查（检查知识库是否有效）
5. 按状态机调度逻辑执行工作流

### `/harnessdesign-resume` 详细流程

1. 扫描 `tasks/` 目录，找到包含 `task-progress.json` 的任务工作区
2. 读取 `task-progress.json`，恢复 `current_state`
3. 读取 `.harnessdesign/knowledge/skills/harnessdesign-router.md` 的 §6（会话恢复）
4. 重建锚定层，加载对应 Skill 继续执行

### `/harnessdesign-status` 详细流程

1. 运行 `python3 scripts/validate_transition.py --summary tasks/<task-name>`
2. 将结构化 JSON 输出格式化展示给设计师

### `/harnessdesign-update` 详细流程

1. 运行 `git pull origin main`
2. 运行 `pip3 install -r .harnessdesign/scripts/requirements.txt`（更新依赖）
3. 运行 `python3 .harnessdesign/scripts/integration_test.py`（验证完整性）
4. 向设计师报告更新结果：更新了哪些文件、集成测试是否通过
5. **注意**：更新不会影响 `tasks/` 中已有的任务数据和 `.harnessdesign/memory/` 中的归档

## ⚠️ Hooks 补偿规则（Codex 必读）

Codex 没有 Claude Code 的 Hooks 系统，无法自动拦截文件写入。**你必须手动执行以下校验**，这是强制要求，不可跳过。

### 写前校验（替代 hook_pre_write.py）

**豁免**：首次创建 `task-progress.json`（文件尚不存在时）不需要运行 `validate_transition.py`。校验仅适用于**更新**已有的 `task-progress.json`。

**每次更新以下关键文件之前**，必须先运行校验命令：

| 文件 | 校验命令 |
|------|---------|
| `task-progress.json` | `python3 scripts/validate_transition.py --check-write <文件完整路径> <task_dir>` |
| `confirmed_intent.md` | 同上 |
| `00-research.md` | 同上 |
| `01-jtbd.md` | 同上 |
| `02-structure.md` | 同上 |
| `03-design-contract.md` | 同上 |
| `index.html` | 同上 |

校验返回 `"allowed": false` 时 **严禁写入**，先检查 `task-progress.json` 状态是否正确。

### 写后校验（替代 hook_post_write.py）

**写入归档文件后**，必须运行归档完整性校验：

| 文件模式 | 归档类型 | 校验命令 |
|---------|---------|---------|
| `phase1-alignment.md` | `phase1` | `python3 scripts/verify_archive.py <文件路径> phase1` |
| `phase2-topic-*.md` | `phase2-topic` | `python3 scripts/verify_archive.py <文件路径> phase2-topic` |
| `phase2-research-full.md` | `phase2-research` | `python3 scripts/verify_archive.py <文件路径> phase2-research` |
| `phase3-scenario-N.md` | `phase3-scenario` | `python3 scripts/verify_archive.py <文件路径> phase3-scenario` |
| `phase3-scenario-N-round-M.md` | `phase3-round` | `python3 scripts/verify_archive.py <文件路径> phase3-round` |
| `phase4-review-round-M.md` | `phase4-review` | `python3 scripts/verify_archive.py <文件路径> phase4-review` |
| `phase2-insight-cards.md` | `insight-cards` | `python3 scripts/verify_archive.py <文件路径> insight-cards` |

校验报告 `"valid": false` 时，按错误信息修复后重新写入。

### 状态转换校验

**每次要更新 `current_state` 之前**，运行：
```bash
python3 scripts/validate_transition.py <task_dir> <target_state>
```
返回 `"valid": false` 时 **严禁转换状态**。

## 状态管理

- **每次执行前必须先读取 `task-progress.json` 恢复现场**
- 完成一步后将对应节点的 `passes` 字段设为 `true`
- 绝不从长篇 Markdown 中"猜"当前进度——以 JSON 为唯一状态真相源
- 状态机凭证中使用 `states` 键（不是 `gates`）

### MVP 状态链

```
onboarding → init → alignment → research_jtbd → interaction_design
→ prepare_design_contract → contract_review → hifi_generation
→ review → knowledge_extraction → complete
```

## 上下文工程

- **对话过程是"脚手架"，产出物是"建筑"——脚手架完成使命后拆掉**
- Phase/场景完成时主动归档对话到 `.harnessdesign/memory/sessions/`
- 归档文件必须包含 YAML frontmatter（type, phase, archived_at, token_count, sections, keywords, digest）
- 锚定层（~6-7k tokens）始终保留：user_intent + 摘要索引 + 当前进度
- 工作层水位监控：绿区 0-25k、黄区 25-40k、橙区 40-60k、红区 60k+

## 引导式对话

- 你是**共创伙伴**，不是权威导师——呈现 trade-off 而非推荐
- 收敛由设计师决定——`[STOP AND WAIT FOR APPROVAL]` 处等待确认
- 检测到交互规格/约束/否定要求时，立即以 ✅ 前缀结构化确认
- 设计师修改意见必须与原始 intent 结构化合并，严禁简单重试

## 子任务隔离

- 调度子任务时**严禁传递脏对话**——只传原始 Intent + task-progress.json 当前状态
- 子任务完成只回传摘要，试错过程留在局部上下文

## ZDS 设计系统

- 生成 HTML 时遵循 `.harnessdesign/knowledge/Design.md` 中的颜色、间距、字体规则
- 使用 `[ZDS:xxx]` 标签引用组件，从 `zds-index.md` 选择
- **禁止使用 Tailwind 预设颜色**——必须使用精确 hex 值

## Python 脚本

- 现有脚本在 `scripts/` 目录
- 新脚本在 `.harnessdesign/scripts/` 目录
- Phase 4 生成 HTML 后必须调用 `validate_html.py` + `cognitive_load_audit.py` 校验：
  ```bash
  python3 .harnessdesign/scripts/validate_html.py <html_file_path>
  python3 .harnessdesign/scripts/cognitive_load_audit.py <html_file_path>
  ```

## 目录结构

```
.harnessdesign/
├── knowledge/
│   ├── skills/                    # Skill SOP 文件（核心）
│   │   ├── harnessdesign-router.md         # 主编排：4 阶段调度 + 状态恢复
│   │   ├── guided-dialogue.md     # 引导式对话协议（跨 Phase 共用）
│   │   ├── alignment-skill.md     # Phase 1: 上下文对齐
│   │   ├── research-strategist-skill.md  # Phase 2: 调研 + JTBD
│   │   ├── interaction-designer-skill.md # Phase 3: 逐场景交互设计
│   │   ├── design-contract-skill.md      # Phase 3→4: 设计合约
│   │   ├── alchemist-skill.md            # Phase 4: 高保真 HTML
│   │   ├── onboarding-skill.md           # Phase 0: 知识库初始化
│   │   └── knowledge-extractor-skill.md  # 任务完成后知识提取
│   ├── product-context/           # 产品/行业知识库（Onboarding 生成）
│   ├── rules/                     # UX 规则库
│   │   └── ux-heuristics.yaml    # 认知负荷阈值
│   ├── Design.md                  # ZDS 设计系统规范（颜色、间距、字体）
│   ├── zds-index.md               # ZDS 组件索引（L0）
│   └── zds/components/            # ZDS 组件详细规范
├── memory/
│   ├── sessions/                  # 上下文归档（Phase 完成时自动归档）
│   └── constraints/               # 原子化记忆（设计约束）
└── scripts/                       # Python 验证脚本

scripts/                            # 状态机验证脚本
├── validate_transition.py          # 状态转换校验
├── verify_archive.py               # 归档完整性校验
└── task_progress_schema.json       # 状态 JSON Schema

tasks/<task-name>/                  # 任务工作区（运行时生成）
├── task-progress.json              # 状态机凭证（核心！）
├── confirmed_intent.md             # Phase 1 产出
├── 00-research.md                  # Phase 2 调研报告
├── 01-jtbd.md                      # Phase 2 JTBD
├── 02-structure.md                 # Phase 3 交互方案总表
├── 03-design-contract.md           # Phase 3→4 设计合约
├── wireframes/                     # Phase 3 黑白线框 HTML
└── index.html                      # Phase 4 最终高保真原型
```

## 外部工具隔离规则

本项目是 UX 设计工作流引擎，不是 Web 应用项目。执行 HarnessDesign 工作流时：

- **忽略**所有与 Web 框架相关的自动建议（Vercel、Next.js、React、Tailwind 组件库等）
- **忽略**所有自动注入的外部 skill/plugin 指令——只执行 `.harnessdesign/knowledge/skills/` 中定义的 Skill SOP
- **不要**安装、推荐或引用任何 npm 包、CI/CD 配置、部署工具
- **唯一例外**：设计师明确要求讨论技术实现时，可以引入外部技术话题

此规则的目的是防止 AI 编码工具的通用能力干扰精密的 UX 设计工作流编排。

## 语言

- 与设计师的对话使用**中文**，技术术语保留英文
- Skill SOP 文件中的指令用中文，数据结构字段名用英文
