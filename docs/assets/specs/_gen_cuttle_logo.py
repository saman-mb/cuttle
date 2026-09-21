#!/usr/bin/env python3
"""Generate the Cuttle mascot: pixel-art cuttlefish poster + 30 s chromatophore loop.

Run this, then render the specs with the shipmates pixelart tool — see
`docs/assets/README.md` for the exact commands.

Built to the art direction:
  * value structure first — a fixed 5-step teal ramp lit from the upper left,
    so the animal reads in greyscale, not just in hue;
  * hue rotation is confined to the chromatophore stripes and to the
    teal -> cyan -> violet -> magenta arc (170-320 deg), never the whole body;
  * the stripe layout never moves or re-randomises; a brightness wave travels
    head -> tail through it;
  * fins undulate on a short sine with a phase offset along the mantle;
  * the eye blinks twice per loop, off the beat.
"""
from __future__ import annotations

import colorsys
import json
import math
import sys
from pathlib import Path

W, H = 96, 54

# ---------------------------------------------------------------- materials --
(EMPTY, INK, RIM, B0, B1, B2, B3, B4, FIN0, FIN1,
 ARM0, ARM1, ARM2, SUCK, SCLERA, PUPIL, SPEC, ST0, ST1, ST2) = range(20)

BODY_MATS = (B0, B1, B2, B3, B4)

# ---------------------------------------------------------------- geometry ---
CY = 27.0
TAIL_X, HEAD_X = 7.0, 56.0     # mantle span
HEAD_END = 70.0
EYE_CX, EYE_CY, EYE_RX, EYE_RY = 58.5, 23.0, 6.8, 5.8
ARM_X, ARM_Y = 62.0, 33.0

PROFILE = [
    (0.00, 0.6), (0.04, 2.2), (0.10, 4.8), (0.20, 8.2), (0.34, 11.4),
    (0.50, 13.4), (0.64, 14.2), (0.78, 14.0), (0.90, 12.8), (1.00, 10.6),
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
    if x < HEAD_X - 4 or x > HEAD_END:
        return 0.0
    t = (x - (HEAD_X - 4)) / (HEAD_END - (HEAD_X - 4))
    return 11.4 * (1 - 0.34 * t * t) * math.cos(t * 0.92) ** 0.5


def in_bounds(x, y):
    return 0 <= x < W and 0 <= y < H


def disc(cx, cy, r):
    out = set()
    for x in range(int(cx - r - 1), int(cx + r + 2)):
        for y in range(int(cy - r - 1), int(cy + r + 2)):
            if in_bounds(x, y) and (x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2 <= r * r:
                out.add((x, y))
    return out


# ------------------------------------------------------------------ shapes ---
def body_cells():
    cells = set()
    for x in range(W):
        h1, h2 = mantle_half(x + 0.5), head_half(x + 0.5)
        for y in range(H):
            dy = (y + 0.5) - CY
            if (h1 > 0 and abs(dy) <= h1) or (h2 > 0 and abs(dy + 1.6) <= h2):
                cells.add((x, y))
    return cells


BODY = body_cells()


def fin_cells(phase: float):
    """Skirt welded to the mantle edge, rippling head -> tail."""
    cells = set()
    for x in range(int(TAIL_X), int(HEAD_X) + 2):
        half = mantle_half(x + 0.5)
        if half <= 2.0:
            continue
        u = (x - TAIL_X) / (HEAD_X - TAIL_X)
        travel = phase - u * 4.4
        taper = min(1.0, 3.4 * min(u + 0.06, 1.06 - u))
        thick = (3.6 + 2.0 * math.sin(travel)) * taper
        lift_t = 2.6 * math.sin(travel) * taper
        lift_b = 1.8 * math.sin(travel + 0.7) * taper
        for k in range(int(round(max(thick, 0.0))) + 1):
            cells.add((x, int(round(CY - half - k + lift_t))))
            cells.add((x, int(round(CY + half + k + lift_b))))
    return {c for c in cells if in_bounds(*c)}


# (start angle deg, bend deg over the arm, length, root thickness, sway phase)
# angles measured from horizontal, positive downward; the crown hangs from
# under the head and curls forward
ARMS_BACK = [
    (-26.0, 34.0, 15.0, 2.4, 0.0),
    (34.0, 44.0, 14.0, 2.4, 2.2),
]
ARMS_FRONT = [
    (-12.0, 40.0, 19.0, 3.2, 0.9),
    (6.0, 46.0, 21.0, 3.6, 1.8),
    (22.0, 52.0, 17.0, 3.0, 2.7),
]
TENTACLES = [
    (-6.0, 46.0, 25.0, 0.6),
    (16.0, 54.0, 27.0, 2.4),
]


def walk(a0, bend, length, thick, ph, t, club=False, sway_amp=7.0):
    """Walk a tapering tentacle along a curving heading; returns cells + suckers."""
    sway = sway_amp * math.sin(2 * math.pi * t * 2.5 + ph)
    cells, suckers = set(), []
    steps = int(length * 8)
    x, y = ARM_X - 4.0, ARM_Y
    for i in range(steps):
        u = i / steps
        ang = math.radians(a0 + bend * (u ** 1.3) + sway * (u ** 2))
        x += math.cos(ang) * (length / steps)
        y += math.sin(ang) * (length / steps)
        r = max(0.8, thick * (1.0 - 0.72 * u))
        if club and 0.74 < u < 0.95:
            r = max(r, 2.2)
        cells |= disc(x, y, r)
        if 0.22 < u < 0.90 and i % 10 == 0:
            nx, ny = math.sin(ang), -math.cos(ang)      # arm normal
            suckers.append((int(round(x + nx * r * 0.6)), int(round(y + ny * r * 0.6))))
    return cells, suckers


def arm_path(spec, t):
    a0, bend, length, thick, ph = spec
    return walk(a0, bend, length, thick, ph, t)


def tentacle_cells(spread, curl, ph, t):
    sway = 2.2 * math.sin(2 * math.pi * t * 1.6 + ph)
    cells = set()
    L = 26.0
    steps = int(L * 7)
    for i in range(steps):
        u = i / steps
        ease = u ** 1.8
        x = ARM_X - 3 + u * L * (1.0 - 0.14 * ease)
        y = ARM_Y + spread * (0.15 + 0.5 * u) + curl * ease + sway * ease
        cells |= disc(x, y, 2.4 if 0.76 < u < 0.94 else 1.4)
    return cells


EYE = {
    (x, y)
    for x in range(W) for y in range(H)
    if ((x + 0.5 - EYE_CX) / EYE_RX) ** 2 + ((y + 0.5 - EYE_CY) / EYE_RY) ** 2 <= 1.0
}

# W-shaped cuttlefish pupil, drawn relative to the eye centre (offset forward)
PUPIL_OFFSETS = [
    # a fat W: outer uprights, inner uprights, and the centre peak
    (-4, -1), (-4, 0), (-4, 1), (-3, 0), (-3, 1), (-3, 2),
    (-2, 1), (-2, 2), (-1, 0), (-1, 1),
    (0, -1), (0, 0), (0, 1),
    (1, 0), (1, 1), (2, 1), (2, 2),
    (3, 0), (3, 1), (3, 2), (4, -1), (4, 0), (4, 1),
]

# fixed chromatophore layout: (centre along the mantle 0..1, half-width in px)
# (centre px from the tail, half-width px) — irregular on purpose, so it
# reads as chromatophore banding rather than a barcode
BANDS = [(6, 1.5), (13, 1.0), (18, 2.0), (26, 1.0), (31, 1.5), (39, 2.0), (45, 1.0)]
SPECKS = [(0.20, -0.62), (0.33, 0.48), (0.45, -0.30), (0.57, 0.64),
          (0.68, -0.52), (0.78, 0.30), (0.88, -0.44), (0.30, 0.20)]


def stamp(grid, cells, mat, ink=True):
    if ink:
        for x, y in cells:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)):
                n = (x + dx, y + dy)
                if in_bounds(*n) and n not in cells:
                    grid[n[1]][n[0]] = INK
    for x, y in cells:
        grid[y][x] = mat


def shade_body(grid):
    """Light from the upper left: five value steps plus a one-pixel rim."""
    for x in range(W):
        half = max(mantle_half(x + 0.5), head_half(x + 0.5), 1.0)
        col = [y for y in range(H) if grid[y][x] in BODY_MATS]
        if not col:
            continue
        top = min(col)
        for y in col:
            rel = ((y + 0.5) - CY) / half
            if y <= top:
                grid[y][x] = RIM
            elif rel < -0.62:
                grid[y][x] = B4
            elif rel < -0.22:
                grid[y][x] = B3
            elif rel < 0.26:
                grid[y][x] = B2
            elif rel < 0.62:
                grid[y][x] = B1
            else:
                grid[y][x] = B0


def stripe_level(u: float, wave_phase: float) -> int:
    """Brightness of the chromatophore at mantle position u, 0..2."""
    v = math.sin(wave_phase - u * 4.2)
    return 2 if v > 0.45 else (1 if v > -0.35 else 0)


def add_chromatophores(grid, wave_phase: float):
    span = HEAD_X - TAIL_X
    for x in range(W):
        half = mantle_half(x + 0.5)
        if half <= 3.0:
            continue
        u = (x - TAIL_X) / span
        for cx, hw in BANDS:
            if abs((x - TAIL_X) - cx) <= hw:
                lvl = stripe_level(cx / span, wave_phase)
                for y in range(H):
                    if grid[y][x] not in BODY_MATS:
                        continue
                    rel = ((y + 0.5) - CY) / half
                    if -0.80 < rel < 0.10:
                        grid[y][x] = (ST0, ST1, ST2)[lvl]
    for cu, rel in SPECKS:
        x = int(TAIL_X + cu * span)
        half = mantle_half(x + 0.5)
        y = int(CY + rel * half)
        if in_bounds(x, y) and grid[y][x] in BODY_MATS:
            grid[y][x] = (ST0, ST1, ST2)[stripe_level(cu, wave_phase)]


def draw_eye(grid, lid: float):
    cols: dict[int, list[int]] = {}
    for x, y in EYE:
        cols.setdefault(x, []).append(y)

    if lid >= 0.9:
        # shut: the eye disappears into the head, leaving a curved lash line
        for x, y in EYE:
            grid[y][x] = B3 if y < CY - 3 else B2
        xs = sorted(cols)
        for i, x in enumerate(xs):
            k = (i / max(len(xs) - 1, 1)) * 2 - 1        # -1..1 across the eye
            y = int(round(EYE_CY + 1 + 1.6 * (1 - k * k)))
            if (x, y) in EYE:
                grid[y][x] = INK
        return

    stamp(grid, EYE, SCLERA)
    for x, ys in cols.items():
        ys.sort()
        cut = ys[0] + int(round(lid * len(ys)))
        for y in ys:
            if y < cut:
                grid[y][x] = B3 if y < CY - 3 else B2
        if lid > 0.05 and cut - 1 in ys:
            grid[cut - 1][x] = INK
    if lid < 0.85:
        for dx, dy in PUPIL_OFFSETS:
            x, y = int(EYE_CX + dx) + 1, int(EYE_CY + dy) + 1
            if (x, y) in EYE and grid[y][x] == SCLERA:
                grid[y][x] = PUPIL
        for dx, dy in ((-2, -3), (-1, -3), (-2, -2)):
            x, y = int(EYE_CX + dx), int(EYE_CY + dy)
            if (x, y) in EYE:
                grid[y][x] = SPEC


def render_grid(t: float, lid: float):
    grid = [[EMPTY] * W for _ in range(H)]
    fin_phase = 2 * math.pi * t * 12.5          # ~12 frames per ripple
    # depth order: back tentacles, back arms, fin, body+head, front arms, eye
    for a0, bend, length, ph in TENTACLES:
        cells, _ = walk(a0, bend, length, 1.5, ph, t, club=True, sway_amp=9.0)
        stamp(grid, cells, ARM0)
    for spec in ARMS_BACK:
        cells, _ = arm_path(spec, t)
        stamp(grid, cells, ARM0)
    stamp(grid, fin_cells(fin_phase), FIN0)
    stamp(grid, BODY, B2)
    shade_body(grid)
    add_chromatophores(grid, 2 * math.pi * t * 6.0)
    for i, spec in enumerate(ARMS_FRONT):
        cells, suckers = arm_path(spec, t)
        stamp(grid, cells, (ARM1, ARM2, ARM1)[i])
        for sx, sy in suckers:
            if in_bounds(sx, sy) and (sx, sy) in cells:
                grid[sy][sx] = SUCK
    draw_eye(grid, lid)
    # fin highlight: brighten the outer edge of the skirt
    for x in range(W):
        fins = [y for y in range(H) if grid[y][x] == FIN0]
        if fins:
            grid[min(fins)][x] = FIN1
    return grid


# ---------------------------------------------------------------- palette ---
INK_HEX = "#042f2e"
FIXED = {
    ".": "#00000000",
    "#": INK_HEX,
    "R": "#99f6e4",   # rim light
    "0": "#134e4a",   # belly
    "1": "#0f766e",
    "2": "#0d9488",
    "3": "#14b8a6",
    "4": "#5eead4",   # lit back
    "f": "#2dd4bf",   # fin
    "F": "#99f6e4",   # fin edge
    "m": "#0b5450",   # arms: shadowed, mid, lit — inside the body ramp
    "n": "#0f766e",
    "o": "#149c92",
    "~": "#99f6e4",   # suckers
    "E": "#ecfdf5",   # sclera
    "P": INK_HEX,     # pupil
    "S": "#ffffff",   # specular
}

STOPS = 20                        # hue stops around the restricted arc
HUE_FROM, HUE_TO = 170.0, 320.0   # teal -> cyan -> violet -> magenta
ST_CHARS = ("abcdeghijklpqrstvwxy", "ABCDGHIJKLMNOQTUVWXY", "uz56789!$%&()*+,-/:;")


def hexcol(h_deg, s, v):
    r, g, b = colorsys.hsv_to_rgb((h_deg % 360) / 360.0, s, v)
    return "#%02x%02x%02x" % (int(r * 255), int(g * 255), int(b * 255))


def build_palette():
    pal = dict(FIXED)
    pool = "".join(ST_CHARS)
    clash = set(pool) & set(FIXED) or (len(set(pool)) != len(pool))
    if clash:
        raise SystemExit(f"palette character clash: {clash}")
    for i in range(STOPS):
        # ping-pong the arc so the loop returns home without crossing the greens
        k = i / STOPS * 2
        k = k if k <= 1 else 2 - k
        hue = HUE_FROM + (HUE_TO - HUE_FROM) * k
        pal[ST_CHARS[0][i]] = hexcol(hue, 0.78, 0.36)   # stripe, dark phase
        pal[ST_CHARS[1][i]] = hexcol(hue, 0.70, 0.62)   # stripe, mid
        pal[ST_CHARS[2][i]] = hexcol(hue, 0.52, 0.92)   # stripe, lit
    return pal


def to_chars(grid, t):
    i = int(t * STOPS) % STOPS
    m = {
        EMPTY: ".", INK: "#", RIM: "R", B0: "0", B1: "1", B2: "2", B3: "3", B4: "4",
        FIN0: "f", FIN1: "F", ARM0: "m", ARM1: "n", ARM2: "o", SUCK: "~",
        SCLERA: "E", PUPIL: "P", SPEC: "S",
        ST0: ST_CHARS[0][i], ST1: ST_CHARS[1][i], ST2: ST_CHARS[2][i],
    }
    return ["".join(m[c] for c in row) for row in grid]


# -------------------------------------------------------------------- loop ---
N_FRAMES, FRAME_MS = 150, 200
BLINKS = (30, 96)                  # ~6 s and ~19 s into the loop
BLINK_SHAPE = (0.62, 1.0, 0.72)    # half, shut, half


def lid_at(frame: int) -> float:
    for start in BLINKS:
        if start <= frame < start + len(BLINK_SHAPE):
            return BLINK_SHAPE[frame - start]
    return 0.0


def render(t: float, lid: float = 0.0):
    return to_chars(render_grid(t, lid), t)


def crop(frames):
    used_r = {r for f in frames for r, row in enumerate(f) if row.strip(".")}
    used_c = {c for f in frames for row in f for c, ch in enumerate(row) if ch != "."}
    r0, r1, c0, c1 = min(used_r), max(used_r), min(used_c), max(used_c)
    return [[row[c0:c1 + 1] for row in f[r0:r1 + 1]] for f in frames]


POSTER_FRAME = 45          # mid-loop: violet banding over the teal body
SCALE = 8
SPECS = Path(__file__).parent


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
