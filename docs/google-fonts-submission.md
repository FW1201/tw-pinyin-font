# Google Fonts 送審準備

Google 文件／簡報只能使用 Google Fonts 的字型，所以要在 Google Workspace 顯示拼音，就必須上架。本文記錄目前的準備狀態。

## 已符合

- OFL 1.1，原始檔與建置流程公開（`make googlefonts` 可從原始碼重建）
- TrueType 輪廓，`fsType = 0`
- 沒有巢狀元件、沒有縮放元件（音節已攤平成簡單 glyph）
- 沒有使用 Stylistic Set（Google Fonts 不支援）；多音字改用 rclt／calt＋IVS
- 讀音資料全部可以用 OFL 散布：審訂表（政府公告）、全字庫（官方提供 OFL 選項）、自建資料

## fontbakery `check-googlefonts`（2026-09-27，v1.000）

**0 FAIL**／98 PASS／18 WARN（`make fontbakery`，設定檔 `fontbakery.yml`）。原本的 5 項 FAIL 處理如下：

| 原 FAIL | 處理 |
|------|------|
| `family_name_compliance`：中文家族名稱 | `--google-fonts` 送審版只保留英文名稱 |
| `family_name_compliance`：「TW」被視為縮寫 | 英文名稱改為 **Taiwan Pinyin Kai** |
| `name/version_format`：版本需 ≥ 1.000 | 版本升為 1.000 |
| `base_has_width`：U+20DD、U+20DE、U+02BE 寬度為 0 | 新增 GDEF，把 63 個組合符號標為 mark；U+02BE（非組合符號）補上前進寬度 |
| `cjk_vertical_metrics` | typo 改為 880／-120 並關閉 USE_TYPO_METRICS；hhea＝win，涵蓋拼音最高點。行高由 hhea／win 決定，拼音不會被裁切（剩下的 WARN：hhea 總和 1.595 em，超過建議的 1.5 em，因為拼音需要額外高度） |
| `file_size`：16 MB > 9 MB | `fontbakery.yml` 設定 CJK 例外上限；Google Fonts 現有的 CJK 字型都超過 9 MB，例如 LXGW WenKai TC 12 MB、Chiron Hei HK 31 MB |

## 關鍵議題一：垂直度量（已解決）

typo 維持 Google Fonts 要求的 880／-120 並關閉 USE_TYPO_METRICS，瀏覽器與 Office 改用 hhea／win 計算行高；hhea＝win＝字形實際最高與最低點，所以拼音有足夠空間。送審時只需說明 hhea 總和 1.595 em 的 WARN。

## 關鍵議題二：分片與多音字

分片實驗（[experiments/slicing](experiments/slicing/index.html)）證實：

- **rclt 詞語規則無法跨分片**：同一個詞的字被分到不同片時，會退回預設讀音。
- **IVS 需要與基字同片**，而且分片工具必須把 `cmap` format 14 的序列一起放進該片。

送審 issue 中要請 Google Fonts 團隊確認：

1. 分片時是否保留 `cmap` format 14（U+E01E0–E01EF 序列）
2. 能否依詞語共現調整分片，至少讓規則詞裡的字盡量分在同一片

即使這兩點都做不到，只要用附加元件先「固定讀音」（寫入 IVS），而且 IVS 能隨基字進同一片，Google 文件仍然能顯示正確讀音。

## 送審步驟

1. 公開 `FW1201/tw-pinyin-font`，建立 release（`fonts/googlefonts/ttf/TaiwanPinyinKai-Regular.ttf`）
2. 在 [google/fonts](https://github.com/google/fonts/issues) 開 issue「Add Taiwan Pinyin Kai」，附上：用途、讀音來源與授權、fontbakery 報告、上述兩個關鍵議題
3. 依審查意見修改；Google Fonts 會把 `METADATA.pb`（含 `subsets: "chinese-traditional"`）與字型放進 `ofl/taiwanpinyinkai/`
