# -*- coding: utf-8 -*-
"""
Builds `data/external/dictionary.json` for the kanji-radical-map viewer.

Sources (all free, CC BY-SA):
  - KANJIDIC2  (https://github.com/scriptin/jmdict-simplified releases) — meanings, readings, grade, JLPT
  - JMdict     (same releases)                                          — related compound words
  - JMdict + Tatoeba example sentences (sentences carry source: "tatoeba")
  - kanji-keys (https://github.com/scriptin/kanji-keys)                — mnemonics

The raw data files are git-ignored; only `dictionary.json` is committed.
Run `python build-dictionary.py` to (re)create them; the script downloads what it needs.
"""
import json
import os
import shutil
import sys
import tarfile
import urllib.request
import urllib.parse
import urllib.error

ROOT = os.path.dirname(os.path.abspath(__file__))
EXTERNAL = os.path.join(ROOT, 'data', 'external')
KANJI_JSON = os.path.join(ROOT, 'data', 'kanji.json')
KEYS_JSON = os.path.join(EXTERNAL, 'kanji-keys.json')
OUT_JSON = os.path.join(EXTERNAL, 'dictionary.json')

RELEASE = 'https://github.com/scriptin/jmdict-simplified/releases/download/3.6.2%2B20261109214828/'
DOWNLOADS = {
    'kanjidic2-en-3.6.2.json': RELEASE + 'kanjidic2-en-3.6.2%2B20261109214828.json.tgz',
    'jmdict-eng-3.6.2.json': RELEASE + 'jmdict-eng-3.6.2%2B20261109214828.json.tgz',
    'jmdict-examples-eng-3.6.2.json': RELEASE + 'jmdict-examples-eng-3.6.2%2B20261109214828.json.tgz',
    'kanji-keys.json': 'https://raw.githubusercontent.com/scriptin/kanji-keys/master/kanji-keys.json',
    # jlpt_new levels (N5..N1), MIT-licensed community JLPT list (tanos.co.uk)
    'kanji-data.json': 'https://raw.githubusercontent.com/davidluzgouveia/kanji-data/master/kanji.json',
}
EX = {
    'kanjidic2-en-3.6.2.json': os.path.join(EXTERNAL, 'kanjidic2-en-3.6.2.json'),
    'jmdict-eng-3.6.2.json': os.path.join(EXTERNAL, 'jmdict-eng-3.6.2.json'),
    'jmdict-examples-eng-3.6.2.json': os.path.join(EXTERNAL, 'jmdict-examples-eng-3.6.2.json'),
}

UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) kanji-radical-map/1.0'}

MAX_WORDS = 5
MAX_EXAMPLES = 2
MAX_EXAMPLES_CANDIDATES = 40
MAX_JPN_EXAMPLE_LEN = 60


def load_kanji_chars():
    with open(KANJI_JSON, encoding='utf-8') as f:
        return [row[0] for row in json.load(f)]


def safe_extract_tgz(tgz_path, dest_dir):
    with tarfile.open(tgz_path) as tf:
        for member in tf.getmembers():
            if not member.name or member.name.startswith('../') or member.name.startswith('/'):
                continue
            tf.extract(member, dest_dir)


def ensure_external_files():
    os.makedirs(EXTERNAL, exist_ok=True)
    for name, url in DOWNLOADS.items():
        dst = os.path.join(EXTERNAL, name)
        if os.path.exists(dst):
            continue
        tmp = dst + '.download'
        print(f'Downloading {name} ...', flush=True)
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=900) as r, open(tmp, 'wb') as f:
            shutil.copyfileobj(r, f)
        if url.endswith('.tgz'):
            print(f'  extracting {name} ...', flush=True)
            safe_extract_tgz(tmp, EXTERNAL)
            os.remove(tmp)
        else:
            os.replace(tmp, dst)


def load_json(name):
    with open(EX[name], encoding='utf-8') as f:
        return json.load(f)


# ---------- KANJIDIC2 ----------

def build_kanji_info(kanji_set):
    print('Reading KANJIDIC2 ...', flush=True)
    data = load_json('kanjidic2-en-3.6.2.json')
    out = {}
    for ch in data['characters']:
        literal = ch['literal']
        if literal not in kanji_set:
            continue
        misc = ch.get('misc') or {}
        on, kun, meanings = [], [], []
        for group in (ch.get('readingMeaning') or {}).get('groups', []):
            for r in group.get('readings', []):
                if r.get('type') == 'ja_on':
                    on.append(r['value'])
                elif r.get('type') == 'ja_kun':
                    kun.append(r['value'])
            for m in group.get('meanings', []):
                if m.get('lang') == 'en':
                    meanings.append(m['value'])
        out[literal] = {
            'm': meanings[:10],
            'on': on[:8],
            'kun': kun[:8],
            'grade': misc.get('grade'),
            'jlpt': misc.get('jlptLevel'),
            'strokes': (misc.get('strokeCounts') or [None])[0],
            'freq': misc.get('frequency'),
        }
    print(f'  {len(out)} of {len(kanji_set)} characters have KANJIDIC2 data', flush=True)
    return out


# ---------- JMdict: related words ----------

def build_word_index(kanji_set):
    print('Reading JMdict (this is the big one) ...', flush=True)
    data = load_json('jmdict-eng-3.6.2.json')
    print(f'  {len(data["words"])} entries', flush=True)

    candidates = {c: [] for c in kanji_set}
    for w in data['words']:
        kanji_forms = [k for k in w.get('kanji', []) if k.get('text')]
        if not kanji_forms:
            continue
        glosses = []
        for s in w.get('sense', []):
            for g in s.get('gloss', []):
                if g.get('lang') == 'eng':
                    glosses.append(g['text'])
        if not glosses:
            continue
        gloss = '; '.join(glosses[:2])
        if len(gloss) > 110:
            gloss = gloss[:107] + '...'
        kana = next((k['text'] for k in w.get('kana', []) if k.get('common')),
                    (w.get('kana') or [{}])[0].get('text', ''))
        for k in kanji_forms:
            text = k['text']
            used = kanji_set.intersection(text)
            if not used:
                continue
            common = bool(k.get('common'))
            tier = 0 if common else 1
            key = (tier, len(text), text)
            for c in used:
                lst = candidates[c]
                lst.append((key, text, kana, gloss))

    print('  trimming candidates ...', flush=True)
    words = {}
    for c, lst in candidates.items():
        lst.sort(key=lambda x: x[0])
        seen = set()
        out = []
        for (_, text, kana, gloss) in lst:
            k = (text, kana)
            if k in seen:
                continue
            seen.add(k)
            out.append([text, kana, gloss])
            if len(out) >= MAX_WORDS:
                break
        words[c] = out
    return words


# ---------- JMdict examples (Tatoeba) ----------

def build_examples(kanji_set):
    print('Reading JMdict example sentences ...', flush=True)
    data = load_json('jmdict-examples-eng-3.6.2.json')
    print(f'  {len(data["words"])} entries', flush=True)

    candidates = {c: [] for c in kanji_set}

    for w in data['words']:
        for s in w.get('sense', []):
            for ex in s.get('examples') or []:
                sents = ex.get('sentences') or []
                jpn = next((x['text'] for x in sents if x.get('lang') == 'jpn'), None)
                eng = next((x['text'] for x in sents if x.get('lang') == 'eng'), None)
                if not jpn or not eng:
                    continue
                jpn = jpn.strip()
                eng = eng.strip()
                if not (3 <= len(jpn) <= MAX_JPN_EXAMPLE_LEN) or not eng:
                    continue
                used = kanji_set.intersection(jpn)
                if not used:
                    continue
                row = (len(jpn), jpn, eng)
                for c in used:
                    lst = candidates[c]
                    if len(lst) < MAX_EXAMPLES_CANDIDATES:
                        lst.append(row)
                    else:
                        worst_i = max(range(len(lst)), key=lambda i: lst[i][0])
                        if len(jpn) < lst[worst_i][0]:
                            lst[worst_i] = row

    examples = {}
    for c, lst in candidates.items():
        lst.sort(key=lambda x: x[0])
        seen = set()
        rows = []
        for _l, jpn, eng in lst:
            if eng in seen:
                continue
            seen.add(eng)
            rows.append({'jpn': jpn, 'eng': eng})
            if len(rows) >= MAX_EXAMPLES:
                break
        examples[c] = rows
    with_examples = sum(1 for v in examples.values() if v)
    print(f'  {with_examples} of {len(kanji_set)} characters have examples', flush=True)
    return examples


# ---------- kanji-keys ----------

def load_keys():
    if not os.path.exists(KEYS_JSON):
        return {}
    with open(KEYS_JSON, encoding='utf-8') as f:
        return json.load(f)


# ---------- JLPT (N5..N1) ----------

def load_jlpt_n_levels(kanji_set):
    """char -> int jlpt_new (5=N5 .. 1=N1), from davidluzgouveia/kanji-data (MIT)."""
    path = os.path.join(EXTERNAL, 'kanji-data.json')
    if not os.path.exists(path):
        print('  kanji-data.json not found; jlpt_n will be null', flush=True)
        return {}
    with open(path, encoding='utf-8') as f:
        data = json.load(f)
    out = {}
    for ch, rec in data.items():
        lvl = rec.get('jlpt_new')
        if isinstance(lvl, int) and 1 <= lvl <= 5:
            out[ch] = lvl
    covered = sum(1 for c in kanji_set if c in out)
    print(f'  jlpt_n levels: {covered} of {len(kanji_set)} characters (unrated: {len(kanji_set) - covered})', flush=True)
    return out


# ---------- main ----------

def main():
    os.makedirs(EXTERNAL, exist_ok=True)
    print('Checking downloads ...', flush=True)
    ensure_external_files()

    kanji_set = set(chars)
    print(f'{len(chars)} kanji in data/kanji.json', flush=True)

    info = build_kanji_info(kanji_set)
    words = build_word_index(kanji_set)
    examples = build_examples(kanji_set)
    keys = load_keys()
    jlpt_n = load_jlpt_n_levels(kanji_set)

    print('Assembling dictionary.json ...', flush=True)
    out = {'kanji': {}}
    for c in chars:
        k = keys.get(c) or {}
        entry = dict(info.get(c) or {})
        entry['key'] = k.get('uniq')
        entry['keys'] = k.get('keys', [])
        entry['jlpt_n'] = jlpt_n.get(c)
        entry['w'] = words.get(c, [])
        entry['x'] = examples.get(c, [])
        out['kanji'][c] = entry

    with open(OUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, separators=(',', ':'))
    print(f'Wrote {OUT_JSON} ({os.path.getsize(OUT_JSON)/1e6:.1f} MB)', flush=True)


if __name__ == '__main__':
    main()
