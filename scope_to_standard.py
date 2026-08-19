"""
scope_to_standard.py

Scopes jianzi_data.json down to a real dictionary-sized character set,
based on the official 《通用规范汉字表》 (Table of General Standard Chinese
Characters, 2013) — the actual PRC government standard for general-use
characters, and roughly what a real printed dictionary like Xinhua Zidian
is scoped to. Run this AFTER build_unihan_data.py and
merge_word_definitions.py.

The 通用规范汉字表 itself is 8,105 characters. That list is used as the
core here; if the core doesn't reach TARGET_COUNT below, it's padded out
with the next-simplest (lowest total-stroke-count) remaining defined
characters, so you end up with a specific target size while still
prioritizing the official standard set first.

Usage:
    python scope_to_standard.py

Requires:
    - jianzi_data.json      (already built + definitions filled in)
    - tongyong_8105.json    (the official character list — a plain JSON
                              array of 8105 single characters; source:
                              https://github.com/jaywcjlove/table-of-general-standard-chinese-characters)

Writes:
    - jianzi_data.json  (updated in place, scoped down)
    - jianzi_data.js    (regenerated to match, for file:// use)
"""

import json

JIANZI_PATH = "jianzi_data.json"
JIANZI_JS_PATH = "jianzi_data.js"
STANDARD_LIST_PATH = "tongyong_8105.json"

TARGET_COUNT = 13000


def main():
    with open(JIANZI_PATH, encoding="utf-8") as f:
        entries = json.load(f)

    with open(STANDARD_LIST_PATH, encoding="utf-8") as f:
        standard_chars = set(json.load(f))

    core = [e for e in entries if e["word"] in standard_chars]
    rest = [e for e in entries if e["word"] not in standard_chars]
    rest.sort(key=lambda e: (e.get("total_strokes") or 99, e["word"]))

    need = max(0, TARGET_COUNT - len(core))
    final = core + rest[:need]
    final.sort(key=lambda e: (e["radical"], e.get("residual_strokes") or 0))

    with open(JIANZI_PATH, "w", encoding="utf-8") as f:
        json.dump(final, f, ensure_ascii=False, indent=2)

    with open(JIANZI_JS_PATH, "w", encoding="utf-8") as f:
        f.write("// Generated browser-safe copy of jianzi_data.json for file:// use.\n")
        f.write("window.JIANZI_FULL_DATA = ")
        json.dump(final, f, ensure_ascii=False)
        f.write(";\n")

    print(f"Official 通用规范汉字表 characters included: {len(core)} / {len(standard_chars)}")
    print(f"Supplemental characters added to reach {TARGET_COUNT}: {len(final) - len(core)}")
    print(f"Final total: {len(final)}")


if __name__ == "__main__":
    main()
