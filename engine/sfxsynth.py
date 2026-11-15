"""Synthesised sound-effect library (no downloads needed): combat layers, footsteps per terrain,
water / underwater sounds, creature voices and looping ambience beds for every scene.
All sounds are deterministic (seeded) and cached in sounds/synth/*.wav the first time they are used.
Use:  import sfxsynth as SX;  x = SX.get("bite-crunch-2")   # float32 mono @ 48 kHz
"""
import os, numpy as np
from scipy.signal import butter, lfilter, fftconvolve
SR = 48000
HERE = os.path.dirname(os.path.abspath(__file__)); CACHE = os.path.join(HERE, "sounds", "synth")

def tt(L): return np.arange(int(L * SR)) / SR
def lp(x, f, o=2): b, a = butter(o, min(f / (SR / 2), 0.99)); return lfilter(b, a, x)
def hp(x, f, o=2): b, a = butter(o, max(f, 5) / (SR / 2), "high"); return lfilter(b, a, x)
def bp(x, f0, f1): return hp(lp(x, f1), f0)
def norm(x, g=0.9): m = np.max(np.abs(x)) or 1.0; return (x / m * g).astype(np.float32)
def env(L, a=0.005, d=0.2):
    t = tt(L); return np.minimum(1, t / max(a, 1e-4)) * np.exp(-np.maximum(0, t - a) / d)
def R(seed): return np.random.default_rng(seed)
def noise(L, seed): return R(seed).standard_normal(int(L * SR))
def verb(x, L=1.2, decay=4.0, wet=0.3, seed=3):
    ir = noise(L, seed) * np.exp(-tt(L) * decay); ir /= np.sqrt(np.sum(ir ** 2)) * 3
    y = fftconvolve(x, ir)[: len(x) + len(ir)]; z = np.zeros(len(y)); z[: len(x)] = x; return z * (1 - wet) + y * wet
def sweep(f0, f1, L, curve=1.0):
    u = (tt(L) / L) ** curve; f = f0 + (f1 - f0) * u; return np.sin(2 * np.pi * np.cumsum(f) / SR)
def grains(L, rate, seed, glen=0.012, f0=1500, f1=7000):
    """crackle: many tiny filtered noise bursts (crunch / gravel / snow)"""
    r = R(seed); y = np.zeros(int(L * SR)); n = int(L * rate)
    for _ in range(n):
        o = r.integers(0, max(1, len(y) - int(glen * SR))); g = noise(glen, r.integers(1e6)) * np.exp(-tt(glen) * r.uniform(150, 500)) * r.uniform(0.2, 1)
        y[o:o + len(g)] += g
    return bp(y, f0, f1)
def mix(*xs):
    n = max(len(x) for x in xs); y = np.zeros(n)
    for x in xs: y[: len(x)] += x
    return y
def pad(x, L): y = np.zeros(int(L * SR)); y[: min(len(x), len(y))] = x[: len(y)]; return y

# ------------------------------------------------------------------ combat
def bite_crunch(v):
    L = 0.55; r = R(10 + v)
    snap = hp(noise(0.03, 11 + v), 1200) * np.exp(-tt(0.03) * 120)          # teeth clack
    crunch = grains(0.4, 900 + 300 * v, 12 + v, 0.008, 900, 6000) * np.exp(-tt(0.4) * 7)
    thud = np.sin(2 * np.pi * (90 + 60 * np.exp(-tt(0.35) * 25)) * tt(0.35)) * np.exp(-tt(0.35) * 12)
    wet = bp(noise(0.3, 13 + v), 200, 1400) * np.exp(-tt(0.3) * 14) * 0.6
    return norm(verb(mix(snap * 0.8, np.concatenate([np.zeros(int(0.015 * SR)), crunch]), thud * 0.9, wet), 0.6, 8, 0.15), 0.95)
def flesh_tear(v):
    L = 0.7; t = tt(L); n = noise(L, 20 + v)
    am = (0.5 + 0.5 * np.sin(2 * np.pi * (28 + 10 * v) * t + np.sin(2 * np.pi * 7 * t) * 3)) * np.minimum(1, t / 0.05) * np.exp(-t * 4)
    y = bp(n, 300, 3500) * am + grains(L, 400, 21 + v, 0.006, 800, 4000) * np.exp(-t * 5) * 0.6
    return norm(y, 0.8)
def blood_splat(v):
    L = 0.45; t = tt(L); y = np.zeros(len(t)); r = R(30 + v)
    for k in range(5 + v):
        o = int(r.uniform(0, 0.2) * SR); d = 0.08; f = r.uniform(250, 600)
        s = np.sin(2 * np.pi * np.cumsum(f * (1 + 2 * np.exp(-tt(d) * 40))) / SR) * np.exp(-tt(d) * 40) * r.uniform(0.4, 1)
        y[o:o + len(s)] += s[: len(y) - o]
    y += bp(noise(L, 31 + v), 300, 2500) * np.exp(-t * 18) * 0.7
    return norm(y, 0.75)
def claw_slash(v):
    L = 0.5; t = tt(L); n = noise(L, 40 + v)
    f = 1200 + 5000 * np.exp(-t * (8 + 3 * v))
    y = np.zeros(len(t)); seg = 480
    for i in range(0, len(t), seg): y[i:i + seg] = bp(n[i:i + seg], f[i] * 0.6, min(f[i] * 1.6, 20000))
    y *= np.minimum(1, t / 0.01) * np.exp(-t * 9)
    rip = grains(0.25, 1400, 41 + v, 0.004, 2000, 9000) * np.exp(-tt(0.25) * 12)
    return norm(mix(y, np.concatenate([np.zeros(int(0.06 * SR)), rip * 0.7])), 0.85)
def body_slam(v):
    L = 1.4; t = tt(L)
    sub = np.sin(2 * np.pi * (34 + 60 * np.exp(-t * (16 + 4 * v))) * t) * np.exp(-t * 3.2)
    smack = lp(noise(L, 50 + v), 1800) * np.exp(-t * 26)
    debris = grains(1.0, 160, 51 + v, 0.02, 400, 4000) * np.exp(-tt(1.0) * 3) * 0.5
    return norm(verb(mix(sub, smack * 0.9, np.concatenate([np.zeros(int(0.05 * SR)), debris])), 1.4, 4, 0.25), 0.98)
def horn_clack(v):
    L = 0.6; t = tt(L); y = 0
    for m, a, d in ((1, 1, 18), (2.3, 0.6, 26), (3.9, 0.35, 34), (6.1, 0.2, 40)):
        y = y + a * np.sin(2 * np.pi * (520 + 90 * v) * m * t) * np.exp(-t * d)
    y += hp(noise(L, 60 + v), 2000) * np.exp(-t * 60) * 0.6
    return norm(verb(y, 0.8, 6, 0.25), 0.8)
def armor_knock(v):
    L = 0.7; t = tt(L); y = 0
    for m, a, d in ((1, 1, 10), (1.7, 0.7, 14), (2.9, 0.4, 20)):
        y = y + a * np.sin(2 * np.pi * (160 + 30 * v) * m * t) * np.exp(-t * d)
    y += lp(noise(L, 70 + v), 3000) * np.exp(-t * 35) * 0.8
    return norm(verb(y, 0.9, 5, 0.25), 0.9)
def tail_whip(v):
    L = 0.6; t = tt(L); n = noise(L, 80 + v)
    sw = bp(n, 300, 2500) * np.sin(np.pi * np.clip(t / 0.35, 0, 1)) ** 2
    crack = np.zeros(len(t)); o = int(0.33 * SR); c = hp(noise(0.05, 81 + v), 1500) * np.exp(-tt(0.05) * 90); crack[o:o + len(c)] = c
    return norm(sw * 0.7 + crack * 1.2, 0.9)
def hitstop_thump(v):
    t = tt(0.5); return norm(np.sin(2 * np.pi * (45 + 80 * np.exp(-t * 30)) * t) * np.exp(-t * 7) + lp(noise(0.5, 90 + v), 400) * np.exp(-t * 20) * 0.5, 0.95)
def heartbeat(v):
    y = np.zeros(int(1.6 * SR))
    for o, g in ((0.0, 1.0), (0.28, 0.7), (0.8, 1.0), (1.08, 0.7)):
        b = np.sin(2 * np.pi * (48 + 30 * np.exp(-tt(0.25) * 30)) * tt(0.25)) * np.exp(-tt(0.25) * 16) * g; i = int(o * SR); y[i:i + len(b)] += b
    return norm(lp(y, 300), 0.9)
def tension_riser(v):
    L = 3.0; t = tt(L); u = t / L
    y = sweep(80, 900, L, 2.2) * 0.35 + hp(noise(L, 95 + v), 1500) * 0.25 + sweep(160, 1800, L, 2.2) * 0.2
    return norm(y * u ** 2.4, 0.7)
def stinger(v):
    L = 2.5; t = tt(L); y = 0
    for f in (55, 82.4, 110, 164.8):
        y = y + (np.sin(2 * np.pi * f * t) + 0.5 * np.sign(np.sin(2 * np.pi * f * t)) * 0.3) * np.exp(-t * 1.4)
    y += lp(noise(L, 96), 900) * np.exp(-t * 10) * 1.5
    return norm(verb(y, 2.0, 2, 0.4), 0.9)
def slowmo_whoosh(v):
    L = 1.6; t = tt(L); n = noise(L, 97 + v); y = np.zeros(len(t)); seg = 960
    f = 200 + 1400 * np.sin(np.pi * t / L) ** 2
    for i in range(0, len(t), seg): y[i:i + seg] = bp(n[i:i + seg], f[i] * 0.5, f[i] * 1.5)
    return norm(verb(y * np.sin(np.pi * t / L) ** 1.5 + sweep(300, 60, L) * 0.25 * np.sin(np.pi * t / L), 1.5, 3, 0.35), 0.75)

# ------------------------------------------------------------------ footsteps by terrain
def step_snow(v):
    L = 0.35; t = tt(L); return norm(grains(L, 2400, 100 + v, 0.005, 1500, 8000) * np.minimum(1, t / 0.03) * np.exp(-t * 9) + lp(noise(L, 101 + v), 300) * np.exp(-t * 25) * 0.8, 0.8)
def step_sand(v):
    L = 0.4; t = tt(L); return norm(bp(noise(L, 110 + v), 300, 3000) * np.minimum(1, t / 0.04) * np.exp(-t * 10) + np.sin(2 * np.pi * 60 * t) * np.exp(-t * 18) * 0.9, 0.8)
def step_mud(v):
    L = 0.5; t = tt(L); y = bp(noise(L, 120 + v), 150, 1200) * np.exp(-t * 9)
    y += np.sin(2 * np.pi * np.cumsum(300 * (1 + np.exp(-t * 18))) / SR) * np.exp(-((t - 0.12) / 0.05) ** 2) * 0.6
    return norm(y + np.sin(2 * np.pi * 55 * t) * np.exp(-t * 15) * 0.8, 0.8)
def step_gravel(v):
    L = 0.4; t = tt(L); return norm(grains(L, 900, 130 + v, 0.01, 600, 5000) * np.exp(-t * 8) + np.sin(2 * np.pi * 65 * t) * np.exp(-t * 16), 0.8)

# ------------------------------------------------------------------ water
def splash_big(v):
    L = 1.8; t = tt(L); r = R(140 + v)
    body = bp(noise(L, 141 + v), 200, 6000) * np.minimum(1, t / 0.02) * np.exp(-t * 2.8)
    drops = np.zeros(len(t))
    for _ in range(60):
        o = int(r.uniform(0.15, 1.5) * SR); f = r.uniform(600, 2500); d = 0.05
        s_ = np.sin(2 * np.pi * np.cumsum(f * (1 + 0.8 * tt(d) / d)) / SR) * np.exp(-tt(d) * 70) * r.uniform(0.1, 0.4); drops[o:o + len(s_)] += s_[: len(drops) - o]
    thump = np.sin(2 * np.pi * (50 + 60 * np.exp(-t * 20)) * t) * np.exp(-t * 6)
    return norm(verb(body + drops + thump * 0.8, 1.0, 5, 0.2), 0.95)
def splash_small(v):
    L = 0.8; t = tt(L); return norm(bp(noise(L, 150 + v), 400, 7000) * np.minimum(1, t / 0.01) * np.exp(-t * 7) + grains(L, 300, 151 + v, 0.02, 800, 3000) * np.exp(-t * 4) * 0.5, 0.75)
def bubbles(v):
    L = 1.6; y = np.zeros(int(L * SR)); r = R(160 + v)
    for _ in range(50 + 20 * v):
        o = int(r.uniform(0, L - 0.1) * SR); f0 = r.uniform(300, 1400); d = r.uniform(0.03, 0.09)
        s_ = np.sin(2 * np.pi * np.cumsum(f0 * (1 + 1.5 * tt(d) / d)) / SR) * np.sin(np.pi * tt(d) / d) * r.uniform(0.2, 1); y[o:o + len(s_)] += s_
    return norm(y * np.exp(-tt(L) * 1.2), 0.7)
def underwater_impact(v):
    L = 2.0; t = tt(L)
    y = np.sin(2 * np.pi * (30 + 50 * np.exp(-t * 10)) * t) * np.exp(-t * 2.2) + lp(noise(L, 170 + v), 500) * np.exp(-t * 6) * 0.8
    return norm(verb(lp(y, 900), 1.8, 2.5, 0.45), 0.98)
def water_swish(v):
    L = 0.9; t = tt(L); n = noise(L, 180 + v); y = np.zeros(len(t)); seg = 960; f = 150 + 900 * np.sin(np.pi * t / L)
    for i in range(0, len(t), seg): y[i:i + seg] = bp(n[i:i + seg], f[i] * 0.6, f[i] * 1.6)
    return norm(lp(y * np.sin(np.pi * t / L) ** 2, 1500), 0.7)
def shark_thrash(v):
    L = 1.4; t = tt(L); am = 0.5 + 0.5 * np.sin(2 * np.pi * (7 + v) * t)
    return norm(lp(bp(noise(L, 190 + v), 150, 2500) * am * np.sin(np.pi * t / L), 1800) + bubbles(v)[: len(t)] * 0.5, 0.85)
def squid_squelch(v):
    L = 0.9; t = tt(L); f = 140 + 120 * np.sin(2 * np.pi * 3 * t)
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * (0.5 + 0.5 * np.sin(2 * np.pi * 23 * t)) + bp(noise(L, 200 + v), 200, 1500) * 0.6
    return norm(lp(y * np.sin(np.pi * t / L), 1600), 0.75)

# ------------------------------------------------------------------ creature voices
def whale_moan(v):
    L = 3.5; t = tt(L); f = 90 + 70 * np.sin(np.pi * t / L) + 15 * np.sin(2 * np.pi * 0.7 * t)
    y = sum(a * np.sin(2 * np.pi * np.cumsum(f * m) / SR) for m, a in ((1, 1), (2, 0.4), (3, 0.2))) * np.sin(np.pi * t / L) ** 0.7
    return norm(verb(lp(y, 1200), 2.5, 1.6, 0.5), 0.85)
def whale_clicks(v):
    L = 1.6; y = np.zeros(int(L * SR)); per = 0.06 + 0.02 * v; k = 0
    while k * per < L - 0.02:
        c = hp(noise(0.006, 210 + k), 800) * np.exp(-tt(0.006) * 800); i = int(k * per * SR); y[i:i + len(c)] += c * (1 - 0.3 * (k % 3 == 0)); k += 1
    return norm(verb(y, 1.2, 3, 0.4), 0.7)
def mammoth_trumpet(v):
    L = 1.9; t = tt(L); u = t / L
    f = 330 + 260 * np.sin(np.pi * np.clip(u * 1.3, 0, 1)) + 40 * np.sin(2 * np.pi * 6 * t) * u
    saw = 2 * ((np.cumsum(f) / SR) % 1) - 1
    y = bp(saw, 250, 4000) + bp(noise(L, 220 + v), 800, 3500) * 0.35 * (0.5 + 0.5 * np.sin(2 * np.pi * 40 * t))
    return norm(verb(y * np.minimum(1, t / 0.08) * np.exp(-np.maximum(0, t - 1.4) * 6), 1.6, 3, 0.35), 0.85)
def cat_snarl(v):
    L = 1.3; t = tt(L); f = 120 + 40 * np.sin(2 * np.pi * 2 * t)
    rasp = bp(noise(L, 230 + v), 300, 3000) * (0.5 + 0.5 * np.sin(2 * np.pi * (30 + 8 * v) * t))
    y = rasp + np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * 0.25
    return norm(lp(y, 3500) * np.minimum(1, t / 0.05) * np.exp(-np.maximum(0, t - 0.9) * 8), 0.8)
def croc_hiss(v):
    L = 1.2; t = tt(L); return norm(bp(noise(L, 240 + v), 1500, 7000) * np.sin(np.pi * t / L) ** 0.5 + np.sin(2 * np.pi * 50 * t) * 0.3 * np.sin(np.pi * t / L), 0.6)
def pain_yelp(v):
    L = 0.9; t = tt(L); f = 600 + 400 * np.exp(-t * 4) + 60 * np.sin(2 * np.pi * 9 * t)
    y = sum(a * np.sin(2 * np.pi * np.cumsum(f * m) / SR) for m, a in ((1, 1), (2, 0.5), (3, 0.25)))
    return norm(verb(bp(y, 300, 4000) * np.minimum(1, t / 0.02) * np.exp(-t * 3), 1.0, 4, 0.3), 0.7)

# ------------------------------------------------------------------ weather / one-shots
def thunder(v):
    L = 5.0; t = tt(L); r = R(250 + v)
    crack = hp(noise(0.25, 251 + v), 1000) * np.exp(-tt(0.25) * 18)
    rumble = lp(noise(L, 252 + v), 160) * (0.4 + 0.6 * lp(np.abs(noise(L, 253 + v)), 3)) * np.exp(-t * 0.8) * 6
    return norm(verb(mix(crack, rumble), 2.5, 1.5, 0.4), 0.98)
def wind_gust(v):
    L = 3.0; t = tt(L); n = noise(L, 260 + v); y = np.zeros(len(t)); seg = 1200; f = 300 + 500 * np.sin(np.pi * t / L) ** 2
    for i in range(0, len(t), seg): y[i:i + seg] = bp(n[i:i + seg], f[i] * 0.7, f[i] * 1.5)
    return norm(y * np.sin(np.pi * t / L) ** 1.4, 0.6)
def rock_debris(v):
    L = 1.2; t = tt(L); return norm(grains(L, 220, 270 + v, 0.03, 300, 5000) * np.exp(-t * 2.5) + lp(noise(L, 271 + v), 200) * np.exp(-t * 6) * 0.6, 0.75)
def lava_burst(v):
    L = 1.6; t = tt(L); return norm(lp(noise(L, 280 + v), 400) * np.exp(-t * 2) * 2 + grains(L, 300, 281 + v, 0.02, 500, 3000) * np.exp(-t * 2), 0.9)

# ------------------------------------------------------------------ ambience beds (loopable ~12 s)
def _loop(y, xf=1.0):
    n = int(xf * SR); a = y[:n].copy(); y = y[n:].copy(); y[-n:] = y[-n:] * np.linspace(1, 0, n) + a * np.linspace(0, 1, n); return y
def _chirps(L, seed, n, f0, f1, dur=0.08, rep=(2, 6)):
    r = R(seed); y = np.zeros(int(L * SR))
    for _ in range(n):
        o = r.uniform(0, L - 1); f = r.uniform(f0, f1); k = r.integers(*rep)
        for j in range(k):
            s_ = np.sin(2 * np.pi * np.cumsum(f * (1 + 0.3 * np.sin(2 * np.pi * 12 * tt(dur)))) / SR) * np.sin(np.pi * tt(dur) / dur) * r.uniform(0.2, 1)
            i = int((o + j * dur * 1.4) * SR); y[i:i + len(s_)] += s_[: len(y) - i]
    return y
def _bed(L, seed, f0, f1, g=1.0): return bp(noise(L, seed), f0, f1) * g
def amb(name):
    L = 13.0; t = tt(L)
    if name == "jungle":
        y = _bed(L, 300, 200, 2500, 0.15) + _chirps(L, 301, 26, 1800, 4200) * 0.25 + _chirps(L, 302, 10, 700, 1200, 0.18, (1, 3)) * 0.2
        y += hp(noise(L, 303), 5000) * (0.5 + 0.5 * np.sin(2 * np.pi * 9 * t)) * 0.06   # insects
    elif name in ("tundra", "snowforest"):
        y = lp(noise(L, 310), 700) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.11 * t)) * 0.6 + bp(noise(L, 311), 1500, 4000) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.07 * t)) ** 3 * 0.15
    elif name in ("canyon", "savanna"):
        y = bp(noise(L, 320), 150, 900) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.09 * t)) * 0.5 + _chirps(L, 321, 6, 2200, 3200, 0.05, (3, 8)) * 0.12
        if name == "savanna": y += hp(noise(L, 322), 4500) * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 14 * t))) * 0.05
    elif name == "swamp":
        y = _bed(L, 330, 100, 800, 0.25) + _chirps(L, 331, 18, 180, 320, 0.12, (2, 5)) * 0.35 + hp(noise(L, 332), 4000) * (0.5 + 0.5 * np.sin(2 * np.pi * 6 * t)) * 0.07
    elif name in ("beach", "ocean"):
        w = 0.5 + 0.5 * np.sin(2 * np.pi * t / 6.5) ** 2
        y = bp(noise(L, 340), 150, 3000) * w * 0.7 + _chirps(L, 341, 4, 1500, 2600, 0.15, (1, 3)) * 0.12
    elif name == "storm":
        y = hp(noise(L, 350), 900) * 0.35 + lp(noise(L, 351), 300) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.13 * t)) * 0.6
    elif name in ("reef", "kelp"):
        y = lp(noise(L, 360), 350) * 0.5
        b = np.zeros(len(t))
        for k in range(8): bb = bubbles(k); i = int((k * 1.5) % (L - 2) * SR); b[i:i + len(bb)] += bb * 0.35
        y = y + b + _chirps(L, 361, 30, 2500, 6000, 0.01, (1, 2)) * 0.15   # snapping shrimp crackle
    elif name in ("deep", "abyss"):
        y = lp(noise(L, 370), 120) * 1.2 + np.sin(2 * np.pi * 41 * t) * 0.15 * (0.5 + 0.5 * np.sin(2 * np.pi * 0.05 * t))
        if name == "abyss":
            for k in range(3): i = int((2 + k * 4) * SR); p = np.sin(2 * np.pi * 1500 * tt(1.5)) * np.exp(-tt(1.5) * 3) * 0.25; y[i:i + len(p)] += verb(p, 1.0, 3, 0.6)[: len(p)]
    elif name == "volcano":
        y = lp(noise(L, 380), 90) * 1.5 + grains(L, 30, 381, 0.04, 300, 2500) * 0.3
    elif name == "rain":
        y = hp(noise(L, 390), 1200) * 0.3 + grains(L, 600, 391, 0.004, 2000, 8000) * 0.2
    elif name == "night":
        y = _bed(L, 400, 100, 600, 0.12) + hp(noise(L, 401), 4200) * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 16 * t))) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.5 * t)) * 0.08
    elif name == "river":
        y = bp(noise(L, 410), 300, 4000) * (0.8 + 0.2 * np.sin(2 * np.pi * 0.7 * t)) * 0.4 + _chirps(L, 411, 10, 1800, 3800) * 0.15
    else:   # land / sunset
        y = bp(noise(L, 420), 120, 900) * 0.25 + _chirps(L, 421, 14, 1800, 4000) * 0.18
    return norm(_loop(y), 0.5)

# ------------------------------------------------------------------ registry
GEN = {
    "bite-crunch": (bite_crunch, 3), "flesh-tear": (flesh_tear, 2), "blood-splat": (blood_splat, 3), "claw-slash": (claw_slash, 3),
    "body-slam": (body_slam, 2), "horn-clack": (horn_clack, 2), "armor-knock": (armor_knock, 2), "tail-whip": (tail_whip, 2),
    "hitstop-thump": (hitstop_thump, 2), "heartbeat": (heartbeat, 1), "tension-riser": (tension_riser, 1), "stinger": (stinger, 1), "slowmo-whoosh": (slowmo_whoosh, 2),
    "step-snow": (step_snow, 4), "step-sand": (step_sand, 4), "step-mud": (step_mud, 4), "step-gravel": (step_gravel, 4),
    "splash-big": (splash_big, 2), "splash-small": (splash_small, 3), "bubbles": (bubbles, 3), "underwater-impact": (underwater_impact, 2),
    "water-swish": (water_swish, 3), "shark-thrash": (shark_thrash, 2), "squid-squelch": (squid_squelch, 2),
    "whale-moan": (whale_moan, 2), "whale-clicks": (whale_clicks, 2), "mammoth-trumpet": (mammoth_trumpet, 2), "cat-snarl": (cat_snarl, 2),
    "croc-hiss": (croc_hiss, 2), "pain-yelp": (pain_yelp, 2), "deep-growl": (lambda v: norm(lp(cat_snarl(v), 500), 0.9), 2), "monster-roar": (lambda v: norm(lp(cat_snarl(v + 2), 1500), 0.9), 2),
    "thunder": (thunder, 2), "wind-gust": (wind_gust, 2), "rock-debris": (rock_debris, 2), "lava-burst": (lava_burst, 2),
}
AMB = ("land", "sunset", "night", "rain", "volcano", "river", "jungle", "tundra", "canyon", "swamp", "beach", "savanna", "storm",
       "snowforest", "ocean", "reef", "kelp", "deep", "abyss")
_MEM = {}
def get(name):
    """name: '<key>-<variant>' (e.g. 'bite-crunch-2'), '<key>' (variant 1) or 'amb-<scene>'"""
    if name in _MEM: return _MEM[name]
    import soundfile as sf
    os.makedirs(CACHE, exist_ok=True); fp = os.path.join(CACHE, name + ".wav")
    if os.path.exists(fp):
        x, _ = sf.read(fp, dtype="float32")
    else:
        if name.startswith("amb-"): x = amb(name[4:])
        else:
            base, v = (name.rsplit("-", 1) if name[-1].isdigit() and name.rsplit("-", 1)[0] in GEN else (name, "1"))
            fn, _n = GEN[base]; x = fn(int(v))
        x = np.asarray(x, np.float32); sf.write(fp, x, SR, subtype="PCM_16")
    _MEM[name] = x; return x
def all_names():
    return [f"{k}-{v}" for k, (_, n) in GEN.items() for v in range(1, n + 1)] + [f"amb-{a}" for a in AMB]
