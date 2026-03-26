# Zoom AI-UX Workflow

便携式 AI 驱动 UX 设计工作流引擎。嵌入 AI 编码工具（Claude Code / Codex）中运行，引导设计师从 PRD 到高保真 HTML 原型。

## 快速开始

### 前置条件

- Python 3.10+
- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) 或 [Codex](https://openai.com/index/introducing-codex/)（二选一）

### 安装

```bash
# 1. 克隆仓库
git clone https://[https://github.com/Pawn-97/ZM-design-flow.git]
cd design-flow

# 2. 安装 Python 依赖（验证脚本需要）
pip install -r .zoom-ai/scripts/requirements.txt

# 3. 验证安装完整性
python3 .zoom-ai/scripts/integration_test.py
# 预期：64 passed, 0 failed
```

### 使用

```bash
# 启动 Claude Code（在项目目录下）
claude

# 启动工作流（首次会触发 Onboarding）
/zoom-start --prd path/to/your-prd.md
```

### 工作流阶段

```
Phase 0: Onboarding（首次使用）→ 建立产品知识库
Phase 1: 上下文对齐 → 确认设计意图
Phase 2: 调研 + JTBD → 用户洞察收敛
Phase 3: 逐场景交互设计 → 黑白线框原型
Phase 4: 高保真 HTML 原型 → ZDS 视觉规范
```

每个阶段都有 `[STOP AND WAIT FOR APPROVAL]` 控制点，设计师始终掌握决策权。

## 目录结构

```
.zoom-ai/
├── knowledge/
│   ├── skills/              # Skill SOP 文件（工作流核心）
│   ├── product-context/     # 产品知识库（Onboarding 生成）
│   ├── rules/               # UX 规则配置
│   ├── Design.md            # ZDS 设计系统规范
│   ├── zds-index.md         # ZDS 组件索引
│   └── zds/components/      # ZDS 组件详细规范
├── memory/
│   ├── sessions/            # 对话归档（运行时生成）
│   └── constraints/         # 设计约束记忆（运行时生成）
└── scripts/                 # Python 验证脚本

scripts/                     # 状态机验证 + Hooks
tasks/                       # 任务工作区（运行时生成，已 gitignore）
```

## 嵌入到已有项目

如果想把工作流嵌入到一个已有项目中（而非单独使用）：

```bash
# 复制核心文件到目标项目
cp -r .zoom-ai/ /path/to/your-project/.zoom-ai/
cp -r scripts/ /path/to/your-project/scripts/
cp CLAUDE.md /path/to/your-project/CLAUDE.md
cp AGENTS.md /path/to/your-project/AGENTS.md

# 如果目标项目已有 CLAUDE.md，手动合并内容
# 安装依赖
pip install -r /path/to/your-project/.zoom-ai/scripts/requirements.txt
```

## 卸载

```bash
rm -rf .zoom-ai/ tasks/
rm -f scripts/validate_transition.py scripts/verify_archive.py
rm -f scripts/hook_pre_write.py scripts/hook_post_write.py
rm -f scripts/task_progress_schema.json
rm -f CLAUDE.md AGENTS.md
rm -rf .claude/hooks.json
```

## 验证

```bash
# 全量一致性检查
python3 .zoom-ai/scripts/integration_test.py

# 查看某个任务的当前状态
python3 scripts/validate_transition.py --summary tasks/<task-name>

# 检查状态转换是否合法
python3 scripts/validate_transition.py tasks/<task-name> <target_state>
```
