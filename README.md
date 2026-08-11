# 检字表 — Book-style Radical + Stroke Index

A from-scratch version of a Xinhua-Zidian-style character lookup: browse
by **radical (部首)**, then by **stroke count**, like flipping to the
index pages at the front of a real paper dictionary.

Data comes straight from Unicode's own **Unihan database** (via the
`unihan-etl` library) — not from any existing GitHub Chinese-dictionary repo.
The radical table itself (all 214 Kangxi radicals) is the standard
reference table used by every Chinese dictionary since 1716 — public
domain, universal, not tied to any specific project.

## Files

- `index.html` — the site itself.
- `radicals_full.js` — the complete 214 Kangxi radicals (glyph, variant
  form, stroke count, pinyin, English meaning). Always loaded — this is
  what powers the left-page index and the thumb tabs now.
- `sample_data.js` — ~50 sample characters across 16 radicals, used as a
  **fallback** only, for when the full dataset isn't available yet.
- `data_loader.js` — tries to `fetch()` `jianzi_data.json`; falls back to
  the sample data automatically if that file doesn't exist yet or the
  page was opened via `file://`.
- `build_unihan_data.py` — run on your own machine (needs internet
  access to unicode.org) to generate `jianzi_data.json`, the full dataset:
  every Han character with radical, stroke count, pinyin, and definition.
- `serve.py` — a one-command local web server. **Required** for the full
  dataset to load, since browsers block `fetch()` of local files opened
  directly via `file://`.

## Try it now (sample data)

Just open `index.html` directly in a browser — no server needed for this.
You'll see all 214 radicals on the left page; only the ~16 with sample
characters will show results when clicked. A badge at the bottom of the
screen confirms you're on sample data.

## Scaling up to the full dictionary

1. Install the library:
   ```
   pip install unihan-etl
   ```
2. Generate the full dataset:
   ```
   python build_unihan_data.py
   ```
   Downloads Unicode's Unihan.zip and writes `jianzi_data.json`
   (tens of thousands of characters — takes a minute or two).

3. Serve the folder (needed now — `fetch()` won't work over `file://`):
   ```
   python serve.py
   ```
   This opens the site in your browser automatically at
   `http://localhost:8000`. `data_loader.js` will detect
   `jianzi_data.json` and load the full dataset — the bottom badge
   will confirm how many characters loaded.

No HTML edits needed for this step — `data_loader.js` already tries the
full dataset first and only falls back to the sample if it's missing.

## Notes

- Stroke groupings on the right page ("+N 画") mean "N strokes beyond the
  radical" — exactly how paper dictionaries organize their 检字表.
- The thumb-index tabs on the right edge jump you to radicals grouped by
  the radical's *own* stroke count (1画 through 17画) — mimicking the
  physical thumb notches cut into real dictionaries.
- The detail card shows total stroke count when the full dataset is
  loaded (Unihan's `kTotalStrokes`); sample entries don't include it.

## Still to build (from the project doc's roadmap)

- Search bar (character / pinyin / meaning) — separate from radical browsing
- Explicit handling for characters with multiple radical candidates
  (currently the build script takes the first `kRSUnicode` candidate)
- Stroke-order animation on the detail card
- Attribution/source page for the Unicode Unihan data
