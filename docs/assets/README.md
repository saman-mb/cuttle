# Docs assets

- `logo.gif` — **README hero**: the Cuttle mascot, a pixel-art cuttlefish on a ~30s seamless loop (fins undulating, two blinks, chromatophore bands cycling teal → cyan → violet → magenta). Spec: `specs/logo-animated.pixelart.json`.
- `logo.png` — static poster (frame 45 of the loop) for reduced-motion, Open Graph and anywhere a 1.4MB GIF is unwelcome.
- `logo-readme.png` — 200px-wide still, sized for the README header.
- `artist1-*`, `artist2-*` — earlier logo candidates, superseded by the current mascot.
- `demo.gif` — illustrative implement run (termgif).

## Regenerating the logo

The sprite is drawn in code, not by hand. Edit `specs/_gen_cuttle_logo.py`, then:

```bash
cd docs/assets
python3 specs/_gen_cuttle_logo.py            # rewrites both pixelart specs
python3 ~/.claude/skills/shipmates-pixelart/pixelart.py \
  --spec specs/logo-animated.pixelart.json --out logo.gif
python3 ~/.claude/skills/shipmates-pixelart/pixelart.py \
  --spec specs/logo.pixelart.json --out logo.png
```

`logo-readme.png` is `logo.png` resampled to 200px wide.

### House rules for the mascot

Keep these when changing the sprite — they are what make it read as an animal
rather than a coloured blob:

- **Value before hue.** The body uses a fixed five-step teal ramp lit from the
  upper left; the sprite must stay readable in greyscale.
- **Hue rotation is for the chromatophore bands only**, and only across the
  teal → magenta arc (170–320°). The body, ink and eye never rotate, so the
  character is recognisable in every frame.
- **The band layout never moves.** A brightness wave travels through fixed
  bands; bands are never repositioned or re-randomised per frame.
- **Nearest-neighbour, whole-number scale, limited palette** — as with every
  pixel-art asset here.
