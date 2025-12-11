"""
scraper.py
Scrapes loan pages from Bank of Maharashtra (scope: loan pages only).
Outputs raw text to data/raw_bom.txt
"""
import requests
from bs4 import BeautifulSoup
import time
import json
import os

# List of Bank of Maharashtra loan-related URLs to target.
# These are examples — add/adjust if new loan URLs are found.
TARGET_URLS = [
    "https://bankofmaharashtra.in/home-loan",
    "https://bankofmaharashtra.in/personal-loan",
    "https://bankofmaharashtra.in/vehicle-loan",
    "https://bankofmaharashtra.in/gold-loan",
    "https://bankofmaharashtra.in/education-loan",
    # add other loan pages if present
]

OUT_DIR = "data"
os.makedirs(OUT_DIR, exist_ok=True)
OUT_FILE = os.path.join(OUT_DIR, "raw_bom.txt")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100 Safari/537.36"
}

def fetch_text(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        # Remove nav/footer/scripts/styles
        for tag in soup(["script", "style", "header", "footer", "nav", "aside", "form"]):
            tag.decompose()

        # Focus on main content
        main = soup.find("main")
        if not main:
            main = soup.body

        texts = []
        # Collect text from paragraphs, headings, lists
        for tag in main.find_all(["h1","h2","h3","h4","p","li","table"]):
            txt = tag.get_text(separator=" ", strip=True)
            if txt:
                texts.append(txt)
        return "\n".join(texts)
    except Exception as e:
        print(f"Failed to fetch {url}: {e}")
        return ""

def main():
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        for url in TARGET_URLS:
            print("Fetching:", url)
            txt = fetch_text(url)
            if txt.strip():
                f.write(f"URL: {url}\n")
                f.write(txt + "\n\n" + ("-"*80) + "\n\n")
            time.sleep(1.0)  # polite pause
    print("Saved raw data to", OUT_FILE)

if __name__ == "__main__":
    main()
