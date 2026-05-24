#!/usr/bin/env bash
# ============================================================
# EPD-nRF5 CLI Tool 打包构建脚本
#
# 使用 uv 进行快速构建
#
# 用法:
#   ./build.sh              # 构建 wheel 安装包
#   ./build.sh install      # 构建并安装到当前环境
#   ./build.sh standalone   # 构建 PyInstaller 独立可执行文件
#   ./build.sh clean        # 清理构建产物
#   ./build.sh all          # 构建 wheel + 独立可执行文件
# ============================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"
BUILD_DIR="$SCRIPT_DIR/dist"
# 优先使用项目根目录的 venv，否则使用 tools 下的
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
if [ -d "$ROOT_DIR/.venv" ]; then
    VENV_DIR="$ROOT_DIR/.venv"
elif [ -d "$SCRIPT_DIR/.venv" ]; then
    VENV_DIR="$SCRIPT_DIR/.venv"
else
    VENV_DIR="$SCRIPT_DIR/.venv"
fi

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

info()  { echo -e "${BLUE}[INFO]${NC}  $*"; }
ok()    { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*" >&2; exit 1; }

check_uv() {
    if ! command -v uv &>/dev/null; then
        error "未找到 uv，请先安装: curl -LsSf https://astral.sh/uv/install.sh | sh"
    fi
    local version
    version=$(uv --version)
    info "uv 版本: $version"
}

ensure_venv() {
    if [ ! -d "$VENV_DIR" ]; then
        info "使用 uv 创建虚拟环境..."
        uv venv "$VENV_DIR"
    fi
    source "$VENV_DIR/bin/activate"
}

build_wheel() {
    info "使用 uv 构建 wheel 安装包..."
    cd "$PROJECT_DIR"
    uv build
    ok "构建完成！产物在 $BUILD_DIR/"
    ls -lh "$BUILD_DIR/"*.whl "$BUILD_DIR/"*.tar.gz 2>/dev/null || true
}

install_local() {
    info "使用 uv 安装到当前环境..."
    cd "$PROJECT_DIR"
    uv pip install -e .
    ok "已安装！运行 'epd-tool --help' 验证"
    epd-tool --help | head -5
}

build_standalone() {
    info "构建独立可执行文件 (PyInstaller)..."
    cd "$PROJECT_DIR"

    uv pip install pyinstaller

    # PyInstaller spec 参数
    local app_name="epd-tool"
    local entry_point="epd_tool.cli:main"

    info "打包 $app_name ..."

    pyinstaller \
        --name "$app_name" \
        --onefile \
        --clean \
        --noconfirm \
        --console \
        --hidden-import bleak \
        --hidden-import bleak.backends.corebluetooth \
        --hidden-import PIL \
        --collect-all bleak \
        "$PROJECT_DIR/epd_tool/cli.py"

    # 移动到 dist 目录
    mkdir -p "$BUILD_DIR"
    if [ -f "dist/$app_name" ]; then
        mv "dist/$app_name" "$BUILD_DIR/"
        chmod +x "$BUILD_DIR/$app_name"
        ok "独立可执行文件: $BUILD_DIR/$app_name"
        ls -lh "$BUILD_DIR/$app_name"
    elif [ -f "dist/$app_name.exe" ]; then
        mv "dist/$app_name.exe" "$BUILD_DIR/"
        ok "独立可执行文件: $BUILD_DIR/$app_name.exe"
        ls -lh "$BUILD_DIR/$app_name.exe"
    fi

    # 清理 PyInstaller 临时文件
    rm -rf build/ *.spec

    ok "独立可执行文件构建完成！"
}

clean() {
    info "清理构建产物..."
    cd "$PROJECT_DIR"
    rm -rf dist/ build/ *.egg-info .eggs/
    rm -rf epd_tool/__pycache__/
    rm -rf .venv/
    find . -name "*.pyc" -delete
    find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    ok "清理完成"
}

show_usage() {
    cat <<EOF

EPD-nRF5 CLI Tool 打包构建脚本

用法: $0 <命令>

命令:
  (无参数)    构建 wheel 安装包 (默认)
  install     构建并安装到当前 Python 环境 (开发模式)
  standalone  使用 PyInstaller 构建独立可执行文件 (无需 Python)
  clean       清理所有构建产物
  all         构建 wheel + 独立可执行文件
  help        显示此帮助信息

安装方式说明:

1. pip 安装 (推荐，需要 Python 环境):
   $0 install
   # 或手动:
   pip install dist/epd_tool-1.0.0-py3-none-any.whl

2. 独立可执行文件 (无需 Python，体积较大):
   $0 standalone
   # 产物: dist/epd-tool

3. 用户从 PyPI 安装 (发布后):
   pip install epd-tool

EOF
}

# ============================================================
# 主流程
# ============================================================

main() {
    local cmd="${1:-wheel}"

    check_uv

    case "$cmd" in
        wheel|"")
            ensure_venv
            build_wheel
            ;;
        install)
            ensure_venv
            install_local
            ;;
        standalone)
            ensure_venv
            build_standalone
            ;;
        clean)
            clean
            ;;
        all)
            ensure_venv
            build_wheel
            build_standalone
            ;;
        help|-h|--help)
            show_usage
            ;;
        *)
            error "未知命令: $cmd\n运行 '$0 help' 查看可用命令"
            ;;
    esac
}

main "$@"
