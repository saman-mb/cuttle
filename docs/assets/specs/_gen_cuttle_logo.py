#!/usr/bin/env python3
"""Generate the Cuttle mascot: pixel-art cuttlefish poster + 30 s chromatophore loop.

Run this, then render the specs with the shipmates pixelart tool — see
`docs/assets/README.md` for the exact commands.

Technique notes (why the code is shaped like this):

* **Lighting from a surface model, not flat bands.** The mantle is treated as
  an ellipsoid; every pixel gets an approximate normal, and a single key light
  from the upper left drives a six-step ramp. That gives a core shadow, a
  terminator, bounce light and a rim for free — and avoids "pillow shading",
  where a sprite is merely darkened towards its outline.
* **Hue-shifted ramps.** Shadows shift cool (towards blue), highlights shift
  warm and desaturate. Saturation peaks mid-ramp; brightness never reaches
  pure black or pure white.
* **Selective outlines.** The outline is dark teal, not black, and it lightens
  where the key light strikes, so the sprite does not read as a sticker.
* **Ambient occlusion** where the arms meet the head and the fin meets the
  mantle; a **cast shadow** along the belly.
* **Dithering** only at ramp boundaries, one checkerboard row deep.
* **Anatomy** follows a real cuttlefish: a fin skirt running the whole mantle
  margin, eight arms (five read at this size) plus two longer club-tipped
  tentacles, a W-shaped pupil, and the species' own pattern vocabulary —
  zebra bands, mottle and an eye ring.
* **Expression.** The mascot is meant to look pleased to see you: arms lifted
  in a forward wave, a raised brow curve over a large eye, a bright specular
  catchlight, and a cheek highlight under the eye.
"""
from __future__ import annotations

import colorsys
import json
import math
from pathlib import Path

W, H = 104, 60

# ---------------------------------------------------------------- materials --
OUTLINE_DARK, OUTLINE_LIT = "ink0", "ink1"
SCLERA, PUPIL, SPEC, EYERING = "sclera", "pupil", "spec", "eyering"

# ---------------------------------------------------------------- geometry ---
CY = 29.0
TAIL_X, HEAD_X = 8.0, 58.0          # mantle span
NECK_X, HEAD_END = 58.0, 74.0       # head span
EYE_CX, EYE_CY, EYE_RX, EYE_RY = 64.0, 25.0, 7.0, 6.2
ARM_X, ARM_Y = 69.0, 34.5

# mantle half-height along its length: blunt at the head, tapering to the tail
PROFILE = [
    (0.00, 1.2), (0.05, 4.0), (0.12, 7.2), (0.22, 10.2), (0.35, 12.6),
    (0.50, 14.0), (0.64, 14.6), (0.78, 14.4), (0.90, 13.4), (1.00, 11.6),
]


def mantle_half(x: float) -> float:
    if x < TAIL_X or x > HEAD_X:
        return 0.0
    t = (x - TAIL_X) / (HEAD_X - TAIL_X)
    for (t0, h0), (t1, h1) in zip(PROFILE, PROFILE[1:]):
        if t0 <= t <= t1:
            k = (t - t0) / (t1 - t0)
            return h0 + (h1 - h0) * (k * k * (3 - 2 * k))
    return 0.0


def head_half(x: float) -> float:
    """The head is narrower than the mantle, with a slight neck constriction."""
    if x < NECK_X - 4 or x > HEAD_END:
        return 0.0
    t = (x - (NECK_X - 4)) / (HEAD_END - (NECK_X - 4))
    return 11.0 * (0.92 + 0.08 * math.cos(t * 3.2)) * math.cos(t * 0.98) ** 0.55


def half_at(x: float) -> float:
    return max(mantle_half(x), head_half(x))


def in_bounds(x, y):
    return 0 <= x < W and 0 <= y < H


def disc(cx, cy, r):
    return {(x, y)
            for x in range(int(cx - r - 1), int(cx + r + 2))
            for y in range(int(cy - r - 1), int(cy + r + 2))
            if in_bounds(x, y) and (x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2 <= r * r}


# ------------------------------------------------------------------ palette --
def hexcol(h_deg, s, v):
    r, g, b = colorsys.hsv_to_rgb((h_deg % 360) / 360.0, max(0.0, min(1.0, s)),
                                  max(0.0, min(1.0, v)))
    return "#%02x%02x%02x" % (round(r * 255), round(g * 255), round(b * 255))


RAMP_STEPS = 6


def ramp(hue_base: float, i: int) -> str:
    """One step of a hue-shifted ramp: cool in shadow, warm and pale in light.

    Saturation peaks mid-ramp; brightness never bottoms out or blows out.
    """
    k = i / (RAMP_STEPS - 1)                       # 0 dark .. 1 light
    hue = hue_base + 34.0 * (0.5 - k)              # shadows cool, lights warm
    sat = 0.30 + 0.46 * math.sin(math.pi * (0.18 + 0.72 * k))
    val = 0.20 + 0.76 * (k ** 0.82)
    return hexcol(hue, sat, val)


BODY_HUE = 174.0                                   # brand teal
ACCENT_FROM, ACCENT_TO = 176.0, 320.0              # teal -> violet -> magenta
STOPS = 20

BODY_CHARS = "012345"
FIN_CHARS = "fgh@"
ACCENT_CHARS = [
    "abcdeijklmnopqrstuvw",     # accent, shadow
    "ABCDEIJKLMNOPQRSTUVW",     # accent, mid
    "XYZ6789!$%&()*+,-/:;",     # accent, light
]
FIXED_CHARS = {
    OUTLINE_DARK: "#", OUTLINE_LIT: "=",
    SCLERA: "e", PUPIL: "p", SPEC: "s", EYERING: "r",
}


def build_palette() -> dict[str, str]:
    pal = {".": "#00000000"}
    for i, ch in enumerate(BODY_CHARS):
        pal[ch] = ramp(BODY_HUE, i)
    # the fin is thinner tissue: paler and slightly bluer than the mantle
    for i, ch in enumerate(FIN_CHARS):
        pal[ch] = hexcol(BODY_HUE + 6 - 5 * i, 0.34 - 0.09 * i, 0.74 + 0.11 * i)
    pal[FIN_CHARS[3]] = hexcol(BODY_HUE + 12, 0.44, 0.46)   # fin, underside
    for s in range(STOPS):
        k = s / STOPS * 2
        k = k if k <= 1 else 2 - k                 # ping-pong, never crosses green
        hue = ACCENT_FROM + (ACCENT_TO - ACCENT_FROM) * k
        pal[ACCENT_CHARS[0][s]] = hexcol(hue - 12, 0.62, 0.30)
        pal[ACCENT_CHARS[1][s]] = hexcol(hue, 0.66, 0.55)
        pal[ACCENT_CHARS[2][s]] = hexcol(hue + 14, 0.42, 0.88)
    pal[FIXED_CHARS[OUTLINE_DARK]] = hexcol(BODY_HUE + 16, 0.58, 0.14)
    pal[FIXED_CHARS[OUTLINE_LIT]] = hexcol(BODY_HUE + 6, 0.52, 0.30)
    pal[FIXED_CHARS[SCLERA]] = hexcol(BODY_HUE + 20, 0.06, 0.97)
    pal[FIXED_CHARS[PUPIL]] = hexcol(BODY_HUE + 18, 0.62, 0.12)
    pal[FIXED_CHARS[SPEC]] = "#ffffff"
    pal[FIXED_CHARS[EYERING]] = hexcol(BODY_HUE - 10, 0.62, 0.30)
    seen = set()
    for ch in pal:
        if ch in seen:
            raise SystemExit(f"palette character clash: {ch!r}")
        seen.add(ch)
    return pal


# ----------------------------------------------------------------- lighting --
LIGHT = (-0.42, -0.74, 0.52)                       # key light: upper left, front
_LN = math.sqrt(sum(c * c for c in LIGHT))
LIGHT = tuple(c / _LN for c in LIGHT)


def surface_level(x: int, y: int) -> float:
    """Approximate lambert term for a pixel on the ellipsoidal body, 0..1."""
    half = max(half_at(x + 0.5), 1.0)
    rel = max(-1.0, min(1.0, ((y + 0.5) - CY) / half))
    nz = math.sqrt(max(0.0, 1.0 - rel * rel))
    slope = (half_at(x + 1.5) - half_at(x - 0.5)) * 0.5
    nx = -slope / (abs(slope) + 2.6)
    ny = rel
    n = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
    d = (nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2]) / n
    bounce = 0.16 * max(0.0, rel) ** 2             # light kicking back off the sea floor
    return max(0.0, min(1.0, 0.5 + 0.62 * d + bounce))


def quantise(level: float, x: int, y: int, steps: int = RAMP_STEPS) -> int:
    """Ramp index, with a single checkerboard row of dithering at boundaries."""
    scaled = level * (steps - 1)
    i = int(scaled)
    frac = scaled - i
    if 0.40 < frac < 0.60 and (x + y) % 2 == 0:
        i += 1
    elif frac > 0.72:
        i += 1
    return max(0, min(steps - 1, i))


# ------------------------------------------------------------------- shapes --
def body_cells():
    cells = set()
    for x in range(W):
        h1, h2 = mantle_half(x + 0.5), head_half(x + 0.5)
        for y in range(H):
            dy = (y + 0.5) - CY
            if (h1 > 0 and abs(dy) <= h1) or (h2 > 0 and abs(dy + 2.0) <= h2):
                cells.add((x, y))
    return cells


BODY = body_cells()


def fin_cells(phase: float):
    """Skirt along the whole mantle margin, rippling head -> tail."""
    top, bottom = set(), set()
    for x in range(int(TAIL_X), int(HEAD_X) + 2):
        half = mantle_half(x + 0.5)
        if half <= 1.6:
            continue
        u = (x - TAIL_X) / (HEAD_X - TAIL_X)
        travel = phase - u * 5.0
        taper = min(1.0, 3.6 * min(u + 0.05, 1.05 - u))
        thick = (2.0 + 1.3 * math.sin(travel)) * taper
        lift_t = 2.4 * math.sin(travel) * taper
        lift_b = 1.4 * math.sin(travel + 0.8) * taper
        for k in range(int(round(max(thick, 0.0))) + 1):
            top.add((x, int(round(CY - half - k + lift_t))))
        for k in range(int(round(max(thick * 0.62, 0.0))) + 1):
            bottom.add((x, int(round(CY + half + k + lift_b))))
    return ({c for c in top if in_bounds(*c)}, {c for c in bottom if in_bounds(*c)})


# (start angle, bend over the limb, length, root thickness, sway phase).
# Angles lean upward at the root so the crown reads as a raised, friendly wave
# rather than a drooping bunch.
ARMS_BACK = [
    (-44.0, 40.0, 13.0, 2.4, 0.0),
    (40.0, 34.0, 12.0, 2.2, 2.2),
]
ARMS_FRONT = [
    (-30.0, 58.0, 18.0, 3.2, 0.9),
    (-4.0, 56.0, 21.0, 3.6, 1.8),
    (24.0, 48.0, 16.0, 3.0, 2.7),
]
TENTACLES = [
    (-28.0, 46.0, 24.0, 0.6),
    (8.0, 56.0, 26.0, 2.4),
]


def walk(a0, bend, length, thick, ph, t, club=False, sway_amp=7.0):
    """Tapering limb along a curving heading; returns its cells and sucker dots."""
    sway = sway_amp * math.sin(2 * math.pi * t * 2.5 + ph)
    cells, suckers = set(), []
    x, y = ARM_X - 5.0, ARM_Y
    steps = int(length * 8)
    for i in range(steps):
        u = i / steps
        ang = math.radians(a0 + bend * (u ** 1.3) + sway * (u ** 2))
        x += math.cos(ang) * (length / steps)
        y += math.sin(ang) * (length / steps)
        r = max(0.8, thick * (1.0 - 0.72 * u))
        if club and 0.74 < u < 0.95:
            r = max(r, 2.2)
        cells |= disc(x, y, r)
        if 0.22 < u < 0.90 and i % 9 == 0:
            nx, ny = math.sin(ang), -math.cos(ang)
            suckers.append((int(round(x + nx * r * 0.62)), int(round(y + ny * r * 0.62))))
    return cells, suckers


EYE = {(x, y) for x in range(W) for y in range(H)
       if ((x + 0.5 - EYE_CX) / EYE_RX) ** 2 + ((y + 0.5 - EYE_CY) / EYE_RY) ** 2 <= 1.0}

PUPIL_OFFSETS = [
    (-4, -1), (-4, 0), (-4, 1), (-3, 0), (-3, 1), (-3, 2),
    (-2, 1), (-2, 2), (-1, 0), (-1, 1),
    (0, -1), (0, 0), (0, 1),
    (1, 0), (1, 1), (2, 1), (2, 2),
    (3, 0), (3, 1), (3, 2), (4, -1), (4, 0), (4, 1),
]

# the species' own pattern vocabulary: zebra bands plus mottle clusters
ZEBRA = [(8, 1.1), (14, 0.6), (19, 1.4), (26, 0.6), (31, 1.1), (38, 1.4), (44, 0.6)]
MOTTLE = [(11, -0.30), (17, 0.34), (24, -0.52), (30, 0.20), (36, -0.38),
          (43, 0.42), (49, -0.24), (26, 0.58)]


# ------------------------------------------------------------------ drawing --
def is_body(val) -> bool:
    return isinstance(val, str) and val in BODY_CHARS


def blank():
    return [[None] * W for _ in range(H)]


def put(grid, x, y, val):
    if in_bounds(x, y):
        grid[y][x] = val


def outline(grid, cells):
    """Selective outline: dark, but lighter where the key light strikes."""
    for x, y in cells:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)):
            nx, ny = x + dx, y + dy
            if in_bounds(nx, ny) and grid[ny][nx] is None:
                lit = dy < 0 or (dx < 0 and dy <= 0)
                grid[ny][nx] = OUTLINE_LIT if lit else OUTLINE_DARK


def shade_cells(grid, cells, chars, lighten=0.0, darken=0.0):
    for x, y in cells:
        lvl = surface_level(x, y) + lighten - darken
        grid[y][x] = chars[quantise(lvl, x, y, len(chars))]


def shade_limb(grid, cells, lighten=0.0):
    """Limbs are tubes: lit along the top of each one, shading to the underside."""
    by_col: dict[int, list[int]] = {}
    for x, y in cells:
        by_col.setdefault(x, []).append(y)
    for x, ys in by_col.items():
        top, bottom = min(ys), max(ys)
        span = max(bottom - top, 1)
        for y in ys:
            k = (y - top) / span                       # 0 top .. 1 underside
            lvl = 0.80 - 0.42 * k + lighten - 0.004 * (y - ARM_Y)
            grid[y][x] = BODY_CHARS[quantise(lvl, x, y)]


def occlude(grid, cells, near, depth=1):
    """Ambient occlusion: darken body pixels sitting against another form."""
    for x, y in cells:
        if any((x + dx, y + dy) in near for dx in (-1, 0, 1) for dy in (-1, 0, 1)):
            cur = grid[y][x]
            if is_body(cur):
                grid[y][x] = BODY_CHARS[max(0, BODY_CHARS.index(cur) - depth)]


def render_grid(t: float, lid: float):
    grid = blank()
    accent = int(t * STOPS) % STOPS
    acc = [ACCENT_CHARS[i][accent] for i in range(3)]

    # --- limbs behind the head
    behind = set()
    for a0, bend, length, ph in TENTACLES:
        cells, _ = walk(a0, bend, length, 1.5, ph, t, club=True, sway_amp=9.0)
        behind |= cells
    for a0, bend, length, thick, ph in ARMS_BACK:
        cells, _ = walk(a0, bend, length, thick, ph, t)
        behind |= cells
    outline(grid, behind)
    shade_limb(grid, behind, lighten=-0.14)

    # --- fin skirt, welded to the mantle margin
    fin_top, fin_bottom = fin_cells(2 * math.pi * t * 12.5)
    fins = fin_top | fin_bottom
    outline(grid, fins)
    for x, y in fin_top:
        grid[y][x] = FIN_CHARS[2]
    for x, y in fin_bottom:
        grid[y][x] = FIN_CHARS[3]

    # --- mantle and head
    outline(grid, BODY)
    shade_cells(grid, BODY, BODY_CHARS)
    occlude(grid, BODY, fins)
    # crease along the mantle margin, so the fin reads as attached tissue
    # rather than a halo floating around the body
    for x in range(int(TAIL_X), int(HEAD_X) + 1):
        half = mantle_half(x + 0.5)
        if half <= 3.0:
            continue
        for y in (int(round(CY - half)), int(round(CY + half))):
            if in_bounds(x, y) and is_body(grid[y][x]):
                grid[y][x] = BODY_CHARS[max(0, BODY_CHARS.index(grid[y][x]) - 2)]
    # cast shadow along the belly, where the body turns away from the light
    for x, y in BODY:
        half = max(half_at(x + 0.5), 1.0)
        if ((y + 0.5) - CY) / half > 0.62 and is_body(grid[y][x]):
            grid[y][x] = BODY_CHARS[max(0, BODY_CHARS.index(grid[y][x]) - 1)]

    # --- chromatophore display: bands curve with the body and vary in depth,
    # lit by the same key light so they sit on the surface rather than floating
    wave = 2 * math.pi * t * 6.0
    span = HEAD_X - TAIL_X
    for i, (cx, hw) in enumerate(ZEBRA):
        bright = math.sin(wave - (cx / span) * 4.2)
        depth = 0.10 + 0.26 * ((i * 7) % 5) / 4.0        # how far down the flank
        for y in range(H):
            rel_row = ((y + 0.5) - CY)
            for x in range(W):
                half = mantle_half(x + 0.5)
                if half <= 3.0 or not is_body(grid[y][x]):
                    continue
                rel = rel_row / half
                if not (-0.84 < rel < -0.10 + depth):
                    continue
                bend = 1.6 * math.sin(rel * 1.7)          # bands wrap the mantle
                if abs((x - TAIL_X) - cx - bend) <= hw:
                    grid[y][x] = acc[quantise(surface_level(x, y) + 0.22 * bright,
                                              x, y, 3)]
    for cx, rel in MOTTLE:
        x = int(TAIL_X + cx)
        half = mantle_half(x + 0.5)
        y = int(CY + rel * half)
        for dx, dy in ((0, 0), (1, 0), (0, 1)):
            if in_bounds(x + dx, y + dy) and is_body(grid[y + dy][x + dx]):
                grid[y + dy][x + dx] = acc[quantise(surface_level(x + dx, y + dy),
                                                    x + dx, y + dy, 3)]

    # --- arms in front. Each arm is outlined against the arms behind it, so
    # the crown reads as separate limbs instead of one merged slab.
    drawn: list[set] = []
    front = set()
    for a0, bend, length, thick, ph in ARMS_FRONT:
        cells, suckers = walk(a0, bend, length, thick, ph, t)
        outline(grid, cells)
        shade_limb(grid, cells)
        for i, (sx, sy) in enumerate(suckers):
            if (sx, sy) in cells:
                put(grid, sx, sy, acc[2] if i % 2 else FIN_CHARS[2])
        for earlier in drawn:
            for x, y in earlier:
                if any((x + dx, y + dy) in cells
                       for dx in (-1, 0, 1) for dy in (-1, 0, 1)):
                    grid[y][x] = OUTLINE_DARK
        drawn.append(cells)
        front |= cells
    occlude(grid, BODY, front)

    draw_eye(grid, lid)
    return grid


def draw_eye(grid, lid: float):
    cols: dict[int, list[int]] = {}
    for x, y in EYE:
        cols.setdefault(x, []).append(y)

    if lid >= 0.9:
        for x, y in EYE:
            grid[y][x] = BODY_CHARS[quantise(surface_level(x, y), x, y)]
        xs = sorted(cols)
        for i, x in enumerate(xs):
            k = (i / max(len(xs) - 1, 1)) * 2 - 1
            y = int(round(EYE_CY + 1 + 1.6 * (1 - k * k)))
            if (x, y) in EYE:
                grid[y][x] = OUTLINE_DARK
        return

    outline(grid, EYE)
    for x, y in EYE:
        grid[y][x] = SCLERA
    # eye ring: a darker rim inside the sclera, as on a real cuttlefish
    for x, y in EYE:
        if any((x + dx, y + dy) not in EYE
               for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            grid[y][x] = EYERING
    for x, ys in cols.items():
        ys.sort()
        cut = ys[0] + int(round(lid * len(ys)))
        for y in ys:
            if y < cut:
                grid[y][x] = BODY_CHARS[quantise(surface_level(x, y), x, y)]
        if lid > 0.05 and cut - 1 in ys:
            grid[cut - 1][x] = OUTLINE_DARK
    if lid < 0.85:
        for dx, dy in PUPIL_OFFSETS:
            x, y = int(EYE_CX + dx) + 1, int(EYE_CY + dy) + 1
            if (x, y) in EYE and grid[y][x] == SCLERA:
                grid[y][x] = PUPIL
        for dx, dy in ((-2, -3), (-1, -3), (-2, -2)):
            x, y = int(EYE_CX + dx), int(EYE_CY + dy)
            if (x, y) in EYE and grid[y][x] != EYERING:
                grid[y][x] = SPEC
    # raised brow above the eye and a cheek highlight below it: the two marks
    # that make the face read as pleased rather than blank
    for i in range(-4, 5):
        bx = int(EYE_CX) + i
        by = int(EYE_CY - EYE_RY) - 1 - int(round(1.4 * (1 - (i / 4.5) ** 2)))
        if in_bounds(bx, by) and is_body(grid[by][bx]):
            grid[by][bx] = BODY_CHARS[min(len(BODY_CHARS) - 1,
                                          BODY_CHARS.index(grid[by][bx]) + 2)]
    for dx, dy in ((-3, 5), (-2, 5), (-2, 6)):
        cx2, cy2 = int(EYE_CX + dx), int(EYE_CY + dy)
        if in_bounds(cx2, cy2) and is_body(grid[cy2][cx2]):
            grid[cy2][cx2] = BODY_CHARS[min(len(BODY_CHARS) - 1,
                                            BODY_CHARS.index(grid[cy2][cx2]) + 1)]


# -------------------------------------------------------------------- loop ---
N_FRAMES, FRAME_MS = 150, 200
BLINKS = (30, 96)
BLINK_SHAPE = (0.62, 1.0, 0.72)
POSTER_FRAME = 45
SCALE = 8
SPECS = Path(__file__).parent


def lid_at(frame: int) -> float:
    for start in BLINKS:
        if start <= frame < start + len(BLINK_SHAPE):
            return BLINK_SHAPE[frame - start]
    return 0.0


def to_chars(grid):
    return ["".join("." if c is None else FIXED_CHARS.get(c, c) for c in row)
            for row in grid]


def render(t: float, lid: float = 0.0):
    return to_chars(render_grid(t, lid))


def crop(frames):
    used_r = {r for f in frames for r, row in enumerate(f) if row.strip(".")}
    used_c = {c for f in frames for row in f for c, ch in enumerate(row) if ch != "."}
    r0, r1, c0, c1 = min(used_r), max(used_r), min(used_c), max(used_c)
    return [[row[c0:c1 + 1] for row in f[r0:r1 + 1]] for f in frames]


def main():
    palette = build_palette()
    frames = crop([render(i / N_FRAMES, lid_at(i)) for i in range(N_FRAMES)])
    animated = {"scale": SCALE, "palette": palette, "frames": frames,
                "durations": [FRAME_MS] * N_FRAMES}
    poster = {"scale": SCALE, "palette": palette, "grid": frames[POSTER_FRAME]}
    (SPECS / "logo-animated.pixelart.json").write_text(json.dumps(animated))
    (SPECS / "logo.pixelart.json").write_text(json.dumps(poster))
    w, h = len(frames[0][0]), len(frames[0])
    print(f"wrote logo-animated.pixelart.json ({N_FRAMES} frames, {w}x{h} logical) "
          f"and logo.pixelart.json (frame {POSTER_FRAME})")


if __name__ == "__main__":
    main()
