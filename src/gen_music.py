"""Synthesize an epic 30s soundtrack (100 BPM, Am-F-C-G) with pure NumPy."""
import os
import wave

import numpy as np

SR = 44100
BPM = 100.0
BEAT = 60.0 / BPM
BAR = 4 * BEAT
BARS = 12
DUR = 30.0

CHORDS = [
    ("Am", 45, [57, 60, 64]),   # A2 root, A3 C4 E4
    ("F", 41, [53, 57, 60]),    # F2 root, F3 A3 C4
    ("C", 48, [55, 60, 64]),    # C3 root, G3 C4 E4
    ("G", 43, [55, 59, 62]),    # G2 root, G3 B3 D4
]


def freq(midi):
    return 440.0 * 2.0 ** ((midi - 69) / 12.0)


def adsr(n, a, d, s, r, sr=SR):
    t = np.arange(n) / sr
    total = n / sr
    a_n, d_n, r_n = max(1, int(a * sr)), max(1, int(d * sr)), max(1, int(r * sr))
    env = np.ones(n) * s
    env[:a_n] = np.linspace(0, 1, a_n)
    env[a_n:a_n + d_n] = np.linspace(1, s, d_n)
    env[-r_n:] *= np.linspace(1, 0, r_n)
    return env * np.exp(-t * 0.25)


def place(buf, start, sig, gain=1.0):
    i = int(start * SR)
    j = min(len(buf), i + len(sig))
    if i < len(buf) and j > i:
        buf[i:j] += sig[: j - i] * gain


def saw(midi, dur, detune=0.0):
    f = freq(midi) * (2 ** (detune / 1200.0))
    t = np.arange(int(dur * SR)) / SR
    out = np.zeros_like(t)
    for k, a in ((1, 1.0), (2, 0.5), (3, 0.33), (4, 0.2), (5, 0.12), (6, 0.08)):
        out += a * np.sin(2 * np.pi * f * k * t)
    return out


def pluck(midi, dur, bright=2):
    f = freq(midi)
    t = np.arange(int(dur * SR)) / SR
    out = np.sin(2 * np.pi * f * t)
    for k in range(2, 2 + bright):
        out += np.sin(2 * np.pi * f * k * t) / k
    return out * np.exp(-t / (dur * 0.25))


def kick():
    n = int(0.30 * SR)
    t = np.arange(n) / SR
    f = 48 + 110 * np.exp(-t / 0.035)
    ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * np.exp(-t / 0.09)
    click = np.random.default_rng(1).standard_normal(n) * np.exp(-t / 0.004) * 0.4
    return body + click


def hat(open_=False):
    n = int((0.14 if open_ else 0.05) * SR)
    t = np.arange(n) / SR
    noise = np.random.default_rng(2).standard_normal(n)
    noise = np.diff(noise, prepend=0.0)
    noise = np.diff(noise, prepend=0.0)
    return noise * np.exp(-t / (0.05 if open_ else 0.014)) * 0.6


def clap():
    n = int(0.22 * SR)
    out = np.zeros(n)
    for off in (0.0, 0.011, 0.023):
        i = int(off * SR)
        m = n - i
        t = np.arange(m) / SR
        burst = np.random.default_rng(3).standard_normal(m)
        burst = np.diff(burst, prepend=0.0)
        out[i:] += burst * np.exp(-t / 0.045)
    return out


def reverb(x):
    wet = np.zeros_like(x)
    for delay, g in ((0.097, 0.34), (0.193, 0.21), (0.291, 0.13), (0.419, 0.08)):
        d = int(delay * SR)
        wet[d:] += x[:-d] * g
    return x + 0.7 * wet


def main():
    n_total = int(DUR * SR)
    pad = np.zeros(n_total)
    bass = np.zeros(n_total)
    drums = np.zeros(n_total)
    arp = np.zeros(n_total)

    def rngkeep(_):
        return True

    for bar in range(BARS):
        t0 = bar * BAR
        _, root, tones = CHORDS[bar % 4]
        pad_len = int(BAR * 1.05 * SR)
        chord_pad = np.zeros(pad_len)
        m = int(pad_len)
        a_env = adsr(m, BAR * 0.25, BAR * 0.25, 0.8, BAR * 0.25)
        for tone in tones:
            chord_pad += saw(tone, BAR * 1.05) + saw(tone, BAR * 1.05, detune=7)
        chord_pad *= a_env / (2 * len(tones) + 4)
        place(pad, t0, chord_pad, 0.9)

        bass_pat = [(0.0, root, 0.30), (BEAT * 0.5, root, 0.18), (BEAT, root + 12, 0.22),
                    (BEAT * 1.5, root, 0.18), (BEAT * 2, root, 0.30),
                    (BEAT * 2.5, root, 0.18), (BEAT * 3, root + 12, 0.22),
                    (BEAT * 3.5, root, 0.18)]
        for off, note, dur in bass_pat:
            place(bass, t0 + off, pluck(note, dur, bright=1), 0.55)

        for b in range(4):
            place(drums, t0 + b * BEAT, kick(), 1.0)
            if b % 2 == 1:
                place(drums, t0 + b * BEAT, clap(), 0.5)
            place(drums, t0 + b * BEAT + BEAT / 2, hat(open_=(b == 3)), 0.8)
            for s in range(4):
                if s % 2 == 1 or rngkeep(bar + b + s):
                    place(drums, t0 + b * BEAT + s * BEAT / 4, hat(), 0.18)

        arp_seq = [tones[0] + 12, tones[1] + 12, tones[2] + 12, tones[1] + 24]
        for s in range(16):
            note = arp_seq[s % 4] if s % 8 != 7 else arp_seq[3]
            place(arp, t0 + s * BEAT / 4, pluck(note, BEAT / 4, bright=1), 0.30)

    pad_w = reverb(pad)
    pad_l, pad_r = pad_w, np.roll(pad_w, int(0.004 * SR))
    arp_w = reverb(arp * 0.8)
    arp_l, arp_r = arp_w, np.roll(arp_w, int(0.007 * SR))
    clap_l = drums.copy()

    fade_in = int(0.05 * SR)
    fade_out = int(2.2 * SR)
    mix_l = pad_l + arp_l + bass + drums
    mix_r = pad_r + arp_r + bass + drums
    for ch in (mix_l, mix_r):
        ch[:fade_in] *= np.linspace(0, 1, fade_in)
        ch[-fade_out:] *= np.linspace(1, 0, fade_out)

    peak = max(np.abs(mix_l).max(), np.abs(mix_r).max())
    mix_l *= 0.88 / peak
    mix_r *= 0.88 / peak

    stereo = np.empty((n_total, 2))
    stereo[:, 0] = mix_l
    stereo[:, 1] = mix_r
    pcm = (np.clip(stereo, -1, 1) * 32767).astype(np.int16)

    out = os.path.join(os.path.dirname(__file__), "..", "video")
    os.makedirs(out, exist_ok=True)
    path = os.path.join(out, "_music.wav")
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    print("wrote", path, f"{DUR:.1f}s BPM={BPM}")


if __name__ == "__main__":
    main()
