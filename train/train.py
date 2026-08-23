"""
train.py — dev-only training script. NEVER imported or run by the shipped
C++ server. Trains a TF-IDF + logistic regression intent classifier on
train/data.csv and exports it to ONNX for the C++ server to load.

Usage:
    python train/train.py

Outputs:
    train/model.onnx        — the exported sklearn Pipeline (vectorizer + LR)
    train/vocab.json        — the fitted vocabulary + idf weights, mirrored
                               here so the C++ side can be inspected/debugged
                               independent of the ONNX graph
    train/labels.json       — index -> intent label mapping
"""
import json

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, classification_report

from skl2onnx import convert_sklearn
from skl2onnx.common.data_types import StringTensorType


def main():
    df = pd.read_csv("train/data.csv")
    X = df["text"].astype(str).tolist()
    y = df["intent"].astype(str).tolist()

    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(lowercase=True, ngram_range=(1, 2), min_df=1)),
        ("clf", LogisticRegression(max_iter=1000, C=5.0)),
    ])
    pipeline.fit(X_train, y_train)

    val_pred = pipeline.predict(X_val)
    acc = accuracy_score(y_val, val_pred)
    print(f"Validation accuracy: {acc:.3f}")
    print(classification_report(y_val, val_pred))

    # Refit on all data before exporting, now that we've validated.
    pipeline.fit(X, y)

    # ---- Export to ONNX ----
    onnx_model = convert_sklearn(
        pipeline,
        initial_types=[("input", StringTensorType([None, 1]))],
        options={id(pipeline.named_steps["clf"]): {"zipmap": False}},
        target_opset=12,
    )
    with open("train/model.onnx", "wb") as f:
        f.write(onnx_model.SerializeToString())
    print("wrote train/model.onnx")

    # ---- Mirror vocab/idf + labels as plain JSON for the C++ port ----
    tfidf = pipeline.named_steps["tfidf"]
    vocab = {term: int(idx) for term, idx in tfidf.vocabulary_.items()}
    idf = tfidf.idf_.tolist()
    with open("train/vocab.json", "w", encoding="utf-8") as f:
        json.dump({
            "vocabulary": vocab,
            "idf": idf,
            "ngram_range": list(tfidf.ngram_range),
            "lowercase": True,
        }, f, ensure_ascii=False, indent=2)
    print("wrote train/vocab.json")

    classes = pipeline.named_steps["clf"].classes_.tolist()
    with open("train/labels.json", "w", encoding="utf-8") as f:
        json.dump({"labels": classes}, f, indent=2)
    print("wrote train/labels.json:", classes)


if __name__ == "__main__":
    main()
