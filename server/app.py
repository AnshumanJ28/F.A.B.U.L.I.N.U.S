import os
import re
import json
import time
import threading
from flask import Flask, request, jsonify, send_from_directory, render_template_string
import onnxruntime as ort

app = Flask(__name__, static_folder="public", static_url_path="")
LIST_TEMPLATE = """
{% if current_list|length == 0 %}
<p class="empty-hint">Your list is empty. Try saying "add milk".</p>
{% else %}
  {% set by_category = {} %}
  {% for entry in current_list %}
    {% set cat = entry.get('category', 'Other') %}
    {% if cat not in by_category %}
      {% set _ = by_category.update({cat: []}) %}
    {% endif %}
    {% set _ = by_category[cat].append(entry) %}
  {% endfor %}

  {% for cat, group_items in by_category|dictsort %}
    <div class="category-group">
      <h3>{{ cat }}</h3>
      {% set is_expanded = cat in expanded_categories %}
      {% set visible_count = group_items|length if is_expanded else [group_items|length, 5]|min %}
      {% for i in range(visible_count) %}
        {% set entry = group_items[i] %}
        <div class="item-row">
          <span>
            {% set is_unit = entry.get('size') and entry.get('size').strip() != "" %}
            {{ entry.item }}{% if entry.get('size') and not is_unit %} ({{ entry.get('size') }}){% endif %}
            {% if entry.get('quantity') or is_unit %}
              <span class="item-qty">×{{ entry.get('quantity', 1) }}{% if is_unit %} {{ entry.get('size') }}{% endif %}</span>
            {% endif %}
          </span>
          <button class="item-remove" onclick="sendCommand('remove {{ entry.item }}')">Remove</button>
        </div>
      {% endfor %}
      {% if group_items|length > 5 %}
        <button class="item-toggle" onclick="toggleCategory('{{ cat }}')" title="{{ 'Show Less' if is_expanded else 'Show More' }}">
          {{ '&#x25B2;'|safe if is_expanded else '&#x25BC;'|safe }}
        </button>
      {% endif %}
    </div>
  {% endfor %}
{% endif %}
"""

SUGGESTIONS_TEMPLATE = """
{% if not suggestions %}
<li class="empty-hint">No suggestions yet.</li>
{% else %}
  {% for s in suggestions %}
    <li class="suggestion-item">
      <span>
        <div>{{ s.item }}</div>
        <div class="reason">{{ s.reason }}</div>
      </span>
      <button class="suggestion-add" onclick="sendCommand('add {{ s.item }}')">Add</button>
    </li>
  {% endfor %}
{% endif %}
"""

# Load Data
def load_json(filename):
    path = os.path.join("data", filename)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

dict_items = load_json("items.json")
dict_categories = load_json("categories.json")
dict_brands = load_json("brands.json")
dict_sizes = load_json("sizes.json")
unit_restrictions = load_json("unit_restrictions.json")

# ONNX Model
model_session = ort.InferenceSession("data/model.onnx")

def classify_intent(text):
    try:
        inputs = {"input": [[text]]}
        outputs = model_session.run(None, inputs)
        label = outputs[0][0]
        return label
    except Exception as e:
        print(f"Model error: {e}")
        return "ADD"

# History State
history = []
if os.path.exists("data/history_seed.json"):
    with open("data/history_seed.json", "r") as f:
        seed = json.load(f)
        now = time.time()
        for e in seed:
            days_ago = e.get("days_ago", 0)
            history.append({"item": e.get("item", ""), "timestamp": now - days_ago * 86400})

def log_history(item):
    history.append({"item": item.lower(), "timestamp": time.time()})

# Global List State (replacing single current_list)
user_lists = {}
list_lock = threading.Lock()

def get_current_list():
    uid = request.args.get("sid")
    if not uid:
        uid = "default"
    if uid not in user_lists:
        user_lists[uid] = []
    return user_lists[uid]

# Entity Extraction Helpers
def find_longest_match(text, dictionary):
    best_key = None
    best_val = None
    for k, v in dictionary.items():
        pattern = r"(?:^|[^a-zA-Z])" + re.escape(k) + r"(?:$|[^a-zA-Z])"
        if re.search(pattern, text):
            if best_key is None or len(k) > len(best_key):
                best_key = k
                best_val = v
    return best_val

def find_array_match(text, arr):
    best = None
    for s in arr:
        pattern = r"(?:^|[^a-zA-Z])" + re.escape(s) + r"(?:$|[^a-zA-Z])"
        if re.search(pattern, text):
            if best is None or len(s) > len(best):
                best = s
    return best

def extract_quantity(text):
    m = re.search(r"-?\d+", text)
    if m:
        return {"found": True, "value": int(m.group(0))}
        
    if re.search(r"(?:minus|negative)\s+half\s+(?:a\s+)?dozen", text):
        return {"found": True, "value": -6}
    if re.search(r"(?:minus|negative)\s+dozen", text):
        return {"found": True, "value": -12}

    words = {"one":1, "a":1, "an":1, "two":2, "three":3, "four":4, "five":5, "six":6, "seven":7, "eight":8, "nine":9, "ten":10}
    for w, v in words.items():
        if re.search(r"(?:^|[^a-zA-Z])(?:minus|negative)\s+" + re.escape(w) + r"(?:$|[^a-zA-Z])", text):
            return {"found": True, "value": -v}
            
    if "half a dozen" in text or "half dozen" in text:
        return {"found": True, "value": 6}
    if "dozen" in text:
        return {"found": True, "value": 12}
        
    for w, v in words.items():
        if re.search(r"(?:^|[^a-zA-Z])" + re.escape(w) + r"(?:$|[^a-zA-Z])", text):
            return {"found": True, "value": v}
            
    return {"found": False, "value": 1}

def extract_entities(text):
    text = text.lower()
    e = {}
    e["item"] = find_longest_match(text, dict_items)
    if e["item"]:
        e["category"] = dict_categories.get(e["item"])
    e["brand"] = find_array_match(text, dict_brands)
    e["size"] = find_longest_match(text, dict_sizes)
    e["quantity"] = extract_quantity(text)
    
    # Check gibberish unit
    m = re.search(r"\b\d+\s+([a-zA-Z]+)\s+of\b", text)
    if m:
        possible_unit = m.group(1)
        if not find_longest_match(possible_unit, dict_sizes):
            e["size"] = "INVALID_UNIT_GIBBERISH"
            
    # Validate unit
    if e["item"] and e.get("size") and e["size"] != "INVALID_UNIT_GIBBERISH":
        cat = e.get("category", "Other")
        is_valid = False
        item_units = unit_restrictions.get("item_units", {})
        cat_units = unit_restrictions.get("category_units", {})
        
        if e["item"] in item_units:
            if e["size"] in item_units[e["item"]]:
                is_valid = True
        elif cat in cat_units:
            if e["size"] in cat_units[cat]:
                is_valid = True
        else:
            is_valid = True
            
        if not is_valid:
            e["size"] = "INVALID_UNIT_RESTRICTED"
            
    return e

@app.route("/")
def index():
    return app.send_static_file("index.html")

@app.route("/api/state", methods=["POST"])
def get_state():
    data = request.json or {}
    expanded = data.get("expanded_categories", [])
    
    with list_lock:
        current_list = get_current_list()
        
    list_html = render_template_string(LIST_TEMPLATE, current_list=current_list, expanded_categories=expanded)
    return jsonify({"list_html": list_html, "list": current_list})

@app.route("/api/clear", methods=["POST"])
def clear_list():
    data = request.json or {}
    expanded = data.get("expanded_categories", [])
    
    with list_lock:
        uid = request.args.get("sid")
        if not uid:
            uid = "default"
        user_lists[uid] = []
        current_list = user_lists[uid]
        
    list_html = render_template_string(LIST_TEMPLATE, current_list=current_list, expanded_categories=expanded)
    return jsonify({"list_html": list_html, "list": current_list})

def get_converted_qty(qty, from_unit, to_unit):
    if from_unit == to_unit:
        return qty
    res = None
    if from_unit == "kg" and to_unit == "g": res = qty * 1000
    elif from_unit == "g" and to_unit == "kg": res = qty / 1000
    elif from_unit == "l" and to_unit == "ml": res = qty * 1000
    elif from_unit == "ml" and to_unit == "l": res = qty / 1000
    
    if res is not None:
        res = round(res, 3)
        if res == int(res):
            return int(res)
        return res
    return None

@app.route("/api/command", methods=["POST"])
def process_command():
    data = request.json or {}
    text = data.get("text", "").lower()
    expanded = data.get("expanded_categories", [])
    
    with list_lock:
        current_list = get_current_list()
        
        parts = [p.strip() for p in re.split(r"\s+and\s+|,\s*", text) if p.strip()]
        if not parts:
            list_html = render_template_string(LIST_TEMPLATE, current_list=current_list, expanded_categories=expanded)
            return jsonify({"list_html": list_html, "list": current_list, "messages": [{"type": "error", "text": "Didn't catch that."}]})
            
        messages = []
        primary_intent = None
        
        for i, part in enumerate(parts):
            intent = classify_intent(part)
            if i == 0:
                primary_intent = intent
            else:
                intent = primary_intent
                
            e = extract_entities(part)
            
            if e.get("size") == "INVALID_UNIT_GIBBERISH":
                messages.append({"type": "error", "text": "Unrecognized unit used."})
                continue
            if e.get("size") == "INVALID_UNIT_RESTRICTED":
                messages.append({"type": "error", "text": f"Unit is not allowed for {e['item']}."})
                continue
                
            if intent == "ADD":
                if not e.get("item"):
                    messages.append({"type": "error", "text": "Couldn't tell what to add."})
                    continue
                    
                if e.get("quantity", {}).get("value", 1) <= 0:
                    messages.append({"type": "error", "text": "Negative quantities are ignored."})
                    continue
                    
                # Conflict checking
                conflict = False
                for existing in current_list:
                    if existing["item"] == e["item"]:
                        ex_size = existing.get("size") or ""
                        new_size = e.get("size") or ""
                        if ex_size != new_size and new_size != "":
                            converted = get_converted_qty(e["quantity"]["value"], new_size, ex_size)
                            if converted is not None:
                                e["quantity"]["value"] = converted
                                e["size"] = ex_size
                            else:
                                messages.append({"type": "error", "text": f"Conflict: {e['item']} exists with different unit."})
                                conflict = True
                                break
                        
                if conflict: continue
                
                # Update or Add
                found = False
                for existing in current_list:
                    if existing["item"] == e["item"]:
                        existing["quantity"] = existing.get("quantity", 1) + e["quantity"]["value"]
                        found = True
                        break
                if not found:
                    new_item = {"item": e["item"], "category": e.get("category", "Other"), "quantity": e["quantity"]["value"]}
                    if e.get("size"):
                        new_item["size"] = e["size"]
                    current_list.append(new_item)
                    
                log_history(e["item"])
                qty_str = f" ×{e['quantity']['value']}" if e['quantity']['value'] > 1 else ""
                sz_str = f" ({e['size']})" if e.get("size") else ""
                messages.append({"type": "success", "text": f"Added {e['item']}{sz_str}{qty_str}"})
                
            elif intent == "REMOVE":
                if not e.get("item"):
                    messages.append({"type": "error", "text": "Couldn't tell what to remove."})
                    continue
                    
                item_to_remove = None
                for x in current_list:
                    if x["item"] == e["item"]:
                        item_to_remove = x
                        break
                        
                if item_to_remove:
                    ex_size = item_to_remove.get("size") or ""
                    new_size = e.get("size") or ""
                    
                    if ex_size != new_size and new_size != "":
                        converted = get_converted_qty(e["quantity"]["value"], new_size, ex_size)
                        if converted is not None:
                            e["quantity"]["value"] = converted
                            e["size"] = ex_size
                        else:
                            messages.append({"type": "error", "text": f"Conflict: {e['item']} exists with different unit."})
                            continue
                        
                    qty_to_remove = e["quantity"]["value"]
                    if qty_to_remove <= 0:
                        messages.append({"type": "error", "text": "Negative quantities are ignored."})
                        continue
                        
                    if item_to_remove.get("quantity", 1) > qty_to_remove:
                        item_to_remove["quantity"] -= qty_to_remove
                        sz_str = f" {e.get('size')}" if e.get("size") and e.get("size") != "" else ""
                        messages.append({"type": "success", "text": f"Removed {qty_to_remove}{sz_str} {e['item']}"})
                    else:
                        uid = request.args.get("sid", "default")
                        user_lists[uid] = [x for x in current_list if x["item"] != e["item"]]
                        current_list = user_lists[uid]
                        messages.append({"type": "success", "text": f"Removed {e['item']}"})
                else:
                    messages.append({"type": "error", "text": f"Couldn't find {e['item']} in the list."})
                    
            elif intent in ["SEARCH_ITEM", "SEARCH_FILTER"]:
                messages.append({"type": "success", "text": f"Searching for {e.get('item', 'items')} (not fully implemented in backend yet)"})
            else:
                messages.append({"type": "error", "text": f"Unrecognized command: '{part}'"})
                
    list_html = render_template_string(LIST_TEMPLATE, current_list=current_list, expanded_categories=expanded)
    return jsonify({"list_html": list_html, "list": current_list, "messages": messages})

@app.route("/api/suggest", methods=["GET"])
def suggest():
    freq = {}
    last_seen = {}
    now = time.time()
    for ev in history:
        item = ev["item"]
        freq[item] = freq.get(item, 0) + 1
        if item not in last_seen or ev["timestamp"] > last_seen[item]:
            last_seen[item] = ev["timestamp"]
            
    scored = []
    for item, count in freq.items():
        days_since = max(1.0, (now - last_seen[item]) / 86400.0)
        score = count + (1.0 / days_since) * 5.0
        scored.append({"item": item, "score": score, "reason": "Frequently bought"})
        
    scored.sort(key=lambda x: x["score"], reverse=True)
    
    with list_lock:
        current_list = get_current_list()
    
    # Filter out items already in list
    in_list = {x["item"] for x in current_list}
    final_suggestions = [x for x in scored if x["item"] not in in_list][:5]
    
    sug_html = render_template_string(SUGGESTIONS_TEMPLATE, suggestions=final_suggestions)
    return jsonify({"sug_html": sug_html, "suggestions": final_suggestions})

@app.route("/api/download", methods=["GET"])
def download_list():
    with list_lock:
        current_list = get_current_list()
        
    if not current_list:
        return "Shopping List is empty\n", 200, {'Content-Type': 'text/plain'}
        
    by_category = {}
    for entry in current_list:
        cat = entry.get('category', 'Other')
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(entry)
        
    content = "Shopping List\n\n"
    for cat in sorted(by_category.keys()):
        content += cat.upper() + "\n"
        for entry in by_category[cat]:
            sz = entry.get('size', '')
            is_unit = bool(sz and sz.strip())
            qty = entry.get('quantity', 1)
            
            item_str = entry['item']
            if sz and not is_unit:
                item_str += f" ({sz})"
                
            qty_str = f" (x{qty}{' ' + sz if is_unit else ''})"
            content += f"- {item_str}{qty_str}\n"
        content += "\n"
        
    return content, 200, {
        'Content-Type': 'text/plain',
        'Content-Disposition': 'attachment; filename="shopping_list.txt"'
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
