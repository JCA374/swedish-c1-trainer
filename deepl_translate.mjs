#!/usr/bin/env node
/**
 * Re-translate every word's English gloss via DeepL (American English, EN-US)
 * and write the results back into index.html in place.
 *
 * Usage:
 *   DEEPL_API_KEY=your-key-here node deepl_translate.mjs
 *
 * Notes:
 *   - Uses the DeepL API. Free keys use https://api-free.deepl.com,
 *     Pro keys use https://api.deepl.com. Free keys end in ":fx".
 *   - Source is Swedish (SV), target is American English (EN-US).
 *   - A timestamped backup of the HTML is written before any change.
 */
import { readFileSync, writeFileSync, copyFileSync } from "node:fs";

const HTML = "index.html";
const KEY = process.env.DEEPL_API_KEY || process.env.DEEPL_AUTH_KEY;
if (!KEY) {
  console.error("Missing DEEPL_API_KEY. Run: DEEPL_API_KEY=... node deepl_translate.mjs");
  process.exit(1);
}
const HOST = KEY.trim().endsWith(":fx") ? "https://api-free.deepl.com" : "https://api.deepl.com";

const html = readFileSync(HTML, "utf8");
const m = html.match(/const SEED_WORDS = (\[[\s\S]*?\]);/);
if (!m) { console.error("Could not locate SEED_WORDS in " + HTML); process.exit(1); }
const words = eval("(" + m[1] + ")");

async function translate(text) {
  const body = new URLSearchParams({
    text, source_lang: "SV", target_lang: "EN-US", formality: "default"
  });
  const res = await fetch(`${HOST}/v2/translate`, {
    method: "POST",
    headers: {
      "Authorization": `DeepL-Auth-Key ${KEY}`,
      "Content-Type": "application/x-www-form-urlencoded"
    },
    body
  });
  if (!res.ok) throw new Error(`DeepL ${res.status}: ${await res.text()}`);
  const json = await res.json();
  return json.translations[0].text;
}

// Serialize one entry to the same compact one-line-per-word format as the file.
function serialize(w) {
  const arr = a => "[" + a.map(s => JSON.stringify(s)).join(",") + "]";
  return `  {id:${JSON.stringify(w.id)},word:${JSON.stringify(w.word)},` +
    `pos:${JSON.stringify(w.pos)},definitionSv:${JSON.stringify(w.definitionSv)},` +
    `synonyms:${arr(w.synonyms)},examples:${arr(w.examples)},` +
    `english:${JSON.stringify(w.english)},difficulty:${w.difficulty}}`;
}

(async () => {
  let done = 0;
  for (const w of words) {
    try {
      // Translate the headword for a clean American-English gloss.
      w.english = await translate(w.word);
      done++;
      process.stdout.write(`\r${done}/${words.length}  ${w.word} -> ${w.english}            `);
    } catch (e) {
      console.error(`\nFailed on "${w.word}": ${e.message}`);
      process.exit(1);
    }
  }
  const block = "const SEED_WORDS = [\n" + words.map(serialize).join(",\n") + "\n];";
  const stamp = new Date().toISOString().replace(/[:.]/g, "-");
  copyFileSync(HTML, `${HTML}.bak-${stamp}`);
  writeFileSync(HTML, html.replace(m[0], block), "utf8");
  console.log(`\nUpdated ${HTML} (${done} glosses). Backup: ${HTML}.bak-${stamp}`);
})();
