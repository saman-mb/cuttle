# Docs assets

- `logo.png` / `logo-240.png` — pixel-art circular cuttlefish mark (from `specs/logo.pixelart.json`), nearest-neighbour upscale.
- `demo.gif` — illustrative README / site hero (from `specs/readme-demo.termgif.json`).
- Regenerate logo: `python3 ~/.cursor/skills/shipmates-pixelart/pixelart.py --spec specs/logo.pixelart.json --out logo.png`
- Regenerate demo: `python3 ~/.cursor/skills/shipmates-termgif/termgif.py --spec specs/readme-demo.termgif.json --out demo.gif`

Demo frames are **illustrative** until the golden-suite ledger ships real numbers.
