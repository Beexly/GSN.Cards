#!/usr/bin/env python3
"""
Card identification prototype — Step 1: Download Scryfall bulk data.
Fetches all Magic card metadata + image URLs, saves to SQLite for local querying.
This is the foundation dataset — the "20M record database" CDP built their AI on.

Usage: python cardai/scryfall_download.py
"""
import json
import os
import sqlite3
import time
from pathlib import Path

import requests

REQUESTS_HEADERS = {"User-Agent": "trawl-cardai/1.0 (contact@example.com)"}

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "scryfall.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

# Scryfall bulk data endpoint — returns all cards in JSON
BULK_URL = "https://api.scryfall.com/bulk-data"

def get_bulk_download_url():
    """Find the 'default_cards' bulk file URL — all Magic cards with images."""
    resp = requests.get(BULK_URL, timeout=30, headers=REQUESTS_HEADERS)
    resp.raise_for_status()
    data = resp.json()
    for item in data["data"]:
        if item["type"] == "default_cards":
            return item["jsonl_download_uri"]
    raise RuntimeError("Could not find default_cards bulk file")

def download_and_index():
    """Download the bulk JSON and index into SQLite."""
    url = get_bulk_download_url()
    print(f"Downloading Scryfall bulk data from: {url}")

    import gzip

    # Stream the download (it's a .gz JSONL file)
    resp = requests.get(url, stream=True, timeout=60, headers=REQUESTS_HEADERS)
    resp.raise_for_status()

    # Decompress gzip on the fly and parse JSONL
    cards = []
    line_count = 0
    decoder = gzip.decompress
    buf = b""
    for chunk in resp.iter_content(65536, decode_unicode=False):
        buf += chunk
        # Try to decompress incrementally isn't trivial with gzip;
        # collect all then decompress
    data = decoder(buf)

    for line in data.decode("utf-8").splitlines():
        if not line:
            continue
        try:
            card = json.loads(line)
            line_count += 1

            # Only keep cards with image URIs and English
            if card.get("lang") != "en":
                continue
            if not card.get("image_uris"):
                continue
            if card.get("layout") in ("token", "double_faced_token", "emblem", "planar"):
                continue

            cards.append({
                "id": card.get("id", ""),
                "name": card.get("name", ""),
                "set": card.get("set", ""),
                "set_name": card.get("set_name", ""),
                "collector_number": card.get("collector_number", ""),
                "year": card.get("released_at", "")[:4] if card.get("released_at") else "",
                "rarity": card.get("rarity", ""),
                "type_line": card.get("type_line", ""),
                "oracle_text": card.get("oracle_text", ""),
                "image_normal": card["image_uris"].get("normal", ""),
                "image_large": card["image_uris"].get("large", ""),
                "image_png": card["image_uris"].get("png", ""),
                "image_small": card["image_uris"].get("small", ""),
                "prices_usd": card.get("prices", {}).get("usd", "") or "",
                "prices_eur": card.get("prices", {}).get("eur", "") or "",
            })
        except (json.JSONDecodeError, KeyError):
            continue

    print(f"Parsed {line_count:,} lines, {len(cards):,} usable card records")

    # Index into SQLite
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DROP TABLE IF EXISTS cards")
    conn.execute("""
        CREATE TABLE cards (
            id TEXT PRIMARY KEY,
            name TEXT,
            set_code TEXT,
            set_name TEXT,
            collector_number TEXT,
            year TEXT,
            rarity TEXT,
            type_line TEXT,
            oracle_text TEXT,
            image_normal TEXT,
            image_large TEXT,
            image_png TEXT,
            image_small TEXT,
            prices_usd TEXT,
            prices_eur TEXT
        )
    """)
    conn.executemany("""
        INSERT INTO cards VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, [(c["id"], c["name"], c["set"], c["set_name"], c["collector_number"],
           c["year"], c["rarity"], c["type_line"], c["oracle_text"],
           c["image_normal"], c["image_large"], c["image_png"], c["image_small"],
           c["prices_usd"], c["prices_eur"]) for c in cards])
    conn.commit()
    conn.close()

    print(f"Indexed {len(cards):,} cards into {DB_PATH}")
    return len(cards)

if __name__ == "__main__":
    n = download_and_index()
    print(f"Done: {n:,} cards indexed")
