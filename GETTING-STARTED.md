# HarnessDesign 使用手册

> 面向 UX 设计师的全流程指南。不需要任何编程或 Git 基础。

---

## 目录

1. [安装前准备](#1-安装前准备)
2. [安装工作流](#2-安装工作流)
3. [日常使用](#3-日常使用)
4. [更新工作流](#4-更新工作流)
5. [移除工作流](#5-移除工作流)
6. [常见问题](#6-常见问题)

---

## 1. 安装前准备

你需要先安装两样东西：**Python** 和 **Claude Code**（或 Codex）。

### 1.1 安装 Python

**检查是否已安装**：打开「终端」（Mac 按 `Cmd + 空格`，输入 `终端` 或 `Terminal`，回车），输入：

```
python3 --version
```

如果显示 `Python 3.10.x` 或更高版本，跳过此步。如果提示找不到命令：

1. 打开浏览器，访问 https://www.python.org/downloads/
2. 点击黄色的 **Download Python 3.x.x** 按钮
3. 下载完成后双击安装包，一路点 **Continue** → **Install**
4. 安装完成后，关闭终端再重新打开，再次运行 `python3 --version` 确认

### 1.2 安装 Claude Code

> 如果你用 Codex，跳到 [1.3](#13-安装-codex替代方案)。

1. 打开浏览器，访问 https://docs.anthropic.com/en/docs/claude-code
2. 按照页面指引安装（需要 Node.js，页面会引导你）
3. 安装完成后，在终端输入 `claude --version`，能看到版本号说明成功

### 1.3 安装 Codex（替代方案）

如果你选择用 OpenAI 的 Codex 而非 Claude Code：

1. 访问 https://openai.com/index/introducing-codex/
2. 按照页面指引安装
3. 安装完成后，在终端输入 `codex --version` 确认

---

## 2. 安装工作流

### 第一步：下载工作流文件

在终端中**逐行**复制粘贴以下命令（每输入一行按一次回车）：

```
cd ~/Desktop
```

```
git clone https://github.com/Pawn-97/harnessurdesign-UX-flow.git
```

> **遇到问题？**
> - 如果提示 `git: command not found`：打开 https://git-scm.com/downloads ，下载安装 Git，然后关闭终端重新打开，再试一次。
> - 如果提示需要登录 GitHub：联系 GuanchengDing 获取仓库访问权限。

### 第二步：安装依赖

```
cd ~/Desktop/harnessurdesign-UX-flow
```

```
pip3 install -r .harnessdesign/scripts/requirements.txt
```

### 第三步：验证安装

```
python3 .harnessdesign/scripts/integration_test.py
```

你应该看到类似这样的输出：

```
✓ 64 passed, 0 failed
```

如果全部通过，安装完成。

### 第四步：配置 Claude Code（可选但推荐）

这一步会禁用与 UX 工作流无关的插件，避免干扰：

```
mkdir -p ~/Desktop/harnessurdesign-UX-flow/.claude
```

然后把下面这整段一起复制粘贴到终端：

```
cat > ~/Desktop/harnessurdesign-UX-flow/.claude/settings.json << 'EOF'
{
  "enabledPlugins": {
    "vercel@claude-plugins-official": false,
    "supabase@claude-plugins-official": false
  }
}
EOF
```

> 如果你用 **Codex** 而非 Claude Code，跳过此步。AGENTS.md 中已内置了隔离规则。

---

## 3. 日常使用

### 3.1 启动工作流

每次使用时，打开终端，运行：

```
cd ~/Desktop/harnessurdesign-UX-flow
```

```
claude
```

> 用 Codex 的话，把 `claude` 换成 `codex`。

进入 AI 对话界面后，输入：

```
/harnessdesign-start --prd path/to/your-prd.md
```

把 `path/to/your-prd.md` 替换成你的 PRD 文件路径。

> **小技巧**：不知道文件路径？在 Finder 中找到 PRD 文件，直接拖拽到终端窗口，路径会自动填入。

**首次启动**会进入 Onboarding（Phase 0），AI 会引导你建立产品知识库。之后的任务会跳过这一步。

### 3.2 工作流四个阶段

| 阶段 | 做什么 | 你需要做什么 |
|------|--------|-------------|
| Phase 1: 上下文对齐 | AI 和你对齐对 PRD 的理解 | 回答问题、确认共识 |
| Phase 2: 调研 + JTBD | AI 引导你做用户调研和任务分析 | 参与讨论、确认洞察 |
| Phase 3: 交互设计 | AI 和你逐场景设计交互方案 | 审阅方案、给反馈 |
| Phase 4: 高保真原型 | AI 生成符合设计系统的 HTML | 审阅原型、指导修改 |

每个阶段结束时，AI 会等你确认（你会看到 `[STOP AND WAIT FOR APPROVAL]`）。**你随时可以说"不"或提出修改意见**——AI 是你的共创伙伴，不是决策者。

### 3.3 中途离开和恢复

可以随时关闭终端。下次回来时：

```
cd ~/Desktop/harnessurdesign-UX-flow
```

```
claude
```

进入对话后输入：

```
/harnessdesign-resume
```

AI 会自动恢复到你上次离开的位置。

### 3.4 查看当前状态

在对话中输入：

```
/harnessdesign-status
```

---

## 4. 更新工作流

当 GuanchengDing 通知有新版本时：

### 方法一：在 AI 对话中更新（推荐）

```
cd ~/Desktop/harnessurdesign-UX-flow
```

```
claude
```

进入对话后输入：

```
/harnessdesign-update
```

AI 会自动拉取最新代码、更新依赖、运行验证测试，并报告结果。

### 方法二：手动更新

如果方法一出问题，在终端中运行：

```
cd ~/Desktop/harnessurdesign-UX-flow
```

```
git pull origin main
```

```
pip3 install -r .harnessdesign/scripts/requirements.txt
```

```
python3 .harnessdesign/scripts/integration_test.py
```

> **注意**：更新不会影响你正在进行的任务（`tasks/` 目录）和知识库（`product-context/`）。

---

## 5. 移除工作流

如果你不再需要这个工作流：

```
rm -rf ~/Desktop/harnessurdesign-UX-flow
```

这会删除整个工作流目录，包括所有任务数据。

> **想保留任务产出物？** 在删除前，先把 `tasks/` 目录中你需要的文件（`index.html`、`wireframes/` 等）复制到其他位置。

---

## 6. 常见问题

### Q: `git clone` 提示 "Permission denied" 或 "Repository not found"

你需要 GitHub 仓库的访问权限。联系 GuanchengDing 把你的 GitHub 账号加入项目。

如果你没有 GitHub 账号：
1. 访问 https://github.com/signup 注册
2. 把你的用户名发给 GuanchengDing

### Q: `pip3 install` 提示 "Permission denied"

在命令前加 `sudo`：

```
sudo pip3 install -r .harnessdesign/scripts/requirements.txt
```

系统会要求你输入电脑登录密码（输入时屏幕不会显示任何字符，这是正常的），输完按回车。

### Q: `python3` 提示 "command not found"

Python 没有安装。回到 [1.1 安装 Python](#11-安装-python) 重新安装。

### Q: Claude Code 里出现很多奇怪的 "Vercel"、"React" 建议

你可能漏了 [第四步：配置 Claude Code](#第四步配置-claude-code可选但推荐)。按照那一步操作即可。

### Q: 工作流卡住了，AI 不响应

1. 关闭终端
2. 重新打开终端
3. 运行 `cd ~/Desktop/harnessurdesign-UX-flow && claude`
4. 输入 `/harnessdesign-resume`

### Q: 想从头开始一个任务（丢弃当前进度）

在终端中运行：

```
rm -rf ~/Desktop/harnessurdesign-UX-flow/tasks/<你的任务名>
```

然后重新 `/harnessdesign-start --prd ...` 即可。

### Q: 更新后验证测试没有全部通过

截图发给 GuanchengDing，附上终端中的错误信息。

---

## 需要帮助？

直接联系 GuanchengDing —— Slack、微信、或任何你方便的渠道。
