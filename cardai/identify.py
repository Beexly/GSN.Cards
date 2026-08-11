#!/usr/bin/env python3
"""
Card identification engine — CLIP + FAISS for photo → card matching.
Uses OpenAI CLIP (via transformers) to embed card images, then FAISS
for nearest-neighbor search against the Scryfall database.

Usage:
    python cardai/build_index.py      # build FAISS index from DB (1000 cards for prototype)
    python cardai/identify.py <image> # identify a card from a photo
"""
import json
import os
import sqlite3
import sys
import time
from pathlib import Path

import numpy as np
import requests
import torch
from PIL import Image
from transformers import CLIPModel, CLIPProcessor

# ── Config ────────────────────────────────────────────────────────────────────
DB_PATH = Path(__file__).resolve().parent.parent / "data" / "scryfall.db"
INDEX_PATH = Path(__file__).resolve().parent.parent / "data" / "faiss_index.bin"
META_PATH = Path(__file__).resolve().parent.parent / "data" / "card_meta.json"
IMAGE_CACHE = Path(__file__).resolve().parent.parent / "data" / "images"
IMAGE_CACHE.mkdir(parents=True, exist_ok=True)

CLIP_MODEL = "openai/clip-vit-base-patch32"
EMBED_DIM = 512
BATCH_SIZE = 16
MAX_IMAGES = 1000  # prototype — scale up after validation

REQUESTS_HEADERS = {"User-Agent": "trawl-cardai/1.0 (contact@example.com)"}


def load_clip():
    print(f"Loading CLIP model: {CLIP_MODEL}")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = CLIPModel.from_pretrained(CLIP_MODEL).to(device)
    processor = CLIPProcessor.from_pretrained(CLIP_MODEL)
    return model, processor, device


def get_card_image(url, card_id):
    local_path = IMAGE_CACHE / f"{card_id}.jpg"
    if local_path.exists() and local_path.stat().st_size > 500:
        return local_path
    try:
        resp = requests.get(url, timeout=15, headers=REQUESTS_HEADERS, stream=True)
        resp.raise_for_status()
        with open(local_path, "wb") as f:
            for chunk in resp.iter_content(1024):
                f.write(chunk)
        return local_path
    except Exception as e:
        print(f"  Failed to download {card_id}: {e}")
        return None


def build_index():
    import faiss

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.execute(
        f"SELECT id, name, set_code, set_name, collector_number, year, "
        f"image_large, image_normal, prices_usd, prices_eur "
        f"FROM cards WHERE image_large != '' LIMIT {MAX_IMAGES}"
    )
    cards = cursor.fetchall()
    conn.close()
    print(f"Indexing {len(cards)} cards from database...")

    model, processor, device = load_clip()

    paths = []
    card_records = []
    for i, card in enumerate(cards):
        url = card["image_large"] or card["image_normal"]
        path = get_card_image(url, card["id"])
        if path:
            paths.append(str(path))
            card_records.append({
                "id": card["id"],
                "name": card["name"],
                "set": card["set_code"],
                "set_name": card["set_name"],
                "number": card["collector_number"],
                "year": card["year"],
                "price_usd": card["prices_usd"],
                "price_eur": card["prices_eur"],
            })
        if (i + 1) % 100 == 0:
            print(f"  Downloaded {i + 1}/{len(cards)} images")

    print(f"Computing CLIP embeddings for {len(paths)} images...")
    embeddings = np.zeros((len(paths), EMBED_DIM), dtype=np.float32)

    for start in range(0, len(paths), BATCH_SIZE):
        end = min(start + BATCH_SIZE, len(paths))
        batch_paths = paths[start:end]
        images = [Image.open(p).convert("RGB") for p in batch_paths]

        inputs = processor(images=images, return_tensors="pt").to(device)
        with torch.no_grad():
            out = model.get_image_features(**inputs)
            # transformers 5.x: get_image_features returns BaseModelOutputWithPooling
            feats = out.pooler_output if hasattr(out, "pooler_output") else out
            feats = feats / feats.norm(dim=-1, keepdim=True)
        embeddings[start:end] = feats.cpu().numpy()
        if (start // BATCH_SIZE + 1) % 5 == 0:
            print(f"  Embedded {end}/{len(paths)}")

    index = faiss.IndexFlatIP(EMBED_DIM)
    index.add(embeddings)
    faiss.write_index(index, str(INDEX_PATH))

    with open(META_PATH, "w") as f:
        json.dump(card_records, f)

    print(f"Index saved: {INDEX_PATH} ({index.ntotal:,} vectors)")
    print(f"Metadata saved: {META_PATH} ({len(card_records):,} records)")


def identify(image_path, top_k=5):
    if not INDEX_PATH.exists() or not META_PATH.exists():
        print("Index not built. Run build first.")
        sys.exit(1)

    import faiss

    model, processor, device = load_clip()
    index = faiss.read_index(str(INDEX_PATH))
    with open(META_PATH) as f:
        records = json.load(f)

    img = Image.open(image_path).convert("RGB")
    inputs = processor(images=img, return_tensors="pt").to(device)
    with torch.no_grad():
        out = model.get_image_features(**inputs)
        query = out.pooler_output if hasattr(out, "pooler_output") else out
        query = query / query.norm(dim=-1, keepdim=True)
    query_vec = query.cpu().numpy().astype(np.float32)

    scores, indices = index.search(query_vec, top_k)

    results = []
    for score, idx in zip(scores[0], indices[0]):
        card = records[idx]
        results.append({
            "score": float(score),
            "name": card["name"],
            "set": card["set"],
            "set_name": card["set_name"],
            "number": card["number"],
            "year": card["year"],
            "price_usd": card["price_usd"],
            "price_eur": card["price_eur"],
        })
    return results


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in ("build", "identify"):
        print("Usage: python identify.py build  |  identify <image_path>")
        sys.exit(1)
    if sys.argv[1] == "build":
        build_index()
    else:
        if len(sys.argv) < 3:
            print("Usage: python identify.py identify <image_path>")
            sys.exit(1)
        start = time.time()
        results = identify(sys.argv[2])
        elapsed = time.time() - start
        for r in results:
            print(f"  {r['score']:.3f}  {r['year']} {r['set']} #{r['number']} "
                  f"{r['name']}  (${r['price_usd']}/€{r['price_eur']})")
        print(f"  ({elapsed:.1f}s)")
