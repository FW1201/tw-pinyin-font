"""公開讀音規則編譯：審訂表 + 全字庫 + 自建資料 → rules/compiled/（不使用任何大陸審音資料）。

讀音來源與優先序（IVS 序號也依此排列，E01E0 = 第 1 個讀音）：
    1. 《國語一字多音審訂表》1999 年公告版（sources/rules/upstream/shendingbiao_1999.csv）
    2. 《國語一字多音審訂表》2012 年初稿追加的讀音（shendingbiao_2012.csv）
    3. 全字庫 CNS11643 字音（只補審訂表未收的字；upstream/cns11643/）
    4. 自建補充讀音（sources/rules/custom/char_readings.tsv）
    5. 自建詞表中出現的讀音（sources/rules/custom/words.tsv）

預設讀音：custom/default_overrides.tsv > 審訂表 1999 第一讀音 > 審訂表 2012 第一讀音 > 全字庫第一個非輕聲讀音。

輸出：
    sources/rules/compiled/chars.tsv   字、預設讀音、讀音清單（IVS 序）
    sources/rules/compiled/rules.tsv   rclt 詞規則（長詞優先），含阻擋用的長詞
    sources/rules/compiled/report.txt  統計與警告
"""

from __future__ import annotations

import csv
import re
import sys
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pinyin import numbered_to_marked, zhuyin_to_pinyin  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
RULES = ROOT / "sources" / "rules"
PINYIN_RE = re.compile(r"[a-zêǜ-̌]+")


def nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s.strip())


def normalize_reading(s: str) -> str:
    """接受 zhuāng 或 zhuang1 兩種寫法。"""
    s = nfc(s).lower()
    if re.fullmatch(r"[a-zêüv]+[1-5]", s):
        return numbered_to_marked(s)
    return s


def strip_tone(s: str) -> str:
    return unicodedata.normalize("NFC", "".join(c for c in unicodedata.normalize("NFD", s) if c not in "\u0300\u0301\u030C\u0304"))


def is_han(ch: str) -> bool:
    return ch == "〇" or unicodedata.name(ch, "").startswith("CJK")


def read_tsv(path: Path):
    if not path.exists():
        return
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = line.split("#", 1)[0].rstrip()
        if line.strip():
            yield lineno, [c.strip() for c in line.split("\t")]


def load_shendingbiao(path: Path, warnings: list[str]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    with path.open(encoding="utf-8-sig") as f:
        for row in csv.reader(f):
            if not row or not row[0].strip().isdigit():
                continue
            ch = row[1].strip()
            if len(ch) != 1:  # 以組字方式表示、Unicode 未收的字
                warnings.append(f"{path.name}: 略過非單一字元「{ch}」")
                continue
            readings: list[str] = []
            for zy in row[2:]:
                zy = zy.strip().replace("‧", "˙").replace("・", "˙")
                if not zy:
                    continue
                try:
                    py = zhuyin_to_pinyin(zy)
                except ValueError as e:
                    warnings.append(f"{path.name}: {ch} {e}")
                    continue
                if py not in readings:
                    readings.append(py)
            if readings:
                out[ch] = readings
    return out


def load_cns(folder: Path, warnings: list[str]) -> dict[str, list[str]]:
    """全字庫注音屬性：CNS 字碼 → Unicode → 拼音。檔案內讀音依注音排序，不代表常用度。"""
    to_uni: dict[str, str] = {}
    for path in sorted(folder.glob("CNS2UNICODE_*.txt")):
        for line in path.read_text(encoding="utf-8-sig").splitlines():
            parts = line.split("\t")
            if len(parts) >= 2 and int(parts[1], 16) < 0xF0000:  # 略過私用區（全字庫自造字）
                to_uni[parts[0]] = chr(int(parts[1], 16))
    out: dict[str, list[str]] = {}
    for line in (folder / "CNS_phonetic.txt").read_text(encoding="utf-8-sig").splitlines():
        code, _, zy = line.partition("\t")
        ch = to_uni.get(code)
        if not ch or not zy:
            continue
        try:
            py = zhuyin_to_pinyin(zy)
        except ValueError as e:
            warnings.append(f"CNS_phonetic: {ch} {e}")
            continue
        lst = out.setdefault(ch, [])
        if py not in lst:
            lst.append(py)
    return out


@dataclass
class Rules:
    readings: dict[str, list[str]] = field(default_factory=dict)
    defaults: dict[str, str] = field(default_factory=dict)
    words: dict[str, list[str]] = field(default_factory=dict)
    rules: list[str] = field(default_factory=list)
    intentional: set[str] = field(default_factory=set)
    warnings: list[str] = field(default_factory=list)

    def reading_index(self, ch: str, reading: str) -> int:
        return self.readings[ch].index(reading)


def compile_rules() -> Rules:
    r = Rules()
    w = r.warnings
    sd1999 = load_shendingbiao(RULES / "upstream/shendingbiao_1999.csv", w)
    sd2012 = load_shendingbiao(RULES / "upstream/shendingbiao_2012.csv", w)
    cns = load_cns(RULES / "upstream/cns11643", w)

    def add(ch: str, reading: str) -> None:
        lst = r.readings.setdefault(ch, [])
        if reading not in lst:
            lst.append(reading)

    for src in (sd1999, sd2012):
        for ch, lst in src.items():
            for py in lst:
                add(ch, py)
    # 全字庫只用來補審訂表沒收的字（審訂表已刪去的舊讀音不再加回來）
    for ch, lst in cns.items():
        if ch not in r.readings:
            for py in lst:
                add(ch, py)

    # 自建補充／修正讀音：「字<TAB>讀音|讀音」追加；「字<TAB>=讀音|讀音」整組取代
    for lineno, cols in read_tsv(RULES / "custom/char_readings.tsv"):
        ch, spec = cols[0], cols[1]
        if spec.startswith("="):
            r.readings[ch] = [normalize_reading(x) for x in spec[1:].split("|")]
        else:
            for x in spec.split("|"):
                add(ch, normalize_reading(x))

    # 自建詞表（預設讀音需先決定，簡寫格式「銀行<TAB>行=háng」要用預設值補齊其他字）
    overrides = {}
    for lineno, cols in read_tsv(RULES / "custom/default_overrides.tsv"):
        overrides[cols[0]] = normalize_reading(cols[1])

    def default_of(ch: str) -> str:
        if ch in overrides:
            return overrides[ch]
        for src in (sd1999, sd2012):
            if ch in src:
                return src[ch][0]
        lst = r.readings.get(ch, [])
        return next((p for p in lst if not p.isascii() or p == "r"), lst[0] if lst else "")

    for lineno, cols in read_tsv(RULES / "custom/words.tsv"):
        word, spec = cols[0], cols[1] if len(cols) > 1 else ""
        if any(not is_han(c) for c in word):
            w.append(f"words.tsv:{lineno}: {word} 含非漢字")
            continue
        tokens = spec.split()
        if "!" in tokens:
            tokens.remove("!")
            r.intentional.add(word)
        if tokens and all("=" in t for t in tokens):
            sy = [default_of(c) for c in word]
            ok = True
            for t in tokens:
                key, val = t.split("=", 1)
                idx = int(key) - 1 if key.isdigit() else word.find(key)
                if not key.isdigit() and word.count(key) > 1:
                    w.append(f"words.tsv:{lineno}: {word} 的「{key}」出現不只一次，請改用位置編號")
                if not 0 <= idx < len(word):
                    w.append(f"words.tsv:{lineno}: {word} 找不到「{key}」")
                    ok = False
                    break
                sy[idx] = normalize_reading(val)
            if not ok:
                continue
        else:
            sy = [normalize_reading(t) for t in tokens]
            if len(sy) != len(word):
                w.append(f"words.tsv:{lineno}: {word} 字數與音節數不符（{spec}）")
                continue
        if "" in sy:
            w.append(f"words.tsv:{lineno}: {word} 有字沒有讀音資料")
            continue
        if word in r.words and r.words[word] != sy:
            w.append(f"words.tsv:{lineno}: {word} 重複且讀音不同（{' '.join(r.words[word])} / {' '.join(sy)}）")
            continue
        for ch, s in zip(word, sy):
            if s not in r.readings.get(ch, []):
                # 輕聲變體（媽 mā → ma）或兒化 r 是預期的，不警告
                toneless = {strip_tone(x) for x in r.readings.get(ch, [])}
                if not (s == strip_tone(s) and (s in toneless or s == "r")):
                    w.append(f"words.tsv:{lineno}: {word} 的「{ch}」讀音 {s} 不在來源清單，已追加")
                add(ch, s)
        r.words[word] = sy

    # 預設讀音
    for ch, lst in r.readings.items():
        d = default_of(ch)
        if d not in lst:
            w.append(f"default_overrides: {ch} 的 {d} 不在讀音清單，已追加")
            lst.append(d)
        r.defaults[ch] = d

    # 檢查：長詞包含「有特殊讀音的短詞」，但長詞在那些位置卻用了預設讀音 → 多半是漏標
    for wd, sy in r.words.items():
        if wd in r.intentional:
            continue
        for n in range(2, len(wd)):
            for i in range(len(wd) - n + 1):
                sub = wd[i : i + n]
                if sub == wd or sub not in r.words:
                    continue
                for j, (c, s_sub) in enumerate(zip(sub, r.words[sub])):
                    if s_sub != r.defaults[c] and sy[i + j] == r.defaults[c]:
                        w.append(f"words.tsv: {wd} 可能漏標「{c}」（短詞 {sub} 讀 {s_sub}，{wd} 用預設 {sy[i + j]}）")

    # rclt 規則：與預設讀音不同的詞，加上「包含它但讀音衝突」的長詞當阻擋
    deviating = {wd for wd, sy in r.words.items() if any(r.defaults[c] != s for c, s in zip(wd, sy))}
    blockers = set()
    for wd, sy in r.words.items():
        if wd in deviating:
            continue
        for n in range(2, len(wd)):
            for i in range(len(wd) - n + 1):
                sub = wd[i : i + n]
                if sub in deviating and r.words[sub] != sy[i : i + n]:
                    blockers.add(wd)
    r.rules = sorted(deviating | blockers, key=lambda x: (-len(x), x))
    return r


def write(r: Rules) -> None:
    out = RULES / "compiled"
    out.mkdir(exist_ok=True)
    with (out / "chars.tsv").open("w", encoding="utf-8") as f:
        f.write("# char\tcodepoint\tdefault\treadings (IVS order: E01E0, E01E1, ...)\n")
        for ch in sorted(r.readings, key=ord):
            f.write(f"{ch}\tU+{ord(ch):04X}\t{r.defaults[ch]}\t{'|'.join(r.readings[ch])}\n")
    with (out / "rules.tsv").open("w", encoding="utf-8") as f:
        f.write("# word\tpinyin — rclt 規則，長詞優先\n")
        for wd in r.rules:
            f.write(f"{wd}\t{' '.join(r.words[wd])}\n")
    with (out / "words_full.tsv").open("w", encoding="utf-8") as f:
        f.write("# word\tpinyin — 自建詞表展開後的完整讀音\n")
        for wd, sy in r.words.items():
            f.write(f"{wd}\t{' '.join(sy)}\n")
    poly = sum(1 for l in r.readings.values() if len(l) > 1)
    report = [
        f"chars={len(r.readings)} polyphonic={poly}",
        f"custom words={len(r.words)} rclt rules={len(r.rules)}",
        f"warnings={len(r.warnings)}",
        *r.warnings,
    ]
    (out / "report.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
    print("\n".join(report[:3]))
    for line in r.warnings[:30]:
        print("  " + line)


if __name__ == "__main__":
    write(compile_rules())
