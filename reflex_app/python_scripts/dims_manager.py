import os
import csv
import datetime
import collections
import unicodedata as ud
from pathlib import Path
from typing import Dict, List, Optional

DOMAINS = [
    "job_titles",
    "qualifications",
    "education_levels",
    "fields",
    "workstyle",
]


def _norm(s: Optional[str]) -> str:
    if s is None:
        return ""
    return ud.normalize("NFKC", str(s)).replace("\u3000", " ").strip()


def _load_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _append_rows(path: Path, fieldnames: List[str], rows: List[Dict[str, str]]):
    path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not path.exists()
    with path.open("a", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        if write_header:
            w.writeheader()
        for r in rows:
            w.writerow(r)


class DimsManager:
    """辞書ロード・未マッチ収集・昇格（overlay）管理。

    base と overlay をマージして使用し、未マッチは pending へ書き出す。
    auto_promote を有効にすれば、一定回数以上の未マッチを overlay に昇格する。
    """

    def __init__(self, dims_dir: str, min_promote_count: int = 3, auto_promote: bool = False):
        self.dims_dir = Path(dims_dir)
        self.min_promote = int(os.getenv("DIMS_MIN_PROMOTE", min_promote_count))
        self.auto_promote = bool(int(os.getenv("DIMS_AUTO_PROMOTE", int(auto_promote))))
        self.maps: Dict[str, Dict[str, Dict[str, str]]] = {}
        self.unmatched: Dict[str, collections.Counter] = {d: collections.Counter() for d in DOMAINS}

        for d in DOMAINS:
            base = self.dims_dir / "base" / f"{d}.csv"
            over = self.dims_dir / "overlay" / f"{d}_overlay.csv"
            rows = _load_csv(base) + _load_csv(over)
            self.maps[d] = self._build_map(rows)

    def _build_map(self, rows: List[Dict[str, str]]):
        canon: Dict[str, Dict[str, str]] = {}
        syn: Dict[str, str] = {}
        for r in rows:
            c = _norm(r.get("canonical"))
            if not c:
                continue
            canon[c] = r
            # synonyms は '|' 区切り
            for s in _norm(r.get("synonyms", "")).split("|"):
                s = _norm(s)
                if s:
                    syn[s] = c
            # display も同義語として拾う
            disp = _norm(r.get("display"))
            if disp:
                syn[disp] = c
        return {"canon": canon, "syn": syn}

    def match(self, domain: str, token: str) -> Optional[str]:
        t = _norm(token)
        if not t:
            return None
        m = self.maps.get(domain, {})
        if t in m.get("canon", {}):
            return t
        if t in m.get("syn", {}):
            return m["syn"][t]
        # 未マッチ収集
        if domain in self.unmatched:
            self.unmatched[domain][t] += 1
        return None

    def flush(self):
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        # 1) 未マッチを pending に吐き出し
        for d, cnt in self.unmatched.items():
            if not cnt:
                continue
            pending = self.dims_dir / "pending" / f"{d}_pending_{ts}.csv"
            rows = [{"token": k, "count": str(v)} for k, v in cnt.most_common()]
            _append_rows(pending, ["token", "count"], rows)

        # 2) 自動昇格
        if self.auto_promote:
            fieldnames = ["canonical", "display", "family", "national", "synonyms"]
            for d, cnt in self.unmatched.items():
                promote = []
                for token, n in cnt.items():
                    if n >= self.min_promote:
                        canonical = _norm(token).replace(" ", "_")
                        promote.append({
                            "canonical": canonical,
                            "display": token,
                            "family": "",
                            "national": "",
                            "synonyms": token,
                        })
                if promote:
                    overlay = self.dims_dir / "overlay" / f"{d}_overlay.csv"
                    _append_rows(overlay, fieldnames, promote)

