/* /c1/monologue: a monologue of about six minutes.
 *
 * Pick a topic card, take a few minutes to prepare, then speak against the
 * clock: the timer says when to move from the introduction to the body and
 * when to wrap up. With the microphone on, the talk is recorded in the
 * browser (MediaRecorder) so it can be played back or saved; the recording
 * never leaves the device.
 */
(function () {
  'use strict';

  var configNode = document.getElementById('mono-config');
  if (!configNode) { return; }
  var config = JSON.parse(configNode.textContent);
  var S = config.strings;
  var TOTAL = config.minutes * 60;
  var els = {
    topic: document.getElementById('mono-topic'),
    random: document.getElementById('mono-random'),
    title: document.getElementById('mono-title'),
    points: document.getElementById('mono-points'),
    prep: document.getElementById('mono-prep'),
    record: document.getElementById('mono-record'),
    phase: document.getElementById('mono-phase'),
    clock: document.getElementById('mono-clock'),
    bar: document.getElementById('mono-bar'),
    start: document.getElementById('mono-start'),
    stop: document.getElementById('mono-stop'),
    result: document.getElementById('mono-result')
  };
  var timer = null;
  var recorder = null;
  var chunks = [];
  var stream = null;
  var spokenSeconds = 0;

  function el(tag, className, text) {
    var node = document.createElement(tag);
    if (className) { node.className = className; }
    if (text !== undefined) { node.textContent = text; }
    return node;
  }

  function clock(seconds) {
    seconds = Math.max(0, Math.round(seconds));
    return Math.floor(seconds / 60) + ':' + ('0' + seconds % 60).slice(-2);
  }

  function showTopic() {
    var topic = config.topics[Number(els.topic.value)];
    els.title.textContent = topic[0];
    els.points.textContent = '';
    topic[1].forEach(function (point) { els.points.appendChild(el('li', null, point)); });
  }

  // Phase of the talk, as a share of the time: introduction, body, ending.
  function phaseAt(elapsed) {
    if (elapsed < TOTAL / 6) { return S.intro; }
    if (elapsed < TOTAL - 60) { return S.body; }
    return S.end;
  }

  function stopTimer() {
    if (timer) { window.clearInterval(timer); timer = null; }
  }

  function countdown(seconds, onTick, onDone) {
    var end = Date.now() + seconds * 1000;
    onTick(seconds);
    timer = window.setInterval(function () {
      var left = (end - Date.now()) / 1000;
      if (left <= 0) {
        stopTimer();
        onTick(0);
        onDone();
      } else {
        onTick(left);
      }
    }, 250);
  }

  function startRecording() {
    if (!els.record.checked || !navigator.mediaDevices || !window.MediaRecorder) {
      if (els.record.checked) { els.result.appendChild(el('p', 'small text-muted', S.noMic)); }
      return Promise.resolve();
    }
    return navigator.mediaDevices.getUserMedia({ audio: true }).then(function (media) {
      stream = media;
      chunks = [];
      recorder = new MediaRecorder(media);
      recorder.ondataavailable = function (event) { if (event.data.size) { chunks.push(event.data); } };
      recorder.onstop = showRecording;
      recorder.start();
    }, function () {
      els.result.appendChild(el('p', 'small text-muted', S.noMic));
    });
  }

  function showRecording() {
    if (stream) { stream.getTracks().forEach(function (track) { track.stop(); }); stream = null; }
    if (!chunks.length) { return; }
    var blob = new Blob(chunks, { type: chunks[0].type || 'audio/webm' });
    var url = URL.createObjectURL(blob);
    var box = el('div', 'course-recording');
    box.appendChild(el('p', 'small mb-1', S.listen));
    var audio = el('audio');
    audio.controls = true;
    audio.src = url;
    box.appendChild(audio);
    var link = el('a', 'btn btn-sm btn-outline-secondary mt-2', S.download);
    link.href = url;
    link.download = 'monoleg.' + (blob.type.indexOf('ogg') >= 0 ? 'ogg' : blob.type.indexOf('mp4') >= 0 ? 'm4a' : 'webm');
    box.appendChild(link);
    els.result.appendChild(box);
  }

  function speak() {
    var started = Date.now();
    startRecording().then(function () {
      countdown(TOTAL, function (left) {
        var elapsed = TOTAL - left;
        spokenSeconds = (Date.now() - started) / 1000;
        els.phase.textContent = phaseAt(elapsed);
        els.clock.textContent = clock(left);
        els.bar.style.width = (100 * elapsed / TOTAL) + '%';
        els.clock.classList.toggle('is-ending', left <= 60);
      }, function () {
        els.phase.textContent = S.done;
        finish();
      });
    });
  }

  function start() {
    els.result.textContent = '';
    els.start.disabled = true;
    els.stop.disabled = false;
    els.topic.disabled = els.random.disabled = els.prep.disabled = els.record.disabled = true;
    spokenSeconds = 0;
    var prep = Number(els.prep.value);
    if (prep > 0) {
      countdown(prep, function (left) {
        els.phase.textContent = S.prep;
        els.clock.textContent = clock(left);
        els.bar.style.width = (100 * (prep - left) / prep) + '%';
      }, speak);
    } else {
      speak();
    }
  }

  function finish() {
    stopTimer();
    if (recorder && recorder.state !== 'inactive') { recorder.stop(); }
    recorder = null;
    els.start.disabled = false;
    els.stop.disabled = true;
    els.topic.disabled = els.random.disabled = els.prep.disabled = els.record.disabled = false;
    if (spokenSeconds > 0) {
      els.result.insertBefore(el('p', 'mb-2', S.stopped.replace('{time}', clock(spokenSeconds))),
                              els.result.firstChild);
    }
    els.clock.classList.remove('is-ending');
  }

  els.topic.addEventListener('change', showTopic);
  els.random.addEventListener('click', function () {
    els.topic.value = String(Math.floor(Math.random() * config.topics.length));
    showTopic();
  });
  els.start.addEventListener('click', start);
  els.stop.addEventListener('click', function () {
    if (els.phase.textContent === S.prep) {
      // Stopped while preparing: nothing was said yet.
      spokenSeconds = 0;
      els.phase.textContent = S.ready;
      els.clock.textContent = clock(TOTAL);
      els.bar.style.width = '0';
    }
    finish();
  });
  showTopic();
})();
