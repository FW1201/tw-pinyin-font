"""漢語拼音工具：注音 → 拼音、聲調符號 ↔ 數字、glyph 命名。"""

from __future__ import annotations

import re
import unicodedata

TONE_MARKS = {"̄": 1, "́": 2, "̌": 3, "̀": 4}
MARK_FOR_TONE = {v: k for k, v in TONE_MARKS.items()}

INITIALS = {
    "ㄅ": "b", "ㄆ": "p", "ㄇ": "m", "ㄈ": "f", "ㄉ": "d", "ㄊ": "t", "ㄋ": "n", "ㄌ": "l",
    "ㄍ": "g", "ㄎ": "k", "ㄏ": "h", "ㄐ": "j", "ㄑ": "q", "ㄒ": "x",
    "ㄓ": "zh", "ㄔ": "ch", "ㄕ": "sh", "ㄖ": "r", "ㄗ": "z", "ㄘ": "c", "ㄙ": "s",
}
# 韻母（有聲母時的寫法）
FINALS = {
    "": "", "ㄚ": "a", "ㄛ": "o", "ㄜ": "e", "ㄝ": "ê", "ㄞ": "ai", "ㄟ": "ei", "ㄠ": "ao", "ㄡ": "ou",
    "ㄢ": "an", "ㄣ": "en", "ㄤ": "ang", "ㄥ": "eng", "ㄦ": "er",
    "ㄧ": "i", "ㄧㄚ": "ia", "ㄧㄛ": "io", "ㄧㄝ": "ie", "ㄧㄞ": "iai", "ㄧㄠ": "iao", "ㄧㄡ": "iu",
    "ㄧㄢ": "ian", "ㄧㄣ": "in", "ㄧㄤ": "iang", "ㄧㄥ": "ing",
    "ㄨ": "u", "ㄨㄚ": "ua", "ㄨㄛ": "uo", "ㄨㄞ": "uai", "ㄨㄟ": "ui", "ㄨㄢ": "uan", "ㄨㄣ": "un",
    "ㄨㄤ": "uang", "ㄨㄥ": "ong",
    "ㄩ": "ü", "ㄩㄝ": "üe", "ㄩㄢ": "üan", "ㄩㄣ": "ün", "ㄩㄥ": "iong",
}
# 零聲母時的寫法
ZERO_INITIAL = {
    "ㄧ": "yi", "ㄧㄚ": "ya", "ㄧㄛ": "yo", "ㄧㄝ": "ye", "ㄧㄞ": "yai", "ㄧㄠ": "yao", "ㄧㄡ": "you",
    "ㄧㄢ": "yan", "ㄧㄣ": "yin", "ㄧㄤ": "yang", "ㄧㄥ": "ying",
    "ㄨ": "wu", "ㄨㄚ": "wa", "ㄨㄛ": "wo", "ㄨㄞ": "wai", "ㄨㄟ": "wei", "ㄨㄢ": "wan", "ㄨㄣ": "wen",
    "ㄨㄤ": "wang", "ㄨㄥ": "weng",
    "ㄩ": "yu", "ㄩㄝ": "yue", "ㄩㄢ": "yuan", "ㄩㄣ": "yun", "ㄩㄥ": "yong",
}
ZHUYIN_TONES = {"ˊ": 2, "ˇ": 3, "ˋ": 4, "˙": 5}


def zhuyin_to_pinyin(zy: str) -> str:
    """ㄏㄤˊ → háng；˙ㄉㄜ → de。無法轉換時丟出 ValueError。"""
    s = zy.strip().replace("丨", "ㄧ").replace("一", "ㄧ").replace(" ", "").replace("　", "")
    tone = 1
    for mark, t in ZHUYIN_TONES.items():
        if mark in s:
            tone = t
            s = s.replace(mark, "")
    initial = ""
    if s and s[0] in INITIALS:
        initial, s = INITIALS[s[0]], s[1:]
    if not initial:
        if s in ZERO_INITIAL:
            base = ZERO_INITIAL[s]
        elif s in FINALS:
            base = FINALS[s]
        else:
            raise ValueError(f"unknown zhuyin: {zy!r}")
    else:
        if s == "":
            base = initial + ("i" if initial in ("zh", "ch", "sh", "r", "z", "c", "s") else "")
            if base == initial:
                raise ValueError(f"initial without final: {zy!r}")
        elif s not in FINALS:
            raise ValueError(f"unknown final in {zy!r}")
        else:
            final = FINALS[s]
            if initial in ("j", "q", "x") and final.startswith("ü"):
                final = "u" + final[1:]
            base = initial + final
    return numbered_to_marked(base.replace("ü", "v") + str(tone))


def _mark_vowel_index(syl: str) -> int:
    """依拼音標調規則找出要加聲調符號的母音位置。"""
    for v in ("a", "e"):
        if v in syl:
            return syl.index(v)
    if "ou" in syl:
        return syl.index("o")
    for i in range(len(syl) - 1, -1, -1):
        if syl[i] in "iouüv":
            return i
    for i in range(len(syl) - 1, -1, -1):  # m̄、ń、ňg 等成音節鼻音
        if syl[i] in "mn":
            return i
    return -1


def numbered_to_marked(num: str) -> str:
    """zhuang1 → zhuāng；lv4 → lǜ；de5 → de。"""
    m = re.fullmatch(r"([a-zêü]+)([1-5])", num)
    if not m:
        raise ValueError(num)
    syl, tone = m.group(1).replace("v", "ü"), int(m.group(2))
    if tone == 5:
        return syl
    i = _mark_vowel_index(syl)
    return unicodedata.normalize("NFC", syl[: i + 1] + MARK_FOR_TONE[tone] + syl[i + 1 :])


def marked_to_numbered(marked: str) -> str:
    """zhuāng → zhuang1；lǜ → lv4；de → de5。"""
    tone = 5
    out = []
    for ch in unicodedata.normalize("NFD", marked.lower()):
        if ch in TONE_MARKS:
            tone = TONE_MARKS[ch]
        elif ch == "̈":  # ü 的分音符
            out[-1] = "v"
        elif ch == "̂":  # ê
            out[-1] = "ê"
        else:
            out.append(ch)
    return "".join(out) + str(tone)


def glyph_suffix(marked: str) -> str:
    """glyph 名稱用的 ASCII 音節：zhuāng → zhuang1；ê̄ → eh1。"""
    return marked_to_numbered(marked).replace("ê", "eh")
