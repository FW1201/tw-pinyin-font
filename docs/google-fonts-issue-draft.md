<!--
Google Fonts 送審 issue 草稿（尚未送出）
送出位置：https://github.com/google/fonts/issues/new?template=1_add-font.md
標題：Add Taiwan Pinyin Kai

送出前請確認下方「送出前待辦」，並把 --- 分隔線以下的內容貼到 issue 內文。
-->

# 送出前待辦（不要貼進 issue）

1. **AI 使用揭露**：Google Fonts 要求揭露 AI 工具的使用。本專案的建置程式、自建詞表初稿、文件都由 Claude（Anthropic）協助產生，並經作者審閱；下方草稿已照實寫明，請確認措辭。
2. **原始檔**：本字型沒有 .glyphs／.ufo 設計原始檔。漢字輪廓直接取自霞鶩文楷 TC 的 TTF，拼音由程式用文楷本身的拉丁字母組合而成。所以範本中「The source files are available in the repo」這一項先不勾，並在內文說明；Google Fonts 可能要求改成 UFO 流程或與上游合作。
3. ~~Repo 結構~~：已完成（`fonts/ttf/`、`fonts/webfonts/`、`DESCRIPTION.en_us.html`、`AUTHORS.txt`、`CONTRIBUTORS.txt`）
4. **你本人的承諾**：範本最後一項是「會維護 repo 並參與 onboarding」，要由你決定能不能勾。

---

**Font Project Git Repo URL:**

https://github.com/FW1201/tw-pinyin-font

**Super short description of the Font Family:**

Taiwan Pinyin Kai (臺灣拼音楷) is a Traditional Chinese font that shows **Hanyu Pinyin above every character**, with readings following the Taiwan Ministry of Education standard. It is built on LXGW WenKai TC (already on Google Fonts, OFL). It is aimed at Mandarin learners and teachers in Taiwan and abroad.

- 20,160 CJK ideographs with pinyin; each glyph is a TrueType composite of the WenKai TC ideograph plus a pinyin syllable drawn from WenKai TC's own Latin glyphs.
- **Polyphonic characters** (多音字):
  - ~1,500 word rules in `rclt`/`calt` pick the reading from context, longest match first (e.g. 銀行 yín **háng** vs. 行人 **xíng** rén).
  - Any reading can be pinned in plain text with an ideographic variation selector, `U+E01E0 + n` (cmap format 14). The pinned reading survives copy and paste, and apps that don't run `rclt` still show it.
- Reading data (all OFL-compatible):
  - MOE *Mandarin Polyphone Review Table* 國語一字多音審訂表 (1999; 2012 draft): a government publication; CSV transcription by g0v under CC0
  - CNS11643 phonetic data, published by Taiwan's National Development Council with an explicit OFL-1.1 option
  - Project-authored defaults and word rules
- No mainland-standard reading data (e.g. Unihan kMandarin) is used.

**Requirements:**

By opening this issue, I confirm the project meets the following requirements:

- [x] The entire font project is available in a Github repository (repo) and licensed under the [OFL](https://openfontlicense.org/open-font-license-official-text/)
- [x] I confirm that by 'entire font project', no "plus" or "pro" or other larger version of the project exists as a retail font anywhere
- [ ] The source files are available in the repo — *see note 1 below*
- [x] I am the sole copyright author of the entire project, or all other copyright authors have licensed their work to me under the OFL, and I commit to clearly disclosing if AI tools were used in the creation of this project. — *see note 2 (upstream authors, data sources, AI disclosure)*
- [x] There are no "Reserved Font Names" in the OFL license information, or in the project documentation of any known upstream projects. (LXGW WenKai TC's OFL declares no RFN.)
- [x] The family name is unique according to [namecheck.fontdata.com](https://namecheck.fontdata.com/) (checked 2026-09-27: no match for "Taiwan Pinyin Kai")
- [x] The name of the font family expected to appear on app menus must be very clearly communicated and definitive: **Taiwan Pinyin Kai**
- [x] The font supports at least the Google Fonts 'Latin Core' glyphset (inherited from LXGW WenKai TC)
- [x] The repo has the [Google Fonts preferred upstream repo structure](https://googlefonts.github.io/gf-guide/upstream.html)
- [x] I have read, agree with, and comply with, the full [Google Fonts contributing requirements](https://googlefonts.github.io/gf-guide/index#pre-production-getting-your-fonts-ready-for-gf)
- [ ] I will maintain the repository and participate in the onboarding process

**Notes for the onboarding team**

1. **Sources.** There are no .glyphs/.ufo design sources. The build (`make googlefonts`, Python + fontTools) does the following:
   - reads the upstream LXGW WenKai TC TTF, pinned in `sources/base/`
   - draws pinyin syllables from its Latin glyphs as simple, flattened glyphs, so there are no nested or scaled components
   - composes the ideograph + syllable glyphs
   - compiles the word rules, from plain TSV in `sources/rules/`, into GSUB

   The whole font is reproducible from the repo. We are open to restructuring the pipeline if you require a different source format.
2. **Authors, data and AI disclosure.**
   - Ideograph and Latin outlines: © The LXGW WenKai Project Authors (OFL).
   - Reading data: CNS11643 (OFL option) and the MOE polyphone review table (government publication).
   - Word rules and default readings: authored for this project.
   - AI disclosure: the build scripts, the first draft of the word list, and the documentation were produced with the help of an AI assistant (Anthropic Claude) and reviewed by the author. The readings were proofread against the MOE *Concised Mandarin Dictionary* 國語辭典簡編本, but no dictionary text or data is included in the repo.
3. **Vertical metrics.** We follow the GF CJK schema:
   - typo 880/−120, USE_TYPO_METRICS off, hhea = win
   - the pinyin sits above the em box, so hhea/win are 1291/−304 and the hhea sum is 1.595 UPM, which only raises a WARN in fontbakery
4. **File size.** 16.9 MB, above fontbakery's 9 MB default. Our `fontbakery.yml` raises the limit as for other CJK families. For comparison, LXGW WenKai TC is 12 MB and Chiron Hei HK is 29–31 MB.
5. **CJK slicing and polyphones (please advise).** In our unicode-range slicing experiment (`docs/experiments/slicing/`):
   - `rclt` word rules stop working when a word's characters fall into different slices.
   - IVS readings keep working only if each slice keeps its characters' `cmap` format 14 sequences (U+E01E0–E01EF).

   Could the slicer keep cmap14 entries with their base characters? Can it take co-occurrence (word rules) into account when building slices?
6. **fontbakery** `check-googlefonts`: **0 FAIL / 98 PASS / 18 WARN**, mostly outline WARNs inherited from WenKai TC.
7. **Compatibility.** Tested on HarfBuzz/Chrome and macOS CoreText: defaults, word rules and IVS all work. On Word/PowerPoint/Excel for Mac, defaults and IVS work, but Office does not run the contextual rules. The details are in `docs/compat-matrix.md`.

**Image:**

![Taiwan Pinyin Kai specimen](https://raw.githubusercontent.com/FW1201/tw-pinyin-font/main/docs/images/specimen-coretext.png)

Line 1: default reading. Line 2: word rules (長大 zhǎng, 銀行 háng, 目的 dì, 睡著 zháo). Line 3: IVS-pinned readings. Line 4: running text.
