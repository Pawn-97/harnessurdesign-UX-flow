# Zoom AI-UX Workflow - 核心产品需求文档 (PRD)

## 1. 产品定位

Zoom AI-UX Harness Workflow 不是一个需要安装的独立软件、SaaS 产品或 Web 应用，而是一套**便携式 Skill + Knowledge 目录（`.zoom-ai/`）**，深度嵌入 AI 编码工具（AI IDE / CLI Agent）中运行。设计师无需安装任何依赖——只需将 `.zoom-ai/` 目录放入项目中，即可在支持的 AI 工具中获得完整的工作流能力。

**宿主 AI 工具即路由器**——无需自建编排引擎。Skill 文件（Markdown + YAML frontmatter）包含完整的 SOP 指令，宿主 AI 工具的 Agent 循环读取并执行这些指令，实现四阶段工作流的全部调度逻辑。设计师使用宿主 AI 工具内置的模型，无需单独配置 LLM。

**支持的宿主 AI 工具**：


| 优先级            | 工具                 | 适配状态                       |
| -------------- | ------------------ | -------------------------- |
| 主要 (Primary)   | **Claude Code**    | Skill 格式原生兼容（SKILL.md）     |
| 主要 (Primary)   | **Codex (OpenAI)** | Skill 格式适配中                |
| 次要 (Secondary) | **Cursor**         | 通过 Rules / .cursorrules 适配 |
| 次要 (Secondary) | **Trae**           | 通过自定义指令适配                  |


核心价值：解决设计师空间直觉与 AI 线性逻辑的鸿沟，消除大模型上下文污染，实现生产级高保真原型的快速推演。

## 2. 目标用户

**唯一目标用户：Zoom 内部 UX 设计师**

- **痛点**：传统 AI 工具上下文容易污染（Lost in the middle）；生成结果不符合 Zoom Design System (ZDS) 规范；缺乏深度的业务逻辑推演。
- **工作环境**：全天候在 AI 编码工具中工作，习惯使用 Markdown 梳理逻辑，使用 HTML/JS/CSS 预览原型。
- **权限与注册**：无需注册体系。基于本地环境和企业内部 Git/SSO 授权，开箱即用。

## 3. 核心交互载体 (The Interface)

本项目没有独立的前端页面，但这不代表没有"界面"。**AI 工具就是界面，文件就是状态，对话就是交互。**

1. **Skill 命令入口**：设计师在 AI 工具的对话界面中通过 Skill 命令（如 `/zoom-start`）初始化工作区、创建 `task-progress.json` 状态锚点。无需独立的 CLI 工具或终端命令——所有操作均在 AI 工具的原生界面中完成。Skill 同时提供 `/recall` 归档回引命令族（`/recall list` 浏览可回引归档目录、`/recall phase2 --query "空状态"` 按关键词精准回引、`/recall phase3-s1 --round 2` 按轮次回引），使设计师在任意阶段都能显式控制归档内容的回引。
2. **AI 工具对话面板 (Chat Panel)**：AI 工具的原生对话界面即为与工作流沟通的主阵地。自然语言输入、口述背景、方案讨论均在此进行。**Plan Mode** 映射到 AI 工具的原生计划模式（如 Claude Code 的 Plan Mode、Codex 的 Plan Mode），让设计师控制 AI 是直接响应还是先输出执行计划。
3. **IDE 资源管理器 (File Explorer)**：通过左侧文件树展示工作流状态。由于采用了 Git Worktree 隔离机制（映射到 Claude Code 的 `EnterWorktree` 命令），子任务的执行对主目录透明，设计师主要通过 `task-progress.json` 的更新和 `Strategy.md` / `Structure.md` 等核心文件来感知进度。
4. **实时渲染预览 (Live Preview & Visual Tweaks)**：废弃了反人类的代码 Diff Viewer，直接通过 IDE 的内嵌浏览器或外部浏览器实时渲染高保真 HTML。在自动化验收（Pass@1）通过后，设计师在此进行视觉审查。
5. **Markdown 逻辑树审查 (Logic Review)**：代码对设计师是透明的，但逻辑不是。设计师通过 Review Markdown 文件的变更（包含验收脚本插入的 `@Warning` 批注）来把控产品的核心走向，并最终执行 Approve（Git Merge）。

## 4. 中央路由与技能挂载架构 (Central Router & Skills Matrix)

系统摒弃了僵化的瀑布流流水线，采用"1 个中央调度器 + N 个解耦技能（Tools/Skills）"的现代化 Agent 架构。

### 4.1 中央路由 Agent (The Central Router)

**核心架构决策：宿主 AI 工具的 Agent 循环即中央路由器。** 不需要自建编排引擎（LangGraph、AutoGen 等）——Skill 文件中的 SOP 指令引导宿主 AI 工具完成所有调度逻辑。

- **职责**：整个工作流的"大脑"。宿主 AI 工具接收设计师的自然语言指令，根据 Skill SOP 判断意图，并在必要时触发 Plan Mode（输出执行计划供人类审批）。
- **执行逻辑**：宿主 AI 工具根据当前上下文和任务目标，按照 Skill SOP 中的指令动态加载和执行相应阶段的技能。Skill SOP 明确规定了每个阶段的输入、输出、工具调用和人类确认点。
- **State 隔离机制**：Skill SOP 严格规定——调度子任务时，**严禁将上一轮的脏对话传递给子任务**。只将原始 Intent 和 `task-progress.json` 中的当前子任务状态作为输入。子任务完成只回传摘要，试错过程留在子任务的局部上下文中，绝不污染全局。Skill SOP 通过显式指令实现此隔离："读取 `task-progress.json` 恢复当前状态，忽略之前的对话历史。"
- **语义合并机制 (Prompt Merging)**：若用户给出修改意见 (`user_feedback`)，Skill SOP 严禁简单重试上一轮 Prompt。SOP 指令要求将原始 `user_intent` 与 `feedback` 结构化合并为新的 Prompt，确保修改意见被精准注入，而非被旧上下文稀释。

### 4.2 核心设计技能层 (Design Skills) - 基于 Markdown+YAML 的动态挂载

系统采用"1 个中央调度器 + N 个解耦技能"的架构，技能按 4 个工作流阶段组织。**关键架构决策：所有 Skill 必须以 Markdown 文件（含 YAML Frontmatter）形式独立存放于** `**.zoom-ai/skills/`** **目录中，格式对齐 Claude Code 的 SKILL.md 规范。**

#### 4.2.1 技能矩阵 (V0.3 含 Onboarding)


| 阶段                      | 技能名                           | 职责                                                                                                  | 核心产出物                                          |
| ----------------------- | ----------------------------- | --------------------------------------------------------------------------------------------------- | ---------------------------------------------- |
| **Phase 0: Onboarding** | **Context Bootstrapper**      | 首次启用时引导用户描述行业/产品，自动 Web Search 生成本地知识库；后续 task 中持续增量学习                                              | `product-context-index.md`（L0 索引）+ 5 个 L1 知识文件 |
| Phase 1: 上下文对齐          | **Alignment Facilitator**     | 阅读 PRD，**结合知识库中的产品/行业上下文**，简述理解，引导设计师提问，确认共识                                                        | `confirmed_intent`（结构化共识摘要）                    |
| Phase 2: 调研+JTBD        | **Research Strategist**       | **先读取知识库已有内容避免重复调研**，自动执行增量市场/竞品/用户调研（Web Search + LLM + 设计师输入），引导发散讨论，产出 JTBD。**调研中发现新洞察时提议更新知识库** | `00-research.md`（调研报告）+ `01-jtbd.md`（各角色 JTBD） |
| Phase 3: 交互方案           | **Interaction Designer**      | 逐场景生成 1-2 个交互方案（AI 根据上下文自主判断方案数量，标准场景通常 1 个即可，分歧较大或存在多种合理路径时提供 2 个），生成黑白 HTML 线框原型，引导设计师逐场景选择       | `02-structure.md` + 各场景 wireframe HTML         |
| Phase 3→4 过渡: 设计合约      | **Design Contract Generator** | 从所有场景归档中定向提取跨场景信息（导航拓扑、交互承诺、全局约束），生成结构化设计合约并双向校验完备性，供设计师 Review 后作为 Phase 4 的生成蓝图                   | `03-design-contract.md`（结构化设计合约）               |
| Phase 4: 高保真原型          | **Alchemist**                 | 基于 Design Contract 整合所有场景方案，生成跨场景一致的完整高保真可交互 HTML                                                   | `index.html`（完整高保真原型）                          |
| **归档学习**                | **Knowledge Extractor**       | task 归档时从所有产出物中提取可复用的产品知识，提议追加到知识库 L1 文件（需用户逐条确认）                                                   | 知识库 L1 文件增量更新                                  |
| **独立评估: Phase 2**       | **Research Evaluator**        | JTBD 产出后、设计师收敛确认前，在独立 session（Context Reset）中评估调研质量和 JTBD 覆盖度。打破"自己调研自己评"的 confirmation bias        | 结构化评估卡片（4 维度打分 + 证据 + 改进建议）                    |
| **独立评估: Phase 3→4**     | **Contract Evaluator**        | 替代原有同一 Agent 自检的 `validate_contract`，在独立 session 中评估 Design Contract 完备性，含归档回引抽查承诺忠实度               | 结构化评估卡片（5 维度打分 + 缺口标注）                         |
| **独立评估: Phase 4**       | **Prototype Evaluator**       | Python 确定性校验通过后、设计师 Review 前，在独立 session 中通过浏览器交互验证原型与 Design Contract 的一致性                         | 结构化评估卡片（4 维度打分 + 截图证据）                         |


#### 4.2.2 引导式对话机制 (Guided Dialogue Protocol)

Phase 1-3 的核心交互模式不是传统的"指令-执行"，而是**引导式对话 (Guided Dialogue)**：AI 作为**共创伙伴 (Co-creation Partner)** 主动提问、呈现选择空间、与设计师共同探索边缘场景。具体协议：

1. **AI 作为共创伙伴主动提问**：AI 以平等共创的姿态主动提出问题、呈现多种可能方向、探索边缘 case，而非以权威导师身份引导设计师走向预设结论。语言模式强调 trade-off 呈现而非推荐式建议（如"另一个角度是 X，它的 trade-off 是..."而非"基于最佳实践，我建议..."）。
2. **收敛由人类决定**：每个阶段只有在**设计师手动确认**后才会进入下一步（如输入 `/done` 或点击 Approve）。AI 可以呈现当前覆盖面并开放性询问（"目前我们已经覆盖了 A、B、C 方向，你觉得还有需要探索的方向吗？"），但最终收敛决定权在设计师。
3. **语义合并保护**：设计师提出修改意见时，Skill SOP 严禁简单重试上一轮 Prompt。必须将原始 `user_intent` 与 `feedback` 结构化合并为新 Prompt，确保修改意见被精准注入。
4. **不满意处理**：当设计师对所有方案都不满意时，AI 询问设计师偏好——继续发散（生成新一轮方案）还是基于设计师提供的想法深化，由设计师决定方向。
5. **即时规格确认 (Inline Spec Acknowledgment)**：当 AI 检测到设计师在对话中提到具体的交互规格、设计约束或否定要求时，**立即以 `✅` 前缀的结构化列表确认**，并追问细节。此规则服务于下游信息保真度——结构化标注降低 RoundDecision 微压缩时的提取遗漏率，同时给设计师即时纠正/补充的机会。示例：
  ```
   设计师: "方案 B 不错，但空状态不要用纯文字，用插画加引导文案。列表要能拖拽。"

   AI: "收到。我记录了两个交互规格：
  ```
  1. ✅ 空状态：插画 + 引导文案（不使用纯文字提示）
  2. ✅ 列表项：支持拖拽排序
    拖拽排序，拖拽过程中的视觉反馈你有偏好吗？
    占位虚线框、半透明幽灵元素、还是直接位移？"
6. **归档回引 (Archive Recall)**：设计师可在任意阶段通过自然语言或 `/recall` 命令主动触发归档内容回引。当设计师话语中包含"回顾/找找之前/拉回来/参考下早期"等回溯意图词 + 具体内容指向时，Skill SOP 指导 AI 自动识别为 recall intent，从归档层按需提取相关内容。设计师也可通过 `/recall list` 浏览所有可回引归档（含 Token 量和摘要），做到归档内容完全可见、可控。示例：
  ```
   设计师: "把 Phase 2 里关于空状态的调研内容拉回来看看"

   AI: "我从 Phase 2 调研报告中找到了相关章节：
        [展示 '用户反馈摘要' 章节中关于空状态处理的内容]

        这里提到竞品 A 使用了插画+引导文案的空状态方案，
        与我们在场景 1 中确认的方向一致。需要我继续参考吗？"
  ```

#### 4.2.3 技能挂载与披露机制

- **统一规范模板**：所有的技能文件（如 `SKILL.md`）顶部使用标准 YAML 定义元数据（包含 `name`, `description`, `allowed_tools`），下方使用纯 Markdown 编写提示词 SOP。格式对齐 Claude Code 的 SKILL.md 规范，确保可移植性。
- **本地字典动态映射器 (Local Dict Converter)**：针对 ZDS 组件规范（延后至 ZDS JSON 提取完成后启用），系统通过辅助脚本将 ZDS JSON 翻译为 Markdown 文件。
- **渐进式披露 (Progressive Disclosure)**：宿主 AI 工具在初始化时，只将 YAML 中的 `name` 和 `description` 注入系统 Prompt（L0 级描述）。当 AI 工具认为需要执行某项技能时，才会主动去读取详细的 Markdown SOP。
- 设计师可以直接通过修改 Markdown 文件来无缝迭代 AI 的工作流（SOP）和验收标准，做到"所写即所得"。
- **人类介入机制 (Human-in-the-loop)**：Skill SOP 中通过 `[STOP]` 标记定义人类确认点。宿主 AI 工具遇到 `[STOP]` 标记时暂停执行并等待设计师确认，这映射到 AI 工具的原生审批机制（如 Claude Code 的 approval prompt）。

### 4.3 护栏与审查层 (The Guardrails) - Skill SOP + 辅助脚本

为防止 Agent 认知过载（既当选手又当裁判），系统将"执行"与"审查"彻底解耦。审查逻辑通过 Skill SOP 步骤 + 确定性辅助脚本实现。

- **机器自动化验收 (Automated Baseline Validation)**：在呈递给设计师之前，Skill SOP 指导 AI 工具强制执行两道机器审查。**只有 Pass@1 验证通过的草稿，才配弹出来让设计师点 Approve。** AI 工具通过 Bash 工具调用辅助脚本完成验收：
  - **举证校验**：校验生成过程中是否引用了 ZDS 组件，若无则阻断，防止大模型凭空捏造组件。
  - **反向提取与轻量级校验**：AI 工具调用 `scripts/validate_html.py`（基于 `BeautifulSoup` 从 HTML 中**反向提取**真实 DOM 树，并运行 Linter 和 `ux-heuristics.yaml` 认知负荷校验）。
- **AST 生成权剥夺原则**：大模型**仅负责生成 HTML**，严禁其输出所谓的 `UI_AST.json`。同时生成 HTML 和 AST 会导致"双写幻觉"——两者逻辑不一致，用虚假 AST 骗过校验。AST 必须由确定性代码（`BeautifulSoup`）从 HTML 反向解析，才具备校验可信度。
- **逻辑判官 (Logic Inquisitor) - 业务逻辑 Linting**：作为独立于主 Skill 的**专用审查 Skill**（`logic-inquisitor-skill.md`），系统引入了**"非对称红蓝对抗" (Asymmetric Red-Teaming)** 机制。彻底抛弃低效的多 Agent 聊天辩论，将逻辑推演降维成类似代码编译的确定性检查：
  - **红军目标 (魔鬼代言人)**：在 `Strategy.md` 和 `Structure.md` 生成后、进入 UI 渲染前，主 Skill 调用 Logic Inquisitor Skill 强制拦截。它的唯一 KPI 是寻找两个文档之间的逻辑断层，证明当前的 Structure 无法实现 Strategy 的目标。
  - **Fresh Session 隔离 (Context Reset for Review)**：Logic Inquisitor **必须在独立 session 中运行**（利用已有的 Context Reset 机制），输入仅为 `Strategy.md` + `Structure.md` 文本 + `confirmed_intent`，**不带生成过程的对话历史**。审查者基于文档本身的逻辑一致性审查，不受生成阶段"为什么做了这个决策"的隐式记忆影响。这打破了"同一模型既生成又审查"的 confirmation bias——审查 session 的 AI 没有"我生成过这个"的上下文记忆。
  - **对抗性激励结构 (Adversarial Incentive)**：Inquisitor Skill SOP 加入以下强制规则：
    - **强制最低输出**：审查结果必须包含至少 2 个 Warning 级问题 + 1 个需人类裁决的 Issue，即使 AI 认为文档无缺陷也必须找到值得标记的风险点——打破"快速说 PASS"的默认路径。
    - **失职问责激励**："如果你判定 PASS 但设计师在后续阶段发现了你遗漏的逻辑断层，说明审查不充分。"
  - **确定性完备性前置检查 (Completeness Lint)**：在 LLM 审查之前，Python 辅助脚本先执行一遍轻量级确定性检查（仅验证"有没有覆盖"，不判断"对不对"），给 AI 一个"基本问题别漏了"的 checklist：
    - 每个列表/数据视图场景是否有 empty state 描述
    - 涉及网络请求的场景是否描述了 error/timeout/retry 行为
    - `Structure.md` 引用的所有 scenario ID 在 `task-progress.json` 中是否存在
    - 每个写操作（create/edit/delete）场景是否有对应的 undo/confirm 描述
  - **四大审查维度**：
    1. **目标偏离 (Goal Misalignment)**：战略目标与实际设计的信息架构不符。
    2. **范围膨胀 (Scope Creep)**：悄悄塞入与核心 JTBD 无关的边缘功能。
    3. **缺失约束 (Missing Constraints)**：高风险操作缺乏逆向流程 (Undo) 或二次确认。
    4. **幸存者偏差 (Happy Path Bias)**：未考虑空状态、无权限、网络超时等边缘情况。
  - **结构化挑战 UX**：如果发现致命逻辑漏洞（Fatal），工作流挂起。不再是无聊的对话，而是在 AI 工具中输出干净的结构化「风险审计卡片」，包含漏洞证据和尖锐反问，并提供明确裁决选项：
    - `[ A ] 接受挑战，让 AI 自动削减/修改功能 (Auto-Pivot)`
    - `[ B ] 我有苦衷，补充上下文给 AI 重新推演 (Add Context)`
    - `[ C ] 闭嘴，按我说的做，直接生成 HTML (Force Override)`
  - **轻度/中度问题 (DOM 层)**：在 HTML 生成后，AI 工具调用 `scripts/ux_audit.py`（读取 `ux-heuristics.yaml` 进行认知负荷审计）。若发现瑕疵，静默在 Markdown 草稿中插入 `@Warning` 批注，不打断主流程。
- **@Warning 闭环修复 (AST-based Patching)**：当 `@Warning` 被设计师 Approve 采纳后，**彻底抛弃易碎的文本级 Search/Replace**。Skill SOP 要求 AI 输出明确的 DOM 操作指令（如 `{"action": "remove", "node_id": "btn-123"}`），然后调用辅助脚本在反向提取的真实 DOM 树上执行结构化手术，重新序列化为 HTML。确保"逻辑判官"的每条裁决都有确定性的闭环执行力，绝不破坏 HTML 结构。

### 4.4 独立评估层 (Independent Evaluator Layer) — V0.4 新增

> **设计灵感**：借鉴 Anthropic 工程团队在前端设计和长运行 Agent 中验证的 Generator-Evaluator 架构（参见 [Harness design for long-running application development](https://www.anthropic.com/engineering/harness-design-for-long-running-application-development)）。核心洞见：让同一 Agent 评估自己的产出效果很差（confirmation bias），分离评估与生成并给评估者独立上下文和对抗性激励，能显著提升产出质量。

**问题**：当前架构中，Phase 2/3/4 的核心产出物均由同一 Agent（或同一 session 延续）生成并自评。文章明确验证：agents tend to respond by confidently praising the work—even when, to a human observer, the quality is obviously mediocre. 这导致三个风险：

1. **长链漂移**：Phase 2→3→4 每一步的轻微偏差在下游放大
2. **自评偏差**：同一 Agent 既生成又评估，天然倾向于"证明自己的工作充分"
3. **错误传播**：Phase 2 的调研偏差 → Phase 3 的方案偏差 → Phase 4 的原型偏差

**解决方案**：在三个关键产出节点引入独立 Evaluator，复用已有的 Context Reset 机制和 Logic Inquisitor 的对抗模式。

**架构原则**：

1. **评估与生成的上下文隔离**：每个 Evaluator 在独立 session（Context Reset）中运行，不带生成过程的对话历史
2. **具体的评分维度**：每个 Evaluator 有 4-5 个可打分的维度，把主观判断转化为可评估的 criteria
3. **对抗性激励**：Evaluator 的 KPI 是找问题，强制最低输出（至少 N 个 Gap/Risk）
4. **人类仲裁**：评估报告附加到产出物一并呈现给设计师，设计师是最终仲裁者（不是自动化多轮迭代）
5. **确定性 + 主观判断双轨**：Python 确定性校验覆盖技术正确性，Evaluator 覆盖语义忠实度和完备性

**三个 Evaluator Skill**：


| Evaluator               | 时机                                                                 | 输入（独立 session）                                                     | 评估维度                                                                                                  | 对抗激励                               |
| ----------------------- | ------------------------------------------------------------------ | ------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------- | ---------------------------------- |
| **Research Evaluator**  | `01-jtbd.md` 生成后、设计师确认前                                            | `confirmed_intent` + `00-research.md`(摘要版) + `01-jtbd.md` + 知识库 L0 | Coverage, Evidence Grounding, Scope Fit, Actionability                                                | 强制 1 Coverage Gap + 1 Evidence Gap |
| **Contract Evaluator**  | `03-design-contract.md` 生成后、设计师 Review 前（替代原 validate_contract 自检） | `03-design-contract.md` + `confirmed_intent` + 知识库 L0 + 归档回引       | Navigation Completeness, State Consistency, Commitment Fidelity, Constraint Conflicts, Generatability | 强制 1 完备性缺口 + 1 承诺忠实度风险点            |
| **Prototype Evaluator** | Python 确定性校验通过后、设计师 Review 前                                       | `03-design-contract.md` + HTML 文件 + 浏览器交互                          | Contract Fidelity, Navigation Coherence, Visual Consistency, Edge Case Coverage                       | 通过浏览器实际交互验证，无法"纸上谈兵"               |


**开销评估**：总计额外 3-5 次 AI 调用 + ~60-80k tokens + ~4-8 分钟。相比整个工作流（多小时），这是很小的开销。

**与文章方法的关键适配差异**：

- 文章使用 5-15 轮对抗迭代追求自动化极致质量 → 本项目每个节点最多 1-2 轮，因为设计师是最终仲裁者
- 文章的前端美学评分（Design Quality, Originality）→ 本项目聚焦忠实度/完备性评分（UX 工作流的核心关注点）
- 文章的 Evaluator 用 Playwright 全程交互 → 仅 Phase 4 Evaluator 做浏览器交互（Phase 2/3 产出是 Markdown）

**渐进式验证路径**：

1. 先实现 Research Evaluator（最轻量），在 2-3 个真实 task 中验证效果
2. 有效后实现 Contract Evaluator（替换现有 validate_contract）
3. 最后实现 Prototype Evaluator（最复杂，需浏览器交互）
4. 每个 Evaluator 的评分维度通过实际使用校准（few-shot 示例）

## 5. 核心工作流与状态管理

### 5.1 混合架构与显式护栏 (The Hybrid Engine)

系统采用"全局文件驱动，局部 Skill SOP 调度"的混合架构，辅以**显式计划模式 (Explicit Plan Mode)** 与 **Git 快照隔离机制**，以平衡可控性与智能度：

- **显式计划模式 (Explicit Plan Mode)**：将判断任务复杂度的权利交还给设计师。映射到宿主 AI 工具的原生 Plan Mode（如 Claude Code 的 Plan Mode、Codex 的 Plan Mode）：开启时先输出 `Execution Plan` 供审批；关闭时极速响应单点修改。
- **状态外化 (JSON Progress Flow)**：摒弃纯 Markdown 状态驱动，剥离出纯机器读写的 `task-progress.json`。Skill SOP 明确规定：AI 每次执行前必须先读取该 JSON 恢复现场，完成一步后将对应节点的 `passes` 字段设为 `true`。绝不让大模型去长篇 Markdown 中"猜"当前进度。
- **严禁同文件并发 (Strict Serialization)**：彻底否决多个任务并发修改同一文件（如 `index.html`）的策略。如果需要并发生成，子任务必须生成独立的模块文件（如 `header.html`, `sidebar.html`），随后由确定性辅助脚本（**DOM Assembler**）将其拼接为主页面。绝不允许将合并工作抛给不可控的 `git merge`，从源头上杜绝冲突。
- **Git 仅做快照与回滚 (Snapshot & Rollback)**：废弃用 Git 处理细粒度并发冲突的幻想。Git Worktree 和 Branch 仅用于里程碑的"只读快照"保存和子任务的沙箱隔离（映射到 Claude Code 的 `EnterWorktree` / `ExitWorktree` 命令）。当设计师要求回退或放弃当前方案时，AI 工具执行 `git reset --hard` 或 `git checkout` 瞬间恢复干净环境。设计师的 Approve 等同于执行 Merge，但合并的是已通过机器校验的完整产出，不存在冲突解决环节。
- **渐进式授权与逻辑审查**：设计师的 Human-in-the-loop 集中在"逻辑层"（审查 Markdown 文件）和"视觉层"（预览 HTML）。绝不要求设计师审查 HTML 代码。

### 5.2 L0/L1/L2 分层加载与本地字典管道 (ZDS to AI Pipeline)

为了解决大模型直接读取复杂 Figma 文件导致的上下文溢出和幻觉问题，系统全面引入**分层上下文加载架构**，采用"降维字典"与"强制对齐"策略：

1. **确定性提取 (Offline Extraction)**：通过独立脚本调用 Figma REST API，将 ZDS 复杂的 Variables 和 Components 提取为纯数据结构的 JSON (此为 **L2 详情层**，仅在最终生成时按需提取，绝不进入长上下文)。此步骤为离线一次性操作，提取结果存储在本地文件系统。
2. **辅助脚本降维翻译**：辅助脚本将 L2 JSON 向上降维翻译为两层结构：
  - **L0 摘要层 (`.abstract.md` / `zds-index.md`)**：极轻量（仅含组件 ID 与一句话描述），常驻锚定层的高频检索上下文。
  - **L1 概览层 (`.overview.md`)**：包含核心骨架和使用场景（不含代码细节），用于 AI 在 Plan 阶段的决策。
3. **强制锚点生成 (Constrained Generation)**：在输出 `Structure.md` 时，Skill SOP 规定 AI 只能从 L0 索引中选菜，并使用严格的标签语法（如 `[ZDS:zds-button]`）进行标记。
4. **本地字典按需穿透 (Concurrent Exact Retrieval)**：在生成 HTML 前，Skill SOP 指导 AI 工具扫描 `Structure.md` 中的 `[ZDS:xxx]` 标签，精准读取对应的 L2 规范文件并注入上下文，实现防幻觉生成。

### 5.3 典型用户旅程 (User Journey) — V0.3 Refined

#### Phase 0: Onboarding — 产品上下文知识库初始化 (Product Context Bootstrapping)

> **触发条件**：首次使用时 `.zoom-ai/knowledge/product-context/product-context-index.md` 不存在，自动触发。后续 task 跳过此阶段。

0a. **引导式问答 (3-5 个问题)**：AI 依次询问：

1. "你所在的行业是什么？（如 SaaS、金融科技、教育科技等）"
2. "你所属的产品叫什么？用一两句话描述它的核心功能。"
3. "你的产品主要服务哪些用户角色？"
4. "你认为最重要的 2-4 个竞品是什么？"
5. （可选）"你的产品处于什么阶段？（早期/成长/成熟/转型）"

0b. **Web Search 自动生成知识库**：AI 并行发起 4 组搜索（行业趋势、竞品对比、设计模式、产品评价），将结果结构化整理为 5 个 L1 Markdown 文件 + 1 个 L0 索引：

```
.zoom-ai/knowledge/product-context/
├── product-context-index.md       # L0：锚定层常驻 (~500-800 tokens)
├── industry-landscape.md           # L1：行业趋势、市场格局
├── competitor-analysis.md          # L1：竞品功能对比、UX 策略
├── design-patterns.md              # L1：行业设计模式、最佳实践
├── user-personas.md                # L1：用户画像、场景、痛点
└── product-internal.md             # L1：产品定位、技术约束（初始较空，后续 task 学习填充）
```

0c. **🔒 设计师确认**：展示知识库概览，设计师可编辑/补充后确认。Onboarding 完成。

> **知识库生长机制**：Onboarding 只是初始化。知识库通过三个路径持续生长：
>
> 1. **用户手动编辑**：设计师随时可修改 `.zoom-ai/knowledge/product-context/` 下的 Markdown 文件
> 2. **Phase 2 增量补充**：每次 Phase 2 调研发现知识库外的新洞察时，AI 提议追加（需设计师确认）
> 3. **Task 完成学习**：每次 task 归档时，AI 从产出物中全维度提取可复用知识（产品约束、用户洞察、设计模式、竞品发现），逐条展示给设计师确认后追加到对应 L1 文件

#### Phase 1: 上下文对齐 (Context Alignment)

1. **初始化**：设计师在 AI 工具中输入 `/zoom-start --prd ./my-prd.md`。Skill SOP 指导 AI 工具创建 `/tasks/task-name/` 工作区，生成初始的 `task-progress.json`。**AI 同时将 `product-context-index.md`（L0）注入锚定层，按需加载 `product-internal.md` + `user-personas.md`（L1）到工作层。**
2. **AI 阅读 PRD**：AI 读取 PRD 内容，**结合知识库中的产品/行业背景**，向设计师简述自己的理解（"我理解你想做的是……"）。
3. **引导式对齐**：AI 引导设计师提问，确保双方对 task 的理解一致。**知识库提供的行业背景让 AI 能更精准地提问和挑战假设。**
4. **🔒 设计师手动确认**：确认 on the same page 后，系统生成 `confirmed_intent`（结构化共识摘要），进入下一阶段。

#### Phase 2: 调研 + 需求发散 → JTBD

1. **AI 自动调研**：AI **先读取知识库 L1 文件**（`industry-landscape.md`, `competitor-analysis.md`, `design-patterns.md`）了解已有知识，然后**聚焦增量信息**并行执行调研：
  - **Web Search**：**跳过知识库已覆盖的基础信息**，聚焦查找与当前 task 相关的增量趋势、竞品新功能、新用户反馈
  - **LLM 内部知识**：行业最佳实践、设计模式
  - **设计师输入**：设计师可在对话中提供竞品截图、内部文档等补充材料
2. **调研结果呈现**：先生成结构化调研报告 Markdown（`00-research.md`），然后在对话中摘要展示并与 task 的 flow/feature 关联。

6a. **知识库增量补充检查**：AI 将调研发现与知识库 L1 内容对照，若发现新洞察（新竞品功能、新行业趋势、新设计模式、新用户洞察），向设计师展示差异并提议更新。**🔒 设计师逐条确认/编辑/跳过**后，追加到对应 L1 文件。
7. **引导式发散对话**：AI 基于调研发现提出洞察、挑战假设、探索边缘场景。设计师补充、纠正、拓展。循环发散直到 AI 判断可以产出 JTBD。
8. **AI 提议收敛**：AI 向设计师确认——是总结 JTBD 还是继续发散。
9. **🔒 设计师手动确认**：确认可以总结后，AI 生成各角色 JTBD 文档（`01-jtbd.md`）。
9a. **独立评估 — Research Evaluator** ← **V0.4 新增**：JTBD 生成后、呈现给设计师前，系统在**独立 session（Context Reset）**中启动 Research Evaluator Skill。评估者的输入仅为 `confirmed_intent` + `00-research.md`（降级摘要版）+ `01-jtbd.md` + 知识库 L0 索引，**不带 Phase 2 的发散讨论历史**，打破"自己调研自己评"的 confirmation bias。评估 4 个维度：
    - **需求覆盖度 (Coverage)**：JTBD 是否覆盖了 confirmed_intent 中的所有核心需求？
    - **调研锚定度 (Evidence Grounding)**：每个 JTBD 是否有调研证据支撑？（检查 research→JTBD 引用链）
    - **范围合理性 (Scope Fit)**：有无范围膨胀或遗漏？
    - **可操作性 (Actionability)**：JTBD 是否具体到可以直接拆分场景？
    - 对抗激励：强制输出至少 1 个 Coverage Gap + 1 个 Evidence Gap
    - 评估结果以结构化卡片附加到 JTBD 一并呈现给设计师，设计师在有评估视角的情况下做收敛决策。最多 1 轮迭代。

#### Phase 3: 交互方案发散 (逐场景)

1. **场景拆分**：AI 分析所有角色的交互场景与链路，列出场景清单。
2. **🔒 设计师确认场景列表**：设计师确认/调整场景拆分后，开始逐场景推进。
3. **场景循环**（每个场景重复以下步骤）：
  - AI 为当前场景生成 **1-2 个交互方案**（AI 根据场景复杂度和前序讨论上下文自主判断：当场景有明确的最优路径时只给 1 个方案，当存在显著的设计分歧或多种合理方向时提供 2 个方案供对比）
    - **未探索替代范式标注 (Pull-model Divergence)**：每次方案展示时，AI 附带一行轻量级标注——"未探索的替代范式：[X] / [Y]"，指出与当前方案在设计哲学上根本不同的方向（如"当前方案是 modal 弹窗流程，未探索方向：inline editing / 异步处理去掉此步骤"）。设计师对某方向感兴趣时告诉 AI 展开即可，不感兴趣则跳过。此标注为 Pull 模式（~50 tokens），不生成完整替代方案，避免 Token 膨胀。
    - 为每个方案生成**黑白 HTML 线框原型**（灰度配色、简单边框、无装饰，专注布局和交互流程）
    - 设计师体验原型
    - **🔒 设计师选择**：
      - 选择某个方案 → 锁定，进入下一场景
      - 都不满意 → AI 询问设计师偏好（继续发散新方案 or 基于设计师想法深化），**由设计师决定**
4. **所有场景完成**：输出各场景确认的交互方案（`02-structure.md` + 各场景 wireframe HTML）。

#### Phase 3→4 过渡: 设计合约生成 (Design Contract)

> **解决"上下文饥饿"问题**：Phase 3 的场景级压缩（每场景 ~200 tokens 摘要）会丢失跨场景导航拓扑、具体交互承诺和全局设计约束。Design Contract 机制在进入 Phase 4 之前，从归档中定向提取这些关键信息，确保 Alchemist 拥有生成跨场景一致原型所需的全部上下文。

1. **设计合约提取 (prepare_design_contract)**：Skill SOP 指导 AI 从所有场景的归档文件（`phase3-scenario-{n}.md` + 各轮次 Recall Buffer）中，提取每个场景的结构化合约（`ScenarioContract`），然后合成为完整的设计合约（`DesignContract`），包含：
  - **导航拓扑图**：场景间的连接关系、入口条件、出口动作
    - **共享状态模型**：跨场景的状态变量（登录态、选中项、表单草稿等）
    - **全局设计约束**：从所有场景的 `constraints_added` 中去重合并的跨场景约束
    - **各场景交互承诺**：讨论中达成的具体交互决策（最多 5 条/场景，如"列表支持拖拽排序"、"空状态用插画"）
    - **边缘态清单**：明确要处理的空状态、错误态、权限缺失等
    - **视觉一致性规则**：从约束推导的全局视觉规范（信息密度、动效基调等）
2. **独立评估 — Contract Evaluator (替代原 validate_contract 自检)** ← **V0.4 改进**：将合约校验从"同一 Agent 自检"升级为**独立 session（Context Reset）评估**。Contract Evaluator Skill 在独立 session 中运行，输入仅为 `03-design-contract.md` + `confirmed_intent` + 知识库 L0，**不带 Phase 3 的场景讨论历史和 prepare_design_contract 的生成过程**。评估 5 个维度：
  - **导航完备性 (Navigation Completeness)**：所有场景出口是否都有对应入口？是否存在死胡同？
    - **状态一致性 (State Consistency)**：shared_state 的 produced_by / consumed_by 是否完整？
    - **承诺忠实度 (Commitment Fidelity)**：抽查 2-3 个场景，从归档中回引该场景最后一轮 RoundDecision，检查 interaction_commitments 是否遗漏（这是独立 Evaluator 的核心优势——自检 Agent 倾向于"我生成的肯定没遗漏"，独立评估者没有这个偏见）
    - **约束矛盾 (Constraint Conflicts)**：跨场景约束是否存在逻辑矛盾？
    - **可生成性 (Generatability)**：作为 Phase 4 输入，Contract 是否足够具体？哪些地方模糊？
    - 发现缺口时自动补充并标记 `[auto-补充]`。对抗激励：强制输出至少 1 个完备性缺口 + 1 个承诺忠实度风险点。
    - Token 开销：约 1-2 次额外 AI 调用（含归档回引）
3. **🔒 设计师 Review/编辑设计合约**：AI 将 `03-design-contract.md` **+ Contract Evaluator 评估报告** 一并呈现给设计师，设计师可以：
  - 确认导航拓扑是否正确
    - 补充遗漏的交互细节
    - 修改全局约束
    - 特别关注 `[auto-补充]` 标记的内容
    - 确认后进入 Phase 4

#### Phase 4: 高保真原型生成

1. **整合生成**：AI 基于 Design Contract 整合所有场景的确认方案，生成包含所有交互场景的完整高保真 HTML 原型（Tailwind CSS + 可点击导航 + JS 交互）。Design Contract 作为 Phase 4 工作层的核心输入（~3-5k tokens），确保跨场景的导航一致性、交互细节忠实度和视觉统一性。
2. **自动化验收（确定性校验）**：AI 工具调用 `scripts/validate_html.py`（举证校验 + DOM 反向提取 + Linter）和 `scripts/ux_audit.py`（认知负荷校验），执行 Max Retries = 3 的自修复循环。

18a. **独立评估 — Prototype Evaluator** ← **V0.4 新增**：确定性校验通过后、呈现给设计师前，系统在**独立 session（Context Reset）中启动 Prototype Evaluator Skill。评估者的输入仅为 `03-design-contract.md` + 生成的 HTML 文件路径，不带 Phase 4 的生成过程对话。Evaluator 通过宿主 AI 工具的浏览器预览能力实际交互**原型页面，评估 4 个维度：
    - **合约忠实度 (Contract Fidelity)**：抽查 Design Contract 中的 3-5 个 interaction_commitments，在原型中逐一验证
    - **导航连贯性 (Navigation Coherence)**：实际点击导航，验证场景间跳转是否符合 navigation_topology
    - **视觉一致性 (Visual Consistency)**：检查 visual_consistency_rules 是否被遵守
    - **边缘态处理 (Edge Case Coverage)**：检查 edge_cases_to_handle 中列出的场景是否实现
    - 评估反馈直接作为 Patch 指令的依据，最多 1-2 轮迭代（结合已有的自修复循环）
    - 与确定性校验互补：Python 脚本覆盖技术正确性，Evaluator 覆盖语义忠实度
19. **🔒 设计师 Review**（含评估报告）：
    - **Approve** → 进入归档
    - **Reject** → 重新生成
    - **Feedback** → AI 输出 DOM 操作指令，辅助脚本精准修补 HTML
20. **归档与沉淀**：点击 `[Complete & Archive]`，触发经验提取。
21. **🔒 知识库学习提取**：AI 从本次 task 所有产出物中全维度提取可复用的产品知识，以结构化列表展示给设计师：
    - **产品约束** → `product-internal.md`（如"移动端 SDK 不支持拖拽手势"）
    - **用户行为洞察** → `user-personas.md`（如"高频用户偏好键盘快捷键"）
    - **设计模式发现** → `design-patterns.md`（如"时间线视图对会议场景效果好"）
    - **竞品新发现** → `competitor-analysis.md`（如"Teams 新增 Loop 组件"）
    - 设计师可**逐条确认/编辑/跳过**。确认后追加到对应 L1 文件，L0 索引自动同步更新。

#### 人类控制点总览


| #   | 控制点                                      | Phase        | 设计师动作                                                         |
| --- | ---------------------------------------- | ------------ | ------------------------------------------------------------- |
| 0   | Onboarding 知识库确认                         | Phase 0      | 首次使用时确认生成的知识库内容                                               |
| 1   | 上下文对齐确认                                  | Phase 1      | 确认 AI 理解正确                                                    |
| 2   | 知识库增量补充确认                                | Phase 2      | 确认/跳过调研中发现的新洞察                                                |
| 3   | JTBD 收敛确认（含 Research Evaluator 评估报告）     | Phase 2      | 查看独立评估报告，确认可以从发散转入总结                                          |
| 4   | 场景列表确认                                   | Phase 3      | 确认/调整场景拆分                                                     |
| 5   | 每场景方案选择                                  | Phase 3      | 选择方案或提供新方向（×N 场景）                                             |
| 6   | 设计合约确认（含 Contract Evaluator 评估报告）        | Phase 3→4 过渡 | Review/编辑 `03-design-contract.md` + 查看独立评估报告，确认导航拓扑、交互承诺、全局约束 |
| 7   | 高保真原型 Review（含 Prototype Evaluator 评估报告） | Phase 4      | 查看独立评估报告 + Approve / Reject / Feedback                        |
| 8   | 归档确认 + 知识库学习                             | Phase 4      | 触发经验提取 + 逐条确认知识库更新                                            |


> **归档回引说明**：上述 7 个控制点是阶段门控（Gate），设计师必须确认后才能流转。归档回引（`/recall` 或自然语言）**不是阶段门控**，而是设计师在任意阶段随时可用的辅助能力。设计师可以在 Phase 3 讨论中回引 Phase 2 的调研报告，在 Phase 4 Review 中回引某个场景的讨论细节，无需等待特定控制点。

### 5.4 上下文工程 (Context Engineering) — V0.2 Refined

为彻底解决长对话"Lost in the Middle"、Token 浪费和注意力衰减问题，系统采用**"任务边界压缩优先 + Token 阈值安全网"**的双轨策略。核心原则：**对话过程是"脚手架"，产出物是"建筑"。脚手架完成使命后就应该拆掉。**

#### 5.4.1 三层上下文架构 (3-Layer Context Architecture)

```
┌─────────────────────────────────────────────────┐
│  锚定层 (Anchor Layer) — 始终存在                  │
│  ├── user_intent（原始需求摘要）                    │
│  ├── product-context-index.md（L0 产品上下文摘要）  │  ← V0.3 新增
│  ├── 语义标签摘要索引（路径+摘要+标签）              │
│  └── 当前 phase + 当前场景的进度状态                 │
│                                        ~6-7k tokens │
├─────────────────────────────────────────────────┤
│  工作层 (Working Layer) — 当前任务的完整上下文       │
│  ├── 当前 Phase 的结构化产出物                      │
│  ├── 当前场景/对话的完整消息历史                     │
│  └── 活跃的调研数据/参考资料                        │
│                                      10k-50k tokens │
├─────────────────────────────────────────────────┤
│  归档层 (Archive Layer) — 磁盘文件，按需回引         │
│  ├── phase1-alignment.md                           │
│  ├── phase2-research.md                            │
│  ├── phase3-scenario-{n}.md                        │
│  └── 完整对话历史                                   │
│                                    不占上下文 token  │
└─────────────────────────────────────────────────┘
```

#### 5.4.2 任务边界压缩 (Primary Strategy)

任务边界压缩是**主动式**的，在每个自然完成点执行。Skill SOP 在每个阶段结束时明确指令 AI 执行对应的归档操作：


| 触发点                       | 归档操作                                                                                            | 上下文保留                                                                           | 设计师感知                            |
| ------------------------- | ----------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- | -------------------------------- |
| Phase 1 完成                | 完整对话 → `phase1-alignment.md`                                                                    | `confirmed_intent`（~500 tokens）                                                 | 静默                               |
| Phase 2 完成                | 调研报告 + 完整对话 → `phase2-research.md`                                                              | JTBD 摘要 + 关键约束列表（~2k tokens）                                                    | 提示："上一阶段讨论已归档至 xxx"              |
| 场景 N 完成                   | 该场景对话 + 该场景所有 `RoundDecision` 卡片 → `phase3-scenario-{n}.md`                                     | 选定方案一句话描述（~200 tokens），语义标签保留在摘要索引中                                             | 静默                               |
| Phase 3 全部完成              | 保留场景方案总表                                                                                        | 各场景选定方案摘要（~2k tokens）                                                           | 提示："交互方案已归档"                     |
| Phase 3→4 过渡              | 从所有场景 Recall Buffer 提取 `ScenarioContract`，合成 `DesignContract`，双向校验完备性 → `03-design-contract.md` | DesignContract（~3-5k tokens，含导航拓扑、交互承诺、全局约束、边缘态清单）                              | 提示："设计合约已生成，请 Review" + 🔒 设计师确认 |
| Phase 4 每轮 Feedback→Patch | 该轮 feedback 对话 page-out 到 `phase4-review-round-{m}.md`（仅备份）                                     | `accumulated_constraints`（追加式约束列表，~200 tokens）+ 当前已 patch 的 HTML（文件引用，不占 token） | 静默                               |


**摘要索引 (Summary Index)**：压缩后始终保留一份索引，确保 AI 知道"我之前做过什么、东西在哪、以及归档中有哪些可能需要回引的关键信息"。索引采用**两层结构**：第一行为路径 + 方案摘要（与现有设计一致），第二行为**语义标签 (Semantic Tags)**——结构化的检索锚点，使 AI 能通过 pattern matching 判断何时需要触发归档回引，解决"回引盲区"（AI 不知道归档里有什么 → 不触发 recall → 信息丢失）问题：

```markdown
## Session Archive Index

### Phase 1 (对齐): .zoom-ai/memory/sessions/phase1-alignment.md
> 设计师需要一个 Zoom 会议仪表盘重设计，核心是提升会前准备效率
> 🏷️ [关键词:会前准备,仪表盘,效率] [约束:面向内部UX团队]

### Phase 2 (调研+JTBD): .zoom-ai/memory/sessions/phase2-research.md
> 3 个角色 JTBD: 主持人（高效启动）、参会者（快速进入状态）、管理员（监控使用率）
> 🏷️ [关键词:竞品A,竞品B,空状态,可访问性,移动端] [章节:市场趋势,竞品对比,用户反馈]

### Phase 3 场景 1 (会前准备): .zoom-ai/memory/sessions/phase3-scenario-1.md
> 选定方案 B: 时间线视图，集成日历 + 议程 + 参会者状态
> 🏷️ [约束:首屏≤5模块,支持零引导上手] [交互:拖拽排序,空状态用插画] [状态:日历数据,参会者状态] [依赖:→场景3筛选]

### Phase 3 场景 2 (会中协作): .zoom-ai/memory/sessions/phase3-scenario-2.md
> 选定方案 A: 浮动工具栏
> 🏷️ [约束:动效≤300ms] [交互:悬停展开工具面板] [状态:会议进行态] [依赖:←场景1参会者状态]
```

**六类语义标签**：


| 类型             | 格式          | 数据来源                                                 | 提取时机                 | recall 触发场景                      |
| -------------- | ----------- | ---------------------------------------------------- | -------------------- | -------------------------------- |
| `keyword`      | `[关键词:xxx]` | 归档文件 YAML frontmatter 的 `keywords` 字段（TF-IDF top-10） | 归档写入时确定性提取           | 任意 Phase 的内容检索（设计师说"之前讨论过的 xxx"） |
| `section`      | `[章节:xxx]`  | 归档文件 YAML frontmatter 的 `sections` 字段                | 归档写入时确定性提取           | section 粒度回引的快速定位（直接按章节名匹配）      |
| `constraint`   | `[约束:xxx]`  | `RoundDecision.constraints_added`                    | 场景完成时确定性提取           | AI 生成新方案时检查是否违反已有约束              |
| `interaction`  | `[交互:xxx]`  | `RoundDecision.interaction_details`                  | 场景完成时确定性提取           | Phase 4 生成 HTML 时需要具体交互规格        |
| `shared_state` | `[状态:xxx]`  | `ScenarioContract.shared_state_dependencies`         | Design Contract 阶段回填 | 跨场景一致性检查                         |
| `dependency`   | `[依赖:→场景N]` | `ScenarioContract.exit_actions`                      | Design Contract 阶段回填 | 导航拓扑验证                           |


**提取时机与机制**：

- **归档写入时**：`keyword` 和 `section` 标签从归档文件的 YAML frontmatter 中**确定性提取**（TF-IDF 计算关键词 + Markdown 标题解析），适用于所有 Phase 的归档文件。这两类标签确保 Phase 1/2 的归档也具备 recall 触发能力
- **场景完成时**：`constraint` 和 `interaction` 标签从该场景所有 `RoundDecision` 中**确定性提取**（遍历结构化字段，无需 LLM），在执行场景边界压缩时同步完成
- **Design Contract 生成后**：`shared_state` 和 `dependency` 标签从 `ScenarioContract` 中提取并**回填**到已有索引条目中，补全跨场景维度

**自适应预算控制**：

- 每场景最多 8 个标签（~120-200 tokens/场景），根据场景复杂度自适应：
  - 简单场景（1 轮即定，无跨场景依赖）：2-3 标签
  - 复杂场景（3+ 轮发散，多个跨场景依赖）：最多 8 标签
  - 判断依据：`len(constraints_added)` + `len(interaction_details)` + 是否有 `shared_state_dependencies`
- 8 场景总计标签层 ~1-1.6k tokens，加上现有摘要，整个索引 ~2.5-3.5k tokens
- 锚定层从 ~3k 膨胀到 ~5-6k（200k 窗口的 ~2.5-3%，完全可接受）

#### 5.4.2.0 Phase 2 话题级 Context Reset (Topic-level Context Reset)

任务边界压缩解决了 Phase 间的上下文管理，但 **Phase 2 的发散讨论阶段是整个工作流中最大的上下文退化风险区**：它既是最鼓励深度 brainstorm 的阶段（AI 主动挑战假设、探索边缘场景、设计师补充大量材料），又是对话轮次最长的阶段。在极端情况下（20 轮深度发散 + 多份设计师补充材料），传统的增量压缩（Compaction）策略虽能控制 Token 总量，但模型在长对话中的注意力退化和"匆忙收工"倾向仍不可避免。

**核心理念：Context Reset > Context Compaction**

系统摒弃了"在同一对话内持续压缩"的 Compaction 策略，转而采用 **Context Reset**——在每个话题域的自然边界处**彻底清空工作层**，用结构化交接文件（InsightCard）将状态传递给全新的 LLM session。这确保每个话题的 LLM 输入都是干净的、结构化的，模型质量不随对话长度退化。

**Phase 2 的内部阶段结构 (Internal Stages)**：

Phase 2 虽然在宏观状态机中是单一节点，但内部有清晰的语义阶段：

```
[Stage A] 调研执行 ──→ [Stage B] 调研呈现与关联 ──→ [Stage C] 发散讨论 ──→ [Stage D] JTBD 收敛
    AI 并行调研               生成 00-research.md         引导式 brainstorm         设计师确认可收敛
    (Web Search +              摘要展示给设计师             每个话题域独立 session     → 生成 01-jtbd.md
     LLM 知识 +                关联到 task flow            话题切换 = Context Reset
     设计师材料)               → Stage B→C 转换时           InsightCard = 交接文件
                                报告降级为摘要版
```

**Stage C 的执行模型**：每个话题域是一次**独立的 LLM 调用**（session），而非同一个长对话中的连续片段。话题切换不是"压缩旧对话释放空间"，而是"结束旧 session → 生成交接文件 → 用交接文件启动新 session"。Skill SOP 通过显式指令管理此流程："当检测到话题切换时，将当前讨论总结为 InsightCard，写入 `phase2-insight-cards.md`，然后读取该文件作为新话题的输入。"

**话题域分类 (Topic Domains)**：

Phase 2 的发散讨论通常围绕以下话题域展开：


| 话题域                | 典型内容            |
| ------------------ | --------------- |
| `market_trends`    | 市场趋势、行业方向       |
| `competitive`      | 竞品功能对比、竞品 UX 分析 |
| `user_pain_points` | 用户痛点、反馈分析       |
| `edge_cases`       | 边缘场景探索          |
| `design_patterns`  | 设计模式、最佳实践       |
| `tech_constraints` | 技术约束、实现限制       |
| `business_context` | 业务上下文补充         |
| `free_exploration` | 自由探索（兜底）        |


**话题转换检测**：

**AI 自主标记（零额外 LLM 调用）**：在 Guided Dialogue SOP 中，要求 AI 在话题转换时自然地总结上一个话题的关键发现，并过渡到新话题。AI 本身参与对话，具备话题感知能力，这是"免费"的。AI 检测到话题域切换时，在回复中插入语义转折，Skill SOP 据此识别 Context Reset 时机。

> **为何不再需要被动兜底（15k 软预算）**：在 Compaction 模型下，如果 AI 标记失灵（话题渐变而非跳转），工作层会在单个对话中无限膨胀，因此需要 15k 软预算作为安全网。在 Context Reset 模型下，即使 AI 标记失灵、单个话题膨胀到 15k+，这只是**当前话题 session** 的问题——不会污染后续话题的上下文质量，因为下一个话题会从零开始。单话题内的膨胀由全局水位 Advisory 25k 兜底即可。

**交接文件：InsightCard**：

InsightCard 是话题间的**结构化交接文件**，不是压缩产物。它从已完成话题的对话中提取关键洞察，持久化到磁盘文件 `phase2-insight-cards.md`，在每次新话题 session 启动时从磁盘完整读入。

```yaml
topic_domain: "competitive"
topic_label: "竞品 A (Notion) 的空状态设计"

key_insights:                              # 最多 5 条核心发现
  - "Notion 使用插画+引导文案的空状态，用户好评率 78%"
  - "Asana 采用任务模板建议，降低认知负荷"
  - "3 个竞品中 2 个采用渐进式信息展开"

constraints_discovered:                    # 本话题中发现的设计约束
  - "Zoom 用户群体含大量低频用户，不能假设用户熟悉功能"

open_questions:                            # 尚未解决的问题（被动保留，不主动注入后续 prompt）
  - "移动端场景下空状态的交互方式待定"

designer_materials_referenced:             # 设计师提供的材料索引
  - "竞品截图 A3.png"

related_flows:                             # 与 task 的哪些 flow/feature 相关
  - "会前准备-空状态"
  - "仪表盘-首屏布局"

blind_spots:                               # AI 自评：本次讨论中未主动探索的角度（反过早收敛机制）
  - "未讨论 progressive disclosure 方式的空状态（先展示部分数据再引导完善）"
  - "未考虑空状态作为 upsell/cross-sell 入口的可能性"
  - "未对比移动端与桌面端空状态设计的差异化策略"
```

每张 InsightCard 约 **350-650 tokens**（对比话题块完整讨论通常 3-8k tokens），信息密度提升约 85-92%。`blind_spots` 字段约增加 50-100 tokens，在归档预算内可忽略。

`**blind_spots` 处理策略 (Self-Reflect at Archive Boundary)**：Skill SOP 规定 AI 在每个话题域归档前**必须**输出 2-3 条"本次讨论中未主动探索的角度"。此字段服务于**反过早收敛**——后续 Phase 引用 InsightCard 时，设计师能看到"当时跳过了什么"，有机会在更晚的阶段重新拉起被搁置的方向。`blind_spots` 与 `open_questions` 性质不同：`open_questions` 是讨论中发现但未解决的问题，`blind_spots` 是讨论中**根本没有触及**的角度。

`**open_questions` 处理策略**：被动保留在 InsightCard 中，随交接文件自然传递给后续话题 session。依赖 AI 在后续 session 中自然发现并提起。不主动注入后续话题的 system prompt，避免累积膨胀。

**调研报告降级 (Research Report Downgrade)**：

进入 Stage C 发散讨论阶段后，工作层中的 `00-research.md` 从完整版降级为 **ToC + 关键数据点摘要**（~2-3k tokens）。完整版归档到磁盘文件 `phase2-research-full.md`，需要时通过 `recall(target=phase2, granularity=section, query="xxx")` 按需回引。降级时机由 Skill SOP 在检测到 Stage B→C 转换时指导 AI 执行。降级后的摘要版作为每个话题 session 的固定输入之一。

**Context Reset 流程**：

```
话题 A 讨论进行中（独立 LLM session）
     ↓
AI 检测到话题转换（A→B）
     ↓
┌─ AI 提取 InsightCard（结构化 YAML 格式）
├─ 话题 A 完整对话 → page-out 到 Recall Buffer:
│    .zoom-ai/memory/sessions/phase2-topic-{domain}-{n}.md
├─ InsightCard 追加写入磁盘: phase2-insight-cards.md
├─ 🔄 彻底清空工作层 (Context Reset)
└─ 启动新 LLM session（话题 B）:
     输入 = 锚定层 + 从磁盘读入所有 InsightCards + 调研摘要 + "继续发散，下一话题是 B"
     （工作层从零开始，无历史残留）
```

**与 Compaction 模型的关键区别**：


|           | Compaction（旧）                 | Context Reset（新）                                                               |
| --------- | ----------------------------- | ------------------------------------------------------------------------------ |
| **话题切换时** | 压缩旧话题消息，保留 InsightCard 在上下文旁  | 彻底清空工作层，InsightCard 从磁盘文件读入                                                    |
| **工作层状态** | 累积式——InsightCards 在上下文中逐渐增长   | 恒定式——每次从磁盘读入完整快照，无历史残留                                                         |
| **模型质量**  | 随对话长度退化（注意力衰减、匆忙收工）           | 每个话题 session 的质量恒定，不受历史长度影响                                                    |
| **被动兜底**  | 需要 15k 软预算作为安全网               | 不需要——单话题膨胀不影响后续话题                                                              |
| **状态恢复**  | 序列化包含 messages + InsightCards | Skill SOP 指导 AI 读取 `phase2-insight-cards.md` + `task-progress.json`，零 messages |


**摘要索引新增话题级条目**：

```markdown
### Phase 2 话题 1 (竞品分析): .zoom-ai/memory/sessions/phase2-topic-competitive-1.md
> Notion/Asana/Monday 空状态对比，渐进式信息展开最佳实践
> 🏷️ [关键词:竞品A,空状态,渐进式展开] [约束:首屏≤5模块来自竞品数据]
```

**工作层峰值分析**：

由于每个话题 session 从零构建，工作层峰值**不随话题数量增长**，而是恒定的：

```
Phase 2 任意话题中（无论第 1 个还是第 6 个），工作层内容：
├── 锚定层（intent + 摘要索引）              ~5-6k tokens
├── 所有 InsightCards（从磁盘读入）           ~2-3k tokens（5 张 × 500 tokens）
├── 00-research.md 摘要版                   ~2-3k tokens
├── 当前话题活跃对话（未压缩）                ~3-5k tokens
└── 总计 ~12-17k tokens（恒定，永远在最佳注意力区间内）
```

> **对比旧模型**：Compaction 模型下工作层也能控制在 ~10-15k，但 InsightCards 是从被压缩的长对话上下文中提取的，提取质量随对话长度下降。Reset 模型下每张 InsightCard 都是从新鲜的短对话（单话题 session）中提取的，提取保真度更高。

**Stage D (JTBD 收敛) 输入**：

最后一个话题的 InsightCard 提取后，执行最后一次 Context Reset，启动 Stage D session：

- 锚定层 ~5-6k + 所有 InsightCards ~3k + 调研摘要 ~3k + "请基于以上洞察总结 JTBD" ≈ **12-15k tokens**
- 生成空间充裕，且输入完全是结构化的，无任何对话残留

**Recall 路径解析扩展**：


| 目标                       | 路径                             |
| ------------------------ | ------------------------------ |
| `phase2 + topic_domain`  | `phase2-topic-{domain}-{n}.md` |
| `phase2`（无 topic_domain） | `phase2-research.md`（原有行为不变）   |


#### 5.4.2.1 轮次边界微压缩 (Round-boundary Micro-compression)

任务边界压缩解决了 Phase 间和场景间的上下文管理，但 Phase 3 的**场景内**存在压缩盲区：一个复杂场景可能经历多轮"方案展示 → 设计师反馈 → 方案迭代"的发散-收敛循环（设计师反复拒绝方案、补充上下文、要求新方向），导致工作层 Token 在**单场景完成之前**就膨胀到危险水平。为此，系统引入**轮次边界微压缩**机制，将压缩粒度从"场景级"下沉到"轮次级"。

**核心概念：轮次 (Round)**

在 Phase 3 的场景循环中，每次"AI 呈现 1-2 个方案 → 设计师做出反馈/选择"构成一个**轮次 (Round)**。轮次边界是场景内的自然语义断点。

**双触发机制**：

1. **轮次边界触发（主动）**：每个 Round 结束时（设计师给出反馈后），Skill SOP 指导 AI 自动执行微压缩。
2. **工作层软预算触发（被动）**：当工作层 Token 超过 **20k tokens 软预算**时，Skill SOP 指导 AI 强制对最老的未压缩 Round 执行微压缩。此软预算独立于全局安全网，是更早介入的第一道防线。

**微压缩操作**：

每个 Round 结束时，Skill SOP 指导 AI 执行：

1. **提取决策卡片 (RoundDecision)**：从该轮对话中提取结构化决策摘要，保留在工作层。
2. **Page-out 完整对话**：该轮的完整消息历史归档到 Recall Buffer 文件（`.zoom-ai/memory/sessions/phase3-scenario-{n}-round-{m}.md`），从工作层移除。

**决策卡片结构 (RoundDecision)**：

```yaml
round: 1
options_presented:
  - "A: 时间线视图 — 横向时间轴展示会前/会中/会后状态"
  - "B: 卡片流视图 — 垂直卡片瀑布流，按优先级排列"
  - "C: 列表视图 — 紧凑表格，适合高频用户"
verdict: "rejected_all"           # selected | rejected_all | partial_accept
selected_option: null
rejection_reason: "三个方案信息密度都太高，新用户无法理解"
constraints_added:
  - "首屏信息密度 ≤ 5 个交互模块"
  - "必须支持无引导上手"
key_discussion_points:
  - "设计师强调 Zoom 用户群体包含大量低频用户"
  - "需要渐进式信息展开而非一次性铺开"
interaction_details:              # 具体交互规格（Phase 4 Design Contract 提取的重要来源）
  - "列表项支持拖拽排序，拖拽时显示占位虚线框"
  - "空状态使用插画 + 一句引导文案，不使用纯文字提示"
```

每张决策卡片约 500-800 tokens（采用"宽口提取"策略后略有膨胀，见下方提取保真机制），远小于该轮完整对话（通常 3k-8k tokens），压缩率约 85-93%。

> `**interaction_details` 字段说明**：与偏宏观的 `key_discussion_points`（捕获决策背后的推理）互补，`interaction_details` 专门捕获具体的交互规格——动效、手势、组件行为、边缘态处理等。这些细节是 Phase 3→4 过渡时 Design Contract 提取的重要来源，也是摘要索引中语义标签的核心数据来源。如果 RoundDecision 中未捕获某个交互细节，Design Contract 也大概率会遗漏，语义标签索引也无法为其生成 recall 触发锚点。

**提取保真机制 (Extraction Fidelity)**：

RoundDecision 是微压缩后唯一保留在工作层的表示，是整个信息保真度链路的"漏斗口"。为防止三类易遗漏信息（附带提及的交互规格、否定式规格如"别用弹窗"、隐含约束如"新用户也要能用"→"支持零引导上手"）在压缩时丢失，系统采用"上游预防 + 宽口提取 + 启发式检查"三层防线：

1. **上游预防——即时确认规则 (Inline Spec Acknowledgment)**：AI 在引导式对话中检测到设计师提及具体交互规格、约束或否定要求时，立即以 `✅` 前缀的结构化列表确认（详见 §4.2.2 引导式对话协议第 5 条），在对话历史中创造结构化标注，降低下游提取遗漏率。
2. **宽口提取 (Over-extraction)**：微压缩的提取指令采用"宁滥勿缺"策略：
  - `interaction_details` 必须包含设计师提到的**所有**具体交互规格，包括否定式（"不使用弹窗"）
  - 必须提取 AI 以 `✅` 确认且设计师未反对的条目
  - 隐含约束需转化为显式表述（如"新用户也要能用" → "需支持零引导上手"）
3. **启发式完备性检查 (Heuristic Completeness Check)**：提取后执行确定性规则检查（非 LLM），当检测到潜在遗漏时才触发补充提取：
  - **轮次/条目比例检查**：设计师 3+ 轮发言但只提取 <2 条规格 → 告警
  - **否定词检查**：设计师文本中有"不要/别/禁止/避免"但提取结果中无否定项 → 告警
  - **✅ 标记检查**：对话中的 ✅ 确认数 > 提取条目数 → 告警
  - 告警时将检查结果作为补充 Prompt 触发一次定向补充提取，预估 ~30% 的 Round 会触发

**微压缩后的工作层状态示例**：

```
场景 3 进行到 Round 3 时，工作层内容：
├── 锚定层（intent + 语义标签索引）           ~5-6k tokens
├── Round 1 决策卡片                       ~500 tokens
├── Round 2 决策卡片                       ~500 tokens
├── Round 3 当前活跃对话（未压缩）            ~3-5k tokens
└── 总计 ~9-12k tokens（远离 20k 软预算）
```

**归档回引机制 (Archive Recall System)**：

归档层不是单向通道——系统提供完整的**双向回引能力**，使压缩进入归档的内容可以按需精准回引。回引通过统一的 `recall` 命令族实现，覆盖所有 Phase 的归档文件，支持 4 级粒度，并受严格的 Token 预算指导保护。

**（一）统一 recall 命令族**

设计师可通过自然语言或 `/recall` 命令触发回引，Skill SOP 指导 AI 解析目标并从归档文件中提取内容：

```
recall(target, granularity, query, max_tokens)

target    = {phase, scenario_id?, round_number?}  # 定位归档文件
granularity = excerpt | section | round | full     # 回引粒度
query     = "空状态"                                # 关键词（excerpt/section 必填）
max_tokens = 5000                                  # 可选，覆盖默认预算
```

**回引路径解析**：

- `phase1` → `phase1-alignment.md`
- `phase2` → `phase2-research.md`（调研报告摘要/完整版）
- `phase2 + topic_domain` → `phase2-topic-{domain}-{n}.md`（话题级 Recall Buffer）
- `phase2 + "research_full"` → `phase2-research-full.md`（调研报告降级后的完整版归档）
- `phase3 + scenario_id` → `phase3-scenario-{id}.md`（含该场景所有 RoundDecision 卡片）
- `phase3 + scenario_id + round_number` → `phase3-scenario-{id}-round-{round}.md`（Recall Buffer）
- `phase4 + round_number` → `phase4-review-round-{round}.md`

**（二）4 级粒度策略**


| 粒度            | 典型场景              | 实现方式                          | Token 代价      |
| ------------- | ----------------- | ----------------------------- | ------------- |
| `excerpt`     | AI 只需一条具体信息       | 按段落切分归档文件，关键词评分，返回 top-3 段落   | 100-500       |
| `section`（默认） | 需要某主题的完整讨论        | 按 Markdown H2/H3 标题切分，返回最匹配章节 | 500-2k        |
| `round`       | 需要某轮完整决策上下文       | 返回整个 Round 文件                 | 3k-8k         |
| `full`        | 极端情况，需完整 Phase 归档 | 返回整个归档文件，强制截断在预算上限内           | max_tokens 上限 |


默认粒度为 `section`——Token 效率和信息完整度的最佳平衡点。检索使用确定性关键词匹配（非 LLM），对设计术语（"空状态"、"拖拽排序"、"竞品分析"）足够精准。若关键词评分为 0（未命中），自动升级到下一粒度（section → round → full），直到命中。

**（三）回引预算指导 (RecallBudget)**

Skill SOP 对回引操作设定以下预算指导，AI 在执行回引时遵循这些上限：


| 参数           | 值          | 理由                              |
| ------------ | ---------- | ------------------------------- |
| 单次回引软上限      | 5k tokens  | 一个 section 通常 500-2k，给足余量       |
| 单次回引硬上限      | 15k tokens | full 粒度的安全阀（Phase 2 报告最多回引 15k） |
| 单次交互中回引总预算   | 30k tokens | 一次交互中最多并发 3-6 次 recall          |
| 工作层绝对上限（含回引） | 80k tokens | 200k 窗口的 40%，为 LLM 生成保留充足空间     |


**超预算降级策略**：

- TRUNCATE：`full` → 自动降级到 `section`；`section` → 截断保留标题+开头；`excerpt` → 减少返回段落数
- DENY：AI 在回复中**明确告知**设计师"当前上下文已满，建议先完成当前讨论后再回顾"（绝不静默吞掉）

**（四）回引内容生命周期规范**

回引内容以临时上下文注入工作层，具有严格的生命周期：


| 规则      | 描述                                               |
| ------- | ------------------------------------------------ |
| 作用域     | 默认为当前交互完成后即释放。Skill SOP 可指定"保留至当前子任务完成"          |
| 状态恢复时排除 | 回引内容不写入 `task-progress.json`，崩溃恢复后需要时重新触发 recall |
| 预算隔离    | 回引内容的 Token 独立于工作层水位计算                           |
| 不可嵌套    | 回引内容中不得触发新的回引（防止递归 page-in）                      |
| 冲突处理    | 回引内容注入时附加提示："如果与当前工作层的最新决策/约束冲突，以当前工作层为准"        |


**（五）双通道触发**

1. **AI 自主回引**：通过摘要索引的语义标签做 pattern matching 判断何时需要读取归档内容。标签体系覆盖 6 类（详见上方语义标签），覆盖所有 Phase。
2. **设计师显式回引**：
  - **自然语言**：设计师在对话中说"把 Phase 2 的竞品分析拉回来"，AI 自动识别 recall intent 并从归档中提取
  - `**/recall` 命令**：`/recall list`（零成本浏览归档目录，含 Token 量和摘要）、`/recall phase2 --query "空状态"`（精确回引）

**（六）边界情况处理**


| 场景                | 处理方式                                         |
| ----------------- | -------------------------------------------- |
| 归档文件丢失/损坏         | graceful degrade：告知设计师"该归档文件已不存在"            |
| 循环回引（同一目标回引 3+ 次） | 自动升级为工作层常驻内容，纳入 20k 软预算                      |
| 回引内容与工作层冲突        | 工作层最新状态优先。回引内容附加 `[RECALL CONTEXT]` 标记       |
| 设计师编辑归档文件后回引      | 惰性索引刷新：recall 时检测文件修改时间 > 索引归档时间，自动重新解析并更新标签 |


#### 5.4.2.2 Phase 4 反馈边界压缩 (Review-round Compression)

Phase 3 的轮次微压缩解决了"发散探索"阶段的上下文膨胀，但 Phase 4 的 Review 循环（Feedback → Patch → Feedback → Patch → ... → Approve）同样存在压缩盲区。设计师对 8 场景高保真原型进行 5-6 轮精修时，feedback 对话在工作层中持续累积。

**核心洞察：HTML 即状态的单一真相源 (HTML as Single Source of Truth)**

Phase 4 与 Phase 3 的反馈循环有本质区别：


|          | Phase 3 场景内循环                | Phase 4 Review 循环                      |
| -------- | ---------------------------- | -------------------------------------- |
| **性质**   | 发散探索（多方案对比、拒绝、换方向）           | 收敛精修（单一 HTML 上的增量调整）                   |
| **状态载体** | 对话中的决策（需 RoundDecision 卡片保留） | HTML DOM（每轮 patch 通过 Assembler 物化在文件里） |
| **历史价值** | 高——被拒方案的原因影响后续方案生成           | 低——视觉微调执行完即无价值                         |
| **回引需求** | 可能（"回到 Round 1 的方案 A"）       | 极低（设计师不会说"回到第 3 轮的间距"）                 |


Phase 4 的工作模式是：**读当前 HTML（已含所有历史 patch）→ 接收最新 feedback → 输出 DOM 操作指令 → 辅助脚本执行**。每轮 patch 执行完，修改已物化在 `index.html` 中。中间轮次的 feedback 对话就是"脚手架"——完成使命后应当拆掉。

**压缩策略**：

每轮 Feedback→Patch 完成后，Skill SOP 指导 AI 执行：

1. 从该轮 feedback 中提取新增的视觉/交互约束，**追加**到 `accumulated_constraints` 列表
2. 该轮完整 feedback 对话 page-out 到 `phase4-review-round-{m}.md`（仅做备份，不期望回引）
3. 从工作层移除该轮对话

`**accumulated_constraints` 约束列表**：

与 Phase 3 的 `RoundDecision`（300-500 tokens）不同，Phase 4 只需保留一个**追加式约束列表**——每轮从 feedback 中提取持续生效的约束条件（非一次性的定点修改不记录）：

```yaml
accumulated_constraints:
  - "全局字体 base size 16px"          # Round 1
  - "按钮圆角统一 8px"                   # Round 2
  - "主色不能用纯黑，使用 #1a1a2e"        # Round 3
  - "侧边栏宽度固定 280px"               # Round 4
```

每条约束 ~20 tokens，5-6 轮精修后整个列表 ~100-200 tokens，极其轻量。

**与语义合并机制的关系修正**：

Phase 4 的 Semantic Merge 输入应为 `**intent + DesignContract + accumulated_constraints + 最新 feedback`**，而非仅 `intent + feedback`。`accumulated_constraints` 作为额外护栏，防止 AI 在生成 DOM 操作指令时意外违反前几轮确立的约束。

**压缩后工作层状态示例**：

```
Phase 4 进行到 Review Round 5 时，工作层内容：
├── 锚定层（intent + 语义标签索引）             ~5-6k tokens
├── DesignContract                           ~3-5k tokens
├── accumulated_constraints（5 轮累积）        ~150 tokens
├── Round 5 当前活跃 feedback 对话（未压缩）    ~1-2k tokens
└── 总计 ~9-13k tokens（与 Phase 4 刚进入时几乎持平）
```

> **注意**：`index.html` 本身不计入上下文 Token——它作为文件存储在磁盘上，AI 工具通过文件读取获取当前 DOM 状态，而非将整个 HTML 塞入 Prompt。

#### 5.4.3 工作层水位监控与 Token 阈值安全网

系统采用**四级渐进式防御**来管理工作层 Token：前三级为工作层水位监控（主动防御），最后两级为全局安全网（被动兜底）。所有水位管理逻辑通过 Skill SOP 中的显式指令实现——AI 工具在每次交互前评估当前上下文规模并按指令执行对应操作。

**（一）工作层水位监控 (Working Layer Water Level Monitor)**

工作层的 10k-50k tokens 描述性范围此前没有强制约束——唯一的保护是全局安全网（170k/190k），但模型注意力衰减（RoPE U 型注意力分布导致的"Lost in the Middle"）在工作层 30-50k 时就已显著影响生成质量，远早于安全网触发。为填补这一防御真空，Skill SOP 新增全局工作层水位指导：


| 水位                | 阈值     | 触发操作                                                                                        | 设计师感知                       |
| ----------------- | ------ | ------------------------------------------------------------------------------------------- | --------------------------- |
| **绿区**            | 0-25k  | 正常运行，无干预                                                                                    | 无感                          |
| **黄区** (Advisory) | 25-40k | 内部预警；若当前 Phase 支持微压缩（Phase 3 Round），加速触发。Phase 2 因采用 Context Reset 机制，工作层恒定在 12-17k，不会触及此水位 | 无感                          |
| **橙区** (Active)   | 40-60k | 主动压缩：将最老的 50% 对话历史压缩为结构化中间摘要（保留在工作层，不归档，因为阶段未完成）                                            | 轻提示："上下文已优化以保持生成质量"         |
| **红区** (Critical) | 60k+   | 强制深度压缩：保留锚定层 + 最近 2 轮对话 + 结构化摘要                                                             | Warning："上下文已大幅压缩，建议确认关键信息" |


**与现有机制的层级关系**：

```
Phase 2 话题级 Context Reset ── Phase 2 专属（每个话题独立 session，工作层恒定 12-17k，无需软预算）
Phase 3 Round 软预算 20k ───┐
                             ├── 工作层水位监控（主动，Phase-agnostic）
全局水位 Advisory 25k ───────┤
全局水位 Active 40k ─────────┤
全局水位 Critical 60k ───────┘
RecallBudget Ceiling 80k ──── 回引专属（管临时注入）
L2 深度摘要 170k ──────────── 全局安全网（被动兜底）
L3 紧急熔断 190k ──────────── 全局安全网（最后防线）
```

各机制互补而非替代：

- **Phase 2 Context Reset**：Phase 2 专属，每个话题域是独立 LLM session，工作层恒定在 12-17k tokens
- **20k 软预算**：Phase 3 专属，管 Phase 3 场景内的 Round 级膨胀
- **25k/40k/60k 水位监控**：全局通用，管所有 Phase 的工作层整体膨胀（包括无专属压缩机制的 Phase 1/4）
- **RecallBudget**：独立系统，管 recall 操作注入的临时内容
- **170k/190k 安全网**：最终兜底，理论上在前几级防御正常工作时极少被触发

**橙区中间摘要与 L2 深度摘要的区别**：


|           | 橙区 Active (40-60k)  | L2 安全网 (170k)              |
| --------- | ------------------- | -------------------------- |
| **触发场景**  | 工作层在 Phase 内自然膨胀    | 极端异常（多级防御全部失效）             |
| **压缩范围**  | 最老 50% 对话 → 中间摘要    | 全部历史 → 结构化摘要               |
| **摘要位置**  | 保留在工作层（阶段未完成）       | 归档到文件系统                    |
| **工作层结果** | ~20-30k（释放部分空间继续工作） | 锚定层 + 摘要 + 最近 2 轮（~10-15k） |


**（二）全局 Token 阈值安全网 (Fallback Strategy)**

任务边界压缩和工作层水位监控是主动策略，全局 Token 阈值作为**最终被动安全网**——在前几级防御正常工作时应极少被触发：


| 级别          | 触发条件                       | 操作                                                  | 设计师感知      |
| ----------- | -------------------------- | --------------------------------------------------- | ---------- |
| **L2** 深度摘要 | 上下文达到 **170k tokens**（85%） | 由 AI 生成结构化摘要，完整对话归档到文件系统，上下文重置为：摘要 + 最近 2 轮对话 + 锚定层 | 提示"上下文已优化" |
| **L3** 紧急熔断 | 上下文达到 **190k tokens**（95%） | 强制清空全部历史，只保留锚定层 + 原子记忆归档                            | Warning 弹窗 |


> **回引排除规则**：L2/L3 安全网和工作层水位监控的 Token 估算均**排除所有临时回引内容**。回引内容的 Token 管控由独立的 RecallBudget 系统负责（详见 §5.4.2 归档回引机制），两套预算体系互不干扰。

#### 5.4.4 L0 位置工程 (Positional Engineering)

Skill SOP 规定每次 AI 构建 Prompt 时，遵循以下位置编排原则：

```
[0-15% 高注意力区]  → user_intent + JTBD 核心 + 当前任务描述
[15-85% 低注意力区] → 已完成场景的压缩摘要 + 历史对话（如有保留）
[85-100% 高注意力区] → 当前场景的最近 2-3 轮对话 + 当前需要回答的具体问题
```

#### 5.4.5 纯文件原子化记忆 (File-based Atomic Memory)

废弃黑盒化的数据库。当达成里程碑时，Skill SOP 指导 AI 将设计决策和约束提取为独立的"原子约束卡片"，以 YAML 格式存入 `.zoom-ai/memory/constraints/` 目录。记忆对设计师 100% 透明、可搜索、可手动编辑。

#### 5.4.6 上下文管理执行流程

上下文工程作为 Skill SOP 中的内置指令，在每次交互前由 AI 工具自动评估和执行：

1. 读取 `task-progress.json` 确认当前 Phase 和状态
2. 检测是否处于任务边界（Phase 完成或场景完成）
3. 若处于边界：执行任务边界压缩：
  - 3a. 归档对话 + 保留产出物（**Phase 3 场景完成时，该场景的 `RoundDecision` 卡片一并归档，从工作层移除**）
  - 3b. **从该场景所有 `RoundDecision` 中确定性提取 `SemanticTags`（遍历 `constraints_added` → `[约束:xxx]` 标签，遍历 `interaction_details` → `[交互:xxx]` 标签，每场景最多 8 标签）**
  - 3c. **格式化标签并追加到摘要索引对应场景条目**
  - 3d. 更新摘要索引到锚定层
4. **[Phase 2 专属] 检测是否处于话题边界（AI 话题转换标记）**
5. **[Phase 2 专属] 若处于话题边界：执行 Context Reset（提取 InsightCard + page-out 完整话题对话到 `phase2-topic-{domain}-{n}.md`）**
6. **[Phase 2 专属] 检测 Stage B→C 转换：将 `00-research.md` 从工作层降级为 ToC + 关键数据点摘要（~2-3k tokens），完整版归档到 `phase2-research-full.md`**
7. **检测是否处于轮次边界（Phase 3 场景内 Round 结束）**
8. **若处于轮次边界：执行轮次微压缩（宽口提取 RoundDecision 决策卡片 + 启发式完备性检查 + page-out 完整对话到 Recall Buffer）**
9. **检测工作层 Token 是否超过 Phase 内软预算（Phase 3: 20k）；若超过，强制对最老的未压缩 Round 执行压缩**
10. **检测是否处于 Phase 4 Review 轮次边界（Feedback→Patch 完成后）**
11. **若处于 Phase 4 Review 边界：执行反馈边界压缩（提取约束追加到 `accumulated_constraints` + page-out feedback 对话）**
12. **检测是否处于 Design Contract 生成完成后：从所有 `ScenarioContract` 中提取 `shared_state` 和 `dependency` 标签，回填到摘要索引中已有的场景条目**
13. **[全局水位监控] 评估工作层总 Token 是否进入黄区（25k）/橙区（40k）/红区（60k），按级别触发对应操作（详见 §5.4.3）**
14. **检测 recall 请求（AI 自主触发或设计师 `/recall` 命令）→ 执行 RecallBudget 预算检查**
15. **若 ALLOW/TRUNCATE → 从归档文件按指定粒度提取内容，注入临时上下文**
16. **若 DENY → AI 在回复中告知设计师预算不足**
17. 若 Token 超全局阈值：按 L2 → L3 逐级评估安全网策略
18. 执行 L0 位置工程，重新组装上下文

### 5.5 异常兜底与鲁棒性设计 (Auto-Fallback Strategies)

为保证工作流的鲁棒性，Skill SOP 在核心流转节点强制引入以下兜底策略，绝不允许异常状态暴露给设计师或导致系统崩溃：

1. **状态防写坏 (WAL Write-Ahead Log)**：大模型输出带有 Markdown 标记的伪 JSON（如 ````json...````）或结构截断，导致 `task-progress.json` 无法解析。Skill SOP 规定：每次更新状态文件前 AI 工具自动备份当前合法版本；使用 YAML schema 强校验输出格式；解析失败时先尝试清洗，仍失败则自动回滚至上一个安全备份，不阻断主线程。
2. **自修复循环 (Self-Correction Loop)**：Skill SOP 引入 `Max_Retries = 3` 的重试机制。验收脚本校验失败时，AI 将错误信息转化为反思 Prompt 重新生成。仅当连续 3 次失败后，才阻断流程并向设计师输出可读的异常报告。
3. **并发灾难防范 (Assembler Pattern)**：在架构级物理禁止同文件并发。并发限制在相互独立的子模块级（生成 `A.html` 和 `B.html`），最后由确定性辅助脚本（DOM Assembler）合并为完整页面树。从源头上抹杀 Git 冲突问题。
4. **语义合并保护 (Semantic Merge Guard)**：当设计师给出修改反馈时，Skill SOP 严禁简单重试上一轮 Prompt。必须将原始意图与反馈结构化合并，防止修改意见被旧上下文"吞没"。

### 5.6 文件目录与数据结构 (File System Schema)

系统的所有状态均物化为文件，设计师可直接在 IDE 中浏览和编辑：

```text
/Users/designer/workspace/
├── .zoom-ai/                              # 便携式 Skill + Knowledge 目录
│   ├── skills/                            # Markdown+YAML 技能定义（SKILL.md 格式）
│   │   ├── zoom-start.md                  # 入口 Skill：工作区初始化
│   │   ├── alignment-skill.md             # Phase 1: 上下文对齐
│   │   ├── research-skill.md              # Phase 2: 调研 + JTBD
│   │   ├── interaction-skill.md           # Phase 3: 交互方案
│   │   ├── design-contract-skill.md       # Phase 3→4: 设计合约生成
│   │   ├── alchemist-skill.md             # Phase 4: 高保真生成
│   │   ├── patch-skill.md                 # 补丁修复
│   │   └── logic-inquisitor-skill.md      # 逻辑判官（独立审查 Skill）
│   ├── knowledge/
│   │   ├── rules/ux-heuristics.yaml       # 认知负荷阈值配置
│   │   └── zds/                           # ZDS 离线 JSON 字典 (延后)
│   │       ├── zds-button.json
│   │       └── zds-avatar.json
│   ├── scripts/                           # 确定性辅助脚本
│   │   ├── validate_html.py               # BeautifulSoup DOM 反向提取 + Linter
│   │   └── ux_audit.py                    # 认知负荷审计
│   └── memory/
│       ├── constraints/                   # 原子化记忆存储区
│       │   ├── 01KMB8ZGDX.yaml
│       │   └── 03ft2m6jaf.yaml
│       └── sessions/                      # 上下文归档区（任务边界压缩产物）
│           ├── phase1-alignment.md
│           ├── phase2-research.md
│           ├── phase2-insight-cards.md
│           ├── phase2-topic-{domain}-{n}.md
│           └── phase3-scenario-{n}.md
├── /tasks/task-name/                      # 任务工作区
│   ├── task-progress.json                 # 机器读写的状态机凭证
│   ├── 00-research.md                     # 调研报告（市场+竞品+用户）
│   ├── 01-jtbd.md                         # 各角色 JTBD 文档
│   ├── 02-structure.md                    # 各场景确认的交互方案总表
│   ├── 03-design-contract.md              # Phase 3→4 设计合约（导航拓扑+交互承诺+全局约束）
│   ├── wireframes/                        # 黑白 HTML 线框原型
│   │   ├── scenario-1-option-a.html
│   │   ├── scenario-1-option-b.html
│   │   ├── scenario-2-option-a.html
│   │   └── ...
│   └── index.html                         # 最终高保真视觉产出
└── .git/                                  # 底层版本控制与 Worktree 支撑
```

## 6. 动态知识与记忆架构 (3-Tier Memory Engine)

系统的配置与记忆通过本地文件实现，完全对设计师透明：

1. **Tier 1: 团队级静态库 (`.zoom-ai/knowledge/`)**：存放 UX 启发式规则、ZDS 规范、历史经验（YAML 原子卡片）。通过 Git 同步团队最新规范。
2. **Tier 2: 行业级动态情报**：AI 工具通过内置的 Web Search 能力获取行业动态。
3. **Tier 3: 任务级短时记忆 (`/tasks/task-name/`)**：单次任务的上下文隔离区（由 Git Worktree 支撑）。

### 6.1 主动与被动记忆归档机制

- **主动触发 (Explicit Archive)**：设计师确认 `[Complete & Archive]`，Skill SOP 指导 AI 提取全局知识并写入 `.zoom-ai/memory/` 目录下的文本文件。
- **被动回收 (Garbage Collection)**：Skill SOP 在启动时检测是否存在未完成的上次任务——若有价值则提示设计师是否继续；若拒绝则彻底丢弃工作区，防止污染。

## 7. 安全与合规设计

1. **Worktree 沙箱隔离 (Git Sandbox Isolation)**：没收 AI 的全局写权限。AI 生成内容必须在系统分配的隔离 Git Worktree 分支中进行（映射到 Claude Code 的 `EnterWorktree` 命令）。只有通过自动化基线验收和人类 Approve，才允许合并回主工作区。
2. **数据隐私与合规 (Data Privacy)**：
  - 工具纯本地运行，**不连接任何外部第三方向量数据库**。记忆存在本地 YAML 文件中。
  - ZDS 组件规范通过离线脚本提取后存储在本地 JSON 文件中，运行时无需调用 Figma API。
  - LLM 调用由宿主 AI 工具管理，遵循宿主工具的安全与合规策略。企业环境下应确保宿主 AI 工具通过 Zoom 内部合规的 AI Gateway 访问模型。

## 8. 性能目标

作为单用户本地工具，性能指标侧重于**上下文管理质量**与**设计流程效率**，而非高并发。


| 指标                       | 目标值               | 备注                                 |
| ------------------------ | ----------------- | ---------------------------------- |
| 上下文窗口容量                  | 200k tokens       | 适配 Claude / GPT 主流模型长上下文窗口         |
| Phase 2 话题 session 工作层峰值 | ≤ 17k tokens      | Context Reset 确保恒定                 |
| Phase 3 场景内工作层峰值         | ≤ 20k tokens      | 轮次微压缩 + 20k 软预算                    |
| Phase 4 Review 工作层峰值     | ≤ 15k tokens      | 反馈边界压缩 + HTML 即真相源                 |
| L2 深度摘要触发阈值              | 170k tokens (85%) | 被动安全网，正常使用不应触发                     |
| L3 紧急熔断阈值                | 190k tokens (95%) | 最后防线                               |
| 自修复循环上限                  | Max 3 次           | 超出后阻断并向设计师报告                       |
| 验收脚本执行延迟                 | < 5s              | `validate_html.py` + `ux_audit.py` |


## 9. 部署与分发方案

- **分发形式**：`git clone` 或直接复制 `.zoom-ai/` 目录到项目根目录。**零依赖、零安装**——设计师只需拥有支持的宿主 AI 工具（Claude Code / Codex / Cursor）即可开始使用。
- **辅助脚本依赖**：`scripts/validate_html.py` 和 `scripts/ux_audit.py` 依赖 Python 3 + BeautifulSoup4。首次使用时 Skill SOP 指导 AI 工具自动安装（`pip install beautifulsoup4`）。
- **团队规范同步 (GitOps)**：`.zoom-ai/` 目录下的系统更新（技能 SOP、认知负荷规则、ZDS 字典）通过 `git pull` 同步最新团队规范，设计师无需手动操作。

## 10. 风险评估


| 风险点                                    | 概率  | 影响  | 缓解策略                                                                                                             |
| -------------------------------------- | --- | --- | ---------------------------------------------------------------------------------------------------------------- |
| **Figma API 限流**                       | 高   | 中   | 绝不让大模型或运行时调用 Figma API。采用"定时脚本离线提取 + 本地字典按需查询"的两级架构。                                                             |
| **并发写冲突 / 状态污染**                       | 高   | 高   | 架构级禁止同文件并发 (Assembler Pattern)。Git 仅做全局快照，用于 `git reset --hard` 回滚，不参与冲突处理。                                      |
| **生成结果静默回归**                           | 中   | 高   | 自动化基线验收（举证校验 + DOM 反向提取 + Linter），在设计师确认前强制机器审查。                                                                 |
| **大模型输出格式损坏**                          | 中   | 中   | WAL 写前备份 + YAML schema 强校验 + 清洗 + 自动回滚，不阻断主线程。                                                                   |
| **上下文注意力衰减 (Context Attention Decay)** | 中   | 高   | 四级渐进式上下文工程：L0 信息位置工程（关键信息锚定窗口首尾 15% 高注意力区）→ L1 任务边界自动卸载 → L2 深度摘要压缩（85% 阈值）→ L3 紧急熔断（95% 阈值）。完整对话归档到文件系统，设计师可溯源。 |
| **宿主 AI 工具兼容性**                        | 中   | 中   | 以 Claude Code 为主要适配目标，Skill 格式对齐 SKILL.md 规范。次要工具（Cursor/Trae）通过适配层转换。保持 Skill SOP 的通用性，避免依赖特定工具的私有 API。         |
| **Skill SOP 指令遵循度**                    | 中   | 高   | Skill SOP 采用简洁、结构化的指令格式，关键步骤用 `[STOP]` 标记强制人类确认。辅助脚本承担确定性校验，不依赖 AI 自觉遵守。                                         |


## 11. MVP 定义与验收标准 — V0.2 Refined

为确保首个迭代可验证，MVP 定义为**设计师最典型的端到端用户场景**：上传 PRD → 多轮 brainstorm → JTBD → 逐场景交互方案 → 高保真 HTML。

### MVP 闭环：全链路 4 阶段

- **范围**：设计师在 AI 工具中执行 `/zoom-start --prd ./my-prd.md` → Phase 1 上下文对齐（引导式对话 + 手动确认）→ Phase 2 调研+JTBD（LLM 知识调研 + 发散对话 + JTBD 生成）→ Phase 3 逐场景交互方案（场景拆分 + 黑白 HTML 线框 + 设计师选择）→ Phase 4 高保真 HTML 生成 → Review（Approve/Reject/Feedback）
- **验收标准**：
  1. 设计师能与 AI 进行引导式对话，AI 主动提问和挑战假设
  2. 每个阶段的人类控制点正常工作（手动确认后才流转）
  3. 逐场景生成黑白 HTML 线框原型，设计师可在浏览器中体验
  4. 最终生成的高保真 HTML 包含所有交互场景、可点击导航
  5. 上下文在 Phase 边界正确压缩，长对话不崩溃
  6. 断开重启不丢失进度（通过 `task-progress.json` 恢复状态）

### 延后模块

- **ZDS 本地字典**：等 Figma 提取脚本完成后再集成，MVP 阶段 HTML 使用 Tailwind CSS
- **Web Search 调研**：Phase 2 MVP 先用 LLM 内部知识，后续迭代接入 Web Search
- **Logic Inquisitor**：红蓝对抗机制作为增强功能在 MVP 后迭代加入

