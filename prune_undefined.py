"""
prune_undefined.py

Removes characters with no definition at all from jianzi_data.json/.js.

The full Unihan database includes every Han character ever encoded —
that's well over 100,000 characters, the vast majority of them extremely
rare historical, dialectal, or duplicate/variant forms that even most
professional dictionaries don't bother listing. Once build_unihan_data.py
and merge_word_definitions.py have both run, tens of thousands of entries
still have no usable content at all (no English gloss from Unihan, no
Chinese gloss from word.json) — just a bare radical/stroke-count
placeholder. Rather than showing "(no definition on file)" for those,
this script drops them from the browsable dictionary entirely, same as
a real dictionary simply wouldn't print a headword with nothing under it.

Run this AFTER build_unihan_data.py and (optionally) merge_word_definitions.py.

Usage:
    python prune_undefined.py

Writes:
    - jianzi_data.json  (updated in place, pruned)
    - jianzi_data.js    (regenerated to match, for file:// use)
"""

import json

JIANZI_PATH = "jianzi_data.json"
JIANZI_JS_PATH = "jianzi_data.js"


def main():
    with open(JIANZI_PATH, encoding="utf-8") as f:
        entries = json.load(f)

    before = len(entries)
    kept = [e for e in entries if e.get("definition")]
    removed = before - len(kept)

    with open(JIANZI_PATH, "w", encoding="utf-8") as f:
        json.dump(kept, f, ensure_ascii=False, indent=2)

    with open(JIANZI_JS_PATH, "w", encoding="utf-8") as f:
        f.write("// Generated browser-safe copy of jianzi_data.json for file:// use.\n")
        f.write("window.JIANZI_FULL_DATA = ")
        json.dump(kept, f, ensure_ascii=False)
        f.write(";\n")

    print(f"Removed {removed} characters with no definition on file.")
    print(f"{len(kept)} characters remain (all with a real definition).")


if __name__ == "__main__":
    main()
