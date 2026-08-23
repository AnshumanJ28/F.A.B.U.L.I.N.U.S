// speech.js — thin wrapper around the Web Speech API.
// Exposes window.VoiceInput with start/stop and callback hooks.

(function () {
  const SpeechRecognitionImpl = window.SpeechRecognition || window.webkitSpeechRecognition;

  function VoiceInput() {
    this.supported = !!SpeechRecognitionImpl;
    this.recognizing = false;
    this.lang = "en-US";
    this.onstart = null;
    this.onresult = null; // (transcript, isFinal) => void
    this.onend = null;
    this.onerror = null;

    if (this.supported) {
      this.recognition = new SpeechRecognitionImpl();
      this.recognition.continuous = false;
      this.recognition.interimResults = true;
      this.recognition.maxAlternatives = 1;

      this.recognition.onstart = () => {
        this.recognizing = true;
        if (this.onstart) this.onstart();
      };

      this.recognition.onresult = (event) => {
        let finalTranscript = "";
        let interimTranscript = "";
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const res = event.results[i];
          if (res.isFinal) {
            finalTranscript += res[0].transcript;
          } else {
            interimTranscript += res[0].transcript;
          }
        }
        if (this.onresult) {
          if (finalTranscript) this.onresult(finalTranscript.trim(), true);
          else this.onresult(interimTranscript.trim(), false);
        }
      };

      this.recognition.onend = () => {
        this.recognizing = false;
        if (this.onend) this.onend();
      };

      this.recognition.onerror = (event) => {
        this.recognizing = false;
        if (this.onerror) this.onerror(event.error);
      };
    }
  }

  VoiceInput.prototype.setLang = function (lang) {
    this.lang = lang;
    if (this.recognition) this.recognition.lang = lang;
  };

  VoiceInput.prototype.start = function () {
    if (!this.supported || this.recognizing) return;
    this.recognition.lang = this.lang;
    try {
      this.recognition.start();
    } catch (e) {
      // start() throws if called while already starting; ignore
    }
  };

  VoiceInput.prototype.stop = function () {
    if (!this.supported || !this.recognizing) return;
    this.recognition.stop();
  };

  window.VoiceInput = VoiceInput;
})();
