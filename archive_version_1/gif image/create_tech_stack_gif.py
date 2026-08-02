from io import BytesIO
from pathlib import Path
from typing import List

import cairosvg
from PIL import Image


# Adjustable settings
ICON_FOLDER = "icons"
OUTPUT_GIF = "tech_stack.gif"
CANVAS_WIDTH = 1600
CANVAS_HEIGHT = 180
ICON_SIZE = 96
ICON_SPACING = 50
FPS = 30
SCROLL_SPEED = 170  # Pixels per second
BACKGROUND_COLOR = None  # Use None for transparent, or a color like "#FFFFFF"


def load_svg_icons(icon_folder: Path) -> List[Image.Image]:
    """Load, render, and normalize all SVG icons in alphabetical order."""
    if not icon_folder.exists() or not icon_folder.is_dir():
        raise FileNotFoundError(f"Missing icons folder: {icon_folder}")

    svg_files = sorted(icon_folder.glob("*.svg"), key=lambda path: path.name.lower())
    if not svg_files:
        raise ValueError(f"No SVG files found in: {icon_folder}")

    icons = []
    invalid_files = []

    for svg_file in svg_files:
        try:
            # Render at the requested target height. CairoSVG preserves SVG
            # transparency, and Pillow keeps it in RGBA form for composition.
            png_bytes = cairosvg.svg2png(
                url=str(svg_file),
                output_height=ICON_SIZE,
            )
            icon = Image.open(BytesIO(png_bytes)).convert("RGBA")

            # Normalize each icon into a fixed-height transparent box while
            # preserving the rendered aspect ratio.
            icon.thumbnail((ICON_SIZE * 4, ICON_SIZE), Image.Resampling.LANCZOS)
            normalized = Image.new("RGBA", (icon.width, ICON_SIZE), (255, 255, 255, 0))
            y = (ICON_SIZE - icon.height) // 2
            normalized.alpha_composite(icon, (0, y))
            icons.append(normalized)
        except Exception as exc:
            invalid_files.append(f"{svg_file.name}: {exc}")

    if invalid_files:
        details = "\n".join(invalid_files)
        raise ValueError(f"Failed to render invalid SVG file(s):\n{details}")

    return icons


def create_icon_row(icons: List[Image.Image]) -> Image.Image:
    """Create one complete horizontal row of all icons."""
    row_width = sum(icon.width for icon in icons) + ICON_SPACING * len(icons)
    row = Image.new("RGBA", (row_width, CANVAS_HEIGHT), (255, 255, 255, 0))

    x = 0
    for icon in icons:
        y = (CANVAS_HEIGHT - icon.height) // 2
        row.alpha_composite(icon, (x, y))
        x += icon.width + ICON_SPACING

    return row


def calculate_frame_count(row_width: int) -> int:
    """Return a frame count that lands exactly on one repeated-row distance."""
    if SCROLL_SPEED <= 0:
        raise ValueError("SCROLL_SPEED must be greater than 0")
    if FPS <= 0:
        raise ValueError("FPS must be greater than 0")

    duration_seconds = row_width / SCROLL_SPEED
    return max(1, round(duration_seconds * FPS))


def alpha_composite_cropped(
    canvas: Image.Image,
    overlay: Image.Image,
    left: int,
    top: int,
) -> None:
    """Composite an overlay even when it extends beyond the canvas bounds."""
    src_left = max(0, -left)
    src_top = max(0, -top)
    src_right = min(overlay.width, canvas.width - left)
    src_bottom = min(overlay.height, canvas.height - top)

    if src_right <= src_left or src_bottom <= src_top:
        return

    cropped_overlay = overlay.crop((src_left, src_top, src_right, src_bottom))
    canvas.alpha_composite(cropped_overlay, (max(0, left), max(0, top)))


def build_frames(row: Image.Image, frame_count: int) -> List[Image.Image]:
    """Build GIF frames from a duplicated row for a seamless infinite loop."""
    row_width = row.width
    repeated_row = Image.new("RGBA", (row_width * 2, CANVAS_HEIGHT), (255, 255, 255, 0))
    repeated_row.alpha_composite(row, (0, 0))
    repeated_row.alpha_composite(row, (row_width, 0))

    frames = []
    for frame_index in range(frame_count):
        # The last frame intentionally stops before row_width, because the next
        # displayed frame is frame 0. That keeps the GIF restart invisible.
        offset = round(frame_index * row_width / frame_count)

        if BACKGROUND_COLOR is None:
            canvas_rgba = Image.new("RGBA", (CANVAS_WIDTH, CANVAS_HEIGHT), (255, 255, 255, 0))
        else:
            canvas_rgba = Image.new("RGBA", (CANVAS_WIDTH, CANVAS_HEIGHT), BACKGROUND_COLOR)

        x = -offset

        while x < CANVAS_WIDTH:
            alpha_composite_cropped(canvas_rgba, repeated_row, x, 0)
            x += repeated_row.width

        # Adaptive palettes keep README GIFs compact while preserving logo
        # colors. Transparency is handled separately so white logo pixels stay
        # opaque instead of becoming transparent.
        frames.append(quantize_frame(canvas_rgba))

    return frames


def quantize_frame(frame: Image.Image) -> Image.Image:
    """Reduce colors while reserving palette index 0 for transparency."""
    rgba_frame = frame.convert("RGBA")
    alpha = rgba_frame.getchannel("A")
    opaque_mask = alpha.point(lambda value: 255 if value >= 128 else 0)

    # Quantize only RGB color data, then shift all visible colors up by one
    # palette slot so index 0 can be reserved for transparent pixels.
    rgb_frame = rgba_frame.convert("RGB")
    quantized = rgb_frame.convert("P", palette=Image.ADAPTIVE, colors=255)
    shifted_quantized = quantized.point([min(index + 1, 255) for index in range(256)])

    transparent_frame = Image.new("P", rgba_frame.size, 0)
    transparent_frame.paste(shifted_quantized, mask=opaque_mask)

    source_palette = quantized.getpalette()[: 255 * 3]
    target_palette = [255, 255, 255] + source_palette
    target_palette.extend([0] * (768 - len(target_palette)))
    transparent_frame.putpalette(target_palette)
    transparent_frame.info["transparency"] = 0

    return transparent_frame


def save_gif(frames: List[Image.Image], output_path: Path) -> None:
    """Save an infinitely looping, optimized GIF."""
    frames[0].save(
        output_path,
        save_all=True,
        append_images=frames[1:],
        duration=round(1000 / FPS),
        loop=0,
        transparency=0,
        optimize=True,
        disposal=2,
    )


def main() -> None:
    icon_folder = Path(ICON_FOLDER)
    output_path = Path(OUTPUT_GIF)

    icons = load_svg_icons(icon_folder)
    row = create_icon_row(icons)
    frame_count = calculate_frame_count(row.width)
    frames = build_frames(row, frame_count)
    save_gif(frames, output_path)

    print(f"Loaded {len(icons)} icons")
    print(f"Created {len(frames)} frames")
    print(f"Saved {OUTPUT_GIF}")


if __name__ == "__main__":
    main()
