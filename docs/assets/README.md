# Docs assets

- `logo.gif` — **README hero**: animated cuttlefish, ~30s seamless chromatophore colour loop (no circular badge / letterbox frame). Spec: `specs/logo-animated.pixelart.json`.
- `logo.png` — static poster (final/mid frame) for reduced-motion / OG fallback.
- `logo-readme.png` — 200px-wide nearest-neighbour still for places that dislike huge GIFs.
- `demo.gif` — illustrative implement run (termgif).
- Regenerate logo:  
  `python3 ~/.cursor/skills/shipmates-pixelart/pixelart.py --spec specs/logo-animated.pixelart.json --out logo.gif --poster logo.png`
