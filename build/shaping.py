"""用 HarfBuzz 排版文字，回傳每個字實際顯示的拼音（測試與驗證用）。

    python build/shaping.py "我們去銀行領錢"
"""

from __future__ import annotations

import sys
from functools import lru_cache
from pathlib import Path

import uharfbuzz as hb
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_FONT = ROOT / "fonts" / "TWPinyinKai-Regular.ttf"
COMPILED = ROOT / "sources/rules/compiled/chars.tsv"


@lru_cache(maxsize=4)
def _load(font_path: str):
    data = Path(font_path).read_bytes()
    face = hb.Face(data)
    font = hb.Font(face)
    tt = TTFont(font_path, lazy=True)
    order = tt.getGlyphOrder()
    readings = {}
    for line in COMPILED.read_text(encoding="utf-8").splitlines():
        if not line.startswith("#") and line.strip():
            ch, _, default, rs = line.split("\t")
            readings[ch] = (rs.split("|"), default)
    # glyph 名稱 → 讀音
    base_to_char = {g: chr(cp) for cp, g in tt["cmap"].getBestCmap().items() if "." not in g}
    # cmap 已改指向注音 glyph，改由 .rN 名稱反推原字
    uni_to_base = {}
    glyph_reading = {}
    for name in order:
        if ".r" in name or name.endswith(".vd"):
            base, suffix = name.rsplit(".", 1)
            uni_to_base.setdefault(base, None)
            glyph_reading[name] = (base, suffix)
    return font, order, readings, glyph_reading


def shape(text: str, font_path: str | Path = DEFAULT_FONT, features: dict | None = None) -> list[str]:
    """回傳每個 glyph 的名稱。"""
    font, order, _, _ = _load(str(font_path))
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(font, buf, features or {})
    return [order[i.codepoint] for i in buf.glyph_infos]


def readings_of(text: str, font_path: str | Path = DEFAULT_FONT, features: dict | None = None) -> list[str | None]:
    """每個漢字的顯示讀音（沒有拼音的字回傳 None）。IVS 選擇子不佔位置。"""
    _, _, readings, glyph_reading = _load(str(font_path))
    glyphs = shape(text, font_path, features)
    chars = [c for c in text if not (0xE0100 <= ord(c) <= 0xE01EF or 0xFE00 <= ord(c) <= 0xFE0F)]
    out: list[str | None] = []
    for ch, g in zip(chars, glyphs):
        if g not in glyph_reading or ch not in readings:
            out.append(None)
            continue
        _, suffix = glyph_reading[g]
        rs, default = readings[ch]
        out.append(default if suffix == "vd" else rs[int(suffix[1:])])
    return out


if __name__ == "__main__":
    text = " ".join(sys.argv[1:]) or "我們去銀行，他長大了，目的確實達成。"
    for ch, r in zip([c for c in text], readings_of(text)):
        print(ch, r or "")
