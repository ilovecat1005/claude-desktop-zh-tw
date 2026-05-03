# Claude Desktop 繁體中文（台灣）補丁

這是一個給 **macOS 版 Claude Desktop** 使用的非官方繁體中文（台灣）介面補丁。安裝後會加入 `中文（台灣）` 語言資源，並盡量把 Claude Desktop、Claude Code、Cowork 相關介面翻成台灣常用的繁體中文用語。

> 目前僅支援 macOS。Windows 版 Claude Desktop 的資源位置、封裝與替換流程不同，本專案暫不支援。

## 功能特色

- 安裝 Claude Desktop 繁體中文（台灣）介面資源。
- 自動將 `zh-TW` 加入 Claude 前端語言白名單。
- 依照使用者目前安裝的 Claude Desktop 版本，將本專案翻譯檔與官方 `en-US.json` 合併。
- 新版 Claude Desktop 若新增尚未翻譯的 key，會保留英文避免介面缺字；部分常見短字串會用內建 fallback 自動翻譯。
- 修補部分前端 bundle 裡的硬編碼英文短字串，例如 Code 側欄、篩選選單與部分設定頁文字。
- 安裝前自動備份原始 `/Applications/Claude.app`，方便還原。
- 自動將 Claude 使用者設定寫入 `zh-TW` locale。

## 適用環境

- macOS。
- 已安裝 Claude Desktop。
- Claude Desktop 位於 `/Applications/Claude.app`。
- 系統可執行 Python 3，通常是 `/usr/bin/python3`。

## 安裝方式

### 方法一：雙擊安裝

1. 退出 Claude Desktop。
2. 下載或 clone 本專案。
3. 雙擊 `install.command`。
4. 依照提示輸入 Mac 登入密碼。
5. 安裝完成後 Claude Desktop 會自動重新開啟。
6. 如果沒有自動切換語言，請打開 Claude 左下角帳號選單，選擇 `Language` → `中文（台灣）`。

### 方法二：終端機安裝

```bash
git clone https://github.com/ilovecat1005/claude-desktop-zh-tw.git
cd claude-desktop-zh-tw
./install.command
```

如果 `install.command` 無法執行，請先加上執行權限：

```bash
chmod +x install.command
./install.command
```

也可以直接執行 Python 補丁：

```bash
sudo /usr/bin/python3 patch_claude_zh_tw.py --user-home "$HOME" --launch
```

## 安裝流程會做什麼

腳本會執行以下動作：

1. 退出正在執行的 Claude Desktop。
2. 複製 `/Applications/Claude.app` 到暫存資料夾。
3. 將 `zh-TW` 加入 Claude 前端語言白名單。
4. 安裝繁體中文（台灣）前端、桌面殼層與 statsig i18n 資源。
5. 合併目前 Claude Desktop 內建的 `en-US.json` 與本專案的 `frontend-zh-TW.json`。
6. 修補部分前端 bundle 裡無法透過 i18n 檔案翻譯的硬編碼短字串。
7. 寫入使用者設定，將 locale 設為 `zh-TW`。
8. 對修補後的 app 做本地 ad-hoc 簽署，並套用 Electron / Cowork 需要的 entitlements。
9. 備份原本的 Claude.app，並把修補後的 Claude.app 放回 `/Applications`。
10. 重新啟動 Claude Desktop。

## 專案檔案

```text
install.command                         # 雙擊安裝入口
patch_claude_zh_tw.py                   # 主要補丁腳本
resources/manifest.json                 # 語言包資訊
resources/frontend-zh-TW.json           # 前端介面翻譯
resources/desktop-zh-TW.json            # 桌面殼層翻譯
resources/statsig-zh-TW.json            # statsig i18n 備援翻譯
resources/Localizable.strings           # macOS 原生字串資源
```

## 更新 Claude Desktop 後

Claude Desktop 更新後可能會覆蓋補丁。如果更新後介面變回英文，請重新執行：

```bash
./install.command
```

## 解除安裝 / 還原

安裝前腳本會在 `/Applications` 底下建立備份，名稱類似：

```text
Claude.backup-before-zh-TW-20260424-120000.app
```

如需還原：

1. 退出 Claude Desktop。
2. 將目前的 `/Applications/Claude.app` 移走或刪除。
3. 將備份 app 改名為 `Claude.app`。
4. 重新開啟 Claude Desktop。

如果想完全回到官方狀態，也可以直接重新安裝官方 Claude Desktop。

## 注意事項

- 本專案只修改本機 Claude Desktop 的本地資源檔。
- 這是非官方補丁，不是 Anthropic 官方提供的語言包。
- 因為修補後會重新做本地 ad-hoc 簽署，`TeamIdentifier` 顯示為 `not set` 是目前預期行為。
- Claude Desktop 更新後資源結構可能改變，若補丁失敗，請更新本專案或回報 issue。
- 請不要把修補後的 `Claude.app` 或備份 app 上傳到 GitHub；本專案只需要保存補丁腳本與翻譯資源。

## Windows 支援狀態

目前不支援 Windows。

Windows 版 Claude Desktop 的安裝路徑、資源封裝、檔案替換與權限流程都與 macOS 不同，因此現有的 `install.command` 與 `patch_claude_zh_tw.py` 無法直接使用。

若未來要支援 Windows，建議另外實作：

```text
install.ps1
patch_claude_zh_tw_windows.py
```

並重新確認 Windows 版 Claude Desktop 的資源檔位置與更新後的封裝格式。

## 致謝

本專案的製作靈感來自 [claude-desktop-zh-cn](https://github.com/javaht/claude-desktop-zh-cn)。感謝原專案作者整理 Claude Desktop 本地化補丁的做法與方向，讓這個繁體中文（台灣）版本可以在其基礎概念上延伸製作。

## 免責聲明

本專案為非官方繁體中文（台灣）補丁，與 Anthropic 官方無關。使用前請自行評估風險；若 Claude Desktop 更新導致補丁失效，請重新執行安裝腳本或等待本專案更新。
