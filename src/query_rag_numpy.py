"""
Simple RAG query script using only numpy for similarity search.
Updated to use GROQ API for answering.
"""

import os
import json
import argparse
import numpy as np
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

# File paths
EMBED_FILE = "data/embeddings.npy"
META_FILE = "data/metadata.json"
EMBED_MODEL = "all-MiniLM-L6-v2"

TOP_K = 3

# Groq API Key
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Default model (Groq recommends: mixtral-8x7b or llama3-8b-8192)
GROQ_MODEL =  "llama-3.1-8b-instant"


# ============================
# Load embeddings + metadata
# ============================
def load_data():
    if not os.path.exists(EMBED_FILE) or not os.path.exists(META_FILE):
        raise FileNotFoundError("Embeddings or metadata not found. Run build_index_numpy.py first.")

    embeddings = np.load(EMBED_FILE)

    with open(META_FILE, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    return embeddings, metadata


# ============================
# Retrieval function
# ============================
def retrieve(question, model, embeddings, meta, top_k=TOP_K):
    q_emb = model.encode([question], convert_to_numpy=True)  # shape (1,d)
    q_norm = q_emb / (np.linalg.norm(q_emb, axis=1, keepdims=True) + 1e-10)
    q_vec = q_norm[0]

    sims = embeddings @ q_vec  # cosine similarity
    top_idx = np.argsort(sims)[-top_k:][::-1]
    top_scores = sims[top_idx]

    retrieved = []
    for score, idx in zip(top_scores, top_idx):
        retrieved.append({
            "score": float(score),
            "metadata": meta[idx]
        })

    return retrieved


# ============================
# Build prompt for the LLM
# ============================
def build_prompt(question, contexts):
    ctx_texts = []

    for c in contexts:
        src = c["metadata"].get("source") or c["metadata"].get("url") or "unknown"
        text = c["metadata"].get("text") or ""
        ctx_texts.append(f"Source ({src}): {text}")

    final_ctx = "\n\n".join(ctx_texts)

    prompt = f"""
You are an assistant answering questions about Bank of Maharashtra loan products.
Use ONLY the information inside the "Context". Do NOT add your own knowledge.
If the answer is not found, say: "I could not find this information in the provided sources."

Context:
{final_ctx}

Question: {question}

Answer concisely and mention the source in brackets, e.g., [Source].
    """.strip()

    return prompt


# ============================
# Groq API call
# ============================
def call_groq(prompt):
    if not GROQ_API_KEY:
        print("ERROR: GROQ_API_KEY not found in .env file\n")
        return None

    try:
        client = Groq(api_key=GROQ_API_KEY)

        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": "You answer based ONLY on provided context."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )

        return response.choices[0].message["content"]

    except Exception as e:
        print("Groq API error:", e, "\n")
        return None


# ============================
# Main
# ============================
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-q", "--question", required=True, help="User question")
    args = parser.parse_args()

    embeddings, meta = load_data()
    model = SentenceTransformer(EMBED_MODEL)

    retrieved = retrieve(args.question, model, embeddings, meta, top_k=TOP_K)

    print("=== Retrieved Contexts ===")
    for r in retrieved:
        src = r["metadata"].get("source") or r["metadata"].get("url") or "unknown"
        snippet = r["metadata"].get("text") or ""
        clean_snippet = snippet[:200].replace("\n", " ")
        print(f"- [score={r['score']:.4f}] {src}: {clean_snippet}")

    prompt = build_prompt(args.question, retrieved)

    answer = call_groq(prompt)

    if answer:
        print("\n=== Final Answer ===")
        print(answer)
    else:
        print("\n(Groq API error — printing the prompt instead)\n")
        print(prompt)


if __name__ == "__main__":
    main()
