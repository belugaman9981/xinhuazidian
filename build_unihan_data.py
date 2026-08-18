"""
build_unihan_data.py

Builds a full radical + stroke-count Chinese character index (检字表)
straight from Unicode's own Unihan database — no third-party GitHub
dataset involved.

Requirements:
    pip install unihan-etl

Usage:
    python build_unihan_data.py

Output:
    jianzi_data.json  — one entry per character:
        {
          "word": "你",
          "radical": 9,          # Kangxi radical number, 1-214
          "residual_strokes": 5, # strokes beyond the radical
          "total_strokes": 7,
          "pinyin": "ni3",
          "definition": "you"
        }

This will take a minute or two the first time — it downloads the
Unihan.zip release directly from unicode.org.
"""

import gzip
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path
from unihan_etl.core import Packager

CEDICT_URL = "https://www.mdbg.net/chinese/export/cedict/cedict_1_0_ts_utf-8_mdbg.txt.gz"
CEDICT_CACHE = Path(__file__).with_name("data") / "cedict_cache.txt.gz"


def load_cedict_definitions():
    """Download CC-CEDICT once and return a single-character -> English definition map."""
    if not CEDICT_CACHE.exists():
        print("Downloading CC-CEDICT…")
        urllib.request.urlretrieve(CEDICT_URL, CEDICT_CACHE)
        print("Done.")

    defs = {}
    entry_re = re.compile(r"^(\S+)\s+(\S+)\s+\[([^\]]+)\]\s+/(.+)/$")
    with gzip.open(CEDICT_CACHE, "rt", encoding="utf-8") as f:
        for line in f:
            if line.startswith("#"):
                continue
            m = entry_re.match(line.rstrip())
            if not m:
                continue
            trad, simp, _pinyin, raw_defs = m.groups()
            # Only single-character entries; store by both forms
            if len(trad) == 1:
                definition = raw_defs.replace("/", "; ")
                defs.setdefault(trad, definition)
            if len(simp) == 1:
                defs.setdefault(simp, raw_defs.replace("/", "; "))
    return defs

# Kangxi radical glyphs, indexed 1-214, for reference/display.
# (Not required for the data build itself — just handy if you want
# to print radical characters instead of bare numbers.)
KANGXI_RADICALS = [
    "一","丨","丶","丿","乙","亅","二","亠","人","儿","入","八","冂","冖","冫",
    "几","凵","刀","力","勹","匕","匚","匸","十","卜","卩","厂","厶","又","口",
    # ... (truncated for brevity — full table of 214 is easy to find and paste in
    # if you want radical glyphs rather than just numbers; the numbers alone
    # are enough to group and sort characters correctly.)
]


def parse_kRSUnicode(value):
    """
    kRSUnicode looks like '9.5' (radical 9, 5 residual strokes) and can list
    multiple candidates separated by spaces, e.g. '85.6 85.7'. We take the
    first (primary) one.
    """
    if not value:
        return None, None
    first = value.split(" ")[0]
    first = first.lstrip("'")  # some entries mark simplified variants with a leading '
    match = re.match(r"(\d+)\.(\d+)", first)
    if not match:
        return None, None
    return int(match.group(1)), int(match.group(2))


WIKTIONARY_CACHE = Path(__file__).with_name("data") / "wiktionary_cache.json"


def fetch_wiktionary_definitions(chars):
    """Fetch Wiktionary summaries for chars not yet covered, with local cache."""
    cache = {}
    if WIKTIONARY_CACHE.exists():
        with WIKTIONARY_CACHE.open(encoding="utf-8") as f:
            cache = json.load(f)

    to_fetch = [ch for ch in chars if ch not in cache]
    if to_fetch:
        print(f"Fetching {len(to_fetch)} definitions from Wiktionary (cached: {len(cache)})…")
        for i, ch in enumerate(to_fetch, 1):
            url = "https://en.wiktionary.org/api/rest_v1/page/summary/" + urllib.parse.quote(ch, safe="")
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "xinhuazidian-builder/1.0"})
                with urllib.request.urlopen(req, timeout=8) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    extract = data.get("extract", "").strip()
                    cache[ch] = extract if len(extract) > 10 else None
            except Exception:
                cache[ch] = None
            if i % 200 == 0:
                print(f"  {i}/{len(to_fetch)}…")
            time.sleep(0.15)

        with WIKTIONARY_CACHE.open("w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False)
        print(f"Done ({len(to_fetch)} fetched).")

    return {k: v for k, v in cache.items() if v}


def load_legacy_definitions():
    """Load the richer local definitions for characters missing Unihan text."""
    path = Path(__file__).with_name("data") / "word.json"
    if not path.exists():
        return {}

    with path.open(encoding="utf-8") as f:
        records = json.load(f)
    definitions = {
        record["word"]: record["explanation"]
        for record in records
        if record.get("word") and record.get("explanation")
    }
    definitions["並"] = definitions.get("并", "")
    return definitions


def main():
    legacy_definitions = load_legacy_definitions()
    cedict_definitions = load_cedict_definitions()
    # hardcoded field->file lookup table (see long comment below) to decide which of the 8 Unihan
    # data files to load when you restrict "fields" — and that table is
    # stale: it still thinks kRSUnicode lives in Unihan_RadicalStrokeCounts.txt,
    # but Unicode moved it (along with kTotalStrokes) into Unihan_IRGSources.txt
    # some releases ago. Restricting "fields" makes it skip that file
    # entirely and silently produce zero radical/stroke matches.
    #
    # Leaving both "fields" and "input_files" at their defaults makes it
    # load all 8 real data files, so kRSUnicode gets found no matter which
    # file Unicode currently keeps it in. We just pick the fields we want
    # back out of the full record below.
    packager = Packager({
        # Newer unihan-etl only returns the parsed records in-memory when
        # format is "python" — "json"/"csv"/"yaml" write straight to a file
        # on disk instead and export() returns None.
        "format": "python",
    })
    packager.download()
    records = packager.export()
    if not records:
        raise SystemExit(
            "unihan-etl returned no records — check that the Unihan.zip "
            "download completed (see the cache dir printed above)."
        )

    out = []
    for rec in records:
        char = rec.get("char")
        if not char:
            continue

        # kRSUnicode, expanded, is a list of dicts:
        #   [{"radical": 9, "strokes": 5, "simplified": False}, ...]
        # (older unihan-etl versions gave a raw "9.5" string instead — the
        # isinstance check below handles both just in case).
        rs_entries = rec.get("kRSUnicode")
        if not rs_entries:
            continue
        first_rs = rs_entries[0] if isinstance(rs_entries, list) else rs_entries

        if isinstance(first_rs, dict):
            radical = first_rs.get("radical")
            residual = first_rs.get("strokes")
        elif isinstance(first_rs, str):
            radical, residual = parse_kRSUnicode(first_rs)
        else:
            continue

        if radical is None:
            continue  # skip entries with no radical/stroke data (rare, mostly obscure symbols)

        # kTotalStrokes, expanded, is {"zh-Hans": int, "zh-Hant": int}
        # (older versions gave a plain list instead).
        total_strokes = rec.get("kTotalStrokes")
        if isinstance(total_strokes, dict):
            total_strokes = total_strokes.get("zh-Hans") or total_strokes.get("zh-Hant")
        elif isinstance(total_strokes, list):
            total_strokes = total_strokes[0] if total_strokes else None

        pinyin = rec.get("kMandarin")
        if isinstance(pinyin, dict):
            pinyin = pinyin.get("zh-Hans") or pinyin.get("zh-Hant")
        elif isinstance(pinyin, list):
            pinyin = pinyin[0] if pinyin else None

        definition = rec.get("kDefinition")
        if isinstance(definition, list):
            definition = "; ".join(definition)
        if not definition:
            definition = legacy_definitions.get(char) or cedict_definitions.get(char)

        out.append({
            "word": char,
            "radical": radical,
            "residual_strokes": residual,
            "total_strokes": total_strokes,
            "pinyin": pinyin,
            "definition": definition,
            "chinese_definition": legacy_definitions.get(char),
        })

    # Wiktionary pass for characters still without any definition
    # Skip CJK Ext-B/C/D/E/F/G (U+20000+) — these won't have Wiktionary pages
    still_missing = sorted(
        e["word"] for e in out
        if not (e.get("chinese_definition") or e.get("definition"))
        and ord(e["word"]) < 0x20000
    )
    if still_missing:
        wiki_defs = fetch_wiktionary_definitions(still_missing)
        for e in out:
            if not (e.get("chinese_definition") or e.get("definition")):
                e["definition"] = wiki_defs.get(e["word"])

    out.sort(key=lambda e: (
        e["radical"],
        e["residual_strokes"] if e["residual_strokes"] is not None else 0,
        e["word"],
    ))

    with open("jianzi_data.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"Wrote {len(out)} characters to jianzi_data.json")


if __name__ == "__main__":
    main()