"""
clean.py
Reads data/raw_bom.txt -> cleans and chunks text -> outputs data/bom_chunks.jsonl
Each line in the jsonl: {"id": <int>, "text": "<chunk text>", "source": "<url-or-note>"}
"""
import re
import json
import os
from nltk.tokenize import sent_tokenize

os.makedirs("data", exist_ok=True)
IN_FILE = "data/raw_bom.txt"
OUT_FILE = "data/bom_chunks.jsonl"

CHUNK_SIZE = 350  # characters per chunk target
CHUNK_OVERLAP = 50

def normalize_text(s):
    s = re.sub(r'\s+', ' ', s)
    s = s.strip()
    return s

def chunk_text(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    # chunk by sentences for coherence
    sents = sent_tokenize(text)
    chunks = []
    cur = ""
    for sent in sents:
        if len(cur) + len(sent) + 1 <= chunk_size or not cur:
            cur = (cur + " " + sent).strip()
        else:
            chunks.append(cur)
            # overlap: keep last few words of cur
            if overlap > 0:
                tail = cur[-overlap:]
                cur = tail + " " + sent
            else:
                cur = sent
    if cur:
        chunks.append(cur)
    return chunks

def main():
    try:
        import nltk
        nltk.data.find('tokenizers/punkt')
    except:
        import nltk
        nltk.download('punkt')

    if not os.path.exists(IN_FILE):
        raise FileNotFoundError(f"{IN_FILE} not found. Run scraper.py first.")

    with open(IN_FILE, 'r', encoding='utf-8') as f:
        full = f.read()

    # Split by the delimiter we put in scraper: "URL: <url>" blocks
    sections = re.split(r"URL:\s*", full)[1:]  # first split piece before any URL is empty
    entries = []
    for sec in sections:
        parts = sec.split("\n", 1)
        url = parts[0].strip()
        body = parts[1].strip() if len(parts) > 1 else ""
        body = normalize_text(body)
        if not body:
            continue
        chunks = chunk_text(body)
        for i, c in enumerate(chunks):
            entries.append({
                "id": f"{len(entries)+1}",
                "text": c,
                "source": url
            })

    with open(OUT_FILE, 'w', encoding='utf-8') as out:
        for e in entries:
            out.write(json.dumps(e, ensure_ascii=False) + "\n")
    print(f"Wrote {len(entries)} chunks to {OUT_FILE}")

if __name__ == "__main__":
    main()
