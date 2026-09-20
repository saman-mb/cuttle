#!/usr/bin/env python3
"""Generate tight-crop animated cuttlefish logo (continuous chromatophore cycle).

Sepia side-view: mantle + undulating fin + W-pupil + short arm fan.
Body silhouette stable; colour is the motion — dense frames, ~30s seamless loop.
No long still holds: every frame advances phase so colour keeps scrolling.
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

# Hand-drawn Sepia, facing RIGHT. # = outline (→ D). B = animating mantle.
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

# Six display moods, crossfaded continuously across the loop (no hard cuts / holds).
# Each mood returns a palette char for a body cell.
MOODS = ("teal", "gold", "leopard", "cyan", "violet", "riot")

# Dense continuous motion: 150 frames × 200ms = 30.0s
N_FRAMES = 150
FRAME_MS = 200


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


def mood_weights(phase: float) -> list[float]:
    """Soft overlap of 6 moods across [0,1); always at least two active."""
    n = len(MOODS)
    # each mood peaks every 1/n of the loop; width ~0.28 so neighbours blend
    width = 0.28
    weights = []
    for i in range(n):
        center = (i + 0.5) / n
        d = abs(phase - center)
        d = min(d, 1.0 - d)  # circular
        w = max(0.0, 1.0 - d / width)
        weights.append(w * w)  # ease
    s = sum(weights) or 1.0
    return [w / s for w in weights]


def sample_mood(mood: str, r: int, c: int, h: int, w: int, phase: float) -> str:
    x = c / max(w - 1, 1)
    y = r / max(h - 1, 1)
    # scrolling phase so colour always migrates left→right (and wraps)
    scroll = phase * 3.0  # ~3 full body scrolls per loop

    if mood == "teal":
        dorsal = 1.0 - y
        base_i = int((0.15 + 0.7 * dorsal + 0.15 * math.sin(x * math.pi + scroll * 2)) * (len(TEAL) - 1))
        ch = TEAL[max(0, min(len(TEAL) - 1, base_i))]
        wave = math.sin(2 * math.pi * (x * 2.0 - scroll) + y * 2.2)
        spots = math.sin(c * 0.95 + scroll * 14) * math.cos(r * 1.15 - scroll * 11)
        if wave > 0.55:
            ch = "F"
        elif spots > 0.72:
            ch = "h"
        elif wave < -0.55:
            ch = "B"
        return ch

    if mood == "gold":
        crest = math.sin(2 * math.pi * (x - scroll) * 1.35 + y * 1.4)
        if crest > 0.35:
            return "g"
        if crest > 0.05:
            return "O"
        if crest > -0.2:
            return "o"
        return "T" if math.sin(2 * math.pi * (x * 1.5 - scroll) + y) > 0 else "C"

    if mood == "leopard":
        sx = math.sin(c * 0.68 + scroll * 11) * math.cos(r * 0.82 - scroll * 8)
        # migrate spots by offsetting sample coords with phase
        sx2 = math.sin((c + scroll * 40) * 0.55) * math.cos((r - scroll * 28) * 0.7)
        v = 0.55 * sx + 0.45 * sx2
        if v > 0.55:
            return "p" if (c + r) % 2 else "m"
        if v > 0.28:
            return "r"
        if v > 0.08:
            return "T"
        return "B"

    if mood == "cyan":
        band_y = 0.18 + 0.64 * ((scroll * 0.85 + x * 0.4) % 1.0)
        band = abs(y - band_y)
        wave = math.sin(2 * math.pi * (x * 1.8 - scroll) + y * 1.5)
        if band < 0.07:
            return "s"
        if band < 0.14:
            return "F"
        if wave > 0.4:
            return "T"
        return "C" if y < 0.55 else "B"

    if mood == "violet":
        flash = math.sin(2 * math.pi * scroll * 2.2 + x * 5.5 + y * 1.2)
        spots = math.sin(c * 1.1 - scroll * 16) * math.cos(r * 0.9 + scroll * 10)
        if flash > 0.45 and spots > -0.15:
            return "v"
        if flash > 0.1:
            return "s" if (r + c + int(scroll * 20)) % 2 == 0 else "F"
        return "B" if y > 0.6 else "C"

    # riot
    patch = int((c * 0.4 + r * 0.5 + scroll * 28)) % len(POP)
    wave = math.sin(2 * math.pi * (x * 1.6 - scroll) + y * 2.0)
    strength = 0.35 + 0.65 * (0.5 + 0.5 * wave)
    if strength > 0.48:
        return POP[patch]
    return TEAL[(patch + int(scroll * 10)) % len(TEAL)]


def chroma(r: int, c: int, h: int, w: int, phase: float) -> str:
    weights = mood_weights(phase)
    # Pick winner + runner-up; dither by cell so blends look like chromatophore patches
    ranked = sorted(range(len(MOODS)), key=lambda i: weights[i], reverse=True)
    i0, i1 = ranked[0], ranked[1]
    w0, w1 = weights[i0], weights[i1]
    # cell hash picks primary vs secondary when close
    cell = (math.sin(c * 3.1 + r * 2.7) * 0.5 + 0.5)
    if w1 > 0.22 and cell > w0 / (w0 + w1 + 1e-9):
        mood = MOODS[i1]
    else:
        mood = MOODS[i0]
    return sample_mood(mood, r, c, h, w, phase)


def paint(base: list[list[str]], frame: int, n: int) -> list[str]:
    h, w = len(base), len(base[0])
    phase = frame / n
    out = [row[:] for row in base]
    for r, c in body_cells(base):
        out[r][c] = chroma(r, c, h, w, phase)

    for r, c in outline_fin_cells(base):
        shimmer = math.sin(2 * math.pi * (c / max(w, 1) * 3.2 - phase * 3) + r * 0.5)
        if shimmer > 0.4:
            out[r][c] = "F"
        elif shimmer > 0.0:
            out[r][c] = "T"
        else:
            out[r][c] = OUT

    # Arm tip colour kiss tracks riot/gold-ish phases
    for r, row in enumerate(base):
        for c, ch in enumerate(row):
            if ch != ARM:
                continue
            tip = math.sin(2 * math.pi * (phase * 2 + (c + r) * 0.15))
            if tip > 0.55 and (r + c + frame) % 3 == 0:
                out[r][c] = "o" if phase % 1 < 0.5 else "v"
            else:
                out[r][c] = ARM

    for r, row in enumerate(base):
        for c, ch in enumerate(row):
            if ch in (EYE, PUP):
                out[r][c] = ch
            if ch == "F" and (r <= 2 or r >= h - 3):
                tip = math.sin(2 * math.pi * (c / max(w, 1) * 4 - phase * 3))
                out[r][c] = "h" if tip > 0.5 else "F"

    return ["".join(row) for row in out]


def main() -> None:
    tight = crop_tight(normalize(RAW), pad=0)
    w = len(tight[0])
    assert all(len(r) == w for r in tight), "ragged after crop"

    n = N_FRAMES
    frames = [paint(tight, i, n) for i in range(n)]

    # Pick a vivid mid-loop poster (gold-leaning ~frame at mood center 1.5/6)
    poster_i = int(n * (1.5 / len(MOODS))) % n

    spec = {
        "scale": 14,
        "palette": PALETTE,
        "frames": frames,
        "durations": FRAME_MS,
    }
    root = Path(__file__).resolve().parent
    anim = root / "artist1-logo-animated.pixelart.json"
    anim.write_text(json.dumps(spec, indent=2) + "\n")

    static = {"scale": 14, "palette": PALETTE, "grid": frames[poster_i]}
    (root / "artist1-logo.pixelart.json").write_text(json.dumps(static, indent=2) + "\n")
    (root / "logo-animated.pixelart.json").write_text(json.dumps(spec, indent=2) + "\n")
    (root / "logo.pixelart.json").write_text(json.dumps(static, indent=2) + "\n")

    print(f"size {w}x{len(tight)}  frames={n}  ms={FRAME_MS}  loop={n * FRAME_MS / 1000:.1f}s  poster={poster_i}")


if __name__ == "__main__":
    main()
