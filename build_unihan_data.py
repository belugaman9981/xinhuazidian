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

Every character in the output is guaranteed to have a real definition.
Unicode's kDefinition only covers a fraction of all Han characters, so
after the Unihan build this script fills the gaps from two optional local
dictionaries (in priority order):

    1. data/word.json        — Chinese-language glosses
    2. data/cedict_cache.txt.gz — CC-CEDICT English glosses

Characters that still have no definition in any source (extremely rare
historical/variant forms) are pruned from the output entirely, so the
dictionary never shows a bare "(no definition)" headword.

This will take a minute or two the first time — it downloads the
Unihan.zip release directly from unicode.org.
"""

import json
import os
import re
from unihan_etl.core import Packager

# Optional Chinese-language dictionary used to fill in a real definition
# for characters that Unicode's kDefinition doesn't cover. If this file
# isn't present, the build still works — it just leaves those characters
# without a definition (see merge_chinese_definitions below).
WORD_JSON_PATH = "data/word.json"

# Optional CC-CEDICT cache (a free Chinese-English dictionary) used as a
# second fallback for characters that neither Unihan nor word.json gloss.
# Same format as the official CC-CEDICT release.
CEDICT_PATH = "data/cedict_cache.txt.gz"

# Characters whose only "definition" is a bare pinyin or a self-referential
# pointer (e.g. "亐yú1.古同\"于\"。") are still real dictionary entries, so we
# keep them — but we strip the leading headword+pinyin noise so the gloss
# reads cleanly.
MAX_DEF_LENGTH = 80
PINYIN_CHARS = "a-zA-ZāáǎàēéěèīíǐìōóǒòūúǔùǖǘǚǜÜüńň"

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


def clean_explanation(raw, word):
    """
    word.json's "explanation" field is long, unstructured dictionary-entry
    text — multiple readings, example sentences with classical-Chinese
    citations, etc. For a 检字表-style gloss we just want a short, useful
    snippet, not the whole entry. Take the first substantive line and
    trim it to a sane length.
    """
    if not raw:
        return None
    for line in raw.split("\n"):
        line = line.strip()
        if not line:
            continue
        # word.json often repeats the headword as the start of a "line"
        # with nothing else useful — sometimes bare ("嗄"), sometimes
        # glued straight to its pinyin ("蘝liǎn"), sometimes with a short
        # part-of-speech tag ("嗄〈叹〉"). Strip a leading copy of the
        # headword and check whether anything substantive is left.
        stripped = line
        while stripped.startswith(word):
            stripped = stripped[len(word):]
        if re.fullmatch(rf"[{PINYIN_CHARS}]*", stripped):
            continue
        if re.fullmatch(r"[〈\(（].{0,6}[〉\)）]", stripped):
            continue
        if len(line) > MAX_DEF_LENGTH:
            line = line[:MAX_DEF_LENGTH].rstrip() + "…"
        return line
    return None


def merge_chinese_definitions(entries):
    """
    Fill in a real Chinese definition (from data/word.json) for every
    character that Unicode's kDefinition left blank. This is what stops
    the dictionary from showing "(no definition on file)" for the tens of
    thousands of rare/variant characters Unihan doesn't gloss in English.

    Returns the number of definitions filled in.
    """
    if not os.path.exists(WORD_JSON_PATH):
        print(f"[merge] {WORD_JSON_PATH} not found — skipping Chinese "
              f"definition fill-in (characters without a Unihan definition "
              f"will be left blank).")
        return 0

    with open(WORD_JSON_PATH, encoding="utf-8") as f:
        word_data = json.load(f)

    # Some characters appear more than once in word.json (variant/oldword
    # entries); keep whichever has the longest explanation, on the
    # assumption that's the most complete one.
    lookup = {}
    for rec in word_data:
        w = rec.get("word")
        exp = rec.get("explanation")
        if not w or not exp:
            continue
        if w not in lookup or len(exp) > len(lookup[w]):
            lookup[w] = exp

    filled = 0
    for entry in entries:
        if entry.get("definition"):
            continue  # already has a real Unihan definition — leave it alone
        raw = lookup.get(entry["word"])
        if not raw:
            continue
        cleaned = clean_explanation(raw, entry["word"])
        if cleaned:
            entry["definition"] = cleaned
            filled += 1

    return filled


def merge_cedict_definitions(entries):
    """
    Second fallback: fill remaining gaps with English glosses from the
    CC-CEDICT cache. CC-CEDICT is a Chinese-English dictionary, so this
    gives a real English definition for characters that neither Unihan's
    kDefinition nor word.json covered.

    Returns the number of definitions filled in.
    """
    if not os.path.exists(CEDICT_PATH):
        print(f"[merge] {CEDICT_PATH} not found — skipping CC-CEDICT "
              f"fallback.")
        return 0

    import gzip

    # Build a lookup of traditional-character -> list of English glosses.
    # CC-CEDICT lines look like:
    #   一 一 [yi1] /one/single/a (article)/.../
    # The first field is the traditional form, the last /.../ block holds
    # the slash-separated definitions.
    lookup = {}
    with gzip.open(CEDICT_PATH, "rt", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            m = re.match(r"^(\S+)\s+\S+\s+\[[^\]]*\]\s+/(.*)/$", line)
            if not m:
                continue
            trad = m.group(1)
            defs = [d for d in m.group(2).split("/") if d]
            if defs:
                lookup.setdefault(trad, []).extend(defs)

    filled = 0
    for entry in entries:
        if entry.get("definition"):
            continue
        glosses = lookup.get(entry["word"])
        if not glosses:
            continue
        # Join the first few glosses into a compact English definition.
        gloss = "; ".join(glosses[:3])
        if len(gloss) > MAX_DEF_LENGTH:
            gloss = gloss[:MAX_DEF_LENGTH].rstrip() + "…"
        entry["definition"] = gloss
        filled += 1

    return filled


def main():
    # IMPORTANT: don't pass "fields" here. unihan-etl uses an internal,
    # hardcoded field->file lookup table to decide which of the 8 Unihan
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

        out.append({
            "word": char,
            "radical": radical,
            "residual_strokes": residual,
            "total_strokes": total_strokes,
            "pinyin": pinyin,
            "definition": definition,
        })

    out.sort(key=lambda e: (e["radical"], e["residual_strokes"] or 0))

    # Fill in real definitions for characters Unihan didn't gloss, so the
    # dictionary never shows a bare "(no definition)". First try the
    # Chinese-language word.json, then fall back to the CC-CEDICT English
    # glosses for anything still blank.
    filled = merge_chinese_definitions(out)
    filled += merge_cedict_definitions(out)

    # Drop the handful of characters that still have no definition in any
    # source. They're extremely rare historical/variant forms that no
    # dictionary lists — keeping them would just show a bare headword with
    # nothing under it, which is exactly the "not defined" clutter we're
    # trying to avoid.
    before = len(out)
    out = [e for e in out if e.get("definition")]
    pruned = before - len(out)

    with open("jianzi_data.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"Wrote {len(out)} characters to jianzi_data.json")
    if filled:
        print(f"Filled in {filled} definitions from word.json / CC-CEDICT.")
    if pruned:
        print(f"Pruned {pruned} characters with no definition in any source.")


if __name__ == "__main__":
    main()