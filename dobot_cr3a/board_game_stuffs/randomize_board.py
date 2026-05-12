"""
Generate randomized variations of Board_w_Korea_cities.png.

Layout (16 perimeter cells):
    - 4 corner cells (TL, TR, BL, BR)
    - 3 side cells along TOP, RIGHT, BOTTOM, LEFT (12 total)

For each generated board:
  * The 4 corners are uniformly shuffled across the 4 corner positions, and
    each is independently rotated by a uniform random multiple of 90°.
    Cells are resized to fit their destination slot when sizes differ.
  * The 3 side cells on each side are uniformly shuffled within that side
    only (top stays top, etc.) so swapped content does not have to traverse
    differently-shaped rows / columns.
  * Grid lines are redrawn at every cell boundary so the black separators
    keep a uniform thickness regardless of resize artefacts.
  * The board interior (logo / whitespace) is preserved.

The source PNG is mildly asymmetric: the middle dividers in the top row do
not line up with those in the bottom row, so each side carries its own
coordinates (TOP_X vs BOTTOM_X).
"""

import argparse
import os
import random

from PIL import Image, ImageDraw

# Image dimensions the bounds were tuned for.
W = H = 1254

# Outer-corner extents (consistent across top / bottom and left / right).
LEFT_INNER  = 292   # x where the left column ends / inner area begins
RIGHT_INNER = 983
TOP_INNER   = 271   # y where the top row ends / inner area begins
BOT_INNER   = 969

# Cell-to-cell dividers within each side (top vs bottom differ; left and
# right share their horizontal dividers).
TOP_X    = [LEFT_INNER, 507, 761, RIGHT_INNER]
BOTTOM_X = [LEFT_INNER, 514, 732, RIGHT_INNER]
SIDE_Y   = [TOP_INNER, 519, 776, BOT_INNER]

# Grid-line style. Sized so the printed border is roughly 3 mm thick.
# Assuming a 30 cm x 30 cm printed board, 1254 px / 300 mm = ~4.18 px/mm,
# so 3 mm rounds to 13 px. Tune if the print size differs.
LINE_COLOR = (0, 0, 0)
LINE_WIDTH = 13

# CORNER_SLOTS index conventions: 0=TL, 1=TR, 2=BL, 3=BR.
# In the source image the GO cell lives at BL, so its source index is 2.
GO_SOURCE_INDEX = 2

# Allowed rotations for the GO cell, keyed by destination slot index.
# Stored as PIL CCW quarter-turns (rotate(90 * q, expand=True)):
#     0°       -> 0 quarters CCW
#     90° CW   -> 3 quarters CCW
#     180°     -> 2 quarters
#     270° CW  -> 1 quarter  CCW
GO_ROTATIONS_BY_SLOT = {
    0: (3, 2),  # TL: 90° CW or 180°
    1: (1, 2),  # TR: 270° CW or 180°
    2: (0, 3),  # BL: 0° (original) or 90° CW
    3: (0, 1),  # BR: 0° (original) or 270° CW
}


def _top_slots():
    return [(TOP_X[i], 0, TOP_X[i + 1], TOP_INNER) for i in range(3)]


def _bottom_slots():
    return [(BOTTOM_X[i], BOT_INNER, BOTTOM_X[i + 1], H) for i in range(3)]


def _left_slots():
    return [(0, SIDE_Y[i], LEFT_INNER, SIDE_Y[i + 1]) for i in range(3)]


def _right_slots():
    return [(RIGHT_INNER, SIDE_Y[i], W, SIDE_Y[i + 1]) for i in range(3)]


CORNER_SLOTS = [
    (0,           0,         LEFT_INNER, TOP_INNER),  # TL
    (RIGHT_INNER, 0,         W,          TOP_INNER),  # TR
    (0,           BOT_INNER, LEFT_INNER, H),          # BL
    (RIGHT_INNER, BOT_INNER, W,          H),          # BR
]

SIDE_SLOT_FACTORIES = [_top_slots, _right_slots, _bottom_slots, _left_slots]


def _paste_into(canvas, cell, slot, rotate_quarters=0):
    if rotate_quarters % 4 != 0:
        cell = cell.rotate(90 * (rotate_quarters % 4), expand=True)
    target = (slot[2] - slot[0], slot[3] - slot[1])
    if cell.size != target:
        cell = cell.resize(target, Image.LANCZOS)
    canvas.paste(cell, (slot[0], slot[1]))


def _hline(draw, x0, x1, y, anchor='center'):
    """Solid black horizontal line spanning x in [x0, x1] inclusive,
    LINE_WIDTH pixels thick. ``anchor`` controls how the strip aligns to y:
        'center' -> centered on y
        'top'    -> the strip starts at y and extends downward (used for the
                    image's top edge so it lies inside the canvas)
        'bottom' -> the strip ends at y and extends upward
    """
    w = LINE_WIDTH
    if anchor == 'top':
        y0, y1 = y, y + w - 1
    elif anchor == 'bottom':
        y0, y1 = y - w + 1, y
    else:
        half = w // 2
        y0, y1 = y - half, y - half + w - 1
    draw.rectangle([x0, y0, x1, y1], fill=LINE_COLOR)


def _vline(draw, y0, y1, x, anchor='center'):
    w = LINE_WIDTH
    if anchor == 'left':
        x0, x1 = x, x + w - 1
    elif anchor == 'right':
        x0, x1 = x - w + 1, x
    else:
        half = w // 2
        x0, x1 = x - half, x - half + w - 1
    draw.rectangle([x0, y0, x1, y1], fill=LINE_COLOR)


def _draw_grid(canvas):
    """Repaint every cell border at exactly LINE_WIDTH thickness.

    Every cell ends up with all four sides drawn:
      * Outer-edge sides come from the image-perimeter strokes.
      * Inner-facing sides (toward the logo) come from the inner-perimeter
        strokes at LEFT_INNER / RIGHT_INNER / TOP_INNER / BOT_INNER.
      * Cell-to-cell sides come from the per-side separator strokes.
    """
    draw = ImageDraw.Draw(canvas)

    # Outer perimeter -- pinned inside the image so nothing is clipped.
    _hline(draw, 0, W - 1, 0,     anchor='top')
    _hline(draw, 0, W - 1, H - 1, anchor='bottom')
    _vline(draw, 0, H - 1, 0,     anchor='left')
    _vline(draw, 0, H - 1, W - 1, anchor='right')

    # Inner perimeter (around the logo whitespace).
    _hline(draw, 0, W - 1, TOP_INNER)
    _hline(draw, 0, W - 1, BOT_INNER)
    _vline(draw, 0, H - 1, LEFT_INNER)
    _vline(draw, 0, H - 1, RIGHT_INNER)

    # Per-side cell-to-cell separators.
    for x in TOP_X[1:-1]:
        _vline(draw, 0, TOP_INNER, x)
    for x in BOTTOM_X[1:-1]:
        _vline(draw, BOT_INNER, H - 1, x)
    for y in SIDE_Y[1:-1]:
        _hline(draw, 0, LEFT_INNER, y)
        _hline(draw, RIGHT_INNER, W - 1, y)


def randomize_board(src_img, rng=None):
    if rng is None:
        rng = random
    canvas = src_img.copy()

    # Snapshot all cells from the unmodified source first.
    corner_cells = [src_img.crop(s) for s in CORNER_SLOTS]
    side_cells = [[src_img.crop(s) for s in factory()]
                  for factory in SIDE_SLOT_FACTORIES]

    # Shuffle the 4 corners across the 4 corner slots, with rotation.
    # The GO cell uses a position-conditional rotation set; other corners
    # spin freely in 90° steps.
    corner_perm = list(range(4))
    rng.shuffle(corner_perm)
    for dst_idx, src_idx in enumerate(corner_perm):
        if src_idx == GO_SOURCE_INDEX:
            rot = rng.choice(GO_ROTATIONS_BY_SLOT[dst_idx])
        else:
            rot = rng.randint(0, 3)
        _paste_into(canvas, corner_cells[src_idx],
                    CORNER_SLOTS[dst_idx], rotate_quarters=rot)

    # Shuffle the 3 cells on each side, within that side only.
    for cells, factory in zip(side_cells, SIDE_SLOT_FACTORIES):
        slots = factory()
        perm = list(range(3))
        rng.shuffle(perm)
        for dst_idx, src_idx in enumerate(perm):
            _paste_into(canvas, cells[src_idx], slots[dst_idx])

    # Repaint cell separators so every border has uniform thickness.
    _draw_grid(canvas)
    return canvas


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument('--src',
                        default=os.path.join(here, 'Board_w_Korea_cities.png'))
    parser.add_argument('--out-dir',
                        default=os.path.join(here, 'generated_boards'))
    parser.add_argument('--count', type=int, default=20)
    parser.add_argument('--seed', type=int, default=None)
    parser.add_argument('--prefix', default='board')
    args = parser.parse_args()

    src = Image.open(args.src).convert('RGB')
    if src.size != (W, H):
        print(f'[warn] source size is {src.size}; '
              f'cell bounds were tuned for {W}x{H}')

    os.makedirs(args.out_dir, exist_ok=True)
    rng = random.Random(args.seed)
    for i in range(args.count):
        out = randomize_board(src, rng=rng)
        path = os.path.join(args.out_dir, f'{args.prefix}_{i:04d}.png')
        out.save(path)
        print(f'wrote {path}')


if __name__ == '__main__':
    main()
