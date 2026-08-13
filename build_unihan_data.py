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

import json
import re
from unihan_etl.core import Packager

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


def main():
    packager = Packager({
        "fields": [
            "kRSUnicode",
            "kTotalStrokes",
            "kMandarin",
            "kDefinition",
        ],
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

        radical, residual = parse_kRSUnicode(
            rec.get("kRSUnicode", [None])[0] if isinstance(rec.get("kRSUnicode"), list) else rec.get("kRSUnicode")
        )
        if radical is None:
            continue  # skip entries with no radical/stroke data (rare, mostly obscure symbols)

        total_strokes = rec.get("kTotalStrokes")
        if isinstance(total_strokes, list):
            total_strokes = total_strokes[0] if total_strokes else None

        pinyin = rec.get("kMandarin")
        if isinstance(pinyin, dict):
            pinyin = pinyin.get("zh-Hans") or pinyin.get("zh-Hant")
        elif isinstance(pinyin, list):
            pinyin = pinyin[0] if pinyin else None

        definition = rec.get("kDefinition")
        if isinstance(definition, list):
            definition = "; ".join(definition)

        out.append({
            "word": char,
            "radical": radical,
            "residual_strokes": residual,
            "total_strokes": total_strokes,
            "pinyin": pinyin,
            "definition": definition,
        })

    out.sort(key=lambda e: (e["radical"], e["residual_strokes"] or 0))

    with open("jianzi_data.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"Wrote {len(out)} characters to jianzi_data.json")


if __name__ == "__main__":
    main()