'use strict';

/**
 * Generates a single self-contained `index.html` with all list/dependency
 * data embedded, so it can be opened directly from the filesystem (file://)
 * without a web server or fetch() calls.
 *
 * Run after `node build.js save` to pick up regenerated lists:
 *   node build-viewer.js
 */

var fs = require('fs');
var path = require('path');

var ROOT = __dirname;
var LISTS_DIR = path.join(ROOT, 'lists');
var DEPS_FILE = path.join(ROOT, 'dependencies', '1-to-N.json');
var KANJI_FILE = path.join(ROOT, 'data', 'kanji.json');
var DICT_FILE = path.join(ROOT, 'data', 'external', 'dictionary.json');
var TEMPLATE_FILE = path.join(ROOT, 'viewer.template.html');
var OUTPUT_FILE = path.join(ROOT, 'index.html');

var PLACEHOLDER = '/*__DATA__*/null';

function readJson(file) {
  return JSON.parse(fs.readFileSync(file, 'utf8'));
}

function main() {
  var lists = {};
  fs.readdirSync(LISTS_DIR)
    .filter(function (f) { return /\.json$/.test(f); })
    .sort()
    .forEach(function (f) {
      lists[f.replace(/\.json$/, '')] = readJson(path.join(LISTS_DIR, f));
    });

  var deps = readJson(DEPS_FILE);
  var kanjiRows = readJson(KANJI_FILE);

  var kanji = {};
  kanjiRows.forEach(function (row) {
    kanji[row[0]] = { s: row[1], c: row[2] };
  });

  // Invert the dependency map: component -> kanji that use it.
  var usedIn = {};
  Object.keys(deps).forEach(function (ch) {
    (deps[ch] || []).forEach(function (part) {
      if (part === '0') return;
      if (!usedIn[part]) usedIn[part] = [];
      if (usedIn[part].indexOf(ch) === -1) usedIn[part].push(ch);
    });
  });

  var data = {
    lists: lists,
    deps: deps,
    kanji: kanji,
    usedIn: usedIn,
    dict: fs.existsSync(DICT_FILE) ? readJson(DICT_FILE) : null
  };
  if (!data.dict) {
    console.warn('WARNING: ' + DICT_FILE + ' not found.');
    console.warn('Run `python build-dictionary.py` to add meanings, readings, words and sentences.');
  }

  var template = fs.readFileSync(TEMPLATE_FILE, 'utf8');
  if (template.indexOf(PLACEHOLDER) === -1) {
    throw new Error('Placeholder ' + PLACEHOLDER + ' not found in template');
  }

  var json = JSON.stringify(data);
  if (json.indexOf('</script>') !== -1) {
    json = json.replace(/<\/script>/gi, '<\\/script>');
  }

  var html = template.replace(PLACEHOLDER, json);
  fs.writeFileSync(OUTPUT_FILE, html, 'utf8');

  var kb = Math.round(Buffer.byteLength(html, 'utf8') / 1024);
  console.log('Wrote ' + OUTPUT_FILE + ' (' + kb + ' KB, ' +
    Object.keys(lists).length + ' lists, ' + Object.keys(kanji).length + ' characters)');
}

main();
