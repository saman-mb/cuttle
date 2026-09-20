#!/usr/bin/env python3
"""Artist 2 — continuous chromatophore scroll for cuttlefish logo.

Dense ~30s seamless loop: every frame shifts colour (no bookend holds).
Silhouette matches Artist 1 / canonical Sepia side-view (facing RIGHT).
"""
from __future__ import annotations

import json
import math
from pathlib import Path

DOT = "."
OUT = "D"
EYE = "E"
PUP = "P"
ARM = "A"

PALETTE = {
    ".": "#00000000",
    "D": "#042f2e",
    "B": "#0f766e",
    "C": "#0d9488",
    "T": "#14b8a6",
    "F": "#5eead4",
    "h": "#99f6e4",
    "E": "#ecfdf5",
    "P": "#0f172a",
    "A": "#134e4a",
    "o": "#f97316",
    "O": "#fb923c",
    "p": "#fb7185",
    "g": "#fbbf24",
    "s": "#38bdf8",
    "v": "#a78bfa",
    "r": "#e11d48",
    "m": "#f472b6",
}

# Same hand-drawn Sepia silhouette as canonical generator (facing RIGHT).
RAW = [
    "..................................................",
    "....F.F.FF.F.FFFF.F.FF.F.F........................",
    "...################################...............",
    "..##################################..............",
    ".###BBBBBBBBBBBBBBBBBBBBBBBBBBBBBB###.............",
    "##BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB##............",
    "##BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB##...........",
    "##BBBBBBBBBBBBBBBBBBEEEEEEEBBBBBBBBBBBB##.........",
    "##BBBBBBBBBBBBBBBBBEEPEEPEEEBBBBBBBBBBB##.A.A.A...",
    "##BBBBBBBBBBBBBBBBBEEPPPPPPEBBBBBBBBBBBB##AAAAAAA.",
    "##BBBBBBBBBBBBBBBBBBEEEEEEEBBBBBBBBBBBBB#AAAAAAAA.",
    "##BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB#A.AAAA.A.",
    "##BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB##.AAAAAA..",
    ".##BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB##..A.A.A...",
    "..##BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB##...........",
    "...###BBBBBBBBBBBBBBBBBBBBBBBBBBBBB###............",
    "....##################################............",
    ".....################################.............",
    "......F.F.FF.F.FFFF.F.FF.F.F......................",
    "..................................................",
]

# Display modes cycle across one loop with overlapping blend windows.
# Names match the product brief colour story.
MODES = (
    "teal",    # depth gradient + slow scroll
    "gold",    # cresting gold wave
    "coral",   # leopard spots migrating
    "cyan",    # horizontal cyan bands
    "violet",  # violet flash bands
    "riot",    # diagonal pop riot
)

N_FRAMES = 120
FRAME_MS = 250  # 120 * 250ms = 30.0s
SCALE = 14


def normalize(rows: list[str]) -> list[list[str]]:
    grid = []
    for row in rows:
        cells = []
        for ch in row:
            cells.append(OUT if ch == "#" else ch)
        grid.append(cells)
    widths = {len(r) for r in grid}
    if len(widths) != 1:
        raise SystemExit(f"ragged rows: {widths}")
    return grid


def crop_tight(grid: list[list[str]], pad: int = 0) -> list[list[str]]:
    h, w = len(grid), len(grid[0])
    min_r, max_r, min_c, max_c = h, -1, w, -1
    for r in range(h):
        for c in range(w):
            if grid[r][c] != DOT:
                min_r, max_r = min(min_r, r), max(max_r, r)
                min_c, max_c = min(min_c, c), max(max_c, c)
    min_r = max(0, min_r - pad)
    max_r = min(h - 1, max_r + pad)
    min_c = max(0, min_c - pad)
    max_c = min(w - 1, max_c + pad)
    return [row[min_c : max_c + 1] for row in grid[min_r : max_r + 1]]


def body_cells(grid: list[list[str]]) -> list[tuple[int, int]]:
    return [(r, c) for r, row in enumerate(grid) for c, ch in enumerate(row) if ch == "B"]


def outline_fin_cells(grid: list[list[str]]) -> list[tuple[int, int]]:
    h, w = len(grid), len(grid[0])
    cells = []
    for r, row in enumerate(grid):
        for c, ch in enumerate(row):
            if ch != OUT:
                continue
            if not (r <= 3 or r >= h - 4):
                continue
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                rr, cc = r + dr, c + dc
                if 0 <= rr < h and 0 <= cc < w and grid[rr][cc] == DOT:
                    cells.append((r, c))
                    break
    return cells


TEAL = ["B", "C", "T", "F", "h"]
POP = ["o", "O", "p", "g", "s", "v", "r", "m"]


def _wrap(t: float) -> float:
    return t - math.floor(t)


def mode_weights(phase: float) -> dict[str, float]:
    """Soft overlapping lobes so adjacent displays blend; loop seams via wrap."""
    n = len(MODES)
    # each mode centred at i/n; width ~1.35 lobes for continuous motion
    weights: dict[str, float] = {}
    for i, name in enumerate(MODES):
        centre = i / n
        d = abs(_wrap(phase - centre + 0.5) - 0.5)  # circular distance [0, 0.5]
        # cosine lobe: full at centre, zero beyond ~0.22
        span = 0.22
        if d >= span:
            w = 0.0
        else:
            w = 0.5 * (1.0 + math.cos(math.pi * d / span))
        weights[name] = w
    s = sum(weights.values()) or 1.0
    return {k: v / s for k, v in weights.items()}


def _pick(palette: list[str], t: float) -> str:
    t = max(0.0, min(0.999, t))
    return palette[int(t * len(palette))]


def sample_mode(name: str, r: int, c: int, h: int, w: int, phase: float) -> str:
    """One continuous pattern sample; phase advances every frame."""
    x = c / max(w - 1, 1)
    y = r / max(h - 1, 1)
    # scroll speeds differ per mode so neighbours always differ
    scroll = phase  # 0..1 over full loop

    if name == "teal":
        # depth gradient + longitudinal scroll + micro-spots drifting aft→fore
        dorsal = 1.0 - y
        base = 0.15 + 0.55 * dorsal + 0.18 * math.sin(2 * math.pi * (x * 2.1 - scroll * 3))
        wave = math.sin(2 * math.pi * (x * 2.4 - scroll * 4) + y * 2.2)
        spots = math.sin(c * 0.85 + scroll * 28) * math.cos(r * 1.05 - scroll * 22)
        t = base + 0.22 * wave
        if spots > 0.72:
            return "h"
        if spots > 0.45:
            return "F"
        return _pick(TEAL, t)

    if name == "gold":
        crest = math.sin(2 * math.pi * (x * 1.35 - scroll * 3.5) + y * 1.4)
        under = math.sin(2 * math.pi * (x * 2.0 - scroll * 2.2) - y * 1.1)
        if crest > 0.55:
            return "g"
        if crest > 0.2:
            return "O"
        if crest > -0.05:
            return "o"
        if under > 0.4:
            return "T"
        if under > 0.0:
            return "C"
        return "B"

    if name == "coral":
        # leopard: discrete spots that migrate diagonally
        sx = math.sin(c * 0.58 + scroll * 18) * math.cos(r * 0.74 - scroll * 14)
        sy = math.sin((c + r) * 0.41 - scroll * 11)
        if sx > 0.55:
            return "p" if (c + r) % 2 else "m"
        if sx > 0.28:
            return "r"
        if sy > 0.55:
            return "O"
        if sx > 0.05:
            return "T"
        return "C" if y < 0.55 else "B"

    if name == "cyan":
        # bands scroll vertically with slight diagonal skew
        band_y = _wrap(scroll * 2.8 + x * 0.28)
        band = abs(y - band_y)
        band2 = abs(y - _wrap(band_y + 0.45))
        d = min(band, band2)
        if d < 0.07:
            return "s"
        if d < 0.13:
            return "F"
        if d < 0.2:
            return "T"
        ripple = math.sin(2 * math.pi * (x * 3 - scroll * 5) + y * 3)
        if ripple > 0.55:
            return "h"
        return "B" if y > 0.6 else "C"

    if name == "violet":
        flash = math.sin(2 * math.pi * (scroll * 5 + x * 4.2) + y * 1.5)
        spark = math.sin(c * 1.1 - scroll * 30) * math.cos(r * 0.9 + scroll * 24)
        if flash > 0.55 and spark > -0.2:
            return "v"
        if flash > 0.2:
            return "s" if (r + c + int(scroll * 40)) % 2 == 0 else "F"
        if spark > 0.65:
            return "m"
        return "B" if y > 0.62 else "C"

    if name == "riot":
        patch = int((c * 0.38 + r * 0.52 + scroll * 36)) % len(POP)
        wave = math.sin(2 * math.pi * (x * 1.8 - scroll * 4) + y * 2)
        strength = 0.35 + 0.65 * (0.5 + 0.5 * wave)
        if strength > 0.48:
            return POP[patch]
        return TEAL[(patch + int(scroll * 12)) % len(TEAL)]

    return "C"


def chroma(r: int, c: int, h: int, w: int, phase: float) -> str:
    """Blend mode samples by weight; always pick the winning mode's char.

    Continuous scroll inside each mode + soft mode crossfade means every
    frame differs from its neighbours even at lobe centres.
    """
    weights = mode_weights(phase)
    # Winner-take-most with a secondary accent: sample top-2 modes.
    ranked = sorted(weights.items(), key=lambda kv: kv[1], reverse=True)
    primary, w1 = ranked[0]
    secondary, w2 = ranked[1] if len(ranked) > 1 else (primary, 0.0)
    a = sample_mode(primary, r, c, h, w, phase)
    if w2 < 0.18:
        return a
    b = sample_mode(secondary, r, c, h, w, phase)
    # checker / noise blend so both modes stay visible during crossfade
    seed = math.sin(c * 2.1 + r * 1.7 + phase * 40)
    mix = w2 / (w1 + w2)
    if seed * 0.5 + 0.5 < mix:
        return b
    return a


def paint(base: list[list[str]], frame_i: int, n: int) -> list[str]:
    h, w = len(base), len(base[0])
    phase = frame_i / n  # seamless: frame 0 == phase after frame n-1+1
    out = [row[:] for row in base]

    for r, c in body_cells(base):
        out[r][c] = chroma(r, c, h, w, phase)

    for r, c in outline_fin_cells(base):
        shimmer = math.sin(2 * math.pi * (c / max(w, 1) * 3.5 - phase * 4) + r * 0.55)
        if shimmer > 0.4:
            out[r][c] = "F"
        elif shimmer > 0.0:
            out[r][c] = "T"
        else:
            out[r][c] = OUT

    # Arm tips tint during warmer / riot phases only (structure preserved)
    weights = mode_weights(phase)
    warm = weights.get("gold", 0) + weights.get("coral", 0) + weights.get("riot", 0)
    for r, row in enumerate(base):
        for c, ch in enumerate(row):
            if ch != ARM:
                continue
            tip = math.sin(2 * math.pi * ((c + r) * 0.15 - phase * 3))
            if warm > 0.35 and tip > 0.35 and (r + c + frame_i) % 3 == 0:
                out[r][c] = "o" if weights.get("gold", 0) + weights.get("coral", 0) > weights.get("riot", 0) else "v"
            else:
                out[r][c] = ARM

    # Guaranteed: eye / pupil never overwritten; fin tip F shimmers lightly
    for r, row in enumerate(base):
        for c, ch in enumerate(row):
            if ch in (EYE, PUP):
                out[r][c] = ch
            elif ch == "F" and (r <= 2 or r >= h - 3):
                tip = math.sin(2 * math.pi * (c / max(w, 1) * 4.2 - phase * 5))
                out[r][c] = "h" if tip > 0.5 else "F"

    return ["".join(row) for row in out]


def main() -> None:
    tight = crop_tight(normalize(RAW), pad=0)
    w = len(tight[0])
    assert all(len(r) == w for r in tight), "ragged after crop"

    frames = [paint(tight, i, N_FRAMES) for i in range(N_FRAMES)]

    # Sanity: consecutive frames must differ on body cells
    body = body_cells(tight)
    diffs = 0
    for i in range(N_FRAMES):
        a, b = frames[i], frames[(i + 1) % N_FRAMES]
        changed = sum(1 for r, c in body if a[r][c] != b[r][c])
        if changed == 0:
            raise SystemExit(f"static neighbour pair at frames {i}->{(i+1)%N_FRAMES}")
        diffs += changed
    avg_diff = diffs / N_FRAMES

    spec = {
        "scale": SCALE,
        "palette": PALETTE,
        "frames": frames,
        "durations": FRAME_MS,
    }
    root = Path(__file__).resolve().parent
    anim_path = root / "artist2-logo-animated.pixelart.json"
    anim_path.write_text(json.dumps(spec, indent=2) + "\n")

    # Poster: mid gold-wave phase (~mode centre for gold = 1/6)
    poster_i = int(round((1 / len(MODES)) * N_FRAMES)) % N_FRAMES
    static = {"scale": SCALE, "palette": PALETTE, "grid": frames[poster_i]}
    (root / "artist2-logo.pixelart.json").write_text(json.dumps(static, indent=2) + "\n")

    total_s = N_FRAMES * FRAME_MS / 1000.0
    print(f"size {w}x{len(tight)}  frames={N_FRAMES}  delay={FRAME_MS}ms  loop={total_s:.1f}s")
    print(f"avg body-cell changes vs next frame: {avg_diff:.1f}/{len(body)}")
    print(f"wrote {anim_path.name} + artist2-logo.pixelart.json (poster frame {poster_i})")


if __name__ == "__main__":
    main()
