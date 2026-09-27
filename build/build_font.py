"""建置拼音字型：霞鶩文楷 TC ＋ 拼音音節 glyph ＋ IVS ＋ rclt 詞語規則。

    python build/build_font.py [--limit N] [--woff2] [--google-fonts]

    --google-fonts  Google Fonts 送審版：只保留英文字型名稱（Google Fonts 不允許非拉丁字母的家族名稱）

流程：
    1. 讀 rules/compiled/chars.tsv、rules.tsv（先跑 build/compile_rules.py）
    2. 用文楷自己的拉丁字母畫出每個帶調音節（簡單 glyph，不用巢狀或縮放元件，符合 Google Fonts 檢查）
    3. 每個漢字 × 每個讀音 = 一個 composite glyph（漢字元件＋音節元件），命名 u<碼位>.rN
       會被詞規則替換的字，另有 u<碼位>.vd（預設讀音的複本），供 IVS 明確指定預設讀音時使用，
       避免被 rclt 改掉；其他讀音的 .rN 本來就不會被替換，IVS 直接指向它們
    4. cmap：字 → 預設讀音 glyph；cmap14：字 + U+E01E0+N → .rN 或 .vd
    5. GSUB：rclt＋calt 共用詞語規則；每條規則從詞首比對整個詞（等同最長詞優先的正向最大比對）
    6. 調整垂直度量與字型名稱
"""

from __future__ import annotations

import argparse
import sys
import unicodedata
from pathlib import Path

from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont, newTable
from fontTools.ttLib.tables import otTables
from fontTools.ttLib.tables._g_l_y_f import USE_MY_METRICS, Glyph, GlyphComponent

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pinyin import glyph_suffix  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
BASE_FONT = ROOT / "sources/base/LXGWWenKaiTC-Regular.ttf"
COMPILED = ROOT / "sources/rules/compiled"
OUT_DIR = ROOT / "fonts"

FAMILY_EN = "TW Pinyin Kai"
FAMILY_ZH_HANT = "臺灣拼音楷"
FAMILY_ZH_HANS = "台湾拼音楷"
PS_NAME = "TWPinyinKai-Regular"
VERSION = "0.100"
REPO_URL = "https://github.com/FW1201/tw-pinyin-font"

# 拼音排版參數（單位：font units，UPM 1000）
PY_SCALE = 0.34        # 拉丁字母縮放比例（x 高約為漢字的 1/6，國小教材可讀）
PY_BASELINE = 990      # 拼音基線高度（漢字頂端約 880，g／y 下伸部不碰漢字）
PY_MAX_WIDTH = 960     # 音節最大寬度；超過就水平壓縮
PY_TRACKING = 8        # 字母間距（縮放後）
ASCENDER = 1310        # 新的 hhea／typo ascender（涵蓋 ǚ 等最高的聲調符號）
DESCENDER = -280

IVS_BASE = 0xE01E0
RULES_PER_SUBTABLE = 64


def load_chars(limit: int | None):
    chars = {}
    for line in (COMPILED / "chars.tsv").read_text(encoding="utf-8").splitlines():
        if line.startswith("#") or not line.strip():
            continue
        ch, _, default, readings = line.split("\t")
        chars[ch] = (readings.split("|"), default)
    return chars


def load_rules():
    rules = []
    for line in (COMPILED / "rules.tsv").read_text(encoding="utf-8").splitlines():
        if line.startswith("#") or not line.strip():
            continue
        word, py = line.split("\t")
        rules.append((word, py.split()))
    return rules


class Builder:
    def __init__(self, font: TTFont):
        self.font = font
        self.glyf = font["glyf"]
        self.hmtx = font["hmtx"]
        self.vmtx = font["vmtx"] if "vmtx" in font else None
        self.cmap = font.getBestCmap()
        self.order = list(font.getGlyphOrder())
        self.syllable_glyphs: dict[str, str] = {}

    # ---------- glyph 基本操作 ----------
    def add_glyph(self, name: str, glyph: Glyph, advance: int, vadvance: tuple[int, int] | None = None):
        glyph.recalcBounds(self.glyf)
        self.glyf[name] = glyph
        self.hmtx[name] = (advance, getattr(glyph, "xMin", 0))
        if self.vmtx is not None:
            self.vmtx[name] = vadvance or (1000, 0)
        self.order.append(name)

    def letter_glyphs(self, text: str) -> list[str]:
        """把音節字串拆成字型裡有的 glyph；沒有預組字就用基本字母＋組合符號。"""
        out = []
        for ch in unicodedata.normalize("NFC", text):
            if ord(ch) in self.cmap:
                out.append(self.cmap[ord(ch)])
            else:
                for part in unicodedata.normalize("NFD", ch):
                    if ord(part) not in self.cmap:
                        raise KeyError(f"字型缺少 {part!r}（{text}）")
                    out.append(self.cmap[ord(part)])
        return out

    # ---------- 1. 音節 glyph ----------
    def syllable(self, reading: str) -> str:
        if reading in self.syllable_glyphs:
            return self.syllable_glyphs[reading]
        name = "py." + glyph_suffix(reading)
        letters = self.letter_glyphs(reading)
        glyphset = self.font.getGlyphSet()
        advances = [self.hmtx[g][0] for g in letters]
        raw_width = sum(advances) * PY_SCALE + PY_TRACKING * max(0, len(letters) - 1)
        sx = PY_SCALE * min(1.0, PY_MAX_WIDTH / raw_width) if raw_width else PY_SCALE
        track = PY_TRACKING * min(1.0, PY_MAX_WIDTH / raw_width) if raw_width else 0
        width = sum(advances) * sx + track * max(0, len(letters) - 1)
        x = (1000 - width) / 2
        pen = TTGlyphPen(None)
        for g, adv in zip(letters, advances):
            glyphset[g].draw(TransformPen(pen, (sx, 0, 0, PY_SCALE, x, PY_BASELINE)))
            if adv:  # 組合符號寬度為 0，疊在前一個字母上
                x += adv * sx + track
        self.add_glyph(name, pen.glyph(), 1000)
        self.syllable_glyphs[reading] = name
        return name

    # ---------- 2. 注音漢字 composite ----------
    def base_components(self, base: str) -> list[tuple[str, int, int, object]]:
        g = self.glyf[base]
        if g.isComposite():
            comps = []
            for c in g.components:
                if self.glyf[c.glyphName].isComposite():
                    raise ValueError(f"{base} 有巢狀元件")
                comps.append((c.glyphName, c.x, c.y, getattr(c, "transform", None)))
            return comps
        return [(base, 0, 0, None)]

    def annotated(self, name: str, base: str, reading: str) -> str:
        adv = self.hmtx[base][0]
        syl = self.syllable(reading)
        glyph = Glyph()
        glyph.numberOfContours = -1
        glyph.components = []
        for i, (gname, x, y, transform) in enumerate(self.base_components(base) + [(syl, (adv - 1000) // 2, 0, None)]):
            comp = GlyphComponent()
            comp.glyphName, comp.x, comp.y = gname, x, y
            comp.flags = USE_MY_METRICS if (i == 0 and gname == base) else 0
            if transform is not None:
                comp.transform = transform
            glyph.components.append(comp)
        vadv = self.vmtx[base] if self.vmtx is not None else None
        self.add_glyph(name, glyph, adv, vadv)
        return name


def build(limit: int | None, woff2: bool, google_fonts: bool = False) -> Path:
    chars = load_chars(limit)
    rules = load_rules()
    font = TTFont(BASE_FONT)
    b = Builder(font)

    # 只處理字型裡有字形的字
    todo = [(ch, readings, default) for ch, (readings, default) in chars.items() if ord(ch) in b.cmap]
    if limit:
        needed = {c for w, _ in rules for c in w}
        todo = [t for t in todo if t[0] in needed] + [t for t in todo if t[0] not in needed][:limit]
    print(f"annotating {len(todo)} chars (of {len(chars)} with readings)")

    # 會被詞規則改讀音的字
    targets = {c for w, sy in rules for c, s in zip(w, sy) if c in chars and s != chars[c][1]}

    default_glyph: dict[str, str] = {}
    variant_glyphs: dict[str, list[str]] = {}   # 字 → [.r0, .r1, ...]
    ivs_glyphs: dict[str, list[str]] = {}       # 字 → IVS 序對應的 glyph
    for ch, readings, default in todo:
        base = b.cmap[ord(ch)]
        stem = f"u{ord(ch):04X}"  # 用碼位命名：相容字與統一字可能共用同一個基底 glyph
        variant_glyphs[ch] = [b.annotated(f"{stem}.r{i}", base, r) for i, r in enumerate(readings)]
        d = readings.index(default)
        default_glyph[ch] = variant_glyphs[ch][d]
        if len(readings) > 1:
            ivs = list(variant_glyphs[ch])
            if ch in targets:
                ivs[d] = b.annotated(f"{stem}.vd", base, default)
            ivs_glyphs[ch] = ivs

    font.setGlyphOrder(b.order)
    font["maxp"].numGlyphs = len(b.order)
    print(f"glyphs: {len(b.order)} (syllables {len(b.syllable_glyphs)})")
    if len(b.order) > 65535:
        raise SystemExit("超過 65,535 glyph 上限")

    # ---------- cmap ----------
    for table in font["cmap"].tables:
        if table.format in (4, 12):
            for ch, g in default_glyph.items():
                if table.format == 12 or ord(ch) <= 0xFFFF:
                    table.cmap[ord(ch)] = g
        elif table.format == 14:
            for ch, glyphs in ivs_glyphs.items():
                for i, g in enumerate(glyphs):
                    table.uvsDict.setdefault(IVS_BASE + i, []).append((ord(ch), g))

    # ---------- GSUB rclt / calt ----------
    add_word_rules(font, rules, chars, default_glyph, variant_glyphs, ivs_glyphs)

    # ---------- 度量與名稱 ----------
    set_metrics(font)
    set_names(font, google_fonts)
    font["head"].fontRevision = float(VERSION)

    OUT_DIR.mkdir(exist_ok=True)
    out = OUT_DIR / ("googlefonts" if google_fonts else "") / f"{PS_NAME}.ttf"
    out.parent.mkdir(parents=True, exist_ok=True)
    font.save(out)
    print(f"saved {out} ({out.stat().st_size / 1e6:.1f} MB)")
    if woff2:
        font.flavor = "woff2"
        wout = out.with_suffix(".woff2")
        font.save(wout)
        print(f"saved {wout} ({wout.stat().st_size / 1e6:.1f} MB)")
    return out


def add_word_rules(font, rules, chars, default_glyph, variant_glyphs, ivs_glyphs) -> None:
    """把詞語規則編成 GSUB lookup，附加到原字型 GSUB 的 rclt 與 calt。"""
    usable = [(w, sy) for w, sy in rules if all(c in default_glyph for c in w)]
    if not usable:
        print("no word rules")
        return

    # 每個讀音序號一個 SingleSubst：預設 glyph → .rN
    max_n = max(len(chars[c][0]) for c in variant_glyphs)
    lines = ["languagesystem DFLT dflt;", "languagesystem hani dflt;", "languagesystem latn dflt;"]
    for n in range(max_n):
        subs = [
            f"    sub {default_glyph[c]} by {v[n]};"
            for c, v in variant_glyphs.items()
            if len(v) > n and v[n] != default_glyph[c]
        ]
        if subs:
            lines += [f"lookup PY_R{n} {{", *subs, f"}} PY_R{n};"]

    def glyph_class(ch: str) -> str:
        gs = list(dict.fromkeys(variant_glyphs[ch] + ivs_glyphs.get(ch, [])))
        return gs[0] if len(gs) == 1 else "[" + " ".join(gs) + "]"

    body = []
    for word, sy in usable:
        parts = []
        changed = False
        for ch, reading in zip(word, sy):
            readings, _ = chars[ch]
            n = readings.index(reading)
            cls = glyph_class(ch)
            if variant_glyphs[ch][n] != default_glyph[ch]:
                parts.append(f"{cls}' lookup PY_R{n}")
                changed = True
            else:
                parts.append(f"{cls}'")
        body.append(("    sub " if changed else "    ignore sub ") + " ".join(parts) + ";")
    # 每 RULES_PER_SUBTABLE 條規則切一個 subtable：避免單一 class-based subtable 的類別數過多
    # （實測 1,000 多類時 HarfBuzz 會漏掉部分規則）。subtable 依序嘗試，長詞優先的語意不變。
    chunked = []
    for i, rule in enumerate(body):
        if i and i % RULES_PER_SUBTABLE == 0:
            chunked.append("    subtable;")
        chunked.append(rule)
    lines += ["lookup PY_WORDS {", *chunked, "} PY_WORDS;"]
    fea = "\n".join(lines)
    (ROOT / "build" / "out").mkdir(exist_ok=True)
    (ROOT / "build" / "out" / "words.fea").write_text(fea, encoding="utf-8")

    # 在暫存字型上編譯，再把 lookup 併入原 GSUB
    tmp = TTFont()
    tmp.setGlyphOrder(font.getGlyphOrder())
    addOpenTypeFeaturesFromString(tmp, fea + "\nfeature rclt { lookup PY_WORDS; } rclt;\n", tables=["GSUB"])
    new = tmp["GSUB"].table
    gsub = font["GSUB"].table
    offset = len(gsub.LookupList.Lookup)
    words_index = None
    for i, lk in enumerate(new.LookupList.Lookup):
        for st in lk.SubTable:
            remap_nested(st, offset)
        gsub.LookupList.Lookup.append(lk)
    for fr in new.FeatureList.FeatureRecord:
        if fr.FeatureTag == "rclt":
            words_index = [i + offset for i in fr.Feature.LookupListIndex]
    gsub.LookupList.LookupCount = len(gsub.LookupList.Lookup)
    for tag in ("rclt", "calt"):
        add_feature(gsub, tag, words_index)
    print(f"word rules: {len(usable)} (lookups +{len(new.LookupList.Lookup)})")


def remap_nested(table, offset: int) -> None:
    """把 contextual／chained lookup 內所有 SubstLookupRecord 的索引加上 offset。

    feaLib 會依規則形狀自動選 type 5／6、format 1／2／3，所以用遞迴走訪所有子結構。
    """
    seen: set[int] = set()

    def walk(obj) -> None:
        if obj is None or id(obj) in seen:
            return
        seen.add(id(obj))
        if isinstance(obj, list):
            for item in obj:
                walk(item)
            return
        if isinstance(obj, otTables.SubstLookupRecord):
            obj.LookupListIndex += offset
            return
        if isinstance(obj, otTables.BaseTable):
            for value in vars(obj).values():
                if isinstance(value, (list, otTables.BaseTable)):
                    walk(value)

    walk(table)


def add_feature(gsub, tag: str, lookup_indices: list[int]) -> None:
    """新增（或擴充）feature，並掛到所有 script／langsys。"""
    fl = gsub.FeatureList
    existing = [i for i, fr in enumerate(fl.FeatureRecord) if fr.FeatureTag == tag]
    if existing:
        feat = fl.FeatureRecord[existing[0]].Feature
        feat.LookupListIndex = sorted(set(feat.LookupListIndex) | set(lookup_indices))
        feat.LookupCount = len(feat.LookupListIndex)
        return
    fr = otTables.FeatureRecord()
    fr.FeatureTag = tag
    fr.Feature = otTables.Feature()
    fr.Feature.FeatureParams = None
    fr.Feature.LookupListIndex = list(lookup_indices)
    fr.Feature.LookupCount = len(lookup_indices)
    old = list(fl.FeatureRecord)
    records = sorted(old + [fr], key=lambda r: r.FeatureTag)
    remap = {old.index(r): records.index(r) for r in old}
    new_index = records.index(fr)
    fl.FeatureRecord = records
    fl.FeatureCount = len(records)
    for sr in gsub.ScriptList.ScriptRecord:
        langsys = [sr.Script.DefaultLangSys] + [l.LangSys for l in sr.Script.LangSysRecord]
        for ls in langsys:
            if ls is None:
                continue
            ls.FeatureIndex = sorted([remap[i] for i in ls.FeatureIndex] + [new_index])
            ls.FeatureCount = len(ls.FeatureIndex)
            if ls.ReqFeatureIndex != 0xFFFF:
                ls.ReqFeatureIndex = remap[ls.ReqFeatureIndex]


def set_metrics(font: TTFont) -> None:
    ymax = max(getattr(font["glyf"][g], "yMax", 0) for g in font.getGlyphOrder())
    ymin = min(getattr(font["glyf"][g], "yMin", 0) for g in font.getGlyphOrder())
    hhea, os2 = font["hhea"], font["OS/2"]
    hhea.ascent, hhea.descent, hhea.lineGap = ASCENDER, DESCENDER, 0
    os2.sTypoAscender, os2.sTypoDescender, os2.sTypoLineGap = ASCENDER, DESCENDER, 0
    os2.usWinAscent = max(ymax, ASCENDER)
    os2.usWinDescent = max(-ymin, -DESCENDER)
    os2.fsSelection |= 1 << 7  # USE_TYPO_METRICS
    os2.fsType = 0             # Installable：Office 可內嵌
    os2.achVendID = "TWPY"


def set_names(font: TTFont, google_fonts: bool = False) -> None:
    name = font["name"]
    copyright_ = (
        "Copyright 2022-2026 The LXGW WenKai Project Authors (https://github.com/lxgw/LxgwWenkaiTC); "
        f"Copyright 2026 The TW Pinyin Kai Project Authors ({REPO_URL})"
    )
    description = (
        "Hanyu Pinyin annotated Traditional Chinese font. Readings based on the Ministry of Education "
        "(Taiwan) Mandarin Polyphone Review Table (1999; 2012 draft), Unihan kMandarin, and project-authored data."
    )
    keep = {0, 1, 2, 3, 4, 5, 6, 10, 13, 14, 16, 17}
    # 先清掉原字型（霞鶩文楷）的名稱，只留 Windows 英文紀錄再覆寫
    name.names = [n for n in name.names if n.nameID in keep and n.nameID not in (16, 17) and n.platformID == 3 and n.langID == 0x409]
    en = {
        0: copyright_,
        1: FAMILY_EN,
        2: "Regular",
        3: f"{VERSION};TWPY;{PS_NAME}",
        4: f"{FAMILY_EN} Regular",
        5: f"Version {VERSION}",
        6: PS_NAME,
        10: description,
        13: "This Font Software is licensed under the SIL Open Font License, Version 1.1. "
        "This license is available with a FAQ at: https://openfontlicense.org",
        14: "https://openfontlicense.org",
    }
    for nid, text in en.items():
        name.setName(text, nid, 3, 1, 0x409)
    for lang, fam in () if google_fonts else ((0x404, FAMILY_ZH_HANT), (0xC04, FAMILY_ZH_HANT), (0x1404, FAMILY_ZH_HANT), (0x804, FAMILY_ZH_HANS)):
        name.setName(fam, 1, 3, 1, lang)
        name.setName("Regular", 2, 3, 1, lang)
        name.setName(f"{fam} Regular", 4, 3, 1, lang)
    # 移除原字型殘留的其他平台名稱
    name.names = [n for n in name.names if n.platformID == 3]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, help="只建前 N 個字（加上規則用到的字），快速測試用")
    ap.add_argument("--woff2", action="store_true")
    ap.add_argument("--google-fonts", action="store_true", help="Google Fonts 送審版（只有英文名稱）")
    args = ap.parse_args()
    build(args.limit, args.woff2, args.google_fonts)


if __name__ == "__main__":
    main()
