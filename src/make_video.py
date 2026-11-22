"""Render a 1080x1920 30fps short: Ken Burns scenes + text animation + beat pulse,
encoded to H.264/AAC with the imageio-ffmpeg bundled binary (no system ffmpeg)."""
import math
import os
import shutil
import subprocess
import tempfile
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFont

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
IMG = os.path.join(ROOT, "img")
OUT_DIR = os.path.join(ROOT, "video")
W, H = 1080, 1920
FPS = 30
DUR = 30.0
N_FRAMES = int(DUR * FPS)
BPM = 100.0
BEAT = 60.0 / BPM
SCENE_LEN = 6.0
FADE = 0.8
FONT_BOLD = os.path.join(
    __import__("matplotlib").get_data_path(),
    "fonts", "ttf", "DejaVuSans-Bold.ttf",
)

TEXTS = [
    ["CRISTIANO", "RONALDO"],
    ["5\u00d7 BALLON D'OR"],
    ["950+", "CAREER GOALS"],
    ["5 CHAMPIONS", "LEAGUES"],
    ["SIUUU!"],
]


def load_scenes():
    names = ["scene1_stadium_night.png", "scene2_golden_trophy.png",
             "scene3_soccer_ball.png", "scene4_number7.png", "scene5_fireworks.png"]
    return [Image.open(os.path.join(IMG, n)).convert("RGB") for n in names]


def ken_burns(scene, pos, idx):
    """Crop a moving window with zoom 1.00 -> 1.14 and lateral drift."""
    sw, sh = scene.size
    t = min(pos / SCENE_LEN, 1.0)
    ease = t * t * (3 - 2 * t)
    zoom = 1.0 + 0.14 * ease
    cw, ch = int(W / zoom), int(H / zoom)
    drift = (60, -40, 0, 80, -50)[idx]
    cx = sw // 2 + int(drift * ease)
    cy = sh // 2 - int(0.05 * ch * ease)
    left = max(0, min(sw - cw, cx - cw // 2))
    top = max(0, min(sh - ch, cy - ch // 2))
    crop = scene.crop((left, top, left + cw, top + ch))
    return crop.resize((W, H), Image.BILINEAR)


def beat_pulse(t):
    phase = (t % BEAT) / BEAT
    return math.exp(-phase * BEAT / 0.09)


def fit_font(d, text, max_w, start_size):
    size = start_size
    while size > 24:
        f = ImageFont.truetype(FONT_BOLD, size)
        if d.textlength(text, font=f) <= max_w:
            return size
        size -= 6
    return size


def text_overlay(idx, seed=0):
    """Pre-render static text block to RGBA with shadow + gold stroke."""
    lines = TEXTS[idx]
    tmp = Image.new("RGBA", (W, 300))
    d = ImageDraw.Draw(tmp)
    line_heights = []
    for line in lines:
        size = fit_font(d, line, 880, 168 if len(lines) > 1 else 190)
        f = ImageFont.truetype(FONT_BOLD, size)
        bb = d.textbbox((0, 0), line, font=f, stroke_width=max(2, size // 22))
        line_heights.append(bb[3] - bb[1])
    total = int(sum(line_heights) + 140 + 60 * (len(lines) - 1))
    h = min(max(total, 200), 900)
    out = Image.new("RGBA", (W, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(out)

    def draw_line(line, y):
        size = fit_font(d, line, 880, 168 if len(lines) > 1 else 190)
        f = ImageFont.truetype(FONT_BOLD, size)
        sw = max(3, size // 20)
        if idx == 4:
            fill, stroke = (255, 215, 90, 255), (255, 150, 30, 255)
        else:
            fill, stroke = (255, 255, 255, 255), (30, 30, 34, 255)
        d.text((W // 2 + 6, y + 8), line, font=f, fill=(0, 0, 0, 200),
               stroke_width=sw, stroke_fill=(0, 0, 0, 200), anchor="ma")
        d.text((W // 2, y), line, font=f, fill=fill,
               stroke_width=sw, stroke_fill=stroke, anchor="ma")
        bb = f.getbbox(line)
        return (bb[3] - bb[1]) + 60

    y = 70
    for line in lines:
        y += draw_line(line, y)
    d.rectangle([W // 2 - 130, y, W // 2 + 130, y + 6], fill=(255, 190, 60, 230))
    return out


def frame_at(t, scenes, overlays):
    k = int(t // SCENE_LEN)
    pos = t - k * SCENE_LEN
    img = ken_burns(scenes[k], pos, k).convert("RGBA")
    if pos > SCENE_LEN - FADE and k < len(scenes) - 1:
        nxt = ken_burns(scenes[k + 1], pos - (SCENE_LEN - FADE), k + 1).convert("RGBA")
        a = (pos - (SCENE_LEN - FADE)) / FADE
        a = a * a * (3 - 2 * a)
        img = Image.blend(img, nxt, a)
    pulse = beat_pulse(t) * (1.6 if k == 4 else 1.0)
    ov = overlays[k]
    appear = pos - 0.10
    if appear > 0:
        grow = 1.0 + 0.05 * pulse
        alpha = min(appear / 0.35, 1.0)
        slide = int((1 - min(appear / 0.5, 1.0)) ** 2 * 70)
        scale = min(grow, 1.25)
        nw, nh = int(ov.width * scale), int(ov.height * scale)
        o = ov.resize((nw, nh), Image.BILINEAR)
        if alpha < 1:
            o.putalpha(o.getchannel("A").point(lambda px: int(px * alpha)))
        img.alpha_composite(o, ((W - nw) // 2, 1210 - nh // 2 + slide))
    img = ImageEnhance.Brightness(img).enhance(1.0 + 0.03 * pulse)
    return img.convert("RGB")


def music_path():
    return os.path.join(OUT_DIR, "_music.wav")


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    scenes = load_scenes()
    overlays = [text_overlay(i) for i in range(5)]
    wav = music_path()
    out = os.path.join(OUT_DIR, "ronaldo_short.mp4")
    ffmpeg = shutil.which("ffmpeg") or __import__("imageio_ffmpeg").get_ffmpeg_exe()
    cmd = [ffmpeg, "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-i", wav, "-filter_complex", "[1:a]afade=t=in:st=0:d=0.3,afade=t=out:st=27.6:d=2.2[a]",
           "-map", "0:v", "-map", "[a]",
           "-c:v", "libx264", "-preset", "medium", "-crf", "22", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-t", str(DUR), out]
    with tempfile.NamedTemporaryFile(suffix=".log", delete=False) as logf:
        err_path = logf.name
    with open(err_path, "wb") as errf:
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                                stdout=subprocess.DEVNULL, stderr=errf)
        for i in range(N_FRAMES):
            t = i / FPS
            proc.stdin.write(frame_at(t, scenes, overlays).tobytes())
        proc.stdin.close()
        proc.wait()
    if proc.returncode != 0:
        with open(err_path) as f:
            raise SystemExit(f.read()[-3000:])
    os.remove(err_path)
    print("wrote", out)


if __name__ == "__main__":
    main()
