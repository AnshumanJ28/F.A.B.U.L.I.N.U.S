(function () {
  "use strict";

  const API_BASE = window.VSA_API_BASE || "";

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

  let currentList = [];

  let voice = null;

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

  function renderList() {
    listCategories.innerHTML = "";
    if (currentList.length === 0) {
      const p = document.createElement("p");
      p.className = "empty-hint";
      p.textContent = "Your list is empty. Try saying \u201cadd milk\u201d.";
      listCategories.appendChild(p);
      return;
    }
    const byCategory = {};
    currentList.forEach((entry) => {
      const cat = entry.category || "Other";
      (byCategory[cat] = byCategory[cat] || []).push(entry);
    });
    Object.keys(byCategory).sort().forEach((cat) => {
      const group = document.createElement("div");
      group.className = "category-group";
      const h3 = document.createElement("h3");
      h3.textContent = cat;
      group.appendChild(h3);
      byCategory[cat].forEach((entry) => {
        const row = document.createElement("div");
        row.className = "item-row";
        const label = document.createElement("span");
        let unitSizes = ["kg", "g", "grams", "gram", "mg", "liter", "liters", "l", "ml", "lb", "lbs", "oz"];
        let isUnit = entry.size && unitSizes.includes(entry.size.toLowerCase());
        
        label.textContent = entry.item + (entry.size && !isUnit ? " (" + entry.size + ")" : "");
        if (entry.quantity || isUnit) {
          const qty = document.createElement("span");
          qty.className = "item-qty";
          qty.textContent = "×" + (entry.quantity || 1) + (isUnit ? " " + entry.size : "");
          label.appendChild(qty);
        }
        const removeBtn = document.createElement("button");
        removeBtn.className = "item-remove";
        removeBtn.textContent = "Remove";
        removeBtn.addEventListener("click", () => removeItem(entry.item));
        row.appendChild(label);
        row.appendChild(removeBtn);
        group.appendChild(row);
      });
      listCategories.appendChild(group);
    });
  }

  function renderSuggestions(suggestions) {
    suggestionsList.innerHTML = "";
    if (!suggestions || suggestions.length === 0) {
      const li = document.createElement("li");
      li.className = "empty-hint";
      li.textContent = "No suggestions yet.";
      suggestionsList.appendChild(li);
      return;
    }
    suggestions.forEach((s) => {
      const li = document.createElement("li");
      li.className = "suggestion-item";
      const info = document.createElement("span");
      info.innerHTML = "";
      const name = document.createElement("div");
      name.textContent = s.item;
      const reason = document.createElement("div");
      reason.className = "reason";
      reason.textContent = s.reason || "";
      info.appendChild(name);
      info.appendChild(reason);
      const addBtn = document.createElement("button");
      addBtn.className = "suggestion-add";
      addBtn.textContent = "Add";
      addBtn.addEventListener("click", () => addItemDirect(s.item));
      li.appendChild(info);
      li.appendChild(addBtn);
      suggestionsList.appendChild(li);
    });
  }

  function renderSearchResults(results, item) {
    if (!results || results.length === 0) {
      searchPanel.hidden = false;
      searchResults.innerHTML = "";
      const li = document.createElement("li");
      li.className = "empty-hint";
      li.textContent = "No matches for \u201c" + item + "\u201d.";
      searchResults.appendChild(li);
      return;
    }
    searchPanel.hidden = false;
    searchResults.innerHTML = "";
    results.forEach((r) => {
      const li = document.createElement("li");
      li.className = "suggestion-item";
      li.textContent = r.name + (r.price != null ? " — $" + r.price.toFixed(2) : "");
      searchResults.appendChild(li);
    });
  }

  async function callParse(text) {
    const res = await fetch(API_BASE + "/parse", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });
    if (!res.ok) throw new Error("parse failed: " + res.status);
    return res.json();
  }

  async function callSuggest() {
    const res = await fetch(API_BASE + "/suggest?list=" + encodeURIComponent(currentList.map(i => i.item).join(",")));
    if (!res.ok) throw new Error("suggest failed: " + res.status);
    return res.json();
  }

  async function callLog(event) {
    try {
      await fetch(API_BASE + "/log", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(event),
      });
    } catch (e) {
    }
  }

  async function refreshSuggestions() {
    try {
      const data = await callSuggest();
      renderSuggestions(data.suggestions);
    } catch (e) {
    }
  }

  function addItemDirect(itemName) {
    handleParsedResult({ intent: "ADD", item: itemName, quantity: 1 }, itemName);
  }

  function removeItem(itemName) {
    handleParsedResult({ intent: "REMOVE", item: itemName }, "remove " + itemName);
  }

  function convertQuantity(qty, fromUnit, toUnit) {
    if (fromUnit === toUnit) return qty;
    if (!fromUnit || !toUnit) return null;
    
    const toGrams = (q, u) => {
      const s = (u || "").toLowerCase();
      if (s === "kg") return q * 1000;
      if (s === "g" || s === "gram" || s === "grams") return q;
      return null;
    };
    const fromGrams = (g, u) => {
      const s = (u || "").toLowerCase();
      if (s === "kg") return g / 1000;
      if (s === "g" || s === "gram" || s === "grams") return g;
      return null;
    };
    
    let g = toGrams(qty, fromUnit);
    if (g !== null) {
      let finalQty = fromGrams(g, toUnit);
      if (finalQty !== null) return finalQty;
    }
    
    const toMl = (q, u) => {
      const s = (u || "").toLowerCase();
      if (s === "l" || s === "liter" || s === "liters") return q * 1000;
      if (s === "ml") return q;
      return null;
    };
    const fromMl = (m, u) => {
      const s = (u || "").toLowerCase();
      if (s === "l" || s === "liter" || s === "liters") return m / 1000;
      if (s === "ml") return m;
      return null;
    };
    
    let ml = toMl(qty, fromUnit);
    if (ml !== null) {
      let finalQty = fromMl(ml, toUnit);
      if (finalQty !== null) return finalQty;
    }
    
    return null;
  }

  function applyAdd(result) {
    let existing = currentList.find((e) => {
      if (e.item.toLowerCase() !== result.item.toLowerCase()) return false;
      if (e.size === result.size) return true;
      if (convertQuantity(1, result.size, e.size) !== null) return true;
      return false;
    });

    if (existing) {
      let addQty = result.quantity || 1;
      if (result.size !== existing.size) {
        let converted = convertQuantity(addQty, result.size, existing.size);
        if (converted !== null) addQty = converted;
      }
      existing.quantity = (existing.quantity || 1) + addQty;
      existing.quantity = Math.round(existing.quantity * 100) / 100;
    } else {
      currentList.push({
        item: result.item,
        quantity: result.quantity || 1,
        category: result.category || "Other",
        size: result.size
      });
    }
    renderList();
    showToast("Added " + result.item + (result.size ? " (" + result.size + ")" : "") + (result.quantity ? " ×" + result.quantity : ""));
    callLog({ type: "add", item: result.item, quantity: result.quantity || 1 });
    refreshSuggestions();
  }

  function applyRemove(result) {
    let idx = currentList.findIndex((e) => {
      if (e.item.toLowerCase() !== (result.item || "").toLowerCase()) return false;
      if (result.size && e.size !== result.size && convertQuantity(1, result.size, e.size) === null) return false;
      return true;
    });

    if (idx !== -1) {
      if (result.quantity_explicit) {
        let deductQty = result.quantity;
        if (result.size && currentList[idx].size && result.size !== currentList[idx].size) {
          let converted = convertQuantity(result.quantity, result.size, currentList[idx].size);
          if (converted !== null) deductQty = converted;
        }
        currentList[idx].quantity -= deductQty;
        currentList[idx].quantity = Math.round(currentList[idx].quantity * 100) / 100;

        if (currentList[idx].quantity <= 0) {
          currentList.splice(idx, 1);
        }
        showToast("Removed " + result.quantity + (result.size ? " " + result.size : "") + " " + result.item);
      } else {
        currentList.splice(idx, 1);
        showToast("Removed " + result.item);
      }
      renderList();
      callLog({ type: "remove", item: result.item });
    } else {
      showToast("Couldn't find \u201c" + result.item + "\u201d on the list", true);
    }
    refreshSuggestions();
  }

  function applySearch(result) {
    searchPanel.hidden = false;
    fetch(API_BASE + "/search?" + new URLSearchParams({
      item: result.item || "",
      brand: result.brand || "",
      size: result.size || "",
      price_max: result.price_range && result.price_range.max != null ? result.price_range.max : "",
      price_min: result.price_range && result.price_range.min != null ? result.price_range.min : "",
    }))
      .then((r) => r.json())
      .then((data) => renderSearchResults(data.results, result.item || ""))
      .catch(() => showToast("Search failed", true));
    showToast("Searching for " + (result.item || "items"));
  }

  function handleParsedResult(result, rawText) {
    if (!result || !result.intent) {
      showToast("Didn't catch that — try again", true);
      return;
    }
    switch (result.intent) {
      case "ADD":
        if (result.item) applyAdd(result);
        else showToast("Couldn't tell what to add", true);
        break;
      case "REMOVE":
        if (result.item) applyRemove(result);
        else showToast("Couldn't tell what to remove", true);
        break;
      case "SEARCH_ITEM":
      case "SEARCH_FILTER":
        applySearch(result);
        break;
      default:
        showToast("Unrecognized command: \u201c" + rawText + "\u201d", true);
    }
  }

  async function processTranscript(text) {
    if (!text) return;
    if (text.toLowerCase().trim() === "clear list") {
      currentList = [];
      renderList();
      showToast("List cleared");
      refreshSuggestions();
      return;
    }
    setOrbState("processing");
    try {
      const result = await callParse(text);
      handleParsedResult(result, text);
    } catch (e) {
      showToast("Couldn't reach the assistant server", true);
    } finally {
      setOrbState("idle");
    }
  }

  voice = new VoiceInput();
  if (!voice.supported) {
    orbStatus.textContent = "Voice input not supported here — use the text field below";
  }
  voice.setLang(langSelect.value);

  voice.onstart = () => setOrbState("listening");
  voice.onresult = (text, isFinal) => {
    transcriptEl.textContent = text;
    if (isFinal) processTranscript(text);
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
    processTranscript(text);
  });

  const downloadListBtn = document.getElementById("download-list-btn");
  if (downloadListBtn) {
    downloadListBtn.addEventListener("click", () => {
      if (currentList.length === 0) {
        showToast("Your list is empty", true);
        return;
      }
      let content = "Shopping List\n\n";
      const byCategory = {};
      currentList.forEach((entry) => {
        const cat = entry.category || "Other";
        (byCategory[cat] = byCategory[cat] || []).push(entry);
      });
      Object.keys(byCategory).sort().forEach((cat) => {
        content += cat.toUpperCase() + "\n";
        byCategory[cat].forEach((entry) => {
          let unitSizes = ["kg", "g", "grams", "gram", "mg", "liter", "liters", "l", "ml", "lb", "lbs", "oz"];
          let isUnit = entry.size && unitSizes.includes(entry.size.toLowerCase());
          content += "- " + entry.item + (entry.size && !isUnit ? " (" + entry.size + ")" : "") + " (x" + (entry.quantity || 1) + (isUnit ? " " + entry.size : "") + ")\n";
        });
        content += "\n";
      });
      
      const blob = new Blob([content], { type: "text/plain" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "shopping_list.txt";
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    });
  }

  const clearListBtn = document.getElementById("clear-list-btn");
  if (clearListBtn) {
    clearListBtn.addEventListener("click", () => {
      if (currentList.length === 0) {
        showToast("Your list is already empty", true);
        return;
      }
      if (confirm("Are you sure you want to clear your entire list?")) {
        currentList = [];
        renderList();
        showToast("List cleared");
        refreshSuggestions();
      }
    });
  }

  setOrbState("idle");
  renderList();
  refreshSuggestions();
})();
