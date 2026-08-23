(function () {
  "use strict";

  const API_BASE = window.VSA_API_BASE || "";
  const SID = Math.random().toString(36).substring(2, 15);

  function getUrl(path) {
    return API_BASE + path + "?sid=" + SID;
  }

  const orb = document.getElementById("orb");
  const orbStatus = document.getElementById("orb-status");
  const transcriptEl = document.getElementById("transcript");
  const textForm = document.getElementById("text-fallback");
  const textInput = document.getElementById("text-input");
  const langSelect = document.getElementById("lang-select");
  const toastRegion = document.getElementById("toast-region");
  const suggestionsList = document.getElementById("suggestions-list");
  const listCategories = document.getElementById("list-categories");
  const searchPanel = document.getElementById("search-panel");
  const searchResults = document.getElementById("search-results");

  let expandedCategories = [];
  let voice = null;

  window.sendCommand = async function(text) {
    if (!text) return;
    setOrbState("processing");
    try {
      const res = await fetch(getUrl("/api/command"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: text, expanded_categories: expandedCategories }),
      });
      if (!res.ok) throw new Error("Command failed");
      const data = await res.json();
      
      listCategories.innerHTML = data.list_html;
      window.currentList = data.list;
      
      data.messages.forEach(msg => {
          showToast(msg.text, msg.type === "error");
      });
      refreshSuggestions();
    } catch (e) {
      showToast("Couldn't reach the backend server", true);
    } finally {
      setOrbState("idle");
    }
  };

  window.toggleCategory = function(cat) {
    if (expandedCategories.includes(cat)) {
      expandedCategories = expandedCategories.filter(c => c !== cat);
    } else {
      expandedCategories.push(cat);
    }
    refreshState();
  };

  function setOrbState(state) {
    orb.classList.remove("is-listening", "is-processing");
    orb.setAttribute("aria-pressed", state === "listening" ? "true" : "false");
    if (state === "listening") {
      orb.classList.add("is-listening");
      orbStatus.textContent = "Listening…";
    } else if (state === "processing") {
      orb.classList.add("is-processing");
      orbStatus.textContent = "Thinking…";
    } else {
      orbStatus.textContent = "Tap the orb or type below";
    }
  }

  function showToast(message, isError) {
    const t = document.createElement("div");
    t.className = "toast" + (isError ? " toast-error" : "");
    t.textContent = message;
    toastRegion.appendChild(t);
    setTimeout(() => t.remove(), 3200);
  }

  async function refreshState() {
    try {
      const res = await fetch(getUrl("/api/state"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ expanded_categories: expandedCategories }),
      });
      const data = await res.json();
      listCategories.innerHTML = data.list_html;
      window.currentList = data.list; // For download function
    } catch (e) {
      console.error(e);
    }
  }

  async function refreshSuggestions() {
    try {
      const res = await fetch(getUrl("/api/suggest"));
      const data = await res.json();
      suggestionsList.innerHTML = data.sug_html;
    } catch (e) {
      console.error(e);
    }
  }

  // Handlers

  voice = new VoiceInput();
  if (!voice.supported) {
    orbStatus.textContent = "Voice input not supported here — use the text field below";
  }
  voice.setLang(langSelect.value);

  voice.onstart = () => setOrbState("listening");
  voice.onresult = (text, isFinal) => {
    transcriptEl.textContent = text;
    if (isFinal) sendCommand(text);
  };
  voice.onend = () => {
    if (!orb.classList.contains("is-processing")) setOrbState("idle");
  };
  voice.onerror = (err) => {
    setOrbState("idle");
    if (err !== "no-speech" && err !== "aborted") showToast("Mic error: " + err, true);
  };

  orb.addEventListener("click", () => {
    if (!voice.supported) return;
    if (voice.recognizing) {
      voice.stop();
    } else {
      transcriptEl.textContent = "";
      voice.start();
    }
  });

  langSelect.addEventListener("change", () => voice.setLang(langSelect.value));

  textForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const text = textInput.value.trim();
    if (!text) return;
    transcriptEl.textContent = text;
    textInput.value = "";
    
    if (text.toLowerCase() === "clear list") {
      fetch(getUrl("/api/clear"), { 
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ expanded_categories: expandedCategories })
      })
        .then(r => r.json())
        .then(data => {
            window.currentList = data.list;
            listCategories.innerHTML = data.list_html;
            showToast("List cleared");
            refreshSuggestions();
        });
      return;
    }
    
    sendCommand(text);
  });

  const downloadListBtn = document.getElementById("download-list-btn");
  if (downloadListBtn) {
    downloadListBtn.addEventListener("click", () => {
      if (!window.currentList || window.currentList.length === 0) {
        showToast("Your list is empty", true);
        return;
      }
      window.location.href = getUrl("/api/download");
    });
  }

  const clearListBtn = document.getElementById("clear-list-btn");
  if (clearListBtn) {
    clearListBtn.addEventListener("click", () => {
      if (window.currentList.length === 0) {
        showToast("Your list is already empty", true);
        return;
      }
      if (confirm("Are you sure you want to clear your entire list?")) {
        fetch(getUrl("/api/clear"), { 
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ expanded_categories: expandedCategories })
        })
          .then(r => r.json())
          .then(data => {
              window.currentList = data.list;
              listCategories.innerHTML = data.list_html;
              showToast("List cleared");
              refreshSuggestions();
          });
      }
    });
  }

  setOrbState("idle");
  refreshState();
  refreshSuggestions();
})();
