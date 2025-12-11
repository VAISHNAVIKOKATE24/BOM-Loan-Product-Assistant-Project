# build_index_numpy.py
"""
Builds embeddings and saves them with metadata, using only numpy.
- Input: data/bom_chunks.jsonl (from clean.py)
- Output:
    data/embeddings.npy      # normalized embeddings
    data/metadata.json       # chunk info (text + source)
"""

import json
import os
import numpy as np
from sentence_transformers import SentenceTransformer

IN_FILE = "data/bom_chunks.jsonl"
OUT_EMB = "data/embeddings.npy"
OUT_META = "data/metadata.json"
EMBED_MODEL = "all-MiniLM-L6-v2"

def load_chunks():
    chunks = []
    with open(IN_FILE, "r", encoding="utf-8") as f:
        for line in f:
            chunks.append(json.loads(line))
    return chunks

def main():
    if not os.path.exists(IN_FILE):
        raise FileNotFoundError(f"{IN_FILE} not found. Run clean.py first.")

    os.makedirs("data", exist_ok=True)

    chunks = load_chunks()
    texts = [c["text"] for c in chunks]
    print(f"Loaded {len(texts)} chunks")

    model = SentenceTransformer(EMBED_MODEL)
    embeddings = model.encode(texts, show_progress_bar=True, convert_to_numpy=True)

    # L2-normalize embeddings so we can use simple dot product as cosine similarity
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True) + 1e-10
    embeddings_normed = embeddings / norms

    np.save(OUT_EMB, embeddings_normed)
    with open(OUT_META, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)

    print("Saved normalized embeddings to", OUT_EMB)
    print("Saved metadata to", OUT_META)

if __name__ == "__main__":
    main()
