#!/usr/bin/env python3
"""Generate tight-crop animated cuttlefish logo (chromatophore cycle).

Sepia side-view: mantle + undulating fin + W-pupil + short arm fan.
Body silhouette stable; colour is the motion (~30s seamless loop).
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
# Eye: explicit W-pupil (two lobes). Arms: short fingered fan, not a stump.
# All rows length 50 before crop.
RAW = [
#    0         1         2         3         4         5
#    01234567890123456789012345678901234567890123456789
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


def normalize(rows: list[str]) -> list[list[str]]:
    grid = []
    for row in rows:
        cells = []
        for ch in row:
            if ch == "#":
                cells.append(OUT)
            else:
                cells.append(ch)
        grid.append(cells)
    widths = {len(r) for r in grid}
    if len(widths) != 1:
        raise SystemExit(f"ragged rows: {widths}")
    return grid


def crop_tight(grid: list[list[str]], pad: int = 1) -> list[list[str]]:
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
    """Dark outline pixels that border empty space on dorsal/ventral edges."""
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


def chroma(r: int, c: int, h: int, w: int, phase: float, beat: int) -> str:
    x = c / max(w - 1, 1)
    y = r / max(h - 1, 1)
    dorsal = 1.0 - y
    base_i = int((0.2 + 0.6 * dorsal + 0.12 * math.sin(x * math.pi)) * (len(TEAL) - 1))
    ch = TEAL[max(0, min(len(TEAL) - 1, base_i))]

    wave = math.sin(2 * math.pi * (x * 1.7 - phase) + y * 2.0)
    pulse = math.sin(2 * math.pi * (phase * 2 + x * 0.7))
    spots = math.sin(c * 0.9 + phase * 12) * math.cos(r * 1.1 - phase * 9)

    # Seed a few permanent-ish accent micro-spots so even calm frames pop
    seed = (math.sin(c * 2.3 + r * 1.7) * math.cos(c * 0.4 - r)) 

    if beat in (0, 1, 14):
        if seed > 0.78 and beat == 0:
            ch = "g" if (c + r) % 2 else "o"
        elif seed > 0.72 and beat == 1:
            ch = "s" if c % 3 else "p"
        elif wave > 0.72:
            ch = "F"
        elif spots > 0.8:
            ch = "h"
        if beat == 14 and wave > 0.6:
            ch = "T"
        return ch

    if beat in (2, 3):
        crest = math.sin(2 * math.pi * (x - phase) * 1.15 + y * 1.2)
        if crest > 0.4:
            ch = "g"
        elif crest > 0.1:
            ch = "O"
        elif crest > -0.1:
            ch = "o"
        elif wave > 0.45:
            ch = "T"
        return ch

    if beat in (4, 5):
        cx, cy = 0.40, 0.50
        dist = math.hypot(x - cx, (y - cy) * 1.25)
        ring = abs(dist - (0.12 + 0.38 * ((phase * 2) % 1.0)))
        if ring < 0.07:
            ch = "o"
        elif ring < 0.13:
            ch = "O"
        elif pulse > 0.55:
            ch = "T"
        return ch

    if beat in (6, 7):
        # leopard: discrete roundish spots
        sx = math.sin(c * 0.62 + phase * 9) * math.cos(r * 0.78 - phase * 7)
        if sx > 0.58:
            ch = "p" if (c + r + beat) % 2 else "m"
        elif sx > 0.32:
            ch = "r"
        elif sx > 0.12:
            ch = "T"
        return ch

    if beat in (8, 9):
        band_y = 0.22 + 0.55 * ((phase * 1.2 + x * 0.35) % 1.0)
        band = abs(y - band_y)
        if band < 0.08:
            ch = "s"
        elif band < 0.15:
            ch = "F"
        elif wave > 0.5:
            ch = "T"
        return ch

    if beat in (10, 11):
        flash = math.sin(2 * math.pi * phase * 3 + x * 5)
        if flash > 0.5 and spots > -0.1:
            ch = "v"
        elif flash > 0.15:
            ch = "s" if (r + c) % 2 == 0 else "F"
        else:
            ch = "B" if y > 0.62 else "C"
        return ch

    if beat in (12, 13):
        # migrating diagonal riot
        patch = int((c * 0.35 + r * 0.55 + phase * 20)) % len(POP)
        strength = 0.4 + 0.6 * (0.5 + 0.5 * wave)
        if strength > 0.5:
            ch = POP[patch]
        else:
            ch = TEAL[(patch + beat) % len(TEAL)]
        return ch

    return ch


def paint(base: list[list[str]], beat: int, n: int) -> list[str]:
    h, w = len(base), len(base[0])
    phase = beat / n
    out = [row[:] for row in base]
    for r, c in body_cells(base):
        out[r][c] = chroma(r, c, h, w, phase, beat)

    # Fin shimmer — never erase fixed F tips; only shimmer OUTLINE fin cells
    for r, c in outline_fin_cells(base):
        shimmer = math.sin(2 * math.pi * (c / max(w, 1) * 3.2 - phase) + r * 0.5)
        if shimmer > 0.45:
            out[r][c] = "F"
        elif shimmer > 0.05:
            out[r][c] = "T"
        else:
            out[r][c] = OUT

    # Soft arm chromatophore kiss on arm tips (keep A structure, tint a few)
    for r, row in enumerate(base):
        for c, ch in enumerate(row):
            if ch != ARM:
                continue
            # outer arm pixels get a warm tip on riot / gold beats
            if beat in (2, 3, 12, 13) and (r + c + beat) % 4 == 0:
                out[r][c] = "o" if beat < 4 else "v"
            else:
                out[r][c] = ARM

    # Guaranteed: never overwrite eye / pupil (restored)
    for r, row in enumerate(base):
        for c, ch in enumerate(row):
            if ch in (EYE, PUP):
                out[r][c] = ch
            # Preserve intentional fin tip F from base
            if ch == "F" and base[r][c] == "F" and (r <= 2 or r >= h - 3):
                # allow mild shimmer on tips
                tip = math.sin(2 * math.pi * (c / w * 4 - phase))
                out[r][c] = "h" if tip > 0.55 else "F"

    return ["".join(row) for row in out]


def main() -> None:
    tight = crop_tight(normalize(RAW), pad=0)
    w = len(tight[0])
    assert all(len(r) == w for r in tight), "ragged after crop"

    n = 15
    frames = [paint(tight, i, n) for i in range(n)]

    spec = {
        "scale": 14,
        "palette": PALETTE,
        "frames": frames,
        "durations": 2000,
    }
    root = Path(__file__).resolve().parent
    anim = root / "artist1-logo-animated.pixelart.json"
    anim.write_text(json.dumps(spec, indent=2) + "\n")

    static = {"scale": 14, "palette": PALETTE, "grid": frames[3]}  # gold-wave poster (richer)
    (root / "artist1-logo.pixelart.json").write_text(json.dumps(static, indent=2) + "\n")
    # also publish canonical names for README wiring
    anim.write_text(json.dumps(spec, indent=2) + "\n")  # noop guard
    (root / "logo-animated.pixelart.json").write_text(json.dumps(spec, indent=2) + "\n")
    (root / "logo.pixelart.json").write_text(json.dumps(static, indent=2) + "\n")

    print(f"size {w}x{len(tight)}  frames={n}  loop={n * 2}s")
    for row in frames[0]:
        print(row)


if __name__ == "__main__":
    main()
