"""字型回歸測試：pytest tests/（需先 build/compile_rules.py 與 build/build_font.py）。"""

from __future__ import annotations

import random
import sys
import unicodedata
from pathlib import Path

import pytest
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "build"))
from shaping import DEFAULT_FONT, readings_of  # noqa: E402
from simulate import Simulator  # noqa: E402

pytestmark = pytest.mark.skipif(not DEFAULT_FONT.exists(), reason="先執行 build/build_font.py")
SIM = Simulator()


def golden_cases():
    for line in (ROOT / "tests/golden_sentences.tsv").read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.startswith("#"):
            sentence, spec = line.split("\t")
            checks = []
            for tok in spec.split():
                key, want = tok.split("=")
                pos = int(key) - 1 if key.isdigit() else sentence.index(key)
                checks.append((pos, unicodedata.normalize("NFC", want)))
            yield pytest.param(sentence, checks, id=sentence)


@pytest.mark.parametrize("sentence,checks", list(golden_cases()))
def test_golden_sentences(sentence, checks):
    got = readings_of(sentence)
    for pos, want in checks:
        assert got[pos] == want, f"{sentence}：第 {pos + 1} 字「{sentence[pos]}」顯示 {got[pos]}，應為 {want}"


def test_font_matches_simulator_on_rule_words():
    """字型 GSUB 必須與 Python 模擬（長詞優先）逐字一致。"""
    mismatches = [w for w in SIM.rules if readings_of(w) != SIM.readings(w)]
    assert not mismatches, f"{len(mismatches)} 個詞不一致，例如 {mismatches[:10]}"


def test_font_matches_simulator_on_random_text():
    rng = random.Random(1234)
    words = list(SIM.rules)
    commons = "的了是我你他在有人這中大來上個們到說和地也子時道出而要於就下得可以"
    for _ in range(300):
        text = "".join(rng.choice([rng.choice(words), rng.choice(commons)]) for _ in range(rng.randint(3, 10)))
        assert readings_of(text) == SIM.readings(text), text


def test_ivs_selects_each_reading():
    for ch in "行長的著樂重":
        readings = SIM.chars[ch][0]
        for i, want in enumerate(readings):
            assert readings_of(ch + chr(0xE01E0 + i)) == [want], (ch, i)


def test_ivs_overrides_word_rule():
    # 「銀行」預設讀 háng；在「行」後加 E01E0（xíng）要蓋過詞規則
    assert readings_of("銀行\U000E01E0") == ["yín", "xíng"]
    assert readings_of("銀行") == ["yín", "háng"]


def test_rclt_off_falls_back_to_defaults():
    assert readings_of("銀行", features={"rclt": False, "calt": False}) == ["yín", "xíng"]


def test_font_tables():
    font = TTFont(DEFAULT_FONT)
    assert "glyf" in font and "CFF " not in font, "Office 只能內嵌 TrueType 輪廓"
    assert font["OS/2"].fsType == 0
    assert len(font.getGlyphOrder()) <= 65535
    os2, hhea = font["OS/2"], font["hhea"]
    assert (os2.sTypoAscender, os2.sTypoDescender) == (880, -120), "Google Fonts CJK 規範"
    assert not os2.fsSelection & (1 << 7), "USE_TYPO_METRICS 必須關閉"
    assert hhea.ascent == os2.usWinAscent and -hhea.descent == os2.usWinDescent
    top = max(getattr(font["glyf"][g], "yMax", 0) for g in font.getGlyphOrder())
    assert hhea.ascent >= top, "行高必須涵蓋拼音最高點"
    glyf = font["glyf"]
    nested = [g for g in font.getGlyphOrder() if glyf[g].isComposite()
              and any(glyf[c.glyphName].isComposite() for c in glyf[g].components)]
    assert not nested, f"巢狀元件：{nested[:5]}"
    names = {n.nameID: n.toUnicode() for n in font["name"].names if n.langID == 0x409}
    assert names[1] == "Taiwan Pinyin Kai" and "Open Font License" in names[13]
    zh = {n.toUnicode() for n in font["name"].names if n.nameID == 1 and n.langID == 0x404}
    assert zh == {"臺灣拼音楷"}


def test_no_mainland_reading_sources():
    upstream = ROOT / "sources/rules/upstream"
    assert not list(upstream.rglob("*nihan*")), "不得使用 Unihan kMandarin（大陸讀音）"
