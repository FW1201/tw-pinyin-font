# 相容性矩陣

最後更新：2026-09-27（v0.100）
符號：✅ 已驗證可用｜❌ 已驗證不可用｜⏳ 待實測｜➖ 不適用

| 環境 | 預設讀音 | 詞語規則 rclt／calt | IVS 指定讀音 | 內嵌字型 | 驗證方式 |
|------|:---:|:---:|:---:|:---:|------|
| HarfBuzz（uharfbuzz 0.56；Chrome、Android、LibreOffice、Figma 等使用的排版引擎） | ✅ | ✅ | ✅ | ➖ | `pytest tests/`：66 項（含 1,469 條規則逐詞比對、300 段隨機文字） |
| Chrome（macOS） | ✅ | ✅ | ✅ | ➖ | [字樣頁](specimen.html) 目視檢查 |
| Chrome＋unicode-range 分片（模擬 Google Fonts） | ✅ | ❌ 跨片失效 | ⚠️ 須與基字同片 | ➖ | [分片實驗](experiments/slicing/index.html) |
| Word（Windows） | ⏳ | ⏳ | ⏳ | ⏳ | 見下方檢核表 |
| Word（macOS） | ⏳ | ⏳ | ⏳ | ⏳ | |
| Word 網頁版 | ⏳ | ⏳ | ⏳ | ➖ | |
| PowerPoint（Windows／macOS） | ⏳ | ⏳ | ⏳ | ⏳ | |
| Excel（Windows／macOS） | ⏳ | ⏳ | ⏳ | ➖ | |
| Pages／Keynote | ⏳ | ⏳ | ⏳ | ➖ | |
| LibreOffice Writer | ⏳ | ⏳ | ⏳ | ⏳ | 使用 HarfBuzz，預期可用 |
| Google 文件／簡報 | ❌ 無法載入自訂字型 | — | — | ➖ | 需先上架 Google Fonts |

## 分片實驗結論

Google Fonts 會把 CJK 字型切成 100 多個 `unicode-range` 分片。在 Chrome 模擬的結果：

1. 詞語規則只在同一片內有效，例如「銀」「行」分在不同片時，「行」會退回預設讀音 xíng。
2. IVS 必須和基字在同一片，而且該片的 `cmap` format 14 要保留這個序列，否則會退回預設讀音。

所以在 Google 端，正確讀音要靠附加元件的「固定讀音」（IVS）來保證；送審時必須確認分片工具會保留每一片的 IVS 序列（見 [google-fonts-submission.md](google-fonts-submission.md)）。

## Office 實測檢核表

請在每個環境安裝 `fonts/TWPinyinKai-Regular.ttf`，把 [`tests/fixtures/office-test.txt`](../tests/fixtures/office-test.txt) 整份複製貼上（含 IVS），字型設為 **TW Pinyin Kai**：

| # | 測試文字 | 預期 | 說明 |
|---|------|------|------|
| 1 | `長` | cháng | 預設讀音（cmap） |
| 2 | `長大`、`銀行` | zhǎng dà、yín háng | 詞語規則；Word 若沒反應，到「字型 → 進階 → 使用內容替代字」勾選後再試 |
| 3 | 從校正器複製「銀行（行指定 xíng）」貼上 | yín xíng | IVS 指定讀音 |
| 4 | 行高 | 拼音不被裁切、行與行不重疊 | 單行間距 |
| 5 | 另存時勾選「在檔案中內嵌字型」，在未安裝字型的電腦開啟 | 顯示與原機相同 | 內嵌（TrueType、fsType 0） |
| 6 | 字型選單名稱 | Windows：臺灣拼音楷／TW Pinyin Kai；Mac：TW Pinyin Kai | 名稱表 |

實測後請更新上表，並附上 Office 版本號。
