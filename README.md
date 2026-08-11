# GSN.Cards

Full-stack card identification engine — photo → structured card data → marketplace listings.

Built on the Card Dealer Pro architecture: a scraping/anti-bot engine (Trawl) + CLIP-based
visual search AI + a vocab-driven data transformation pipeline.

## Architecture

```
┌─────────────┐   ┌──────────────┐   ┌───────────────┐   ┌────────────────┐
│  Card Photo │──>│  CLIP+FAISS  │──>│ Scryfall DB   │──>│ transform.go   │──> eBay/CollX/etc
│ (scanner,   │   │  (embeddings) │   │ (metadata +   │   │ (subset/para   │
│  phone cam) │   │              │   │  images)      │   │  splitting)    │
└─────────────┘   └──────────────┘   └───────────────┘   └────────────────┘
                                           ▲
                                           │ Trawl (anti-bot scraper)
                                           │ fetches from eBay, TCGplayer,
                                           │ card marketplaces
                                           │
                                           ▼
                                     Market pricing &
                                     additional card data
```

## Components

### 1. Scraping Engine (`trawl/`)
Trawl — self-hosted web scraping engine with anti-bot bypass (Cloudflare, Akamai, Imperva,
CAPTCHAs). 4-tier escalation: plain HTTP → cached session → fresh browser solve → residential proxy.

### 2. Card Database (`cardai/scryfall_download.py`)
Downloads Scryfall's complete Magic card database (106K+ cards) with metadata and image URLs
into a local SQLite database. This is the reference dataset — equivalent to CDP's "20M record database."

### 3. Visual Search (`cardai/identify.py`)
CLIP image embeddings + FAISS vector search for photo-to-card identification.
Downloads card images, computes embeddings, builds a searchable index.

### 4. Data Transformation (`cdp_export_tool/`)
Port of Card Dealer Pro's transformation pipeline:
- `transform_cards.py` / `transform.go` — vocab-driven splitter for subset/parallel
- `parallel_vocab.txt` — 350+ parallel tokens, 46 qualifiers
- Brand-family rules (Panini/Topps/Fleer prefix insertion, year-based)

## Quick Start

```bash
# 1. Start the scraping engine
cd trawl
docker compose up -d

# 2. Download card database
python cardai/scryfall_download.py

# 3. Build the FAISS search index
python cardai/identify.py build

# 4. Identify a card from a photo
python cardai/identify.py identify /path/to/card.jpg
```

## Live Services

- Trawl API: http://localhost:8191
- Trawl forward proxy: http://localhost:8192
- Health check: http://localhost:8191/health

## Related Repos

- `trawl/` — scraping engine (submodule of germondai/trawl)
- `cdp_export_tool/` — CDP data transformation pipeline
