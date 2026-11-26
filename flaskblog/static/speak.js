/* "Listen" buttons: <button class="btn-speak" data-say="text">, with
 * data-lang="en" (es, fr, de, uk...) for a word of another language section;
 * Catalan by default.
 *
 * Uses the browser's own speech synthesis with a Catalan voice, so nothing is
 * sent to an outside service. Without a Catalan voice on the device we do not
 * fall back to another language (a Spanish voice reading Catalan teaches the
 * wrong sounds); instead we explain how to install one.
 */
(function () {
  if (!('speechSynthesis' in window)) {
    // Also hides buttons added later (the text page draws its own).
    document.documentElement.classList.add('no-speech');
    return;
  }

  function voiceFor(lang) {
    var voices = window.speechSynthesis.getVoices();
    var matching = voices.filter(function (voice) {
      return voice.lang && voice.lang.toLowerCase().replace('_', '-').split('-')[0] === lang;
    });
    // Prefer voices installed on the device (they work offline).
    matching.sort(function (a, b) { return (b.localService ? 1 : 0) - (a.localService ? 1 : 0); });
    return matching[0] || null;
  }

  // Chrome fills the voice list asynchronously; asking early starts loading.
  window.speechSynthesis.getVoices();

  function showHint() {
    var hint = document.getElementById('speak-hint');
    if (!hint) {
      hint = document.createElement('div');
      hint.id = 'speak-hint';
      hint.className = 'alert alert-warning alert-dismissible fade show speak-hint';
      hint.setAttribute('role', 'status');
      hint.innerHTML = (window.SPEAK_HINT || '') +
        '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="×"></button>';
      document.body.appendChild(hint);
    }
  }

  // One listener for every button, including ones added after the page loaded.
  document.addEventListener('click', function (event) {
    var button = event.target.closest ? event.target.closest('.btn-speak') : null;
    if (!button) { return; }
    var lang = button.getAttribute('data-lang') || 'ca';
    var voice = voiceFor(lang);
    // The hint explains how to install a Catalan voice; other languages have
    // a voice on almost every device, so the browser picks one.
    if (!voice && lang === 'ca') { showHint(); return; }
    window.speechSynthesis.cancel();
    var utterance = new SpeechSynthesisUtterance(button.getAttribute('data-say'));
    if (voice) { utterance.voice = voice; }
    utterance.lang = voice ? voice.lang : lang;
    utterance.rate = 0.85;
    button.classList.add('speaking');
    utterance.onend = utterance.onerror = function () { button.classList.remove('speaking'); };
    window.speechSynthesis.speak(utterance);
  });
})();
