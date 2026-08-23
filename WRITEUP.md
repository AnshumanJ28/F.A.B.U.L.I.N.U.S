# Approach write-up

This is a hybrid C++/ONNX voice shopping assistant, built to satisfy two firm
constraints: no LLM anywhere, and no Python at runtime.

The frontend is plain HTML/CSS/JS using the Web Speech API for
speech-to-text, with a dark "Jarvis HUD" orb as the voice control (idle
breathing pulse, faster pulse while listening, brief tightening while
processing; `prefers-reduced-motion` falls back to a static ring).

The backend is a single C++ binary (cpp-httplib) that also serves the static
frontend. Intent classification (ADD / REMOVE / SEARCH_ITEM / SEARCH_FILTER)
uses a TF-IDF + logistic regression model trained offline in Python with
scikit-learn and exported via skl2onnx. Because skl2onnx compiles the *entire*
pipeline — including tokenization and TF-IDF weighting — into the ONNX graph,
the C++ server never re-implements vectorization: it hands ONNX Runtime the
raw transcript string and reads back a predicted label. Python touches the
app exactly once, offline, to produce `model.onnx`.

Entity extraction (item, quantity, brand, size, price range) is intentionally
not ML: it's regex plus JSON dictionary lookups, which is more debuggable and
more accurate for this narrow, structured task than a model would be, and
keeps the whole pipeline free of any generative component.
