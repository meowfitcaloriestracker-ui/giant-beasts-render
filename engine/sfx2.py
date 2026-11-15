"""Richer SFX + drum bed library for shorts.  Use: from sfx2 import Mixer"""
import numpy as np, soundfile as sf
from scipy.signal import fftconvolve, butter, lfilter
SR = 48000
rng = np.random.default_rng(7)
def tt(L): return np.arange(int(L * SR)) / SR
def lp(x, f): b, a = butter(2, min(f / (SR / 2), 0.99)); return lfilter(b, a, x)
def hp(x, f): b, a = butter(2, f / (SR / 2), "high"); return lfilter(b, a, x)
def bp(x, f0, f1): return hp(lp(x, f1), f0)
_IR = rng.standard_normal(int(0.9 * SR)) * np.exp(-np.arange(int(0.9 * SR)) / SR * 6.0); _IR /= np.abs(_IR).sum() ** 0.5 * 6
def verb(x, wet=0.3): y = fftconvolve(x, _IR)[:len(x) + int(0.9 * SR)]; z = np.zeros(len(y)); z[:len(x)] = x; return z * (1 - wet) + y * wet
def norm(x, g=1.0): m = np.max(np.abs(x)) or 1; return x / m * g
# ---- sounds
def whoosh(L=0.55, up=True):
    t = tt(L); n = rng.standard_normal(len(t)); f = np.linspace(300, 3500, len(t)) if up else np.linspace(3500, 300, len(t))
    y = np.zeros(len(t)); seg = 960
    for i in range(0, len(t), seg): y[i:i + seg] = bp(n[i:i + seg], f[i] * 0.6, f[i] * 1.4)
    return norm(y * np.sin(np.pi * t / L) ** 1.5, 0.6)
def boom(L=2.2):
    t = tt(L); sub = np.sin(2 * np.pi * (38 + 70 * np.exp(-t * 14)) * t) * np.exp(-t * 2.2)
    crack = lp(rng.standard_normal(len(t)), 2500) * np.exp(-t * 22) * 0.8
    return norm(verb(sub + crack, 0.35), 0.95)
def hit(L=0.45):
    t = tt(L); return norm(np.sin(2 * np.pi * (80 + 160 * np.exp(-t * 30)) * t) * np.exp(-t * 10) + lp(rng.standard_normal(len(t)), 4000) * np.exp(-t * 40) * 0.7, 0.85)
def bell(f=1320, L=1.2):
    t = tt(L); y = sum(a * np.sin(2 * np.pi * f * m * t) * np.exp(-t * d) for m, a, d in ((1, 1, 4), (2.76, 0.4, 7), (5.4, 0.2, 10)))
    return norm(verb(y, 0.35), 0.4)
def sparkle(L=1.4):
    y = np.zeros(int(L * SR) + SR)
    for k in range(14):
        f = 1800 + k * 180 + rng.uniform(-60, 60); o = int(k * 0.06 * SR); b = bell(f, 0.5); y[o:o + len(b)] += b * (0.6 - k * 0.02)
    return norm(y, 0.45)
def pop(L=0.16): t = tt(L); f = 400 + 1400 * t / L; return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 16) * 0.45
def boing(L=0.7): t = tt(L); f = 200 + 140 * np.sin(2 * np.pi * 7 * t) * np.exp(-t * 3); return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 3.5) * 0.45
def snort(L=0.8):
    t = tt(L); n = bp(rng.standard_normal(len(t)), 150, 900); am = (0.5 + 0.5 * np.sin(2 * np.pi * 18 * t)) * np.exp(-((t - 0.3) / 0.22) ** 2)
    return norm(n * am + np.sin(2 * np.pi * 70 * t) * am * 0.4, 0.7)
def crunch(L=0.18): t = tt(L); return norm(bp(rng.standard_normal(len(t)), 1500, 6000) * np.exp(-t * 30) * (rng.random(len(t)) > 0.4), 0.35)
def riser(L=2.0):
    t = tt(L); n = rng.standard_normal(len(t)); f = 200 + 2400 * (t / L) ** 2
    return norm((hp(n, 800) * 0.3 + np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.3) * (t / L) ** 2.2, 0.55)
def scratch(L=0.4): t = tt(L); f = 300 + 900 * np.abs(np.sin(2 * np.pi * 3 * t)); return norm(bp(rng.standard_normal(len(t)), 300, 3000) * 0.5 + np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.4, 0.5) * np.exp(-t * 3)
def tick(L=0.05): t = tt(L); return np.sin(2 * np.pi * 2600 * t) * np.exp(-t * 90) * 0.4
# ---- drums
def kick(): t = tt(0.45); return np.sin(2 * np.pi * (48 + 110 * np.exp(-t * 35)) * t) * np.exp(-t * 8) * 0.95
def snare(): t = tt(0.3); return (bp(rng.standard_normal(len(t)), 900, 7000) * np.exp(-t * 18) * 0.6 + np.sin(2 * np.pi * 190 * t) * np.exp(-t * 25) * 0.4)
def hat(o=False): t = tt(0.25 if o else 0.06); return hp(rng.standard_normal(len(t)), 7000) * np.exp(-t * (14 if o else 70)) * 0.35
def taiko(): t = tt(0.8); return np.sin(2 * np.pi * (70 + 50 * np.exp(-t * 30)) * t) * np.exp(-t * 6) * 0.9 + lp(rng.standard_normal(len(t)), 1200) * np.exp(-t * 40) * 0.3
class Mixer:
    def __init__(s, total): s.n = int((total + 1.5) * SR); s.fx = np.zeros(s.n); s.dr = np.zeros(s.n)
    def add(s, t0, x, g=1.0, bus="fx"):
        b = s.fx if bus == "fx" else s.dr; o = int(t0 * SR); m = min(len(x), s.n - o)
        if m > 0 and o >= 0: b[o:o + m] += g * x[:m]
    def drums(s, t0, t1, bpm=100, inten=lambda t: 1.0, style="pop"):
        beat = 60 / bpm; k = 0
        while t0 + k * beat / 2 < t1:
            tb = t0 + k * beat / 2; g = inten(tb); step = k % 8
            if style == "pop":
                if step in (0, 3, 4): s.add(tb, kick(), 0.8 * g, "dr")
                if step in (2, 6): s.add(tb, snare(), 0.55 * g, "dr")
                s.add(tb, hat(step == 7), 0.5 * g, "dr")
            else:
                if step in (0, 4): s.add(tb, taiko(), 0.7 * g, "dr")
                if step in (6, 7): s.add(tb, taiko(), 0.35 * g, "dr")
                s.add(tb, hat(), 0.3 * g, "dr")
            k += 1
    def write(s, path, fx_g=1.0, dr_g=0.55):
        y = s.fx * fx_g + lp(s.dr, 9000) * dr_g; y = np.tanh(y * 1.1) / 1.1
        sf.write(path, np.stack([y, y], 1).astype(np.float32), SR)
