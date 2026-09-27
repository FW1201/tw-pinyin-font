# Google Fonts 送審準備

Google 文件／簡報只能使用 Google Fonts 的字型，所以要在 Google Workspace 顯示拼音，就必須上架。本文記錄目前的準備狀態。

## 已符合

- OFL 1.1，原始檔與建置流程公開（`make googlefonts` 可從原始碼重建）
- TrueType 輪廓，`fsType = 0`
- 沒有巢狀元件、沒有縮放元件（音節已攤平成簡單 glyph）
- 沒有使用 Stylistic Set（Google Fonts 不支援）；多音字改用 rclt／calt＋IVS
- 讀音資料全部可以用 OFL 散布：審訂表（政府公告）、全字庫（官方提供 OFL 選項）、自建資料

## fontbakery `check-googlefonts`（2026-09-27）

88 PASS／16 WARN／**5 FAIL**：

| FAIL | 狀態 | 處理 |
|------|------|------|
| `family_name_compliance`：中文家族名稱 | ✅ 已處理 | `--google-fonts` 送審版只保留英文名稱 |
| `name/version_format`：版本需 ≥ 1.000 | 發布時處理 | 正式送審時把 `VERSION` 改成 `1.000` |
| `base_has_width`：U+02BE、U+20DD、U+20DE 寬度為 0 | 上游繼承 | 霞鶩文楷 TC 原有，可一併詢問上游或在送審版補寬度 |
| `file_size`：16 MB > 9 MB | 需申請例外 | CJK 字型一律超過；Google Fonts 會以分片提供 |
| `cjk_vertical_metrics`：要求 typo 880／-120、關閉 USE_TYPO_METRICS | **設計衝突** | 見下節 |

## 關鍵議題一：垂直度量

拼音放在漢字上方（約 990–1310 units），所以 ascender 必須超過標準 CJK 字身的 880。依 Google Fonts 的 CJK 規範設成 880／-120 的話，瀏覽器預設行高會讓上一行的漢字壓到下一行的拼音。

兩個選項：

1. **申請例外（建議）**：說明這是注音類字型，拼音需要額外高度，並提供行高測試截圖。
2. **縮小漢字**：送審版把漢字縮到約 80%，讓總高度落在 1.4 em 內。但縮放後的漢字必須攤平成新的輪廓，檔案約會變成 2 倍大，而且和 Office 版的外觀不同，所以不建議。

## 關鍵議題二：分片與多音字

分片實驗（[experiments/slicing](experiments/slicing/index.html)）證實：

- **rclt 詞語規則無法跨分片**：同一個詞的字被分到不同片時，會退回預設讀音。
- **IVS 需要與基字同片**，而且分片工具必須把 `cmap` format 14 的序列一起放進該片。

送審 issue 中要請 Google Fonts 團隊確認：

1. 分片時是否保留 `cmap` format 14（U+E01E0–E01EF 序列）
2. 能否依詞語共現調整分片，至少讓規則詞裡的字盡量分在同一片

即使這兩點都做不到，只要用附加元件先「固定讀音」（寫入 IVS），而且 IVS 能隨基字進同一片，Google 文件仍然能顯示正確讀音。

## 送審步驟

1. 公開 `FW1201/tw-pinyin-font`，建立 release（`fonts/googlefonts/TWPinyinKai-Regular.ttf`）
2. 在 [google/fonts](https://github.com/google/fonts/issues) 開 issue「Add TW Pinyin Kai」，附上：用途、讀音來源與授權、fontbakery 報告、上述兩個關鍵議題
3. 依審查意見修改；Google Fonts 會把 `METADATA.pb`（含 `subsets: "chinese-traditional"`）與字型放進 `ofl/twpinyinkai/`
