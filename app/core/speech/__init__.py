"""Lightweight, dependency-free speech helpers.

Text-to-speech is implemented here using the browser's built-in
``SpeechSynthesis`` Web API via an embedded HTML/JS snippet (rendered with
``st.components.v1.html``). It needs no API key, works offline, and runs
entirely on the user's device.

Speech-to-text (voice questions) is a natural follow-up: modern Gemini
models accept audio input directly, so a future version could let kids
upload or record a short clip and send it to
:class:`app.core.providers.gemini.GeminiProvider` for transcription. That is
intentionally left out of this starter to avoid adding a fragile custom
Streamlit component.
"""

from __future__ import annotations

import json
import re

_MARKDOWN_NOISE = re.compile(r"[*_#>`]+")
_CODE_BLOCK = re.compile(r"```.*?```", re.S)
_LINK = re.compile(r"\[([^\]]*)\]\([^)]*\)")
_WHITESPACE = re.compile(r"\s+")


def clean_text_for_speech(text: str) -> str:
    """Strip Markdown syntax so it doesn't get read aloud literally."""

    text = _CODE_BLOCK.sub(" ", text or "")
    text = _LINK.sub(r"\1", text)
    text = _MARKDOWN_NOISE.sub(" ", text)
    return _WHITESPACE.sub(" ", text).strip()


def text_to_speech_html(text: str, lang: str = "en-US", rate: float = 0.95, label: str = "Read it aloud") -> str:
    """Return an HTML/JS snippet with a button that reads ``text`` aloud.

    Render it with ``st.components.v1.html(html, height=64)``. Uses the
    browser's ``speechSynthesis`` API, so it needs no network access and no
    API key. If the browser doesn't support it, the button is disabled with
    a short explanatory note.
    """

    spoken = clean_text_for_speech(text)
    payload = json.dumps(spoken)
    js_lang = json.dumps(lang or "en-US")
    js_rate = json.dumps(max(0.5, min(rate, 1.5)))

    return f"""
<div style="display:flex;align-items:center;gap:0.6rem;font-family:'Source Sans Pro',sans-serif;">
  <button id="tts-btn" type="button" style="
    border:1px solid rgba(0,0,0,0.15);
    border-radius:999px;
    padding:0.4rem 0.9rem;
    background:#ffffff;
    cursor:pointer;
    font-size:0.9rem;
  ">🔊 {label}</button>
  <span id="tts-status" style="font-size:0.8rem;color:#6b7280;"></span>
</div>
<script>
(function() {{
  const text = {payload};
  const lang = {js_lang};
  const rate = {js_rate};
  const btn = document.getElementById('tts-btn');
  const status = document.getElementById('tts-status');

  if (!('speechSynthesis' in window) || !text) {{
    btn.disabled = true;
    btn.style.opacity = '0.5';
    status.textContent = !text ? '' : 'Voice playback is not supported in this browser.';
    return;
  }}

  btn.addEventListener('click', function() {{
    if (window.speechSynthesis.speaking) {{
      window.speechSynthesis.cancel();
      status.textContent = '';
      return;
    }}
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = lang;
    utterance.rate = rate;
    utterance.onstart = function() {{ status.textContent = 'Playing… click again to stop.'; }};
    utterance.onend = function() {{ status.textContent = ''; }};
    utterance.onerror = function() {{ status.textContent = 'Could not play audio.'; }};
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(utterance);
  }});
}})();
</script>
"""
