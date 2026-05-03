#!/bin/bash
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON="/usr/bin/python3"

if [ ! -x "$PYTHON" ]; then
 PYTHON="$(command -v python3)"
fi

echo "Claude Desktop 繁體中文（台灣）補丁"
echo "目錄: $DIR"
echo

if [ "$(id -u)" -ne 0 ]; then
 echo "需要管理員權限來替換 /Applications/Claude.app。"
 echo "請依照提示輸入這台 Mac 的登入密碼。"
 echo
 sudo "$PYTHON" "$DIR/patch_claude_zh_tw.py" --user-home "$HOME" --launch "$@"
 STATUS=$?
 echo
 echo "按 Return 鍵結束。"
 read -r _
 exit "$STATUS"
fi

USER_HOME="$HOME"
if [ -n "${SUDO_USER:-}" ] && [ "$SUDO_USER" != "root" ]; then
 USER_HOME="/Users/$SUDO_USER"
fi

"$PYTHON" "$DIR/patch_claude_zh_tw.py" --user-home "$USER_HOME" --launch "$@"

echo
echo "完成。按 Return 鍵結束。"
read -r _
