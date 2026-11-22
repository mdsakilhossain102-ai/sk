from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance

W, H = 1080, 1920
anton = lambda sz: ImageFont.truetype("Anton.ttf", sz)
mont  = lambda sz: ImageFont.truetype("Montserrat.ttf", sz)

SCENES = [
    ("s1.jpg", ("LIONEL MESSI", "Not just soccer. Pure art.")),
    ("s2.jpg", ("DEFENDERS CAN'T TOUCH HIM", "Dribbling that breaks ankles")),
    ("s3.jpg", ("CHEAT CODE FREE KICKS", "Top corner, every time")),
    ("s4.jpg", ("WORLD CHAMPION", "8 Golden Balls. A trophy case like no other")),
    ("s5.jpg", ("NOW HE OWNS MIAMI", "Sold-out crowds in every single MLS city")),
    ("s6.jpg", ("THE GOAT. NO DEBATE.", "Greatest to ever play the game")),
]

def build(photo, big, small, idx, out):
    im = Image.open(photo).convert("RGB")
    # background: fill 9:16, blur, darken
    bw = max(W, int(im.height * 9 / 16 * (im.width / im.height) ** 0))
    scale = max(W / im.width, H / im.height)
    bg = im.resize((int(im.width * scale) + 1, int(im.height * scale) + 1), Image.LANCZOS)
    bg = bg.crop(((bg.width - W)//2, (bg.height - H)//2, (bg.width - W)//2 + W, (bg.height - H)//2 + H))
    bg = bg.filter(ImageFilter.GaussianBlur(28))
    bg = ImageEnhance.Brightness(bg).enhance(0.45)
    frame = bg
    # foreground photo band, full width
    ph = im.resize((W, int(im.height * W / im.width)), Image.LANCZOS)
    y0 = (H - ph.height) // 2
    frame.paste(ph, (0, y0))
    # soft shadow above/below photo band
    grad = Image.new("L", (1, H), 0)
    px = grad.load()
    fade_top_end = y0 + 120
    fade_bot_start = y0 + ph.height - 120
    for y in range(H):
        v = 0
        if y < 60: v = 200 - int(y * 2.5)
        elif y < fade_top_end: v = 160 - int(160 * (y - 60) / (fade_top_end - 60))
        elif y > H - 60: v = 200
        elif y > fade_bot_start: v = int(160 * (y - fade_bot_start) / (H - 60 - fade_bot_start))
        px[0, y] = max(0, min(255, v))
    grad = grad.resize((W, H))
    shadow = Image.new("RGB", (W, H), (8, 10, 20))
    frame = Image.composite(shadow, frame, grad)
    d = ImageDraw.Draw(frame)
    # bottom gradient for text zone
    g2 = Image.new("L", (1, 700), 0)
    px2 = g2.load()
    for y in range(700):
        px2[0, y] = int(190 * (y / 700) ** 1.6)
    g2 = g2.resize((W, 700))
    dark = Image.new("RGB", (W, 700), (8, 10, 20))
    frame.paste(dark, (0, H - 700), g2)
    d = ImageDraw.Draw(frame)
    # big title (wrap if long)
    big_font = anton(96)
    words = big.split()
    lines, cur = [], ""
    for wd in words:
        t = (cur + " " + wd).strip()
        if d.textlength(t, font=big_font) > W - 140 and cur:
            lines.append(cur); cur = wd
        else:
            cur = t
    lines.append(cur)
    block_h = len(lines) * 106
    ty = H - 700 + (700 - block_h - 120)
    small_f = mont(46)
    # small line above big block
    sw = d.textlength(small, font=small_f)
    d.text(((W - sw) / 2 + 3, ty - 78 + 3), small, font=small_f, fill=(0, 0, 0))
    d.text(((W - sw) / 2, ty - 78), small, font=small_f, fill=(255, 220, 90))
    for i, ln in enumerate(lines):
        w = d.textlength(ln, font=big_font)
        x = (W - w) / 2
        yy = ty + i * 106
        d.text((x + 5, yy + 5), ln, font=big_font, fill=(0, 0, 0))
        d.text((x, yy), ln, font=big_font, fill=(255, 255, 255))
    # top kicker
    kick_font = mont(38)
    kick = "PLAY OF THE DAY  -  SCENE %d" % (idx + 1) if idx else "GOAT STATUS  -  ALL-TIME"
    kw = d.textlength(kick, font=kick_font)
    d.rectangle([(W - kw) / 2 - 30, 96, (W + kw) / 2 + 30, 168], fill=(0, 0, 0, 160))
    d.text(((W - kw) / 2, 108), kick, font=kick_font, fill=(255, 255, 255))
    frame.save(out, "PNG")
    print("built", out)

for i, (p, (b, s)) in enumerate(SCENES):
    build(p, b, s, i, f"c{i}.png")
