"""Turn the raw illustrations in images/ into small web assets in web/public/img/.

Usage: uv run --with pillow python scripts/prepare_images.py
Raw files stay out of git (images/ is gitignored); only the optimized WebP files are committed.
"""

from pathlib import Path

from PIL import Image

RAW = Path("images")
OUT = Path("web/public/img")

# output name: (source file, crop box as fractions or None, max side px, remove dark haze?)
ASSETS = {
    "area-body": ("Tên de luz_ Lua crescente no tênis pastel.png", None, 256, False),
    "area-mind": ("Ícones de Sono e Saúde em Vidro Fosco.png", (0.5, 0, 1, 1), 256, False),
    "area-growth": ("Livro Aberto Rumo à Conquista.png", None, 256, False),
    "area-money-social": ("Brinde de Café e Prosperidade.png", None, 256, False),
    "quadrant-yellow": ("Blob Amarelo em Salto Alegre.png", None, 192, False),
    "quadrant-red": ("Criaturinha Ansiosa sob Tempestade.png", None, 192, False),
    "quadrant-blue": ("Blob Azul Sob a Chuva.png", None, 192, False),
    "quadrant-green": ("Descanso Aconchegante do Broto Verde.png", None, 192, False),
    "feature-sleep": ("feature-sleep.png", None, 320, False),
    "feature-habits": ("feature-habits.png", None, 320, False),
    "feature-wellbeing": ("feature-wellbeing.png", None, 320, False),
    "feature-patterns": ("feature-patterns.png", None, 320, False),
    "feature-needs": ("feature-needs.png", None, 320, False),
    "dashboard": ("Painel de Vida em Harmonia.png", None, 384, False),
    "empty-state": ("empty-state.png", None, 320, False),
    "support": ("support.png", None, 320, False),
    "celebrate": ("celebrate.png", None, 320, False),
    "hero-tracks": ("Caminhos Luminosos ao Pôr do Sol.png", None, 1600, False),
}


def remove_haze(img: Image.Image) -> Image.Image:
    """Drop the dark, semi-transparent glow some generations put behind the subject."""
    img = img.convert("RGBA")
    px = img.load()
    w, h = img.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
            if a < 250 and lum < 90:
                px[x, y] = (r, g, b, 0)
            elif a < 250 and lum < 140:
                px[x, y] = (r, g, b, int(a * (lum - 90) / 50))
    return img


def trim(img: Image.Image, pad: float = 0.04) -> Image.Image:
    if img.mode != "RGBA":
        return img
    box = img.getchannel("A").point(lambda v: 255 if v > 24 else 0).getbbox()
    if not box:
        return img
    x0, y0, x1, y1 = box
    p = int(max(x1 - x0, y1 - y0) * pad)
    return img.crop(
        (max(0, x0 - p), max(0, y0 - p), min(img.width, x1 + p), min(img.height, y1 + p))
    )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, (src, crop, size, haze) in ASSETS.items():
        img = Image.open(RAW / src)
        if crop:
            w, h = img.size
            img = img.crop((int(crop[0] * w), int(crop[1] * h), int(crop[2] * w), int(crop[3] * h)))
        if haze:
            img = remove_haze(img)
        img = trim(img)
        img.thumbnail((size, size) if name != "hero-tracks" else (size, size * 2), Image.LANCZOS)
        out = OUT / f"{name}.webp"
        img.save(out, "WEBP", quality=82, method=6)
        print(f"{out}  {img.size[0]}x{img.size[1]}  {out.stat().st_size // 1024} KB")

    icon = Image.open(RAW / "Ondas Neon com Orbes Luminosos.png").convert("RGBA")
    icon = trim(icon)
    for px in (192, 512):
        icon.resize((px, px), Image.LANCZOS).save(OUT / f"icon-{px}.png", optimize=True)
    icon.resize((64, 64), Image.LANCZOS).save(OUT.parent / "favicon.png", optimize=True)
    print("icons written")


if __name__ == "__main__":
    main()
