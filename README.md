# GSN.Cards — Card Dealer Pro 2.0

A modern trading card management web application implementing the [Card Dealer Pro 2.0 (CDP2)](https://www.carddealerpro.com/cdp2) design and features.

## Features

- **Magic Scan AI** — Visual search AI that recognizes cards from 20M+ records, 15× faster than v1 with live batch processing
- **Bulk Inventory Slabs** — Cert lookup via PSA, SGC, CGC, and BGS APIs; input via barcode scanner, keyboard, or paste
- **Lightning Fast Search** — Real-time card database search with instant results
- **Batch Inspector** — Review and edit card details efficiently in a unified view
- **Multi-Channel Listing** — Cross-list to eBay, Shopify, Whatnot, and CollX with inventory sync
- **Expanded Card Database** — Wrestling, soccer, multi-sport, and tens of thousands of new sets
- **Desktop Scanner App** — Windows & macOS app for auto-feed scanners and flatbeds
- **Open API** — Programmatic access for custom workflows and integrations

## Project Structure

```
index.html   — Main landing page
styles.css   — All styles (dark theme, responsive)
app.js       — Interactive behaviors (nav, animations, filters)
```

## Getting Started

Open `index.html` in any modern browser — no build step required.

```bash
open index.html
# or
python3 -m http.server 8080
```

## Tech Stack

- Vanilla HTML5, CSS3, JavaScript (ES5-compatible)
- Responsive design with CSS Grid and Flexbox
- Dark theme with CSS custom properties
- Intersection Observer API for scroll animations
