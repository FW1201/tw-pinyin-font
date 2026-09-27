"""以 Python 模擬字型的 rclt 行為（正向最長詞比對），供測試與校正器對照。"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COMPILED = ROOT / "sources/rules/compiled"


def _tsv(path: Path):
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.startswith("#"):
            yield line.split("\t")


class Simulator:
    def __init__(self, compiled: Path = COMPILED):
        self.chars = {c: (rs.split("|"), d) for c, _, d, rs in _tsv(compiled / "chars.tsv")}
        self.rules = {w: py.split() for w, py in _tsv(compiled / "rules.tsv")}
        self.max_len = max((len(w) for w in self.rules), default=1)

    def readings(self, text: str) -> list[str | None]:
        """每個字的讀音；IVS（U+E01E0 起）指定的讀音優先，且不參與詞比對。"""
        base, forced = [], {}
        for ch in text:
            if 0xE01E0 <= ord(ch) <= 0xE01EF and base:
                forced[len(base) - 1] = ord(ch) - 0xE01E0
            else:
                base.append(ch)
        out: list[str | None] = []
        i = 0
        while i < len(base):
            for n in range(min(self.max_len, len(base) - i), 1, -1):
                w = "".join(base[i : i + n])
                if w in self.rules:
                    out.extend(self.rules[w])
                    i += n
                    break
            else:
                c = base[i]
                out.append(self.chars[c][1] if c in self.chars else None)
                i += 1
        for pos, n in forced.items():
            rs = self.chars.get(base[pos], ([], None))[0]
            if n < len(rs):
                out[pos] = rs[n]
        return out
