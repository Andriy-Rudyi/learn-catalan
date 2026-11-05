/* /c1/article: write an opinion article of about 410 words.
 *
 * A live word count, connectors to insert at the cursor and a check of the
 * text's shape: paragraphs, connectors used, words repeated too often and
 * sentences that run too long. The draft and the topic stay in this
 * browser (localStorage); nothing is sent anywhere.
 */
(function () {
  'use strict';

  var configNode = document.getElementById('article-config');
  if (!configNode) { return; }
  var config = JSON.parse(configNode.textContent);
  var S = config.strings;
  var STORE = 'learn-catalan:c1-article:v1';
  var text = document.getElementById('article-text');
  var topic = document.getElementById('article-topic');
  var counter = document.getElementById('article-counter');
  var report = document.getElementById('article-report');
  var WORD = /[A-Za-zÀ-ÿ·'’-]+/g;
  // Words too common to count as repetitions.
  var STOP = ('el la els les l lo un una uns unes de del dels d a al als en i o u que qui què per ' +
    'pel pels amb sense es se s em m et t ens us li hi ho ne n no sí és són ser estar ha han he ' +
    'hem heu haver va van vaig fer fa més molt molts molta moltes tot tots tota totes aquest ' +
    'aquesta aquests aquestes això aquell aquella com quan on si però ja també perquè doncs ' +
    'seu seva seus seves meu meva nostre nostra cap altre altra altres pot poden cal hi han ' +
    'tenir té tenen sobre fins entre després abans encara així doncs mateix mateixa').split(' ');
  var stopSet = {};
  STOP.forEach(function (w) { stopSet[w] = true; });
  var connectors = [].concat.apply([], config.connectors);

  function format(template, values) {
    return template.replace(/\{(\w+)\}/g, function (all, key) { return key in values ? values[key] : all; });
  }

  function words(value) { return (value.match(WORD) || []).filter(function (w) { return /[A-Za-zÀ-ÿ]/.test(w); }); }

  function save() {
    try {
      window.localStorage.setItem(STORE, JSON.stringify({ text: text.value, topic: topic.value }));
    } catch (e) { /* private window: no draft */ }
  }

  function load() {
    try {
      var data = JSON.parse(window.localStorage.getItem(STORE) || '{}') || {};
      if (data.text) { text.value = data.text; }
      if (data.topic) { topic.value = data.topic; }
    } catch (e) { /* nothing saved */ }
  }

  function updateCount() {
    var n = words(text.value).length;
    counter.textContent = format(S.words, { n: n, target: config.target });
    var ratio = n / config.target;
    counter.classList.toggle('is-good', ratio >= 0.9 && ratio <= 1.1);
    counter.classList.toggle('is-long', ratio > 1.1);
  }

  function line(className, message) {
    var p = document.createElement('p');
    p.className = 'mb-1 ' + className;
    p.textContent = message;
    report.appendChild(p);
    return p;
  }

  function check() {
    report.textContent = '';
    var value = text.value.trim();
    var list = words(value);
    var n = list.length;
    if (n < config.target * 0.9) {
      line('text-warning-emphasis', format(S.short, { n: config.target - n }));
    } else if (n > config.target * 1.1) {
      line('text-warning-emphasis', format(S.long, { n: n - config.target }));
    } else {
      line('text-success', S.good);
    }

    var blocks = value.split(/\n\s*\n|\n/).map(function (b) { return b.trim(); }).filter(Boolean);
    var title = blocks.length ? blocks[0] : '';
    if (!title || words(title).length > 14 || /[.!]$/.test(title)) {
      line('text-warning-emphasis', S.noTitle);
    }
    var paragraphs = blocks.length - 1;
    line(paragraphs >= 4 && paragraphs <= 6 ? 'text-success' : 'text-warning-emphasis',
         format(paragraphs >= 4 && paragraphs <= 6 ? S.paragraphsOk : S.paragraphs, { n: Math.max(paragraphs, 0) }));

    var lower = ' ' + value.toLowerCase().replace(/[’]/g, "'") + ' ';
    var used = connectors.filter(function (c) {
      var needle = c.toLowerCase().replace(/[’]/g, "'").replace(/…/g, '');
      return lower.indexOf(needle) >= 0;
    });
    line(used.length >= 6 ? 'text-success' : 'text-warning-emphasis', format(S.connectors, { n: used.length }));
    if (used.length < 6) { line('text-warning-emphasis', S.fewConnectors); }

    var counts = {};
    list.forEach(function (w) {
      var key = w.toLowerCase().replace(/^[ldmnst]['’]/, '');
      if (key.length < 4 || stopSet[key]) { return; }
      counts[key] = (counts[key] || 0) + 1;
    });
    var repeated = Object.keys(counts).filter(function (k) { return counts[k] >= 4; })
      .sort(function (a, b) { return counts[b] - counts[a]; }).slice(0, 8);
    if (repeated.length) {
      var p = line('mb-1', S.repeated + ' ');
      repeated.forEach(function (w, i) {
        var tag = document.createElement('span');
        tag.className = 'course-repeat';
        tag.lang = 'ca';
        tag.textContent = w + ' ×' + counts[w];
        p.appendChild(tag);
        if (i < repeated.length - 1) { p.appendChild(document.createTextNode(' ')); }
      });
    } else {
      line('text-success', S.noRepeats);
    }

    var sentences = value.split(/[.!?]+\s/);
    var long = sentences.filter(function (s) { return words(s).length > 40; }).length;
    if (long) { line('text-warning-emphasis', format(S.longSentences, { n: long })); }
  }

  function insert(snippet) {
    var start = text.selectionStart == null ? text.value.length : text.selectionStart;
    var end = text.selectionEnd == null ? start : text.selectionEnd;
    var before = text.value.slice(0, start);
    var piece = snippet.replace(/…$/, '');
    // A capital letter after a full stop or at the start, a space before.
    var sentenceStart = !before.trim() || /[.!?]\s*$/.test(before) || /\n\s*$/.test(before);
    piece = sentenceStart ? piece.charAt(0).toUpperCase() + piece.slice(1) : piece.charAt(0).toLowerCase() + piece.slice(1);
    var spaceBefore = before && !/\s$/.test(before) ? ' ' : '';
    // "Tot i que", "Perquè", "Pel que fa a" lead into the clause: no comma.
    var addition = spaceBefore + piece + (/(que|perquè|fa a|com ara)$/i.test(piece) ? ' ' : ', ');
    text.value = before + addition + text.value.slice(end);
    var at = start + addition.length;
    text.focus();
    text.setSelectionRange(at, at);
    updateCount();
    save();
  }

  document.querySelectorAll('[data-insert]').forEach(function (button) {
    button.addEventListener('mousedown', function (event) { event.preventDefault(); });
    button.addEventListener('click', function () { insert(button.getAttribute('data-insert')); });
  });
  text.addEventListener('input', function () { updateCount(); save(); });
  topic.addEventListener('change', save);
  document.getElementById('article-random').addEventListener('click', function () {
    topic.selectedIndex = Math.floor(Math.random() * topic.options.length);
    save();
  });
  document.getElementById('article-check').addEventListener('click', check);
  document.getElementById('article-copy').addEventListener('click', function (event) {
    var button = event.currentTarget;
    if (!navigator.clipboard) { return; }
    navigator.clipboard.writeText(topic.value + '\n\n' + text.value).then(function () {
      var old = button.textContent;
      button.textContent = S.copied;
      setTimeout(function () { button.textContent = old; }, 1500);
    }, function () {});
  });
  document.getElementById('article-clear').addEventListener('click', function () {
    if (text.value && !window.confirm(S.confirmClear)) { return; }
    text.value = '';
    report.textContent = '';
    updateCount();
    save();
  });

  load();
  updateCount();
})();
