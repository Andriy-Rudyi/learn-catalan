/* /c1/frases-fetes: filter the list, mark phrases as known (kept in this
 * browser) and practise: "what does this phrase mean?" and "which phrase
 * means this?", on the phrases the filter shows. */
(function () {
  'use strict';

  var configNode = document.getElementById('phrases-config');
  if (!configNode) { return; }
  var config = JSON.parse(configNode.textContent);
  var S = config.strings;
  var STORE = 'learn-catalan:c1-phrases-known:v1';
  var ROUND = 10;
  var search = document.getElementById('phrase-search');
  var theme = document.getElementById('phrase-theme');
  var unknownOnly = document.getElementById('phrase-unknown');
  var quiz = document.getElementById('phrase-quiz');
  var list = document.getElementById('phrase-list');
  if (!search) { return; }

  var items = config.phrases.map(function (ca, i) {
    return { ca: ca, meaning: config.meanings[i], theme: config.themes[i] };
  });

  function el(tag, className, text) {
    var node = document.createElement(tag);
    if (className) { node.className = className; }
    if (text !== undefined) { node.textContent = text; }
    return node;
  }

  function shuffle(array) {
    array = array.slice();
    for (var i = array.length - 1; i > 0; i--) {
      var j = Math.floor(Math.random() * (i + 1));
      var t = array[i]; array[i] = array[j]; array[j] = t;
    }
    return array;
  }

  function loadKnown() {
    try { return JSON.parse(window.localStorage.getItem(STORE) || '{}') || {}; } catch (e) { return {}; }
  }

  function saveKnown(known) {
    try { window.localStorage.setItem(STORE, JSON.stringify(known)); } catch (e) { /* private window */ }
  }

  function normal(text) {
    return (text || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '');
  }

  // -- the list --------------------------------------------------------------------------------
  function visible() {
    var query = normal(search.value.trim());
    var wanted = theme.value;
    var known = loadKnown();
    return items.filter(function (item) {
      if (wanted && item.theme !== wanted) { return false; }
      if (unknownOnly.checked && known[item.ca]) { return false; }
      return !query || normal(item.ca).indexOf(query) >= 0 || normal(item.meaning).indexOf(query) >= 0;
    });
  }

  function filter() {
    var shown = {};
    visible().forEach(function (item) { shown[item.ca] = true; });
    list.querySelectorAll('.course-phrase').forEach(function (node) {
      node.hidden = !shown[node.getAttribute('data-phrase')];
    });
    list.querySelectorAll('.course-theme').forEach(function (section) {
      section.hidden = !section.querySelector('.course-phrase:not([hidden])');
    });
  }

  var known = loadKnown();
  list.querySelectorAll('[data-known]').forEach(function (box) {
    box.checked = !!known[box.getAttribute('data-known')];
    box.addEventListener('change', function () {
      var current = loadKnown();
      if (box.checked) { current[box.getAttribute('data-known')] = true; } else { delete current[box.getAttribute('data-known')]; }
      saveKnown(current);
      if (unknownOnly.checked) { filter(); }
    });
  });
  search.addEventListener('input', filter);
  theme.addEventListener('change', filter);
  unknownOnly.addEventListener('change', filter);

  // -- practice --------------------------------------------------------------------------------------
  var round = null;

  function startPractice() {
    var pool = visible();
    quiz.classList.remove('d-none');
    quiz.textContent = '';
    if (pool.length < 4) {
      quiz.appendChild(el('p', 'mb-0', S.few));
      return;
    }
    round = { pool: pool, questions: shuffle(pool).slice(0, ROUND), index: 0, score: 0 };
    show();
    quiz.scrollIntoView({ block: 'nearest' });
  }

  function options(answer, field) {
    // Three wrong answers, from the same theme when there are enough.
    var same = round.pool.filter(function (p) { return p !== answer && p.theme === answer.theme; });
    var others = round.pool.filter(function (p) { return p !== answer && p.theme !== answer.theme; });
    var wrong = shuffle(same).concat(shuffle(others)).slice(0, 3);
    return shuffle([answer].concat(wrong)).map(function (p) { return { item: p, label: p[field] }; });
  }

  function show() {
    quiz.textContent = '';
    if (round.index >= round.questions.length) { return finish(); }
    var answer = round.questions[round.index];
    var reverse = round.index % 2 === 1;
    quiz.appendChild(el('div', 'small text-muted mb-1',
      (round.index + 1) + ' / ' + round.questions.length));
    quiz.appendChild(el('p', 'fw-semibold mb-1', reverse ? S.which : S.meaning));
    var target = el('div', 'course-quiz-target', reverse ? answer.meaning : answer.ca);
    if (!reverse) { target.lang = 'ca'; }
    quiz.appendChild(target);
    var box = el('div', 'trainer-options');
    options(answer, reverse ? 'ca' : 'meaning').forEach(function (option) {
      var button = el('button', 'trainer-option', option.label);
      if (reverse) { button.lang = 'ca'; }
      button.type = 'button';
      button.addEventListener('click', function () {
        var ok = option.item === answer;
        if (ok) { round.score += 1; }
        box.querySelectorAll('button').forEach(function (other) { other.disabled = true; });
        button.classList.add(ok ? 'is-right' : 'is-wrong');
        if (!ok) {
          box.querySelectorAll('button').forEach(function (other) {
            if (other.textContent === (reverse ? answer.ca : answer.meaning)) { other.classList.add('is-right'); }
          });
        }
        var feedback = el('div', 'trainer-feedback ' + (ok ? 'is-ok' : 'is-no'));
        feedback.appendChild(el('strong', null, ok ? S.right : S.wrong + ' '));
        if (!ok) {
          var right = el('span', null, answer.ca + ' – ' + answer.meaning);
          feedback.appendChild(right);
        }
        quiz.appendChild(feedback);
        var go = el('button', 'btn btn-info mt-3', round.index + 1 >= round.questions.length ? S.finish : S.next);
        go.type = 'button';
        go.addEventListener('click', function () { round.index += 1; show(); });
        quiz.appendChild(go);
        go.focus();
      });
      box.appendChild(button);
    });
    quiz.appendChild(box);
  }

  function finish() {
    var box = el('div', 'trainer-done');
    box.appendChild(el('div', 'trainer-big', round.score + ' / ' + round.questions.length));
    var again = el('button', 'btn btn-info me-2', S.again);
    again.type = 'button';
    again.addEventListener('click', startPractice);
    var close = el('button', 'btn btn-outline-secondary', S.close);
    close.type = 'button';
    close.addEventListener('click', function () { quiz.classList.add('d-none'); quiz.textContent = ''; });
    box.appendChild(again);
    box.appendChild(close);
    quiz.appendChild(box);
  }

  document.getElementById('phrase-practice').addEventListener('click', startPractice);
})();
