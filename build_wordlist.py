#!/usr/bin/env python3
"""
Build the C1 word list from two open sources and write it into index.html.

  - Swedish Kelly list (Språkbanken, Göteborgs universitet; CC BY-SA 3.0)
    gives the headwords and their CEFR level (here: C1, <cefr>5</cefr>).
  - Folkets lexikon (KTH; CC BY-SA 2.5) gives definitions, synonyms,
    example phrases and English translations.

Usage:
  python3 build_wordlist.py            # download, build, write index.html
  python3 build_wordlist.py --dry-run  # build and print a sample, don't write
  python3 build_wordlist.py --cache DIR  # reuse/keep downloaded XML in DIR

Words are kept only if they work in at least one exercise type: a usable
example (fill-in-the-blank) or a usable synonym (synonym match).
"""
import argparse, html, json, os, random, re, statistics, sys, unicodedata, urllib.request
import xml.etree.ElementTree as ET

KELLY_URL = "https://svn.spraakdata.gu.se/sb-arkiv/pub/lexikon/kelly/kelly.xml"
FOLKETS_URL = "https://folkets-lexikon.csc.kth.se/folkets/folkets_sv_en_public.xml"
HTML = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")
BEGIN, END = "/* KELLY_C1:BEGIN */", "/* KELLY_C1:END */"

C1 = "5"
SYN_MIN_LEVEL = 3.5        # Folkets synonym quality (0–5); below this is too noisy
MAX_SYNONYMS = 4
MAX_EXAMPLES = 3

# Kelly POS -> (Folkets class, Swedish label)
POS = {
    "noun-en": ("nn", "substantiv"), "noun-ett": ("nn", "substantiv"), "noun": ("nn", "substantiv"),
    "verb": ("vb", "verb"), "adjective": ("jj", "adjektiv"), "adverb": ("ab", "adverb"),
    "prep": ("pp", "preposition"), "interj": ("in", "interjektion"),
}


def fetch(url, cache):
    if cache:
        path = os.path.join(cache, os.path.basename(url))
        if not os.path.exists(path):
            os.makedirs(cache, exist_ok=True)
            urllib.request.urlretrieve(url, path)
        return ET.parse(path).getroot()
    with urllib.request.urlopen(url) as r:
        return ET.fromstring(r.read())


def norm(s):
    """Same idea as normalizeAnswer() in index.html: lower-case, trimmed."""
    return (s or "").strip().lower()


def slug(word):
    s = unicodedata.normalize("NFKD", word.lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def stem_of(word):
    """Mirror blankOut() in index.html: first word minus 2 chars, at least 3."""
    base = word.split(" ")[0]
    return base[: max(3, len(base) - 2)].lower()


def blankable(example, word):
    return re.search(r"\b" + re.escape(stem_of(word)) + r"\w*", example, re.I) is not None


def clean(s):
    return html.unescape(s or "").strip()


def good_synonym(syn, word, fclass, classes):
    if not syn or norm(syn) == norm(word):
        return False
    if syn[0].isupper() or len(syn.split()) > 2:   # names, phrases
        return False
    if re.search(r"[^a-zåäöéü \-]", syn.lower()):
        return False
    # Folkets mixes senses; a synonym with another word class (e.g. noun "hög"
    # -> adjective "påtänd") belongs to a different sense. Phrases can't be checked.
    return " " in syn or fclass in classes.get(syn, ())


def build(kelly, folkets):
    by_word, classes = {}, {}
    for w in folkets.iter("word"):
        by_word.setdefault(w.get("value"), []).append(w)
        classes.setdefault(w.get("value"), set()).add(w.get("class"))

    c1 = []
    seen = set()
    for e in kelly.findall("LexicalEntry"):
        if e.findtext("cefr") != C1:
            continue
        word = (e.findtext("gf") or "").strip()
        kpos = e.findtext("pos") or ""
        if not word or word in seen or kpos not in POS:
            continue
        seen.add(word)
        fclass, pos_sv = POS[kpos]
        wpm = float((e.findtext("wpm") or "0").replace(",", "."))
        # One Folkets entry = one sense. Use the first one of the right class
        # that has a definition, so definition, synonyms, examples and English
        # all describe the same meaning.
        entries = [f for f in by_word.get(word, [])
                   if f.get("class") == fclass and f.find("definition") is not None][:1]
        if not entries:
            continue

        defs = [clean(d.get("value")) for f in entries for d in f.findall("definition")]
        defs = [d for d in defs if d]
        eng = []
        for f in entries:
            for t in f.findall("translation"):
                v = clean(t.get("value"))
                if v and v not in eng:
                    eng.append(v)
        if not defs or not eng:
            continue
        definition = defs[0]

        syns = []
        for f in entries:
            for s in f.findall("synonym"):
                v = clean(s.get("value"))
                if float(s.get("level") or 0) >= SYN_MIN_LEVEL and good_synonym(v, word, fclass, classes) and v not in syns:
                    syns.append(v)
        syns = syns[:MAX_SYNONYMS]
        # The definition is shown in synonym mode; if it contains every synonym
        # the answer would be given away, so the word can't use that mode.
        if syns and all(norm(s) in norm(definition) for s in syns):
            syns = []

        examples = []
        for f in entries:
            for x in f.findall("example"):
                v = clean(x.get("value"))
                if v and blankable(v, word) and v not in examples:
                    examples.append(v[0].upper() + v[1:])
        examples = examples[:MAX_EXAMPLES]

        if not syns and not examples:
            continue
        c1.append({
            "id": slug(word), "word": word, "pos": pos_sv, "definitionSv": definition,
            "synonyms": syns, "examples": examples, "english": " / ".join(eng[:2]),
            "wpm": wpm, "level": "C1",
        })

    # Rarer words (lower frequency) are a bit harder.
    median = statistics.median(w["wpm"] for w in c1)
    for w in c1:
        w["difficulty"] = 4 if w.pop("wpm") < median else 3
    return c1


def seed_ids(text):
    return set(re.findall(r'\{id:"([^"]+)"', text))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--cache")
    args = ap.parse_args()

    words = build(fetch(KELLY_URL, args.cache), fetch(FOLKETS_URL, args.cache))
    text = open(HTML, encoding="utf8").read()
    # Hand-curated seed entries win over generated ones with the same id.
    seeds = seed_ids(text.split(BEGIN)[0] if BEGIN in text else text)
    dupes = [w["word"] for w in words if w["id"] in seeds]
    words = [w for w in words if w["id"] not in seeds]

    both = sum(1 for w in words if w["synonyms"] and w["examples"])
    fill = sum(1 for w in words if w["examples"] and not w["synonyms"])
    syn = sum(1 for w in words if w["synonyms"] and not w["examples"])
    print(f"C1 words: {len(words)} (both modes {both}, fill only {fill}, synonym only {syn}); "
          f"skipped as already in seed: {dupes}")
    random.seed(7)
    for w in random.sample(words, min(30, len(words))):
        print(f"  {w['word']} ({w['pos']}): {w['definitionSv']} | syn {w['synonyms']} | "
              f"ex {w['examples'][:1]} | {w['english']}")

    if args.dry_run:
        return
    body = ",\n".join(json.dumps(w, ensure_ascii=False) for w in words)
    block = f"{BEGIN}\nconst KELLY_C1 = [\n{body}\n];\n{END}"
    if BEGIN not in text:
        sys.exit(f"Markers {BEGIN} … {END} not found in {HTML}")
    pre, rest = text.split(BEGIN, 1)
    post = rest.split(END, 1)[1]
    open(HTML, "w", encoding="utf8").write(pre + block + post)
    print(f"Wrote {len(words)} words into {HTML}")


if __name__ == "__main__":
    main()
