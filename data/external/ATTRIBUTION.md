# Third-party data attribution

`data/external/dictionary.json` (and the `index.html` viewer that embeds it) contains
data from the following sources, all free and redistributable with attribution:

- **KANJIDIC2** and **JMdict** — Electronic Dictionary Research and Development Group
  (EDRDG), licensed under **CC BY-SA 4.0**. English-only, pre-built as JSON by
  <https://github.com/scriptin/jmdict-simplified> (Kanjidic/JMdict release artifacts).
  Used for meanings, on/kun readings, grade, JLPT level, stroke count, and common
  compound words containing each kanji.
- **Tatoeba** — example sentences contributed by the Tatoeba volunteer community,
  licensed under **CC BY-SA 2.0 FR**. The JMdict example-sentence data carries the
  original `source: "tatoeba"` attribution. Source: <https://tatoeba.org>.
- **kanji-keys** — mnemonic keywords by the TopoKanji author (Dmitry Shpika),
  multi-licensed: Apache-2.0+, CC-BY-4.0+, EPL-1.0+, LGPL-3.0+, MIT.
  Source: <https://github.com/scriptin/kanji-keys>.
- **kanji-data** — JLPT N5–N1 levels per kanji, by David Gouveia, **MIT License**.
  Source: <https://github.com/davidluzgouveia/kanji-data> (JLPT levels were derived from
  tanos.co.uk's community JLPT resources).

The raw data files (KANJIDIC2/JMdict JSON, ~250 MB) are git-ignored and are
re-downloaded on demand by:

    python build-dictionary.py

This is a personal learning tool; if you redistribute `index.html` or `dictionary.json`,
keep this attribution and respect the CC BY-SA (share-alike) terms of the EDRDG/Tatoeba
data.
