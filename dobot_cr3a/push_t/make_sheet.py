"""Draw the PushT sheet texture for 9a_imitation_push_t_simulation.usd.

White sheet with the goal T filled black. Geometry (sheet size, T proportions, goal pose) comes
from movensys-imitation's ``movensys_imitation/tasks/pusht/geometry.py`` so the sheet matches the
imitation repo's task, scorer and printed sheet.

    python3 dobot_cr3a/push_t/make_sheet.py [--imitation ~/movensys-imitation]

Needs numpy and Pillow (system python3 has both). Writes ``target_sheet.png`` next to this file.
"""

from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
PX_PER_M = 2000  # 0.60 x 0.30 m sheet -> 1200 x 600 px
GOAL_RGB = (0, 0, 0)  # goal T, filled black
SHEET_RGB = (255, 255, 255)  # white background


def load_geometry(imitation: Path):
    # Load geometry.py on its own: importing the movensys_imitation package pulls in torch.
    path = imitation / "movensys_imitation/tasks/pusht/geometry.py"
    spec = importlib.util.spec_from_file_location("pusht_geometry", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--imitation", type=Path, default=Path.home() / "movensys-imitation")
    ap.add_argument("--out", type=Path, default=HERE / "target_sheet.png")
    args = ap.parse_args()

    g = load_geometry(args.imitation)
    sw, sh = g.SHEET_SIZE
    w, h = round(sw * PX_PER_M), round(sh * PX_PER_M)

    def px(x: float, y: float) -> tuple[float, float]:
        # Sheet frame (origin at centre, +y away from the operator) to image pixels. The scene's
        # quad maps st (0, 0) to the sheet's (-x, -y) corner and image row 0 is st t = 1.
        return ((x + sw / 2) * PX_PER_M, (sh / 2 - y) * PX_PER_M)

    img = Image.new("RGB", (w, h), SHEET_RGB)
    goal = g.block_polygon(g.goal_pose())
    ImageDraw.Draw(img).polygon([px(x, y) for x, y in goal], fill=GOAL_RGB)
    img.save(args.out)
    print(f"wrote {args.out} ({w} x {h} px), goal pose {tuple(round(v, 4) for v in g.goal_pose())}")


if __name__ == "__main__":
    main()
