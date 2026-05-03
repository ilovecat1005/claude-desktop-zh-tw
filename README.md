# Claude Desktop 繁體中文補丁（zh-TW）

這是一個 macOS 版 Claude Desktop 的繁體中文（台灣）介面補丁。把本專案下載到本機後，雙擊 `install.command`，即可替 Claude Desktop 加入 `中文（台灣）` 語言選項，並安裝台灣繁中介面資源。

## 功能特色

- 一鍵安裝 Claude Desktop 繁體中文（台灣）介面資源。
- 自動把 `zh-TW` 加進 Claude 前端語言白名單。
- 自動合併目前 Claude 版本的英文語言檔與本專案附帶的台灣繁中翻譯。
- 新版本新增但尚未翻譯的欄位會保留英文，避免介面缺字；部分常見短字串會用內建 fallback 自動翻譯。
- 修補部分 Claude Code / Cowork 前端 bundle 內的硬編碼英文短字串，例如 Code 側欄和篩選選單。
- 安裝前自動備份原始 `/Applications/Claude.app`。
- 自動寫入 Claude 使用者設定，將語言設定為 `zh-TW`。

## 適用環境

- **目前僅支援 macOS 版 Claude Desktop。**
- 已安裝 Claude Desktop，且應用程式位於 `/Applications/Claude.app`。
- Windows 版 Claude Desktop 的安裝路徑、資源封裝、簽章/替換流程與 macOS 不同；本專案的 `install.command` 與 `patch_claude_zh_tw.py` 不適用於 Windows。
- 系統內建 Python 3（通常路徑為 `/usr/bin/python3`）

## 使用方式

1. 退出 Claude Desktop。
2. 下載或 clone 本專案。
3. 雙擊 `install.command`。
4. 依照提示輸入 Mac 登入密碼。
5. Claude 會自動重新開啟。
6. 如果沒有自動切換，請打開左下角帳號選單，選擇 `Language` -> `中文（台灣）`。

也可以在終端機執行：

```bash
cd /path/to/claude-desktop-zh-tw
sudo /usr/bin/python3 patch_claude_zh_tw.py --user-home "$HOME" --launch
```

## 從 GitHub 下載

```bash
git clone https://github.com/<your-name>/claude-desktop-zh-tw.git
cd claude-desktop-zh-tw
./install.command
```

如果 `install.command` 無法雙擊執行，可以先執行：

```bash
chmod +x install.command
./install.command
```

## 檔案說明

- `install.command`：雙擊執行入口。
- `patch_claude_zh_tw.py`：實際執行補丁的 Python 腳本。
- `resources/manifest.json`：語言包資訊。
- `resources/frontend-zh-TW.json`：Claude 前端介面台灣繁中翻譯。
- `resources/desktop-zh-TW.json`：Claude 桌面殼層台灣繁中翻譯。
- `resources/Localizable.strings`：macOS 原生選單台灣繁中資源。
- `resources/statsig-zh-TW.json`：statsig i18n 備援資源。

## 腳本會做什麼

- 備份目前的 `/Applications/Claude.app` 到同一個資料夾，名稱類似：
 `Claude.backup-before-zh-TW-20260424-120000.app`
- 複製 Claude.app 到暫存資料夾並套用補丁。
- 把 `zh-TW` 加進前端語言白名單。
- 停用 3p 模式下 Claude Desktop 不支援、但前端仍可能嘗試呼叫的 billing / GitHub repo API，避免 `custom_3p_not_available` 503 重複出現在 log。
- 合併目前 Claude 版本的 `en-US.json` 和本專案附帶的台灣繁中翻譯：
 已翻譯的 key 會顯示繁中；新版本新增但本專案尚未翻譯的 key 會保留英文，避免應用程式缺欄位。
- 寫入 `~/Library/Application Support/Claude/config.json`，設定 `"locale": "zh-TW"`。
- 重新啟動 Claude。

## 注意事項

Claude Desktop 更新後可能會覆蓋補丁，需要重新執行 `install.command`。

此補丁會修改 Claude.app 的本地資源，因此安裝流程會在替換前對修補後的 app 做 ad-hoc 簽署，並帶上 Electron / Cowork 需要的 entitlements。這會讓 `TeamIdentifier` 顯示為 `not set`，屬於目前本地補丁的預期狀態。若要回到官方簽章，請重新安裝官方 Claude Desktop；重新安裝後需要再執行本專案的 `install.command` 才會恢復繁中補丁。

## 解除安裝 / 還原

腳本安裝前會在 `/Applications` 底下產生備份，名稱類似：

```text
Claude.backup-before-zh-TW-20260424-120000.app
```

如需還原，請先退出 Claude Desktop，將目前的 `/Applications/Claude.app` 移走，再把備份 app 改名為 `Claude.app`。

## 免責聲明

本專案是非官方繁體中文（台灣）補丁，只會修改本機 Claude Desktop 的本地資源檔。Claude Desktop 更新後資源結構可能改變；若補丁失敗，請先更新本專案或重新執行安裝腳本。
