"""
merge_word_definitions.py

Fills in the "no definition on file" gaps in jianzi_data.json.

Unicode's own kDefinition field (what build_unihan_data.py normally uses)
is English-only and only covers a fraction of all Han characters — most
entries in the full Unihan set have no kDefinition at all. This script
uses the word.json dataset (a Chinese-language character/word dictionary,
keyed by character) that's been added under data/word.json to fill in a
real definition for characters that were missing one, without touching
any entry that already has a genuine Unihan definition.

Usage:
    python merge_word_definitions.py

Requires:
    - jianzi_data.json  (already built by build_unihan_data.py)
    - data/word.json    (the added dataset — same folder layout as the
                          pwxcoo/chinese-xinhua project, but any word.json
                          with the same {word, explanation, ...} shape works)

Writes:
    - jianzi_data.json  (updated in place — entries with an existing
                          definition are left completely untouched)
    - jianzi_data.js    (regenerated to match, for file:// use)
"""

import json
import re

JIANZI_PATH = "jianzi_data.json"
JIANZI_JS_PATH = "jianzi_data.js"
WORD_JSON_PATH = "data/word.json"

MAX_DEF_LENGTH = 80
PINYIN_CHARS = "a-zA-ZāáǎàēéěèīíǐìōóǒòūúǔùǖǘǚǜÜüńň"


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


def main():
    with open(JIANZI_PATH, encoding="utf-8") as f:
        entries = json.load(f)

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

    with open(JIANZI_PATH, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)

    with open(JIANZI_JS_PATH, "w", encoding="utf-8") as f:
        f.write("// Generated browser-safe copy of jianzi_data.json for file:// use.\n")
        f.write("window.JIANZI_FULL_DATA = ")
        json.dump(entries, f, ensure_ascii=False)
        f.write(";\n")

    still_missing = sum(1 for e in entries if not e.get("definition"))
    print(f"Filled in {filled} definitions from data/word.json.")
    print(f"{still_missing} characters still have no definition on file "
          f"(genuinely obscure/rare ones not covered by either source).")


if __name__ == "__main__":
    main()
