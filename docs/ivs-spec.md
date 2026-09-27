# 拼音 IVS 規格（Taiwan Pinyin Kai v0.1）

## 編碼

在漢字後面加一個異體字選擇子（Variation Selector Supplement）：

```
<漢字> U+E01E0+n
```

會顯示該字讀音清單中的第 `n` 個讀音（`n` = 0–15）。讀音清單的順序固定記錄在
[`sources/rules/compiled/chars.tsv`](../sources/rules/compiled/chars.tsv) 第 4 欄，依以下來源的先後排列：

1. 《國語一字多音審訂表》1999 年版的讀音（依原表順序：注音符號序）
2. 2012 年初稿追加的讀音
3. 全字庫字音（只用於審訂表未收的字）
4. 自建補充讀音、自建詞表出現的讀音（例如輕聲 `ma`、兒化 `r`）

例：`行`＝`xíng|xìng|háng|hàng`，所以 `行 U+E01E2` 顯示 háng。

**沒有 IVS** 的字顯示「自動讀音」：先看詞語規則（rclt／calt），沒有規則命中時使用預設讀音（`chars.tsv` 第 3 欄）。

## 與 bpmfvs（注音 IVS）的關係

本規格沿用 [ButTaiwan/bpmfvs](https://github.com/ButTaiwan/bpmfvs) 的精神：把讀音序號編在 IVS 中，讓讀音跟著文字走。不過兩者的讀音順序**不保證相同**：bpmfvs 以注音字型的讀音表排序，本字型以審訂表排序。在兩種字型之間切換時，請重新用校正器固定讀音。

## 穩定性承諾

- 已發布的讀音序號**不會改變**；新讀音只會加在清單尾端。
- 預設讀音與詞語規則可能在新版本中調整，所以需要長期固定的讀音，請用 IVS。

## 字型實作

| 項目 | 作法 |
|------|------|
| glyph | `u<碼位>.rN` = 漢字元件＋第 N 個讀音的音節元件（TrueType composite，深度 1） |
| 預設 | `cmap`（format 4／12）指向預設讀音的 `.rN` |
| IVS | `cmap` format 14：非預設讀音指向 `.rN`；預設讀音若可能被詞語規則改掉，另指向複本 `.vd` |
| 詞語規則 | GSUB contextual lookup，同時掛在 `rclt` 與 `calt`；每條規則比對整個詞，只替換預設 glyph，所以 IVS 指定的 glyph 不會被改掉，重複套用也不會出錯 |
| subtable | 每 64 條規則切一個 subtable。單一 class-based subtable 超過約 1,000 類時，實測 HarfBuzz 會漏掉部分規則 |
