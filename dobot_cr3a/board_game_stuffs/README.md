# Board Generation

Generate randomized variations of `Board_w_Korea_cities.png`.

## Usage

```bash
# 20 random boards into ./generated_boards
python3 randomize_board.py

# specify count
python3 randomize_board.py --count 20 --seed 42

# custom source / output
python3 randomize_board.py \
    --src Board_w_Korea_cities.png \
    --out-dir my_boards \
    --prefix korea \
    --count 10
```

## Flags

| flag | default | description |
|---|---|---|
| `--src` | `Board_w_Korea_cities.png` | source board image |
| `--out-dir` | `generated_boards` | output directory |
| `--count` | `20` | number of boards to generate |
| `--seed` | `None` | RNG seed for reproducibility |
| `--prefix` | `board` | filename prefix (`<prefix>_0000.png`, …) |

## What gets randomized

- **Corners (4):** uniformly shuffled across the 4 corner slots, each rotated by a random multiple of 90°. The `GO` cell uses a position-conditional rotation set so its arrow points in a valid direction.
- **Side cells (3 per side):** uniformly shuffled within their own side only (top stays top, etc.).
- **Inner area (logo):** preserved.
- **Cell borders:** repainted at uniform thickness on every side.
