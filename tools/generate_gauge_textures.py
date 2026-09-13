#!/usr/bin/env python3

from pathlib import Path
import math

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1] / "src" / "factory_inspection_mission" / "worlds" / "benchmark_assets"
OUTPUTS = {
    "gauge_panel_nominal": ("GAUGE NORMAL", 170, "gauge_nominal.png"),
    "gauge_panel_warning": ("GAUGE WARNING", 100, "gauge_warning.png"),
    "gauge_panel_critical": ("GAUGE ALARM", 30, "gauge_critical.png"),
}

SIZE = 768
BG = "#f1efe7"
BORDER = "#29333d"
HEADER = "#234d5f"
RIM = "#282828"
NEEDLE = "#ea2027"
HUB = "#ea2027"
TEXT = "#23313d"


def polar_point(cx: float, cy: float, radius: float, angle_deg: float) -> tuple[float, float]:
    angle_rad = math.radians(angle_deg)
    return (cx + radius * math.cos(angle_rad), cy - radius * math.sin(angle_rad))


def draw_panel(title: str, angle_deg: float, output_path: Path) -> None:
    image = Image.new("RGBA", (SIZE, SIZE), BG)
    draw = ImageDraw.Draw(image)

    border_width = 12
    draw.rounded_rectangle((20, 20, SIZE - 20, SIZE - 20), radius=28, outline=BORDER, width=border_width)
    draw.rounded_rectangle((60, 60, SIZE - 60, 150), radius=18, fill=HEADER)

    font = ImageFont.load_default()
    draw.text((SIZE / 2 - 36, 100), title, fill="white", font=font)

    cx = SIZE / 2
    cy = SIZE / 2 + 20
    radius = 220
    draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), outline=RIM, width=8)

    for tick in range(13):
        tick_angle = 180 - tick * 15
        outer = polar_point(cx, cy, radius - 6, tick_angle)
        inner_radius = radius - (42 if tick % 3 == 0 else 26)
        inner = polar_point(cx, cy, inner_radius, tick_angle)
        draw.line((inner, outer), fill=RIM, width=5 if tick % 3 == 0 else 3)

    tip = polar_point(cx, cy, radius - 48, angle_deg)
    left = polar_point(cx, cy, 28, angle_deg + 98)
    right = polar_point(cx, cy, 22, angle_deg - 98)
    draw.polygon((tip, left, right), fill=NEEDLE, outline="#a00000")
    draw.ellipse((cx - 24, cy - 24, cx + 24, cy + 24), fill=HUB, outline="#8c0c18", width=4)

    draw.text((SIZE / 2 - 16, cy - radius - 2), "WARN", fill="#8a6b1f", font=font)
    draw.text((cx - radius + 18, cy + radius / 2), "NORMAL", fill="#335433", font=font)
    draw.text((cx + radius - 58, cy + radius / 2), "ALARM", fill="#a32b2b", font=font)
    draw.text((SIZE / 2 - 48, SIZE - 95), "AUTONOMOUS INSPECTION TARGET", fill=TEXT, font=font)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path)


def main() -> None:
    for model_name, (title, angle_deg, filename) in OUTPUTS.items():
        texture_path = ROOT / model_name / "materials" / "textures" / filename
        draw_panel(title, angle_deg, texture_path)
        print(f"wrote {texture_path}")


if __name__ == "__main__":
    main()
