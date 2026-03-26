# HarnessDesign 使用手册

> 面向 UX 设计师的全流程指南。不需要任何编程或 Git 基础。

---

## 目录

1. [安装前准备](#1-安装前准备)
2. [为新项目安装工作流](#2-为新项目安装工作流)
3. [日常使用](#3-日常使用)
4. [多项目管理与切换](#4-多项目管理与切换)
5. [更新工作流](#5-更新工作流)
6. [移除工作流](#6-移除工作流)
7. [常见问题](#7-常见问题)

---

## 1. 安装前准备

你需要先安装三样东西：**Git**、**Python** 和 **Claude Code**（或 Codex）。已安装的可以跳过。

> **怎么打开终端？** Mac 按 `Cmd + 空格`，输入 `终端` 或 `Terminal`，回车。

### 1.1 安装 Git

在终端输入：

```
git --version
```

如果显示版本号（如 `git version 2.x.x`），跳过。如果提示找不到命令：

- **Mac**：终端会自动弹窗提示安装 Xcode Command Line Tools，点 **Install** 即可
- **Windows**：访问 https://git-scm.com/downloads 下载安装

### 1.2 安装 Python

在终端输入：

```
python3 --version
```

如果显示 `Python 3.10.x` 或更高版本，跳过。否则：

1. 访问 https://www.python.org/downloads/
2. 点击黄色的 **Download Python 3.x.x** 按钮
3. 双击安装包，一路点 **Continue** → **Install**
4. **关闭终端再重新打开**，再次运行 `python3 --version` 确认

### 1.3 安装 Claude Code

> 如果你用 Codex，跳到 [1.4](#14-安装-codex替代方案)。

1. 访问 https://docs.anthropic.com/en/docs/claude-code
2. 按照页面指引安装
3. 在终端输入 `claude --version`，能看到版本号说明成功

### 1.4 安装 Codex（替代方案）

1. 访问 https://openai.com/index/introducing-codex/
2. 按照页面指引安装
3. 在终端输入 `codex --version` 确认

---

## 2. 为新项目安装工作流

> **核心概念**：选一个文件夹安装工作流，之后在这个文件夹里启动多个设计任务。所有任务共享产品知识库和设计约束记忆，每个任务的产出物自动归档到独立的子文件夹中。

### 一键安装

把下面这行命令**整行**复制粘贴到终端，把末尾的路径换成你想要的**目标文件夹**：

```
curl -fsSL https://raw.githubusercontent.com/Pawn-97/harnessurdesign-UX-flow/main/install.sh | bash -s -- /Desktop/my-design-workspace
```

你可以选择任何你喜欢的文件夹位置和名称。**举几个例子**：

```
# 以产品线命名
curl -fsSL ... | bash -s -- ~/Desktop/my-design-workspace

# 以季度命名
curl -fsSL ... | bash -s -- ~/Desktop/2026-Q1-designs

# 放在项目目录里
curl -fsSL ... | bash -s -- ~/Projects/my-ux-workspace
```

安装脚本会自动：
- 下载工作流引擎文件
- 创建 Python 虚拟环境（`.venv/`）并安装依赖
- 配置 Claude Code（自动禁用无关插件）
- 运行完整性验证

看到 **安装成功！** 字样就说明一切就绪。

> **遇到问题？**
> - `git: command not found` → 回到 [1.1 安装 Git](#11-安装-git)
> - `Permission denied` 或 `Repository not found` → 联系 GuanchengDing 获取仓库访问权限
> - Python 版本过低 → 安装 Homebrew Python：`brew install python3`，然后重新运行安装命令

---

## 3. 日常使用

### 3.1 启动新任务

打开终端，进入你的工作空间文件夹：

```
cd ~/Desktop/my-design-workspace
```

启动 Claude Code：

```
claude
```

> 用 Codex 的话，把 `claude` 换成 `codex`。

在 AI 对话界面中输入：

```
/harnessdesign-start
```

就这么简单，不需要带任何参数。AI 会邀请你描述本次设计任务，你可以自由选择：

- **口头描述**：直接打字说你要做什么
- **上传 PRD**：把 PRD 文件拖拽到终端窗口
- **两者兼具**：先说背景，再上传文件

AI 收到任务后，会自动创建一个子文件夹（如 `tasks/spam-dashboard/`）来存放这个任务的所有产出。

**首次启动**会进入 Onboarding（Phase 0），AI 会引导你建立知识库。**后续任务会自动跳过这一步**，直接复用已有知识库。同一工作空间内所有任务共享知识库、设计约束和调研洞察。

### 3.2 并行处理多个任务

你可以**同时打开多个终端窗口**，在同一个工作空间文件夹中启动不同的设计任务：

**终端窗口 1**：
```
cd ~/Desktop/my-design-workspace && claude
/harnessdesign-start
→ "我要重新设计 Spam Dashboard..."
```

**终端窗口 2**（同时）：
```
cd ~/Desktop/my-design-workspace && claude
/harnessdesign-start
→ "我要优化 Call Quality 监控页面..."
```

每个任务的产出会在各自的子文件夹中：
```
tasks/spam-dashboard/     ← 终端 1 的产出
tasks/call-quality/       ← 终端 2 的产出
```

两个任务共享同一份产品知识库和设计约束记忆。

### 3.3 工作流四个阶段

| 阶段 | 做什么 | 你需要做什么 |
|------|--------|-------------|
| Phase 1: 上下文对齐 | AI 和你对齐对 PRD 的理解 | 回答问题、确认共识 |
| Phase 2: 调研 + JTBD | AI 引导你做用户调研和任务分析 | 参与讨论、确认洞察 |
| Phase 3: 交互设计 | AI 和你逐场景设计交互方案 | 审阅方案、给反馈 |
| Phase 4: 高保真原型 | AI 生成符合设计系统的 HTML | 审阅原型、指导修改 |

每个阶段结束时，AI 会等你确认（你会看到 `[STOP AND WAIT FOR APPROVAL]`）。**你随时可以说"不"或提出修改意见**——AI 是你的共创伙伴，不是决策者。

### 3.4 所有斜杠命令

在 Claude Code 对话界面中输入 `/` 即可看到所有可用命令：

| 命令 | 用途 |
|------|------|
| `/harnessdesign-start` | 启动新任务（主入口） |
| `/harnessdesign-resume` | 恢复上次未完成的任务 |
| `/harnessdesign-onboarding` | 单独运行 Phase 0：知识库初始化 |
| `/harnessdesign-alignment` | 单独运行 Phase 1：上下文对齐 |
| `/harnessdesign-research` | 单独运行 Phase 2：调研 + JTBD |
| `/harnessdesign-interaction` | 单独运行 Phase 3：交互设计 |
| `/harnessdesign-contract` | 单独运行 Phase 3→4：设计合约 |
| `/harnessdesign-hifi` | 单独运行 Phase 4：高保真 HTML |
| `/harnessdesign-extract` | 单独运行知识萃取 |

> 一般只需要 `/harnessdesign-start` 和 `/harnessdesign-resume`，AI 会自动调度到正确的阶段。其余命令用于跳过或重跑特定阶段。

### 3.5 中途离开和恢复

可以随时关闭终端。下次回来时：

```
cd ~/Desktop/my-design-workspace
```

```
claude
```

进入对话后输入：

```
/harnessdesign-resume
```

AI 会自动恢复到你上次离开的位置。

### 3.6 查看当前状态

在对话中输入：

```
/harnessdesign-status
```

### 3.7 你的工作空间里有什么

多个任务完成后，文件夹结构大致是这样的：

```
~/Desktop/my-design-workspace/
│
├── tasks/                              ← ★ 所有任务的产出物
│   ├── spam-dashboard/                 ← 任务 A
│   │   ├── confirmed_intent.md         ← Phase 1: 对齐共识
│   │   ├── 00-research.md              ← Phase 2: 调研报告
│   │   ├── 01-jtbd.md                  ← Phase 2: 用户任务分析
│   │   ├── 02-structure.md             ← Phase 3: 交互方案总表
│   │   ├── 03-design-contract.md       ← Phase 3→4: 设计合约
│   │   ├── wireframes/                 ← Phase 3: 黑白线框 HTML
│   │   └── index.html                  ← Phase 4: 高保真原型 ★
│   └── call-quality/                   ← 任务 B（同样的结构）
│       └── ...
│
├── .harnessdesign/                     ← 工作流引擎 + 共享知识（不用管）
│   ├── knowledge/product-context/      ← 知识库（所有任务共享）
│   └── memory/constraints/             ← 设计约束记忆（所有任务共享）
├── .venv/                              ← Python 虚拟环境（不用管）
├── scripts/                            ← 验证脚本（不用管）
└── CLAUDE.md / AGENTS.md              ← AI 配置（不用管）
```

**共享机制**：同一工作空间内的所有任务自动共享：
- **知识库**（Onboarding 只需跑一次）
- **设计约束记忆**（前一个任务确认的设计规则，后续任务自动继承）
- **知识提取**（每个任务完成后，AI 会把学到的新知识回写到知识库）

---

## 4. 多任务管理

### 4.1 切换到之前的任务

关闭当前 claude 会话（`Ctrl + C` 或关闭终端），重新进入：

```
cd ~/Desktop/my-design-workspace && claude
```

输入：

```
/harnessdesign-resume
```

如果有多个未完成的任务，AI 会列出来让你选择。

### 4.2 查看所有任务状态

在终端中运行（不需要进入 claude）：

```
cd ~/Desktop/my-design-workspace
for d in tasks/*/task-progress.json; do
  task=$(basename $(dirname "$d"))
  state=$(python3 -c "import json; print(json.load(open('$d'))['current_state'])")
  echo "  $task: $state"
done
```

### 4.3 如果需要完全独立的工作空间

大多数情况下一个工作空间就够了。但如果你需要完全独立的知识库（比如切换到一条全新的产品线），再安装一个：

```
curl -fsSL https://raw.githubusercontent.com/Pawn-97/harnessurdesign-UX-flow/main/install.sh | bash -s -- ~/Desktop/another-workspace
```

---

## 5. 更新工作流

当 GuanchengDing 通知有新版本时，对**每个工作空间文件夹**重新运行安装命令：

```
curl -fsSL https://raw.githubusercontent.com/Pawn-97/harnessurdesign-UX-flow/main/install.sh | bash -s -- ~/Desktop/my-design-workspace
```

安装脚本会：
- 更新引擎文件（skills、scripts、设计系统规范）
- **不会覆盖**你的任务数据（`tasks/`）、知识库（`product-context/`）和对话归档（`memory/`）
- 不会覆盖你自定义过的 `CLAUDE.md` / `AGENTS.md`
- 重新验证安装完整性

> **或者在 AI 对话中更新**：进入项目的 claude 会话后输入 `/harnessdesign-update`

---

## 6. 移除工作流

### 移除整个工作空间

```
rm -rf ~/Desktop/my-design-workspace
```

> **想保留产出物？** 先把 `tasks/` 目录中需要的文件复制到别处。

### 只移除工作流引擎（保留项目文件）

如果文件夹里还有其他你的文件，只移除工作流部分：

```
cd ~/Desktop/my-design-workspace
rm -rf .harnessdesign scripts .claude CLAUDE.md AGENTS.md tasks
```

---

## 7. 常见问题

### Q: 安装命令提示 "curl: command not found"

Mac 自带 curl，一般不会出现这个问题。如果出现，先安装 Xcode Command Line Tools：

```
xcode-select --install
```

### Q: `Permission denied` 或 `Repository not found`

你需要 GitHub 仓库的访问权限。联系 GuanchengDing 把你的 GitHub 账号加入项目。

如果你没有 GitHub 账号：
1. 访问 https://github.com/signup 注册
2. 把你的用户名发给 GuanchengDing

### Q: 安装提示 "externally-managed-environment" 或 pip 权限错误

这是旧版安装脚本的问题。请重新运行最新的安装命令即可——新版脚本会自动创建 `.venv/` 虚拟环境，不再往系统 Python 里装包。

### Q: Claude Code 里出现奇怪的 "Vercel"、"React" 建议

安装脚本已自动禁用无关插件。如果仍然出现，检查项目文件夹下是否有 `.claude/settings.json`：

```
cat ~/Desktop/你的项目/.claude/settings.json
```

如果不存在，重新运行安装命令。

### Q: 工作流卡住了，AI 不响应

1. 关闭终端
2. 重新打开终端
3. `cd ~/Desktop/你的项目 && claude`
4. 输入 `/harnessdesign-resume`

### Q: 想重新开始一个任务（丢弃当前进度）

```
rm -rf ~/Desktop/my-design-workspace/tasks/任务名
```

然后重新 `/harnessdesign-start`

### Q: 更新后验证测试没有全部通过

截图发给 GuanchengDing，附上终端中的错误信息。

### Q: 同一个项目能不能跑多个任务？

可以。每次 `/harnessdesign-start` 会创建一个新的任务工作区。`/harnessdesign-resume` 会让你选择要恢复哪个任务。

---

## 需要帮助？

直接联系 GuanchengDing —— Slack、微信、或任何你方便的渠道。
