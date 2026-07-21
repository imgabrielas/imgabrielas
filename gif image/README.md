# Tech Stack GIF Generator

`create_tech_stack_gif.py` turns a folder of SVG icons into a single looping,
transparent-background GIF of them scrolling horizontally — handy for a
README "tech stack" banner.

## How it works

1. Loads every `.svg` file from `icons/`, sorted alphabetically, and renders
   each one to a fixed-height transparent PNG with `cairosvg`.
2. Lays the icons out in a single row (`create_icon_row`), spaced evenly.
3. Duplicates the row and slides a canvas-sized window across it frame by
   frame, so the animation loops seamlessly with no visible restart
   (`build_frames`).
4. Quantizes each frame's palette while reserving one index for
   transparency, so logo colors stay accurate and the background stays see
   -through (`quantize_frame`).
5. Saves all frames as one infinitely looping GIF (`save_gif`).

## Usage

Install dependencies:

```bash
pip install -r requirements.txt
```

Add or replace the SVG icons in `icons/`, then run:

```bash
python create_tech_stack_gif.py
```

This produces `tech_stack.gif` in the project root.

## Configuration

Adjust the constants at the top of `create_tech_stack_gif.py` to customize
the output:

| Setting | Description |
| --- | --- |
| `ICON_FOLDER` | Folder to read SVG icons from |
| `OUTPUT_GIF` | Output file path |
| `CANVAS_WIDTH` / `CANVAS_HEIGHT` | Size of the GIF in pixels |
| `ICON_SIZE` | Rendered height of each icon in pixels |
| `ICON_SPACING` | Horizontal gap between icons in pixels |
| `FPS` | Frames per second |
| `SCROLL_SPEED` | Scroll speed in pixels per second |
| `BACKGROUND_COLOR` | `None` for transparent, or a hex color like `"#FFFFFF"` |