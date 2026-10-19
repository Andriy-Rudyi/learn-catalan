/* /text: click a word of a Catalan text for its form, translation and
 * synonyms in that same form (flaskblog/reader). A synonym can replace the
 * word; every replacement is kept in a history you can go back through.
 *
 * The reading pages (/reading/...) use the same panel in "read" mode: the
 * text is already on the page, its words are clickable, nothing is replaced.
 *
 * Everything the server sends is put on the page with textContent, never as
 * HTML. The text and its history stay in this browser (localStorage) so a
 * reload does not lose them.
 */
(function () {
  'use strict';

  var configNode = document.getElementById('reader-config');
  if (!configNode) { return; }
  var config = JSON.parse(configNode.textContent);
  var S = config.strings;
  var READ_ONLY = config.mode === 'read';
  var STORE = 'learn-catalan:text:v1';
  var sourceNode = document.getElementById('reader-source');
  var MAX = (sourceNode && parseInt(sourceNode.getAttribute('maxlength'), 10)) || 20000;

  var els = {
    input: document.getElementById('reader-input'),
    source: document.getElementById('reader-source'),
    start: document.getElementById('reader-start'),
    example: document.getElementById('reader-example'),
    view: document.getElementById('reader-view'),
    text: document.getElementById('reader-text'),
    edit: document.getElementById('reader-edit'),
    undo: document.getElementById('reader-undo'),
    copy: document.getElementById('reader-copy'),
    empty: document.getElementById('reader-panel-empty'),
    body: document.getElementById('reader-panel-body'),
    panel: document.getElementById('reader-panel'),
    close: document.getElementById('reader-panel-close'),
    historyBox: document.getElementById('reader-history-box'),
    history: document.getElementById('reader-history')
  };

  // history[0] is the text as pasted; each later step = {text, from, to}.
  var state = { history: [], active: -1, request: 0 };
  var cache = {};

  // -- helpers -------------------------------------------------------------------
  function el(tag, className, text) {
    var node = document.createElement(tag);
    if (className) { node.className = className; }
    if (text !== undefined && text !== null) { node.textContent = text; }
    return node;
  }

  function current() {
    var last = state.history[state.history.length - 1];
    return last ? last.text : '';
  }

  function save() {
    try {
      window.localStorage.setItem(STORE, JSON.stringify({ history: state.history }));
    } catch (e) { /* private window or storage off: the page still works */ }
  }

  function load() {
    try {
      var raw = window.localStorage.getItem(STORE);
      var data = raw ? JSON.parse(raw) : null;
      if (data && Array.isArray(data.history) && data.history.length &&
          typeof data.history[0].text === 'string') {
        return data.history;
      }
    } catch (e) { /* ignore */ }
    return null;
  }

  // Words are the runs of non-space characters; the spaces are kept as they are.
  function chunks(text) {
    return text.split(/(\s+)/).filter(function (chunk) { return chunk !== ''; });
  }

  // The cleaned word inside a chunk ("l'home," holds "home"): replace only that.
  function replaceIn(chunk, core, replacement) {
    var at = chunk.toLowerCase().indexOf(core.toLowerCase());
    if (at < 0 || !core) { return replacement; }
    return chunk.slice(0, at) + replacement + chunk.slice(at + core.length);
  }

  // -- the text ------------------------------------------------------------------------
  function render() {
    var text = current();
    els.text.textContent = '';
    var index = 0;
    chunks(text).forEach(function (chunk) {
      if (/^\s+$/.test(chunk)) {
        els.text.appendChild(document.createTextNode(chunk));
        return;
      }
      var span = el('span', 'reader-word', chunk);
      span.setAttribute('data-i', String(index));
      if (index === state.active) { span.classList.add('is-active'); }
      els.text.appendChild(span);
      index += 1;
    });
    els.undo.disabled = state.history.length < 2;
    renderHistory();
  }

  function words() {
    return els.text.querySelectorAll('.reader-word');
  }

  function renderHistory() {
    els.history.textContent = '';
    if (state.history.length < 2) {
      els.historyBox.hidden = true;
      return;
    }
    els.historyBox.hidden = false;
    state.history.forEach(function (step, position) {
      var item = el('li');
      if (position === 0) {
        item.appendChild(el('span', 'text-muted', S.original));
      } else {
        item.appendChild(el('del', null, step.from));
        item.appendChild(document.createTextNode(' → '));
        item.appendChild(el('ins', null, step.to));
      }
      if (position < state.history.length - 1) {
        var back = el('button', 'btn btn-link btn-sm reader-history-back', S.restore);
        back.type = 'button';
        back.addEventListener('click', function () {
          state.history = state.history.slice(0, position + 1);
          state.active = -1;
          save();
          render();
          showEmpty();
        });
        item.appendChild(back);
      }
      els.history.appendChild(item);
    });
  }

  function start(text) {
    text = (text || '').replace(/\r\n?/g, '\n');
    if (!text.trim()) { return; }
    if (text.length > MAX) {
      window.alert(S.tooLong);
      return;
    }
    state.history = [{ text: text }];
    state.active = -1;
    save();
    els.input.hidden = true;
    els.view.hidden = false;
    render();
    showEmpty();
    els.text.focus();
  }

  function showEmpty() {
    els.body.textContent = '';
    els.empty.hidden = false;
    closeSheet();
  }

  // -- the panel as a bottom sheet on narrow screens (see main.css) ---------------
  var sheetQuery = window.matchMedia ? window.matchMedia('(max-width: 991.98px)') : null;

  function isSheet() {
    return !!(sheetQuery && sheetQuery.matches);
  }

  function openSheet(span) {
    if (!isSheet() || !els.panel) { return; }
    els.panel.classList.add('is-open');
    document.body.classList.add('reader-sheet-open');
    // Keep the tapped word in sight above the sheet: near the top third.
    if (span && span.getBoundingClientRect) {
      var top = span.getBoundingClientRect().top;
      var wanted = window.innerHeight * 0.25;
      if (top > window.innerHeight * 0.4 || top < 60) {
        window.scrollBy({ top: top - wanted, behavior: 'smooth' });
      }
    }
  }

  function closeSheet() {
    if (!els.panel) { return; }
    els.panel.classList.remove('is-open');
    document.body.classList.remove('reader-sheet-open');
  }

  // -- one word ------------------------------------------------------------------------------
  function select(index) {
    var list = words();
    if (!list.length) { return; }
    index = Math.max(0, Math.min(list.length - 1, index));
    state.active = index;
    list.forEach(function (span) { span.classList.remove('is-active'); });
    var span = list[index];
    span.classList.add('is-active');
    if (isSheet()) {
      openSheet(span);
    } else if (span.scrollIntoView) {
      span.scrollIntoView({ block: 'nearest' });
    }
    var previous = index > 0 ? list[index - 1].textContent : '';
    lookup(span.textContent, previous, index);
  }

  function lookup(surface, previous, index) {
    var key = surface + '\u0000' + previous;
    var ticket = ++state.request;
    els.empty.hidden = true;
    els.body.textContent = '';
    els.body.appendChild(el('p', 'text-muted mb-0', S.loading));
    if (cache[key]) {
      show(cache[key], index);
      return;
    }
    var url = config.wordUrl + '?w=' + encodeURIComponent(surface) + '&prev=' + encodeURIComponent(previous);
    fetch(url, { headers: { Accept: 'application/json' }, credentials: 'same-origin' })
      .then(function (response) {
        if (!response.ok) { throw new Error(String(response.status)); }
        return response.json();
      })
      .then(function (data) {
        cache[key] = data;
        if (ticket === state.request) { show(data, index); }
      })
      .catch(function () {
        if (ticket !== state.request) { return; }
        els.body.textContent = '';
        els.body.appendChild(el('p', 'text-danger mb-0', S.error));
      });
  }

  function show(data, index) {
    els.body.textContent = '';
    var head = el('div', 'reader-panel-head');
    head.appendChild(el('span', 'reader-panel-word', data.word || '—'));
    if (data.word) {
      var listen = el('button', 'btn-speak btn-speak-sm', '🔊');
      listen.type = 'button';
      listen.setAttribute('data-say', data.word);
      listen.setAttribute('aria-label', S.listen + ': ' + data.word);
      listen.title = S.listen;
      head.appendChild(listen);
    }
    els.body.appendChild(head);
    if (data.transcription) {
      var sound = el('div', 'reader-panel-sound',
                     (data.transcription.certain ? '' : '≈ ') + '[' + data.transcription.ipa + ']' +
                     (data.transcription.cyrillic ? ' · ' + data.transcription.cyrillic : ''));
      if (!data.transcription.certain) { sound.title = S.approximate; }
      els.body.appendChild(sound);
    }

    if (!data.readings.length && !data.groups.length) {
      els.body.appendChild(el('p', 'text-muted mb-0', S.nothing));
      return;
    }

    data.readings.forEach(function (reading) { els.body.appendChild(readingCard(reading)); });

    var title = el('div', 'reader-panel-title', S.synonyms);
    title.setAttribute('role', 'heading');
    title.setAttribute('aria-level', '2');
    els.body.appendChild(title);
    if (!data.groups.length) {
      els.body.appendChild(el('p', 'text-muted small', S.noSynonyms));
      return;
    }
    data.groups.forEach(function (group) {
      var box = el('div', 'reader-group');
      // The thesaurus's note on the meaning ("anatomia"), and the word the
      // group belongs to when the click had several readings.
      var label = [];
      if (data.readings.length > 1) { label.push(group.lemma); }
      if (group.gloss) { label.push(group.gloss); }
      if (label.length) { box.appendChild(el('div', 'reader-group-label', label.join(' · '))); }
      var list = el('div', 'reader-chips');
      group.items.forEach(function (item) { list.appendChild(chip(item, data.word, index)); });
      box.appendChild(list);
      els.body.appendChild(box);
    });
  }

  function readingCard(reading) {
    var card = el('div', 'reader-reading');
    var title = el('div', 'reader-reading-title');
    title.appendChild(el('strong', null, reading.lemma));
    if (reading.part_of_speech) { title.appendChild(el('span', 'text-muted small', reading.part_of_speech)); }
    card.appendChild(title);
    if (reading.form) { card.appendChild(el('div', 'reader-reading-form', reading.form)); }
    if (reading.translation) { card.appendChild(el('div', 'reader-reading-translation', reading.translation)); }
    var links = el('div', 'reader-reading-links');
    if (reading.url) { links.appendChild(link(reading.url, S.dictionary)); }
    if (reading.conjugation_url) { links.appendChild(link(reading.conjugation_url, S.conjugation)); }
    if (reading.save_url) { links.appendChild(saveButton(reading)); }
    if (links.childNodes.length) { card.appendChild(links); }
    return card;
  }

  function link(href, text) {
    var a = el('a', 'btn btn-sm btn-outline-secondary', text);
    a.href = href;
    return a;
  }

  function saveButton(reading) {
    var button = el('button', 'btn btn-sm btn-outline-info', reading.saved ? S.saved : S.save);
    button.type = 'button';
    button.disabled = !!reading.saved;
    button.addEventListener('click', function () {
      var token = document.getElementById('csrf_token');
      var body = new URLSearchParams();
      if (token) { body.append('csrf_token', token.value); }
      button.disabled = true;
      fetch(reading.save_url, { method: 'POST', body: body, credentials: 'same-origin' })
        .then(function (response) {
          if (!response.ok) { throw new Error(String(response.status)); }
          button.textContent = S.saved;
          reading.saved = true;
        })
        .catch(function () { button.disabled = false; });
    });
    return button;
  }

  function chip(item, core, index) {
    if (READ_ONLY) {
      // The text is the author's: show the synonyms, don't swap them in.
      var tag = el('span', 'reader-chip is-static');
      tag.appendChild(el('span', 'reader-chip-text', item.text));
      if (item.register) { tag.appendChild(el('span', 'reader-chip-register', item.register)); }
      if (item.translation) { tag.appendChild(el('span', 'reader-chip-translation', item.translation)); }
      return tag;
    }
    var button = el('button', 'reader-chip');
    button.type = 'button';
    button.appendChild(el('span', 'reader-chip-text', item.text));
    if (item.register) { button.appendChild(el('span', 'reader-chip-register', item.register)); }
    if (item.translation) { button.appendChild(el('span', 'reader-chip-translation', item.translation)); }
    button.title = S.replace.replace('{text}', item.text);
    button.setAttribute('aria-label', button.title);

    // Hover or focus: see it in the sentence first.
    function preview(on) {
      var span = words()[index];
      if (!span) { return; }
      var chunk = chunks(current()).filter(function (c) { return !/^\s+$/.test(c); })[index];
      span.textContent = on ? replaceIn(chunk, core, item.text) : chunk;
      span.classList.toggle('is-preview', on);
    }
    button.addEventListener('mouseenter', function () { preview(true); });
    button.addEventListener('mouseleave', function () { preview(false); });
    button.addEventListener('focus', function () { preview(true); });
    button.addEventListener('blur', function () { preview(false); });
    button.addEventListener('click', function () { replace(index, core, item.text); });
    return button;
  }

  function replace(index, core, replacement) {
    var parts = chunks(current());
    var seen = -1;
    var before = null;
    for (var i = 0; i < parts.length; i++) {
      if (/^\s+$/.test(parts[i])) { continue; }
      seen += 1;
      if (seen === index) {
        before = parts[i];
        parts[i] = replaceIn(parts[i], core, replacement);
        break;
      }
    }
    if (before === null) { return; }
    state.history.push({ text: parts.join(''), from: before, to: parts[i] });
    save();
    render();
    select(index);
  }

  // -- read mode: wrap the words already on the page --------------------------------------
  function wrapWords() {
    var index = 0;
    els.text.querySelectorAll('[data-words]').forEach(function (node) {
      var text = node.textContent;
      node.textContent = '';
      chunks(text).forEach(function (chunk) {
        if (/^\s+$/.test(chunk)) {
          node.appendChild(document.createTextNode(chunk));
          return;
        }
        var span = el('span', 'reader-word', chunk);
        span.setAttribute('data-i', String(index));
        node.appendChild(span);
        index += 1;
      });
    });
  }

  // -- controls --------------------------------------------------------------------------------
  function wireTextControls() {
  els.start.addEventListener('click', function () { start(els.source.value); });
  els.example.addEventListener('click', function () {
    els.source.value = config.example;
    start(config.example);
  });
  els.edit.addEventListener('click', function () {
    els.source.value = current();
    els.view.hidden = true;
    els.input.hidden = false;
    showEmpty();
    els.source.focus();
  });
  els.undo.addEventListener('click', function () {
    if (state.history.length < 2) { return; }
    state.history.pop();
    save();
    render();
    if (state.active >= 0) { select(state.active); }
  });
  els.copy.addEventListener('click', function () {
    var text = current();
    var done = function () {
      var old = els.copy.textContent;
      els.copy.textContent = S.copied;
      setTimeout(function () { els.copy.textContent = old; }, 1500);
    };
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(done, function () {});
    }
  });
  }

  if (READ_ONLY) {
    wrapWords();
    // Pages that put Catalan text on the page later (the translator) wrap it again.
    window.LearnCatalanReader = {
      rewrap: function () {
        state.active = -1;
        wrapWords();
        showEmpty();
      }
    };
  } else {
    wireTextControls();
  }

  els.text.addEventListener('click', function (event) {
    var span = event.target.closest ? event.target.closest('.reader-word') : null;
    if (span) { select(parseInt(span.getAttribute('data-i'), 10)); }
  });
  els.text.addEventListener('keydown', function (event) {
    var count = words().length;
    if (!count) { return; }
    if (event.key === 'ArrowRight') {
      event.preventDefault();
      select(state.active < 0 ? 0 : state.active + 1);
    } else if (event.key === 'ArrowLeft') {
      event.preventDefault();
      select(state.active < 0 ? 0 : state.active - 1);
    } else if (event.key === 'Enter' && state.active >= 0) {
      event.preventDefault();
      var first = els.body.querySelector('.reader-chip');
      if (first) { first.focus(); }
    }
  });
  els.body.addEventListener('keydown', function (event) {
    if (event.key === 'Escape') {
      closeSheet();
      els.text.focus();
    }
  });
  if (els.close) {
    els.close.addEventListener('click', function () {
      closeSheet();
      els.text.focus({ preventScroll: true });
    });
  }
  document.addEventListener('keydown', function (event) {
    if (event.key === 'Escape' && els.panel && els.panel.classList.contains('is-open')) { closeSheet(); }
  });

  // A text from an earlier visit comes back where it was left.
  var saved = READ_ONLY ? null : load();
  if (saved) {
    state.history = saved;
    els.input.hidden = true;
    els.view.hidden = false;
    render();
  }
})();
