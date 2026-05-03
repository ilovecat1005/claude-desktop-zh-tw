#!/usr/bin/env python3
"""
Claude Desktop macOS 中文（台灣）一鍵補丁。

流程：
1. 將 /Applications/Claude.app 複製到暫存工作區。
2. 將 zh-TW 加入 Claude Desktop 語言白名單。
3. 安裝台灣繁中桌面殼層與前端 i18n 資源。
4. 將目前使用者的 Claude 設定 locale 寫為 zh-TW。
5. 備份原本的 app，並安裝修補後的 app。

請在本資料夾執行：
    sudo /usr/bin/python3 patch_claude_zh_tw.py --user-home "$HOME"
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import plistlib
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


APP_DEFAULT = Path("/Applications/Claude.app")
LANG_CODE = "zh-TW"
LANG_LABEL = "中文（台灣）"
ROOT = Path(__file__).resolve().parent
RESOURCES = ROOT / "resources"

FRONTEND_TRANSLATION = RESOURCES / "frontend-zh-TW.json"
DESKTOP_TRANSLATION = RESOURCES / "desktop-zh-TW.json"
STATSIG_TRANSLATION = RESOURCES / "statsig-zh-TW.json"
LOCALIZABLE_STRINGS = RESOURCES / "Localizable.strings"

FRONTEND_I18N_REL = Path("Contents/Resources/ion-dist/i18n")
FRONTEND_ASSETS_REL = Path("Contents/Resources/ion-dist/assets/v1")
DESKTOP_RESOURCES_REL = Path("Contents/Resources")

LANG_LIST_RE = re.compile(
    r'\["en-US","de-DE","fr-FR","ko-KR","ja-JP","es-419","es-ES","it-IT","hi-IN","pt-BR","id-ID"(.*?)\]'
)

# Newer Claude Desktop builds sometimes add short UI labels before this zh-TW
# pack has the corresponding hashed i18n keys. When merging en-US -> zh-TW,
# translate these exact English fallback values so menus do not regress to English.
FRONTEND_EXACT_FALLBACK_TRANSLATIONS = {
    "New task": "新增任務",
    "New session": "新增任務",
    "Projects": "專案",
    "Scheduled": "排程",
    "Customize": "自訂",
    "Pinned": "釘選",
    "Drag to pin": "拖到這裡釘選",
    "Drop here": "拖到這裡",
    "Let go": "放開",
    "Recents": "最近使用",
    "View all": "檢視全部",
    "Status": "狀態",
    "Active": "進行中",
    "Archived": "已封存",
    "Project": "專案",
    "Environment": "環境",
    "Last activity": "上次活動",
    "Group by": "分組依據",
    "Sort by": "排序依據",
    "All": "全部",
    "None": "無",
    "Recency": "最近使用",
    "Alphabetically": "依字母排序",
    "Created time": "建立時間",
    "Updated time": "更新時間",
    "Newest": "最新",
    "Oldest": "最舊",
    "Date": "日期",
    "Local": "本機",
    "Cloud": "雲端",
    "All projects": "所有專案",
}


def run(cmd: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=check)


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    os.replace(tmp, path)


def require_file(path: Path) -> None:
    if not path.exists():
        raise SystemExit(f"找不到必要檔案：{path}")


def quit_claude() -> None:
    run(["osascript", "-e", 'tell application "Claude" to quit'], check=False)
    for _ in range(60):
        result = run(["pgrep", "-x", "Claude"], check=False)
        if result.returncode != 0:
            return
        import time
        time.sleep(0.5)
    print("警告：Claude 主程式仍在執行，可能會覆寫 locale 設定。", file=sys.stderr)


def copy_app(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    print(f"正在複製 Claude.app 到暫存工作區：{dst}")
    run(["ditto", str(src), str(dst)])


def refresh_zstd_asset(path: Path) -> None:
    compressed = path.with_suffix(path.suffix + ".zst")
    if not compressed.exists():
        return
    zstd = shutil.which("zstd") or next(
        (candidate for candidate in ["/opt/homebrew/bin/zstd", "/usr/local/bin/zstd"] if Path(candidate).exists()),
        None,
    )
    if zstd:
        run([zstd, "-f", "-q", str(path), "-o", str(compressed)])
        return
    try:
        import zstandard as zstd_module  # type: ignore[import-not-found]
    except Exception:
        compressed.unlink()
        print(f"找不到 zstd，已移除舊壓縮資源以避免載入過期 bundle：{compressed.name}")
        return
    compressor = zstd_module.ZstdCompressor()
    compressed.write_bytes(compressor.compress(path.read_bytes()))


def patch_language_whitelist(app: Path) -> Path:
    assets_dir = app / FRONTEND_ASSETS_REL
    candidates = sorted(assets_dir.glob("index-*.js"))
    if not candidates:
        raise SystemExit(f"找不到前端 index bundle：{assets_dir}")

    for path in candidates:
        text = path.read_text(encoding="utf-8")
        match = LANG_LIST_RE.search(text)
        if not match:
            continue

        language_list = match.group(0)
        if '"zh-TW"' in language_list:
            print(f"語言白名單已包含 zh-TW：{path.name}")
            return path

        patched = LANG_LIST_RE.sub(
            '["en-US","de-DE","fr-FR","ko-KR","ja-JP","es-419","es-ES","it-IT","hi-IN","pt-BR","id-ID","zh-TW"]',
            text,
            count=1,
        )
        path.write_text(patched, encoding="utf-8")
        refresh_zstd_asset(path)
        print(f"已修補語言白名單：{path.name}")
        return path

    raise SystemExit("無法修補語言白名單。Claude 的 bundle 格式可能已變更。")


def patch_hardcoded_frontend_strings(app: Path) -> None:
    assets_dir = app / FRONTEND_ASSETS_REL
    replacements = {
        json.dumps(source, ensure_ascii=False): json.dumps(target, ensure_ascii=False)
        for source, target in FRONTEND_EXACT_FALLBACK_TRANSLATIONS.items()
    }
    patched_files = 0
    patched_strings = 0

    for path in sorted(assets_dir.glob("*.js")):
        text = path.read_text(encoding="utf-8")
        patched = text
        count = 0
        for source, target in replacements.items():
            occurrences = patched.count(source)
            if occurrences:
                patched = patched.replace(source, target)
                count += occurrences
        if patched != text:
            path.write_text(patched, encoding="utf-8")
            refresh_zstd_asset(path)
            patched_files += 1
            patched_strings += count

    print(f"已修補硬編碼前端字串：{patched_strings} 處，{patched_files} 個檔案")


def patch_third_party_unavailable_requests(app: Path) -> None:
    assets_dir = app / FRONTEND_ASSETS_REL
    candidates = sorted(assets_dir.glob("index-*.js"))
    if not candidates:
        raise SystemExit(f"找不到前端 index bundle：{assets_dir}")

    patches = [
        (
            "function Qk",
            'function Qk(e,t,n="json"){const s=Zk();return p.useCallback(async(a,r)=>{const i=await s(a,r);',
            'function Qk(e,t,n="json"){const s=Zk();return p.useCallback(async(a,r)=>{if(zS()?.deploymentMode==="3p"&&"string"==typeof a&&a.includes("/code/repos?skip_status=false"))return{repos:[]};if(zS()?.deploymentMode==="3p"&&"string"==typeof a&&a.includes("/individual_plan_pricing/v2"))return{};const i=await s(a,r);',
        ),
        (
            "individual_plan_pricing/v2",
            "x=p.useCallback(e=>{a(e),e.noCache&&i(void 0),d(e)},[d]);return{fiveXPricing:m",
            "x=p.useCallback(e=>{if(zS()?.deploymentMode===\"3p\")return;a(e),e.noCache&&i(void 0),d(e)},[d]);return{fiveXPricing:m",
        ),
        (
            "SYNC_GH_REPOS_WITH_STATUS_QUERY_KEY",
            "enabled:Boolean(a&&r&&i&&t),...void 0!==s&&{refetchOnWindowFocus:s},meta:{noToast:!0}})},uVe=",
            "enabled:!1,...void 0!==s&&{refetchOnWindowFocus:s},meta:{noToast:!0}})},uVe=",
        ),
    ]
    patched_files = 0
    patched_sites = 0

    for path in candidates:
        text = path.read_text(encoding="utf-8")
        patched = text
        for marker, old, new in patches:
            if marker not in patched or new in patched:
                continue
            occurrences = patched.count(old)
            if occurrences != 1:
                raise SystemExit(f"3p API 修補點不相容：{path.name} 找到 {marker}，但修補點有 {occurrences} 處")
            patched = patched.replace(old, new, 1)
            patched_sites += 1
        if patched != text:
            path.write_text(patched, encoding="utf-8")
            refresh_zstd_asset(path)
            patched_files += 1

    if patched_sites:
        print(f"已停用 3p 模式不支援 API 呼叫：{patched_sites} 處，{patched_files} 個檔案")
    else:
        print("3p 模式不支援 API 呼叫已停用或目前 bundle 不需要修補")


def merge_frontend_locale(app: Path) -> tuple[int, int, int]:
    source = app / FRONTEND_I18N_REL / "en-US.json"
    target = app / FRONTEND_I18N_REL / "zh-TW.json"
    require_file(source)
    require_file(FRONTEND_TRANSLATION)

    en = load_json(source)
    zh_pack = load_json(FRONTEND_TRANSLATION)
    if not isinstance(en, dict) or not isinstance(zh_pack, dict):
        raise SystemExit("前端 i18n JSON 結構不支援。")

    merged: dict[str, Any] = {}
    translated = 0
    fallback = 0
    exact_fallback = 0
    for key, value in en.items():
        if key in zh_pack:
            merged[key] = zh_pack[key]
            if zh_pack[key] != value:
                translated += 1
        elif isinstance(value, str) and value in FRONTEND_EXACT_FALLBACK_TRANSLATIONS:
            merged[key] = FRONTEND_EXACT_FALLBACK_TRANSLATIONS[value]
            exact_fallback += 1
        else:
            merged[key] = value
            fallback += 1

    save_json(target, merged)
    extra = len(set(zh_pack) - set(en))
    print(
        f"已安裝前端 zh-TW：{translated} 筆翻譯、"
        f"{exact_fallback} 筆短字串保底翻譯、{fallback} 筆英文保底、"
        f"忽略 {extra} 筆舊版 key"
    )
    return translated, fallback, extra


def install_desktop_locale(app: Path) -> None:
    resources_dir = app / DESKTOP_RESOURCES_REL
    require_file(DESKTOP_TRANSLATION)
    require_file(LOCALIZABLE_STRINGS)

    shutil.copy2(DESKTOP_TRANSLATION, resources_dir / "zh-TW.json")
    for folder in ["zh-TW.lproj", "zh_TW.lproj"]:
        out_dir = resources_dir / folder
        out_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(LOCALIZABLE_STRINGS, out_dir / "Localizable.strings")
    print("已安裝桌面殼層 zh-TW 資源")


def install_statsig_locale(app: Path) -> None:
    statsig_dir = app / FRONTEND_I18N_REL / "statsig"
    if not statsig_dir.exists():
        return
    target = statsig_dir / "zh-TW.json"
    if STATSIG_TRANSLATION.exists():
        shutil.copy2(STATSIG_TRANSLATION, target)
    elif (statsig_dir / "en-US.json").exists():
        shutil.copy2(statsig_dir / "en-US.json", target)
    print("已安裝 statsig zh-TW 資源")


def sign_app_for_local_patch(app: Path, dry_run: bool) -> None:
    entitlements = {
        "com.apple.security.cs.disable-library-validation": True,
        "com.apple.security.cs.allow-jit": True,
        "com.apple.security.cs.allow-unsigned-executable-memory": True,
        "com.apple.security.virtualization": True,
    }
    entitlements_path = app.parent / "claude-zh-tw-entitlements.plist"
    if dry_run:
        print(f"[dry-run] 將會用 ad-hoc 簽署並套用 Electron/Cowork entitlements：{app}")
        return

    with entitlements_path.open("wb") as f:
        plistlib.dump(entitlements, f)
    try:
        run([
            "codesign",
            "--force",
            "--deep",
            "--sign",
            "-",
            "--options",
            "runtime",
            "--entitlements",
            str(entitlements_path),
            str(app),
        ])
    finally:
        try:
            entitlements_path.unlink()
        except FileNotFoundError:
            pass
    print("已用 ad-hoc 簽署 Claude.app 並套用 Electron/Cowork entitlements")


def set_user_locale(user_home: Path) -> None:
    config_paths = [
        user_home / "Library/Application Support/Claude/config.json",
        user_home / "Library/Application Support/Claude-3p/config.json",
    ]
    sudo_uid = os.environ.get("SUDO_UID")
    sudo_gid = os.environ.get("SUDO_GID")

    for config in config_paths:
        config.parent.mkdir(parents=True, exist_ok=True)
        data: dict[str, Any] = {}
        if config.exists():
            try:
                loaded = load_json(config)
                if isinstance(loaded, dict):
                    data = loaded
            except Exception:
                backup = config.with_suffix(".json.bak-invalid")
                shutil.copy2(config, backup)
                print(f"既有 config 不是有效 JSON，已備份到：{backup}")
        data["locale"] = LANG_CODE
        save_json(config, data)

        if sudo_uid and sudo_gid:
            os.chown(config, int(sudo_uid), int(sudo_gid))
        print(f"已設定 Claude 使用者 locale：{config}")


def backup_and_replace(original: Path, patched: Path, dry_run: bool) -> Path:
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = original.with_name(f"Claude.backup-before-zh-TW-{stamp}.app")
    if dry_run:
        print(f"[dry-run] 將會移動 {original} -> {backup}")
        print(f"[dry-run] 將會移動 {patched} -> {original}")
        return backup

    print(f"正在備份目前 app：{backup}")
    shutil.move(str(original), str(backup))
    print(f"正在安裝修補後的 app：{original}")
    shutil.move(str(patched), str(original))
    return backup


def verify(app: Path) -> None:
    frontend = app / FRONTEND_I18N_REL / "zh-TW.json"
    data = load_json(frontend)
    values = [v for v in data.values() if isinstance(v, str)]
    chinese = sum(1 for v in values if re.search(r"[\u4e00-\u9fff]", v))
    print(f"已驗證前端 zh-TW JSON：{chinese}/{len(values)} 筆字串包含中文")

    result = run(["codesign", "-dv", str(app)], check=False).stdout
    for line in result.splitlines():
        if line.startswith("TeamIdentifier="):
            print(line)


def main() -> int:
    parser = argparse.ArgumentParser(description="替 Claude Desktop 安裝 zh-TW 台灣繁中資源。")
    parser.add_argument("--app", type=Path, default=APP_DEFAULT, help="Claude.app 路徑")
    parser.add_argument("--user-home", type=Path, default=Path.home(), help="要寫入 Claude config 的使用者家目錄")
    parser.add_argument("--dry-run", action="store_true", help="準備並驗證暫存 app，但不替換 /Applications/Claude.app")
    parser.add_argument("--launch", action="store_true", help="安裝完成後啟動 Claude")
    args = parser.parse_args()

    require_file(FRONTEND_TRANSLATION)
    require_file(DESKTOP_TRANSLATION)
    require_file(LOCALIZABLE_STRINGS)
    if not args.app.exists():
        raise SystemExit(f"找不到 Claude.app：{args.app}")

    try:
        in_applications = args.app.resolve().as_posix().startswith("/Applications/")
    except Exception:
        in_applications = str(args.app).startswith("/Applications/")
    if os.geteuid() != 0 and in_applications:
        print("/Applications 受系統保護，通常需要使用 sudo 執行。", file=sys.stderr)

    if args.dry_run:
        print("[dry-run] 不會結束 Claude。")
    else:
        quit_claude()
    tmp_root = Path(tempfile.mkdtemp(prefix="claude-zh-tw-patch."))
    patched_app = tmp_root / "Claude.app"

    copy_app(args.app, patched_app)
    patch_language_whitelist(patched_app)
    patch_third_party_unavailable_requests(patched_app)
    patch_hardcoded_frontend_strings(patched_app)
    merge_frontend_locale(patched_app)
    install_desktop_locale(patched_app)
    install_statsig_locale(patched_app)
    sign_app_for_local_patch(patched_app, args.dry_run)
    if args.dry_run:
        print(f"[dry-run] 將會設定此使用者目錄下的 Claude locale：{args.user_home}")
    else:
        set_user_locale(args.user_home)
    verify(patched_app)

    backup = backup_and_replace(args.app, patched_app, args.dry_run)
    if not args.dry_run:
        print(f"備份保留於：{backup}")
        if args.launch:
            run(["open", "-a", str(args.app)], check=False)

    print(f"完成。若尚未自動套用，請在 Claude 的 Language 選單選擇 {LANG_LABEL}。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
