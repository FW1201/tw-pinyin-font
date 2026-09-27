# 臺灣拼音楷 Taiwan Pinyin Kai

打中文字，字的上方就自動顯示**漢語拼音**的繁體中文字型。讀音採**臺灣教育部標準**，並能依詞語自動判斷多音字（例如「銀行 háng／行人 xíng」「長大 zhǎng／很長 cháng」）。

- 基底字型：[霞鶩文楷 TC](https://github.com/lxgw/LxgwWenkaiTC)（OFL 1.1）
- 收字：20,160 字（字型內所有有讀音資料的漢字）；多音字 3,400 多個可用 IVS 指定讀音
- 格式：TrueType（`.ttf`），`fsType = 0`，**Word／PowerPoint 可內嵌字型**
- 下載：[GitHub Releases](https://github.com/FW1201/tw-pinyin-font/releases/latest)｜線上工具：[拼音讀音校正器](https://tw-pinyin-editor.vercel.app)
- 授權：[SIL Open Font License 1.1](OFL.txt)

## 讀音從哪裡來

| 來源 | 用途 | 授權 |
|------|------|------|
| 教育部《國語一字多音審訂表》1999 公告版＋2012 初稿 | 多音字的讀音清單 | 政府公告；CSV 由 g0v 以 CC0 整理 |
| 全字庫 CNS11643 字音屬性 | 審訂表未收字的讀音 | 本專案選用 OFL 1.1 |
| 本專案自建：`sources/rules/custom/` | 預設讀音、詞語規則（約 1,500 詞） | OFL 1.1 |

**不使用任何大陸審音資料**，例如 Unihan kMandarin、《普通話異讀詞審音表》。讀音一律標本調，不標變調（一、不、三聲連讀）。詳見 [sources/rules/upstream/README.md](sources/rules/upstream/README.md)。

## 多音字怎麼處理

1. **自動（rclt／calt）**：字型內建約 1,500 條詞語規則，從左到右以「最長詞優先」判斷讀音。
2. **手動（IVS）**：在字後加上 Unicode 異體字選擇子 `U+E01E0 + n`，就會顯示第 n 個讀音（n 從 0 起算，順序見 [`sources/rules/compiled/chars.tsv`](sources/rules/compiled/chars.tsv)）。IVS 會蓋過自動判斷，而且複製貼上不會遺失。規格見 [docs/ivs-spec.md](docs/ivs-spec.md)。

**Microsoft Office（實測 Mac 版 Word／PowerPoint／Excel 16.113）不執行詞語規則**，只會顯示預設讀音；但 IVS 完全支援。所以在 Office 中請先到 **[拼音讀音校正器](https://tw-pinyin-editor.vercel.app)** 按「複製（固定讀音）」再貼上，或使用 Office 增益集的「固定讀音」：它只在需要的字後插入 IVS，讀音就會正確。瀏覽器、macOS（Pages、Keynote、TextEdit）、Android 會自動判斷詞語，不需要這一步。

## 安裝與使用

- **Windows**：在 `fonts/ttf/TaiwanPinyinKai-Regular.ttf` 上按右鍵 →「為所有使用者安裝」
- **macOS**：雙擊 `.ttf` →「安裝字體」。Mac 版 Office 的字型選單只顯示英文名 **Taiwan Pinyin Kai**；Office 有自己的字型快取，安裝後若沒出現，請把 Office 完全結束再開（實測有時要重開兩次）
- **Word／PowerPoint**：選字型「Taiwan Pinyin Kai」（中文名「臺灣拼音楷」）。PowerPoint 的**行距請設 1.5 倍**，因為單行間距時拼音會碰到上一行；Word 的單行間距就足夠。要傳給沒有安裝字型的人，請對方安裝字型，或改寄 PDF：實測 Word for Mac 的「內嵌字型」只存子集，移除字型後會用替代字型顯示
- **Google 文件／簡報**：只能使用 Google Fonts 的字型，本字型送審中，詳見 [docs/google-fonts-submission.md](docs/google-fonts-submission.md)

各軟體實測結果見 [docs/compat-matrix.md](docs/compat-matrix.md)。

## 建置

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
make            # 編譯讀音規則 → 建置字型（TTF＋WOFF2）→ 測試
```

| 指令 | 說明 |
|------|------|
| `make rules` | `build/compile_rules.py`：審訂表＋全字庫＋自建資料 → `sources/rules/compiled/` |
| `make font` | `build/build_font.py`：產生 `fonts/ttf/、fonts/webfonts/`（約 1 分鐘） |
| `make test` | `pytest tests/`：真實句子讀音、字型與模擬器一致性、IVS、表格檢查 |
| `make fontbakery` | Google Fonts 規範檢查 |

### 自建詞表格式（`sources/rules/custom/words.tsv`）

```
銀行	行=háng          ← 只寫與預設讀音不同的字
為所欲為	1=wéi 4=wéi     ← 同字出現兩次時用位置
爸爸	bà ba           ← 也可以逐字寫完整拼音
```

`compile_rules.py` 會檢查字數不符、重複詞、讀音不在來源清單，以及長詞漏標短詞的特殊讀音。

## 專案結構

```
sources/base/          霞鶩文楷 TC 上游字型與授權
sources/rules/upstream 審訂表、全字庫（上游資料，不修改）
sources/rules/custom   自建：預設讀音、補充讀音、詞表
sources/rules/compiled 編譯結果（字型與工具共用）
build/                 pinyin.py（注音→拼音）、compile_rules.py、build_font.py、shaping.py、simulate.py
tests/                 golden_sentences.tsv（自建真實句子）、test_font.py
docs/                  規格、相容性、Google Fonts 送審、字樣頁、分片實驗
```

## 致謝

霞鶩文楷 TC（LXGW WenKai Project Authors）、全字庫（國家發展委員會）、教育部《國語一字多音審訂表》、g0v moedict-data-csld、ButTaiwan bpmfvs（IVS 注音字型規格的先行者）。
