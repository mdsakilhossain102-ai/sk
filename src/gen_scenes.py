"""Generate 5 stylized cinematic 9:16 scenes (1440x2560) with PIL + NumPy."""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1440, 2560
OUT = os.path.join(os.path.dirname(__file__), "..", "img")
os.makedirs(OUT, exist_ok=True)

FONT_BOLD = os.path.join(
    __import__("matplotlib").get_data_path(),
    "fonts", "ttf", "DejaVuSans-Bold.ttf",
)


def radial_glow(size, cx, cy, radius, color, strength):
    """Additive gaussian glow blob on a numpy float image."""
    hh, ww = size
    y, x = np.mgrid[0:hh, 0:ww]
    d2 = (x - cx) ** 2 + (y - cy) ** 2
    g = np.exp(-d2 / (2.0 * radius ** 2)) * strength
    return g[..., None] * np.array(color, dtype=float)[None, None, :]


def vgrad(size, top, bottom):
    hh, ww = size
    t = np.linspace(0.0, 1.0, hh)
    col = (1 - t)[:, None] * np.array(top) + t[:, None] * np.array(bottom)
    return np.repeat(col[:, None, :], ww, axis=1)


def bokeh(rng, n, y0, y1, rmin, rmax, brightness):
    """Binary bokeh dot layer as float image."""
    hh, ww = H, W
    layer = np.zeros((hh, ww), dtype=float)
    yy, xx = np.mgrid[0:hh, 0:ww]
    for _ in range(n):
        cx, cy = rng.uniform(0, ww), rng.uniform(y0, y1)
        r = rng.uniform(rmin, rmax)
        b = rng.uniform(0.3, 1.0) * brightness
        layer = np.maximum(layer, np.exp(-((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * r ** 2)) * b)
    return layer[..., None]


def vignette(strength=0.55):
    yy, xx = np.mgrid[0:H, 0:W]
    d = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
    v = 1.0 - strength * np.clip(d - 0.55, 0, None) ** 1.6
    return np.clip(v, 0, 1)[..., None]


def finish(a):
    a *= vignette()
    a = np.clip(a, 0, 255).astype(np.uint8)
    return Image.fromarray(a).filter(ImageFilter.GaussianBlur(0.6))


def draw_text(img, xy, text, size, fill, stroke, anchor="mm"):
    d = ImageDraw.Draw(img)
    d.text(xy, text, font=ImageFont.truetype(FONT_BOLD, size), fill=fill,
           stroke_width=max(2, size // 22), stroke_fill=stroke, anchor=anchor)


def pentagon(cx, cy, r, rot=0.0):
    return [(cx + r * np.cos(np.radians(rot + 72 * i - 90)),
             cy + r * np.sin(np.radians(rot + 72 * i - 90))) for i in range(5)]


def scene_stadium_night():
    a = vgrad((H, W), (6, 10, 34), (10, 22, 48))
    rng = np.random.default_rng(7)
    a += bokeh(rng, 520, 540, 1010, 8, 34, 160) * np.array([1.0, 0.9, 0.7])
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    for lx in (170, W - 170):
        d.polygon([(lx - 30, 300), (lx + 30, 300), (lx + 520, 1150), (lx - 520, 1150)],
                  fill=(200, 215, 255, 40))
        for row in range(2):
            for col in range(3):
                x = lx - 70 + col * 72
                y = 150 + row * 62
                d.rectangle([x - 30, y - 22, x + 30, y + 22], fill=(255, 255, 235, 255))
    ov = ov.filter(ImageFilter.GaussianBlur(6))
    img = Image.alpha_composite(img, ov)
    b = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")
    d = ImageDraw.Draw(b)
    for lx in (170, W - 170):
        for row in range(2):
            for col in range(3):
                x = lx - 70 + col * 72
                y = 150 + row * 62
                d.rectangle([x - 30, y - 22, x + 30, y + 22], fill=(255, 255, 240))
    d.rectangle([lx - 20, 274, lx + 20, 420], fill=(24, 26, 40))
    d.rectangle([W - 190, 274, W - 150, 420], fill=(24, 26, 40))
    d.rectangle([0, 1010, W, 1120], fill=(12, 14, 26))
    for x in range(-40, W + 40, 90):
        d.polygon([(x, 1010), (x + 45, 1010), (x + 25, 1120), (x - 20, 1120)], fill=(18, 20, 38))
    d.rectangle([0, 1120, W, H], fill=(8, 46, 26))
    d.rectangle([50, 1120, 240, H], fill=(11, 60, 33))
    d.rectangle([W - 240, 1120, W - 50, H], fill=(11, 60, 33))
    d.rectangle([50, 1120, 240, 1150], fill=(13, 70, 38))
    d.rectangle([W - 240, 1120, W - 50, 1150], fill=(13, 70, 38))
    d.ellipse([W // 2 - 130, 1750, W // 2 + 130, 1930], outline=(230, 240, 220), width=8)
    return finish(np.asarray(b.convert("RGB")).astype(float))


def scene_golden_trophy():
    a = vgrad((H, W), (14, 10, 2), (30, 20, 4))
    a += radial_glow((H, W), W // 2, 1120, 620, (255, 190, 60), 260)
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(img)
    cx = W // 2
    cup = [(cx - 330, 640), (cx + 330, 640), (cx + 290, 1080), (cx + 130, 1240), (cx + 130, 1330),
           (cx + 250, 1430), (cx + 250, 1500), (cx - 250, 1500), (cx - 250, 1430),
           (cx - 130, 1330), (cx - 130, 1240), (cx - 290, 1080)]
    d.polygon(cup, fill=(255, 200, 70), outline=(140, 90, 10))
    d.ellipse([cx - 360, 1330, cx + 360, 1500], fill=(200, 140, 30))
    d.rectangle([cx - 190, 1500, cx + 190, 1680], fill=(190, 130, 25))
    d.rectangle([cx - 260, 1680, cx + 260, 1780], fill=(160, 105, 18))
    for hx, s in ((hx, s) for hx, s in ((cx - 420, 1), (cx + 420, -1))):
        d.arc([hx - 40 * s if s > 0 else hx - 220, 660, hx + 220 if s > 0 else hx + 40, 1080],
              start=90, end=270, fill=(255, 210, 90), width=46)
    d.ellipse([cx - 60, 700, cx + 60, 820], fill=(255, 235, 160, 255), outline=None)
    rng = np.random.default_rng(3)
    for _ in range(140):
        x, y = rng.uniform(60, W - 60), rng.uniform(400, 2200)
        r = rng.uniform(1.5, 5)
        d.ellipse([x - r, y - r, x + r, y + r], fill=(255, rng.integers(190, 240), 110))
    return finish(np.asarray(img).astype(float))


def scene_soccer_ball():
    a = vgrad((H, W), (8, 12, 30), (16, 20, 40))
    a += radial_glow((H, W), W // 2, 1180, 700, (120, 160, 255), 170)
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.line([(200, H), (900, 420)], fill=(90, 130, 220, 70), width=12)
    d.line([(W - 200, H), (W - 900, 420)], fill=(90, 130, 220, 70), width=12)
    cx, cy, r = W // 2, 1210, 430
    d.ellipse([cx - r - 40, cy - r - 40, cx + r + 40, cy + r + 40], fill=(255, 255, 255, 40))
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(238, 240, 246))
    dark = (22, 22, 30)
    d.polygon(pentagon(cx, cy, r * 0.42, 0), fill=dark)
    for i in range(5):
        ang = 72 * i - 90 + 36
        px = cx + r * 0.93 * np.cos(np.radians(ang))
        py = cy + r * 0.93 * np.sin(np.radians(ang))
        d.polygon(pentagon(px, py, r * 0.30, ang + 180), fill=dark)
        v1 = pentagon(cx, cy, r * 0.42, 0)[i]
        v2 = pentagon(px, py, r * 0.30, ang + 180)[3]
        d.line([v1, v2], fill=(70, 70, 84), width=14)
    d.ellipse([cx - r * 0.25, cy - r * 0.25, cx + 10, cy + 10], fill=(255, 255, 255))
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(60, 62, 80), width=6)
    return finish(np.asarray(img.convert("RGB")).astype(float))


def scene_number7():
    a = vgrad((H, W), (10, 8, 24), (22, 14, 36))
    a += radial_glow((H, W), W // 2, 1250, 800, (255, 150, 40), 200)
    rng = np.random.default_rng(11)
    a += bokeh(rng, 200, 200, 2400, 5, 20, 40) * np.array([1.0, 0.75, 0.4])
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dg = ImageDraw.Draw(glow)
    dg.text((W // 2, 1210), "7", font=ImageFont.truetype(FONT_BOLD, 1500),
            fill=(255, 170, 40, 255), anchor="mm")
    glow = glow.filter(ImageFilter.GaussianBlur(38))
    img = Image.alpha_composite(img.convert("RGBA"), glow)
    d = ImageDraw.Draw(img)
    d.text((W // 2, 1210), "7", font=ImageFont.truetype(FONT_BOLD, 1500), fill=(255, 205, 90),
           stroke_width=16, stroke_fill=(120, 60, 5), anchor="mm")
    for _ in range(60):
        x, y = rng.uniform(100, W - 100), rng.uniform(400, 2200)
        ln = rng.uniform(20, 90)
        d.line([(x, y), (x + ln * 0.2, y + ln)], fill=(255, 190, 90), width=3)
    return finish(np.asarray(img.convert("RGB")).astype(float))


def scene_fireworks():
    a = vgrad((H, W), (2, 2, 14), (10, 6, 30))
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(img)
    rng = np.random.default_rng(21)
    bursts = [(360, 700, 300, (255, 120, 60)), (1080, 560, 340, (255, 210, 90)),
              (760, 300, 240, (120, 180, 255)), (1200, 1050, 260, (255, 120, 160)),
              (240, 1150, 220, (140, 255, 180))]
    for bx, by, br, col in bursts:
        for ang in range(0, 360, 8):
            x2 = bx + br * np.cos(np.radians(ang))
            y2 = by + br * np.sin(np.radians(ang))
            d.line([(bx, by), (x2, y2)], fill=col, width=5)
        for _ in range(50):
            ang = rng.uniform(0, 2 * np.pi)
            rr = rng.uniform(0.5, 1.15) * br
            x, y = bx + rr * np.cos(ang), by + rr * np.sin(ang)
            r = rng.uniform(2, 7)
            d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 235, 190))
        d.ellipse([bx - 26, by - 26, bx + 26, by + 26], fill=(255, 255, 240))
    d.rectangle([0, 1980, W, H], fill=(6, 6, 16))
    for x in range(0, W, 120):
        h = rng.integers(90, 320)
        d.rectangle([x, 1980 - h, x + 100, 1980], fill=(12, 12, 26))
        for wx in range(x + 15, x + 95, 25):
            for wy in range(1980 - h + 20, 1975, 45):
                if rng.random() < 0.55:
                    d.rectangle([wx, wy, wx + 10, wy + 16], fill=(240, 200, 110))
    d.rectangle([0, 1980, W, 2005], fill=(14, 12, 30))
    return finish(np.asarray(img).astype(float))


SCENES = {
    "scene1_stadium_night.png": scene_stadium_night,
    "scene2_golden_trophy.png": scene_golden_trophy,
    "scene3_soccer_ball.png": scene_soccer_ball,
    "scene4_number7.png": scene_number7,
    "scene5_fireworks.png": scene_fireworks,
}


def main():
    for name, fn in SCENES.items():
        p = os.path.join(OUT, name)
        fn().save(p, optimize=True)
        print("wrote", p)


if __name__ == "__main__":
    main()
