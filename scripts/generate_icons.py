"""Generate PWA and Android launcher icons cleanly using Pillow."""

from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
PWA_ICON_DIR = ROOT / "docs" / "icons"
ANDROID_RES_DIR = ROOT / "android" / "app" / "src" / "main" / "res"

MIPMAP_SIZES = {
    "mipmap-mdpi": 48,
    "mipmap-hdpi": 72,
    "mipmap-xhdpi": 96,
    "mipmap-xxhdpi": 144,
    "mipmap-xxxhdpi": 192,
}


def find_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        r"C:\Windows\Fonts\malgunbd.ttf",
        r"C:\Windows\Fonts\malgun.ttf",
        "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    for path in candidates:
        p = Path(path)
        if p.exists():
            return ImageFont.truetype(str(p), size=size)
    return ImageFont.load_default()


def draw_master_icon(canvas_size: int = 1024, circular: bool = False) -> Image.Image:
    """Draw a sharp high-res teal + amber fuel/cashback icon."""
    img = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    margin = int(canvas_size * 0.04)
    bounds = [margin, margin, canvas_size - margin, canvas_size - margin]

    if circular:
        draw.ellipse(bounds, fill=(15, 118, 110, 255))
    else:
        radius = int(canvas_size * 0.22)
        draw.rounded_rectangle(bounds, radius=radius, fill=(15, 118, 110, 255))

    # Subtle inner highlight ring
    inner_m = int(canvas_size * 0.075)
    inner_bounds = [inner_m, inner_m, canvas_size - inner_m, canvas_size - inner_m]
    if circular:
        draw.ellipse(inner_bounds, outline=(20, 184, 166, 95), width=max(4, canvas_size // 128))
    else:
        draw.rounded_rectangle(
            inner_bounds,
            radius=int(canvas_size * 0.18),
            outline=(20, 184, 166, 95),
            width=max(4, canvas_size // 128),
        )

    # Fuel pump body (white card)
    pump_l = int(canvas_size * 0.26)
    pump_t = int(canvas_size * 0.23)
    pump_r = int(canvas_size * 0.61)
    pump_b = int(canvas_size * 0.77)
    draw.rounded_rectangle(
        [pump_l, pump_t, pump_r, pump_b],
        radius=int(canvas_size * 0.06),
        fill=(255, 255, 255, 255),
    )

    # Base stand
    draw.rounded_rectangle(
        [int(canvas_size * 0.22), int(canvas_size * 0.74), int(canvas_size * 0.65), int(canvas_size * 0.80)],
        radius=int(canvas_size * 0.025),
        fill=(226, 232, 240, 255),
    )

    # Digital price screen inside pump
    scr_l = int(canvas_size * 0.31)
    scr_t = int(canvas_size * 0.29)
    scr_r = int(canvas_size * 0.56)
    scr_b = int(canvas_size * 0.45)
    draw.rounded_rectangle(
        [scr_l, scr_t, scr_r, scr_b],
        radius=int(canvas_size * 0.03),
        fill=(13, 148, 136, 255),
    )

    # Fuel hose + nozzle on right side
    hose_w = max(8, int(canvas_size * 0.036))
    draw.arc(
        [int(canvas_size * 0.54), int(canvas_size * 0.35), int(canvas_size * 0.75), int(canvas_size * 0.72)],
        start=280,
        end=95,
        fill=(248, 250, 252, 255),
        width=hose_w,
    )
    draw.rounded_rectangle(
        [int(canvas_size * 0.67), int(canvas_size * 0.28), int(canvas_size * 0.76), int(canvas_size * 0.44)],
        radius=int(canvas_size * 0.025),
        fill=(253, 224, 71, 255),
    )

    # Cashback coin badge overlapping bottom-right of pump
    coin_cx = int(canvas_size * 0.64)
    coin_cy = int(canvas_size * 0.65)
    coin_r = int(canvas_size * 0.175)
    draw.ellipse(
        [coin_cx - coin_r - int(canvas_size * 0.015), coin_cy - coin_r - int(canvas_size * 0.015),
         coin_cx + coin_r + int(canvas_size * 0.015), coin_cy + coin_r + int(canvas_size * 0.015)],
        fill=(15, 118, 110, 255),
    )
    draw.ellipse(
        [coin_cx - coin_r, coin_cy - coin_r, coin_cx + coin_r, coin_cy + coin_r],
        fill=(245, 158, 11, 255),
    )
    inner_coin_r = int(coin_r * 0.84)
    draw.ellipse(
        [coin_cx - inner_coin_r, coin_cy - inner_coin_r, coin_cx + inner_coin_r, coin_cy + inner_coin_r],
        outline=(254, 243, 199, 210),
        width=max(3, canvas_size // 180),
    )

    # "%" or "₩" text inside coin
    font = find_font(int(canvas_size * 0.165))
    symbol = "₩"
    bbox = draw.textbbox((0, 0), symbol, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.text(
        (coin_cx - tw / 2 - bbox[0], coin_cy - th / 2 - bbox[1]),
        symbol,
        fill=(255, 255, 255, 255),
        font=font,
    )

    return img


def main() -> None:
    PWA_ICON_DIR.mkdir(parents=True, exist_ok=True)
    square_master = draw_master_icon(1024, circular=False)
    round_master = draw_master_icon(1024, circular=True)

    # PWA icons
    square_master.resize((512, 512), Image.Resampling.LANCZOS).save(PWA_ICON_DIR / "icon-512.png")
    square_master.resize((192, 192), Image.Resampling.LANCZOS).save(PWA_ICON_DIR / "icon-192.png")

    # Apple touch icon (opaque background required on iOS)
    apple_bg = Image.new("RGB", (1024, 1024), (15, 118, 110))
    apple_fg = draw_master_icon(1024, circular=False)
    apple_bg.paste(apple_fg, (0, 0), apple_fg)
    apple_bg.resize((180, 180), Image.Resampling.LANCZOS).save(PWA_ICON_DIR / "apple-touch-icon.png")

    # Android mipmap icons
    for folder, px in MIPMAP_SIZES.items():
        out_dir = ANDROID_RES_DIR / folder
        out_dir.mkdir(parents=True, exist_ok=True)
        square_master.resize((px, px), Image.Resampling.LANCZOS).save(out_dir / "ic_launcher.png")
        round_master.resize((px, px), Image.Resampling.LANCZOS).save(out_dir / "ic_launcher_round.png")

    print(f"Generated PWA and Android icons in {PWA_ICON_DIR} and {ANDROID_RES_DIR}")


if __name__ == "__main__":
    main()
