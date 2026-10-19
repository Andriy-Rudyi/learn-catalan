/* /translator: Catalan <-> Ukrainian, English, French (flaskblog/translator).
 *
 * The Catalan side (the text or its translation) is put in #reader-text,
 * where reader.js makes every word clickable. A sentence that came out word
 * by word can be corrected; the correction goes to the translation memory.
 * Everything from the server goes on the page with textContent, never as
 * HTML. The last translations stay in this browser (localStorage).
 */
(function () {
  'use strict';

  var configNode = document.getElementById('translator-config');
  if (!configNode) { return; }
  var config = JSON.parse(configNode.textContent);
  var S = config.strings;
  var STORE = 'learn-catalan:translator:v1';
  var HISTORY = 20;

  var els = {
    form: document.getElementById('translator-form'),
    source: document.getElementById('translator-source'),
    target: document.getElementById('translator-target'),
    swap: document.getElementById('translator-swap'),
    text: document.getElementById('translator-text'),
    count: document.getElementById('translator-count'),
    say: document.getElementById('translator-say'),
    result: document.getElementById('translator-result'),
    sentences: document.getElementById('translator-sentences'),
    catalan: document.getElementById('reader-text'),
    copy: document.getElementById('translator-copy'),
    sayResult: document.getElementById('translator-say-result'),
    historyBox: document.getElementById('translator-history-box'),
    history: document.getElementById('translator-history'),
    historyClear: document.getElementById('translator-history-clear')
  };
  var last = null;

  function el(tag, className, text) {
    var node = document.createElement(tag);
    if (className) { node.className = className; }
    if (text !== undefined && text !== null) { node.textContent = text; }
    return node;
  }

  // -- languages: one side is always Catalan ------------------------------------------------
  function fixPair(changed) {
    var source = els.source.value;
    var target = els.target.value;
    if (source === target || (source !== 'ca' && target !== 'ca')) {
      if (changed === els.source) {
        els.target.value = source === 'ca' ? (last && last.other) || 'en' : 'ca';
      } else {
        els.source.value = target === 'ca' ? (last && last.other) || 'en' : 'ca';
      }
    }
    updateSay();
  }

  function updateSay() {
    var catalan = els.source.value === 'ca';
    els.say.hidden = !catalan || !els.text.value.trim();
    els.say.setAttribute('data-say', catalan ? els.text.value : '');
    els.count.textContent = els.text.value.length + ' / ' + config.max;
  }

  els.source.addEventListener('change', function () { fixPair(els.source); });
  els.target.addEventListener('change', function () { fixPair(els.target); });
  els.text.addEventListener('input', updateSay);
  els.swap.addEventListener('click', function () {
    var source = els.source.value;
    els.source.value = els.target.value;
    els.target.value = source;
    if (last && last.translation) { els.text.value = last.translation; }
    updateSay();
  });

  // -- translating -------------------------------------------------------------------------------
  els.form.addEventListener('submit', function (event) {
    event.preventDefault();
    run(els.text.value, els.source.value, els.target.value, true);
  });

  function run(text, source, target, remember) {
    text = (text || '').trim();
    if (!text) {
      els.text.focus();
      return;
    }
    els.result.hidden = false;
    els.sentences.textContent = '';
    els.catalan.hidden = true;
    els.sentences.appendChild(el('p', 'text-muted mb-0', '…'));
    fetch(config.runUrl, {
      method: 'POST',
      credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify({ text: text, source: source, target: target })
    })
      .then(function (response) {
        if (response.status === 429) { throw new Error('429'); }
        if (!response.ok) { throw new Error(String(response.status)); }
        return response.json();
      })
      .then(function (data) {
        show(data);
        if (remember) { remember_(text, data); }
      })
      .catch(function (error) {
        els.sentences.textContent = '';
        els.sentences.appendChild(el('p', 'text-danger mb-0', error.message === '429' ? S.tooMany : S.error));
      });
  }

  function translationOf(data) {
    return data.sentences.map(function (s) { return s.target; }).join(' ');
  }

  function show(data) {
    var translation = translationOf(data);
    last = {
      source: data.source,
      target: data.target,
      other: data.source === 'ca' ? data.target : data.source,
      translation: translation
    };
    els.sentences.textContent = '';
    data.sentences.forEach(function (sentence) { els.sentences.appendChild(sentenceCard(sentence, data)); });

    // The Catalan side, clickable word by word.
    var catalan = data.source === 'ca'
      ? data.sentences.map(function (s) { return s.source; })
      : data.sentences.map(function (s) { return s.target; });
    els.catalan.textContent = '';
    catalan.forEach(function (line) {
      var p = el('p', 'translator-catalan-line');
      p.setAttribute('data-words', '');
      p.textContent = line;
      els.catalan.appendChild(p);
    });
    els.catalan.hidden = false;
    if (window.LearnCatalanReader) { window.LearnCatalanReader.rewrap(); }

    var targetCatalan = data.target === 'ca';
    els.sayResult.hidden = !targetCatalan;
    els.sayResult.setAttribute('data-say', targetCatalan ? translation : '');
  }

  function sentenceCard(sentence, data) {
    var card = el('div', 'translator-sentence');
    var head = el('div', 'translator-sentence-head');
    head.appendChild(el('span', 'translator-source-text', sentence.source));
    var badge = el('span', 'translator-badge ' + (sentence.method === 'memory' ? 'is-memory' : 'is-words'),
                   sentence.method === 'memory' ? S.memory : S.words);
    head.appendChild(badge);
    card.appendChild(head);

    var line = el('div', 'translator-target-text');
    line.setAttribute('lang', data.target);
    if (sentence.tokens) {
      // Word by word: unknown words marked, each gloss with its dictionary meaning.
      sentence.tokens.forEach(function (token, index) {
        if (token.gloss === '') { return; }
        if (index > 0 && line.childNodes.length && !token.punct) { line.appendChild(document.createTextNode(' ')); }
        var text = token.gloss !== null && token.gloss !== undefined ? token.gloss : token.text;
        var piece;
        if (token.url) {
          piece = el('a', 'translator-gloss', text);
          piece.href = token.url;
        } else {
          piece = el('span', 'translator-gloss', text);
        }
        if (token.gloss === null || token.gloss === undefined) {
          piece.classList.add('is-unknown');
          piece.title = S.unknown;
        } else if (token.full || token.form) {
          piece.title = [token.lemma, token.form, token.full].filter(Boolean).join(' · ');
        }
        if (token.guess) { piece.classList.add('is-guess'); }
        line.appendChild(piece);
      });
      // Capital letter as the sentence has it.
      var first = line.firstChild;
      if (first && sentence.target) {
        first.textContent = sentence.target.charAt(0) + first.textContent.slice(1);
      }
    } else {
      line.textContent = sentence.target;
    }
    card.appendChild(line);

    if (sentence.similar) {
      var similar = el('div', 'translator-similar');
      similar.appendChild(el('span', 'text-muted', S.similar + ' '));
      similar.appendChild(el('span', null, sentence.similar.source));
      similar.appendChild(document.createTextNode(' → '));
      similar.appendChild(el('em', null, sentence.similar.target));
      card.appendChild(similar);
    }
    if (sentence.method !== 'memory' || sentence.origin === 'course') {
      card.appendChild(improveBox(sentence, data));
    }
    return card;
  }

  function improveBox(sentence, data) {
    var box = el('div', 'translator-improve');
    var open = el('button', 'btn btn-link btn-sm p-0', S.improve);
    open.type = 'button';
    box.appendChild(open);
    open.addEventListener('click', function () {
      if (!config.loggedIn) {
        box.textContent = '';
        var login = el('a', null, S.login);
        login.href = config.loginUrl;
        box.appendChild(login);
        return;
      }
      open.hidden = true;
      var input = el('textarea', 'form-control form-control-sm mb-2');
      input.rows = 2;
      input.maxLength = 1000;
      input.value = sentence.target;
      input.setAttribute('lang', data.target);
      var send = el('button', 'btn btn-sm btn-info me-2', S.send);
      send.type = 'button';
      var cancel = el('button', 'btn btn-sm btn-outline-secondary', S.cancel);
      cancel.type = 'button';
      box.appendChild(input);
      box.appendChild(send);
      box.appendChild(cancel);
      input.focus();
      cancel.addEventListener('click', function () {
        box.replaceWith(improveBox(sentence, data));
      });
      send.addEventListener('click', function () {
        var text = input.value.trim();
        if (!text) { return; }
        var body = new URLSearchParams();
        var token = document.getElementById('csrf_token');
        if (token) { body.append('csrf_token', token.value); }
        body.append('source', data.source);
        body.append('target', data.target);
        body.append('source_text', sentence.source);
        body.append('target_text', text);
        send.disabled = true;
        fetch(config.suggestUrl, { method: 'POST', body: body, credentials: 'same-origin' })
          .then(function (response) {
            if (!response.ok) { throw new Error(String(response.status)); }
            return response.json();
          })
          .then(function (result) {
            box.textContent = '';
            box.appendChild(el('span', 'text-success small', result.status === 'approved' ? S.saved : S.thanks));
          })
          .catch(function () { send.disabled = false; });
      });
    });
    return box;
  }

  els.copy.addEventListener('click', function () {
    if (!last || !navigator.clipboard) { return; }
    navigator.clipboard.writeText(last.translation).then(function () {
      var old = els.copy.textContent;
      els.copy.textContent = S.copied;
      setTimeout(function () { els.copy.textContent = old; }, 1500);
    }, function () {});
  });

  // -- history (this browser only) -----------------------------------------------------------
  function loadHistory() {
    try {
      var data = JSON.parse(window.localStorage.getItem(STORE) || '[]');
      return Array.isArray(data) ? data : [];
    } catch (e) {
      return [];
    }
  }

  function saveHistory(items) {
    try {
      window.localStorage.setItem(STORE, JSON.stringify(items.slice(0, HISTORY)));
    } catch (e) { /* private window: no history */ }
  }

  function remember_(text, data) {
    var items = loadHistory().filter(function (item) {
      return !(item.text === text && item.source === data.source && item.target === data.target);
    });
    items.unshift({ text: text, source: data.source, target: data.target, translation: translationOf(data) });
    saveHistory(items);
    renderHistory();
  }

  function renderHistory() {
    var items = loadHistory();
    els.history.textContent = '';
    els.historyBox.hidden = !items.length;
    items.forEach(function (item) {
      var li = el('li');
      var button = el('button', 'translator-history-item');
      button.type = 'button';
      button.appendChild(el('span', 'translator-history-langs', item.source + ' → ' + item.target));
      button.appendChild(el('span', 'translator-history-text', item.text));
      button.appendChild(el('span', 'translator-history-result', item.translation));
      button.addEventListener('click', function () {
        els.source.value = item.source;
        els.target.value = item.target;
        els.text.value = item.text;
        updateSay();
        run(item.text, item.source, item.target, false);
      });
      li.appendChild(button);
      els.history.appendChild(li);
    });
  }

  els.historyClear.addEventListener('click', function () {
    saveHistory([]);
    renderHistory();
  });

  renderHistory();
  updateSay();
})();
