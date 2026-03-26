#!/usr/bin/env bash
# HarnessDesign Installer
# 用法: curl -fsSL https://raw.githubusercontent.com/Pawn-97/harnessurdesign-UX-flow/main/install.sh | bash -s -- [目标文件夹]
# 或:   bash install.sh [目标文件夹]
#
# 如果不指定目标文件夹，默认安装到当前目录。

set -euo pipefail

# ─── 颜色 ───
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

info()  { echo -e "${BLUE}▸${NC} $*"; }
ok()    { echo -e "${GREEN}✓${NC} $*"; }
warn()  { echo -e "${YELLOW}⚠${NC} $*"; }
fail()  { echo -e "${RED}✗${NC} $*"; exit 1; }

REPO_URL="https://github.com/Pawn-97/harnessurdesign-UX-flow.git"
TARGET_DIR="${1:-.}"

# ─── 前置检查 ───
command -v git   >/dev/null 2>&1 || fail "需要安装 Git。请访问 https://git-scm.com/downloads"
command -v python3 >/dev/null 2>&1 || fail "需要安装 Python 3.10+。请访问 https://www.python.org/downloads/"

# 优先使用 Homebrew / 用户安装的 python3，而非 macOS 系统自带的旧版本
if command -v /opt/homebrew/bin/python3 >/dev/null 2>&1; then
  PYTHON3="/opt/homebrew/bin/python3"
elif command -v /usr/local/bin/python3 >/dev/null 2>&1; then
  PYTHON3="/usr/local/bin/python3"
else
  PYTHON3="python3"
fi

PYTHON_VERSION=$("$PYTHON3" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)
if [ "$PYTHON_MAJOR" -lt 3 ] || { [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 10 ]; }; then
  fail "Python 版本需要 3.10+，当前版本: $PYTHON_VERSION（路径: $PYTHON3）"
fi

# ─── 清理并解析目标路径 ───
# 去除可能由 curl | bash 管道引入的 \r 等不可见字符
TARGET_DIR=$(printf '%s' "$TARGET_DIR" | tr -d '\r\n')

if [ -d "$TARGET_DIR" ]; then
  TARGET_DIR=$(cd "$TARGET_DIR" && pwd)
else
  mkdir -p "$TARGET_DIR"
  TARGET_DIR=$(cd "$TARGET_DIR" && pwd)
fi

echo ""
echo -e "${BOLD}╭─────────────────────────────────────╮${NC}"
echo -e "${BOLD}│   HarnessDesign UX Workflow 安装器   │${NC}"
echo -e "${BOLD}╰─────────────────────────────────────╯${NC}"
echo ""
info "目标文件夹: ${BOLD}$TARGET_DIR${NC}"
info "安装后可在此文件夹中启动多个设计任务，共享知识库和设计约束"
echo ""

# ─── 检查是否已安装 ───
if [ -d "$TARGET_DIR/.harnessdesign/knowledge/skills" ]; then
  warn "检测到已有 HarnessDesign 安装。将更新引擎文件（不影响你的任务数据和知识库）。"
  echo ""
fi

# ─── 下载引擎 ───
info "下载工作流引擎..."
TMPDIR=$(mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT
git clone --depth 1 --quiet "$REPO_URL" "$TMPDIR/repo"
ok "下载完成"

# ─── 复制引擎文件 ───
info "安装引擎文件..."

# 核心引擎（始终覆盖更新）
mkdir -p "$TARGET_DIR/.harnessdesign/knowledge/skills"
mkdir -p "$TARGET_DIR/.harnessdesign/knowledge/rules"
mkdir -p "$TARGET_DIR/.harnessdesign/knowledge/zds"
mkdir -p "$TARGET_DIR/.harnessdesign/scripts"
mkdir -p "$TARGET_DIR/scripts"

cp -r "$TMPDIR/repo/.harnessdesign/knowledge/skills/"*     "$TARGET_DIR/.harnessdesign/knowledge/skills/"
cp -r "$TMPDIR/repo/.harnessdesign/knowledge/rules/"*      "$TARGET_DIR/.harnessdesign/knowledge/rules/"
cp -r "$TMPDIR/repo/.harnessdesign/knowledge/zds/"*        "$TARGET_DIR/.harnessdesign/knowledge/zds/"
cp    "$TMPDIR/repo/.harnessdesign/knowledge/Design.md"    "$TARGET_DIR/.harnessdesign/knowledge/Design.md"
cp    "$TMPDIR/repo/.harnessdesign/knowledge/zds-index.md" "$TARGET_DIR/.harnessdesign/knowledge/zds-index.md"
cp -r "$TMPDIR/repo/.harnessdesign/scripts/"*              "$TARGET_DIR/.harnessdesign/scripts/"
cp -r "$TMPDIR/repo/scripts/"*                             "$TARGET_DIR/scripts/"

# 工作区目录（不覆盖已有数据）
mkdir -p "$TARGET_DIR/.harnessdesign/knowledge/product-context"
mkdir -p "$TARGET_DIR/.harnessdesign/memory/sessions"
mkdir -p "$TARGET_DIR/.harnessdesign/memory/constraints"
mkdir -p "$TARGET_DIR/tasks"

# .gitkeep 文件
touch "$TARGET_DIR/.harnessdesign/knowledge/product-context/.gitkeep"
touch "$TARGET_DIR/.harnessdesign/memory/sessions/.gitkeep"
touch "$TARGET_DIR/.harnessdesign/memory/constraints/.gitkeep"

# 配置文件（仅在不存在时创建，避免覆盖用户自定义）
for file in CLAUDE.md AGENTS.md .gitignore; do
  if [ ! -f "$TARGET_DIR/$file" ]; then
    cp "$TMPDIR/repo/$file" "$TARGET_DIR/$file"
  else
    warn "$file 已存在，跳过（如需更新请手动合并）"
  fi
done

ok "引擎文件安装完成"

# ─── 禁用无关 Claude Code 插件 ───
info "配置 Claude Code 环境..."
mkdir -p "$TARGET_DIR/.claude"
if [ ! -f "$TARGET_DIR/.claude/settings.json" ]; then
  cat > "$TARGET_DIR/.claude/settings.json" << 'SETTINGS'
{
  "enabledPlugins": {
    "vercel@claude-plugins-official": false,
    "supabase@claude-plugins-official": false
  }
}
SETTINGS
  ok "已禁用无关插件（Vercel、Supabase）"
else
  warn ".claude/settings.json 已存在，跳过"
fi

# 复制 hooks.json（仅在不存在时）
if [ ! -f "$TARGET_DIR/.claude/hooks.json" ] && [ -f "$TMPDIR/repo/.claude/hooks.json" ]; then
  cp "$TMPDIR/repo/.claude/hooks.json" "$TARGET_DIR/.claude/hooks.json"
  ok "已安装写入校验 hooks"
fi

# 复制斜杠命令（始终覆盖更新）
if [ -d "$TMPDIR/repo/.claude/commands" ]; then
  mkdir -p "$TARGET_DIR/.claude/commands"
  cp -r "$TMPDIR/repo/.claude/commands/"* "$TARGET_DIR/.claude/commands/"
  ok "已安装斜杠命令（/harnessdesign-*）"
fi

# ─── 安装 Python 依赖（使用 venv） ───
info "创建 Python 虚拟环境并安装依赖..."
VENV_DIR="$TARGET_DIR/.venv"
if [ ! -d "$VENV_DIR" ]; then
  "$PYTHON3" -m venv "$VENV_DIR"
fi
"$VENV_DIR/bin/pip" install -q -r "$TARGET_DIR/.harnessdesign/scripts/requirements.txt"
ok "Python 依赖安装完成（虚拟环境: .venv/）"

# ─── 验证安装 ───
info "运行完整性验证..."
echo ""
(cd "$TARGET_DIR" && "$VENV_DIR/bin/python3" .harnessdesign/scripts/integration_test.py) && VERIFY_OK=true || VERIFY_OK=false

echo ""
if [ "$VERIFY_OK" = true ]; then
  echo -e "${GREEN}${BOLD}安装成功！${NC}"
else
  echo -e "${YELLOW}${BOLD}安装完成，但验证测试未全部通过。请联系 GuanchengDing 排查。${NC}"
fi

echo ""
echo -e "${BOLD}下一步：${NC}"
echo ""
echo -e "  ${BLUE}1.${NC} 进入项目文件夹："
echo -e "     ${BOLD}cd \"$TARGET_DIR\"${NC}"
echo ""
echo -e "  ${BLUE}2.${NC} 启动 Claude Code："
echo -e "     ${BOLD}claude${NC}"
echo ""
echo -e "  ${BLUE}3.${NC} 启动工作流（AI 会邀请你描述任务）："
echo -e "     ${BOLD}/harnessdesign-start${NC}"
echo ""
echo -e "  ${YELLOW}提示:${NC} Python 依赖已安装在 ${BOLD}.venv/${NC} 虚拟环境中。"
echo -e "     如需手动运行脚本，请先激活: ${BOLD}source .venv/bin/activate${NC}"
echo ""
