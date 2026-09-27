# 相容性矩陣

最後更新：2026-09-27（v0.100）
符號：✅ 已驗證可用｜❌ 已驗證不可用｜⏳ 待實測｜➖ 不適用

| 環境 | 預設讀音 | 詞語規則 rclt／calt | IVS 指定讀音 | 內嵌字型 | 驗證方式 |
|------|:---:|:---:|:---:|:---:|------|
| HarfBuzz（uharfbuzz 0.56；Chrome、Android、LibreOffice、Figma 等使用的排版引擎） | ✅ | ✅ | ✅ | ➖ | `pytest tests/`：66 項（含 1,469 條規則逐詞比對、300 段隨機文字） |
| Chrome（macOS） | ✅ | ✅ | ✅ | ➖ | [字樣頁](specimen.html) 目視檢查 |
| Chrome＋unicode-range 分片（模擬 Google Fonts） | ✅ | ❌ 跨片失效 | ⚠️ 須與基字同片 | ➖ | [分片實驗](experiments/slicing/index.html) |
| Word（Windows） | ⏳ | ⏳ | ⏳ | ⏳ | 見下方檢核表 |
| Word（macOS 16.113） | ✅ | ❌（開啟「內容替代字」也無效） | ✅ | ❌ 內嵌子集字型不被使用 | 2026-09-27 實測；單行間距即足夠，不需 1.5 倍 |
| Word 網頁版 | ⏳ | ⏳ | ⏳ | ➖ | |
| PowerPoint（macOS 16.113） | ✅ | ❌ | ✅ | ⏳ | 2026-09-27 實測；單行間距拼音會壓到上一行，需 1.5 倍行高 |
| PowerPoint（Windows） | ⏳ | ⏳ | ⏳ | ⏳ | |
| Excel（macOS 16.113） | ✅ | ❌ | ✅ | ➖ | 2026-09-27 實測；列高需調高 |
| Excel（Windows） | ⏳ | ⏳ | ⏳ | ➖ | |
| macOS CoreText（Pages、Keynote、TextEdit、Safari） | ✅ | ✅ | ✅ | ➖ | 2026-09-27 以 AppKit 繪製實測 |
| LibreOffice Writer | ⏳ | ⏳ | ⏳ | ⏳ | 使用 HarfBuzz，預期可用 |
| Google 文件／簡報 | ❌ 無法載入自訂字型 | — | — | ➖ | 需先上架 Google Fonts |

## Mac 版 Office 實測結論（2026-09-27）

- Mac 版 PowerPoint／Excel 對中文文字**完全不執行 GSUB 情境替換**。實驗版把詞語規則同時掛在 ccmp、liga、clig、rlig 上也無效；但預設讀音（cmap）與 **IVS（cmap 14）完全正確**。
- Word for Mac 同樣不執行詞語規則，即使在 docx 中開啟 `w14:cntxtAlts`（使用內容替代字）也一樣；「固定讀音」後全部正確（[截圖](images/word-pinned.png)）。Word 的單行間距會依字型度量保留拼音空間，不需要調行距。
- **內嵌字型**：Word for Mac 儲存時只內嵌子集（實測 488 KB，cmap 與內文不對應），移除字型後重開仍然使用替代字型。所以傳給沒有安裝字型的人時，請對方安裝字型，或改寄 PDF。Windows 版 Word 的內嵌尚未實測。
- Mac 版 Office 有自己的字型快取：安裝或更新字型後，第一次重開仍可能用替代字型，要再完全結束、重開一次才會生效。
- 所以 Office 的建議流程是：用校正器或增益集「固定讀音」寫入 IVS，再把行距設為 1.5 倍。已用「固定讀音」後的簡報驗證：長大、銀行、目的、睡著、弟弟、音樂、快樂、得到、覺得、高興地全部正確。

## 分片實驗結論

Google Fonts 會把 CJK 字型切成 100 多個 `unicode-range` 分片。在 Chrome 模擬的結果：

1. 詞語規則只在同一片內有效，例如「銀」「行」分在不同片時，「行」會退回預設讀音 xíng。
2. IVS 必須和基字在同一片，而且該片的 `cmap` format 14 要保留這個序列，否則會退回預設讀音。

所以在 Google 端，正確讀音要靠附加元件的「固定讀音」（IVS）來保證；送審時必須確認分片工具會保留每一片的 IVS 序列（見 [google-fonts-submission.md](google-fonts-submission.md)）。

## Office 實測檢核表

請在每個環境安裝 `fonts/ttf/TaiwanPinyinKai-Regular.ttf`，把 [`tests/fixtures/office-test.txt`](../tests/fixtures/office-test.txt) 整份複製貼上（含 IVS），字型設為 **Taiwan Pinyin Kai**：

| # | 測試文字 | 預期 | 說明 |
|---|------|------|------|
| 1 | `長` | cháng | 預設讀音（cmap） |
| 2 | `長大`、`銀行` | zhǎng dà、yín háng | 詞語規則；Word 若沒反應，到「字型 → 進階 → 使用內容替代字」勾選後再試 |
| 3 | 從校正器複製「銀行（行指定 xíng）」貼上 | yín xíng | IVS 指定讀音 |
| 4 | 行高 | 拼音不被裁切、行與行不重疊 | 單行間距 |
| 5 | 另存時勾選「在檔案中內嵌字型」，在未安裝字型的電腦開啟 | 顯示與原機相同 | 內嵌（TrueType、fsType 0） |
| 6 | 字型選單名稱 | Windows：臺灣拼音楷／Taiwan Pinyin Kai；Mac：Taiwan Pinyin Kai | 名稱表 |

實測後請更新上表，並附上 Office 版本號。
