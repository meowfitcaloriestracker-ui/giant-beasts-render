# -*- coding: utf-8 -*-
"""Living scenes (v21): the background stays the same scene the whole clip, but it is alive.

  mid(img, env, t, xoff)   - drawn on the world canvas right after the painted background, BEFORE the fighters:
                             * near trees that sway in the wind (pivot at the trunk base, tips move most)
                             * far animals going about their day (herds walking along the horizon, flyers, fish schools)
                             * near grass band that ripples
  front(img, env, t)       - drawn on the output frame after the camera: corner foliage that sways (replaces the static fronds)

Everything is a pure function of (env, t) seeded with crc32 -> every parallel render part draws the same world.
Env switches:  LIVING=0 turns it all off, LIV_TREES / LIV_ANIMALS / LIV_FRONT = 0 to turn one part off.
Add a new scene preset to PRESET; add a new background animal to ANIMALS (a draw function).
"""
import math, random, zlib, os
from PIL import Image, ImageDraw, ImageFilter
import scenes as SC

ON = os.environ.get("LIVING", "1") == "1"
def _on(k): return ON and os.environ.get(k, "1") == "1"
HZ, GY = SC.HZ, SC.GY

# ---------------------------------------------------------------- presets per scene
#   trees: (kind, colour, count, scale range)   herd: animal kind, how many, colour   fly: flyers   wind: sway strength
PRESET = {
 "jungle":     dict(trees=("broad", (62, 96, 60), 5, (1.1, 1.5)), herd=("sauropod", 4, (96, 122, 104)), fly=("ptero", 3), wind=1.0, grass=(70, 110, 52)),
 "savanna":    dict(trees=("acacia", (84, 76, 44), 3, (1.0, 1.3)), herd=("sauropod", 5, (150, 110, 80)), fly=("ptero", 4), wind=0.8, grass=(214, 176, 96)),
 "swamp":      dict(trees=("dead", (64, 78, 60), 4, (1.0, 1.4)), herd=("duckbill", 5, (110, 124, 104)), fly=("ptero", 2), wind=0.6, grass=(96, 110, 50)),
 "canyon":     dict(trees=("dead", (120, 84, 60), 2, (0.8, 1.1)), herd=("duckbill", 4, (170, 120, 90)), fly=("ptero", 3), wind=0.5, grass=(150, 140, 80)),
 "beach":      dict(trees=("palm", (54, 96, 58), 3, (1.1, 1.4)), herd=("duckbill", 3, (150, 140, 120)), fly=("ptero", 4), wind=1.2, grass=None),
 "storm":      dict(trees=("broad", (48, 60, 50), 4, (1.0, 1.3)), herd=("sauropod", 3, (84, 92, 96)), fly=None, wind=2.2, grass=(80, 96, 56)),
 "tundra":     dict(trees=("conifer", (84, 100, 104), 4, (0.7, 1.0)), herd=("mammoth", 4, (150, 150, 160)), fly=("bird", 5), wind=0.9, grass=(170, 156, 110)),
 "snowforest": dict(trees=("conifer", (66, 88, 94), 5, (1.0, 1.3)), herd=("deer", 4, (130, 136, 150)), fly=("bird", 4), wind=0.7, grass=None),
 "reef":       dict(trees=None, herd=("fish", 3, (60, 150, 180)), fly=None, wind=0.0, grass=None),
 "kelp":       dict(trees=None, herd=("fish", 3, (50, 120, 120)), fly=None, wind=0.0, grass=None),
 "deep":       dict(trees=None, herd=("fish", 2, (40, 80, 120)), fly=None, wind=0.0, grass=None),
}

def _rnd(env, salt): return random.Random((zlib.crc32((env + ":" + salt).encode()) & 0xffffff))
def _mix(a, b, u): return tuple(int(a[i] + (b[i] - a[i]) * u) for i in range(3))

# ---------------------------------------------------------------- swaying trees
_TREE = {}
def _tree_sprite(kind, col, s, seed):
    key = (kind, col, round(s, 2), seed)
    if key not in _TREE:
        w, h = int(700 * s), int(820 * s); L = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        SC.tree_sil(ImageDraw.Draw(L), w / 2, h - 4, s, col, random.Random(seed), kind)
        _TREE[key] = L.filter(ImageFilter.GaussianBlur(1.2))   # a touch softer than the fighters = sits behind them
    return _TREE[key]

def _sway(sp, ang_deg):
    """bend: rotate around the trunk base (bottom centre); top moves, roots stay planted"""
    w, h = sp.size
    return sp.rotate(ang_deg, resample=Image.BICUBIC, center=(w / 2, h - 4), expand=False)

def trees(img, env, t, xoff):
    P = PRESET.get(env);
    if not P or not P["trees"]: return
    kind, col, n, (s0, s1) = P["trees"]; r = _rnd(env, "trees"); W_ = img.size[0]
    # keep them at the sides / behind the fight so they frame the action instead of hiding it
    slots = [r.uniform(-150, 380) for _ in range((n + 1) // 2)] + [r.uniform(W_ - 380, W_ + 150) for _ in range(n // 2)]
    for k, wx in enumerate(slots):
        s = r.uniform(s0, s1); seed = r.randint(0, 9999); ph = r.uniform(0, 6.28); fq = r.uniform(0.35, 0.6)
        gust = 0.5 + 0.5 * math.sin(t * 0.21 + ph * 0.3)                       # slow gusts
        ang = P["wind"] * (1.6 * math.sin(t * fq * 6.283 + ph) + 1.2 * gust * math.sin(t * 2.3 + ph)) * (1.0 if kind != "conifer" else 0.5)
        sp = _sway(_tree_sprite(kind, col, s, seed), ang)
        base_y = HZ + 60 + k % 3 * 26
        x = int(wx - xoff * 0.15 - sp.size[0] / 2)                            # tiny parallax vs the painted far layer
        img.alpha_composite(sp, (x, int(base_y - sp.size[1])))

# ---------------------------------------------------------------- far animals
def _sauropod(d, x, y, s, col, ph, dirn):
    a = col + (255,)
    d.ellipse((x - 60 * s, y - 70 * s, x + 60 * s, y - 20 * s), fill=a)                              # body
    nx = x + dirn * 50 * s; d.line([(nx, y - 55 * s), (nx + dirn * 50 * s, y - 120 * s + 4 * s * math.sin(ph * 0.5)), (nx + dirn * 70 * s, y - 128 * s)], fill=a, width=max(2, int(16 * s)))
    d.ellipse((nx + dirn * 62 * s - 9 * s, y - 136 * s, nx + dirn * 62 * s + 13 * s, y - 120 * s), fill=a)
    d.line([(x - dirn * 55 * s, y - 50 * s), (x - dirn * 110 * s, y - 40 * s + 6 * s * math.sin(ph)), (x - dirn * 150 * s, y - 30 * s)], fill=a, width=max(2, int(10 * s)))
    for k, lx in enumerate((-35, -20, 25, 40)):
        sw = 9 * s * math.sin(ph + (k % 2) * math.pi); d.line([(x + lx * s, y - 35 * s), (x + lx * s + sw, y)], fill=a, width=max(2, int(12 * s)))
def _duckbill(d, x, y, s, col, ph, dirn):
    a = col + (255,); d.ellipse((x - 40 * s, y - 62 * s, x + 40 * s, y - 28 * s), fill=a)
    d.line([(x + dirn * 30 * s, y - 50 * s), (x + dirn * 55 * s, y - 72 * s)], fill=a, width=max(2, int(10 * s)))
    d.ellipse((x + dirn * 48 * s - 12 * s, y - 82 * s, x + dirn * 48 * s + 14 * s, y - 66 * s), fill=a)
    d.line([(x - dirn * 35 * s, y - 45 * s), (x - dirn * 95 * s, y - 40 * s + 5 * s * math.sin(ph))], fill=a, width=max(2, int(8 * s)))
    for k, lx in enumerate((-8, 10)):
        sw = 10 * s * math.sin(ph + k * math.pi); d.line([(x + lx * s, y - 35 * s), (x + lx * s + sw, y)], fill=a, width=max(2, int(8 * s)))
def _mammoth(d, x, y, s, col, ph, dirn):
    a = col + (255,); d.ellipse((x - 55 * s, y - 85 * s, x + 50 * s, y - 25 * s), fill=a); d.ellipse((x + dirn * 30 * s - 25 * s, y - 95 * s, x + dirn * 30 * s + 25 * s, y - 55 * s), fill=a)
    d.line([(x + dirn * 50 * s, y - 65 * s), (x + dirn * 58 * s, y - 25 * s + 4 * s * math.sin(ph))], fill=a, width=max(2, int(9 * s)))
    d.arc((x + dirn * 30 * s - 10 * s, y - 70 * s, x + dirn * 30 * s + 50 * s, y - 20 * s), 20 if dirn > 0 else 100, 160 if dirn > 0 else 200, fill=(240, 236, 220, 255), width=max(2, int(4 * s)))
    for k, lx in enumerate((-35, -18, 15, 32)):
        sw = 7 * s * math.sin(ph + (k % 2) * math.pi); d.line([(x + lx * s, y - 40 * s), (x + lx * s + sw, y)], fill=a, width=max(2, int(13 * s)))
def _deer(d, x, y, s, col, ph, dirn):
    a = col + (255,); d.ellipse((x - 30 * s, y - 58 * s, x + 30 * s, y - 36 * s), fill=a)
    d.line([(x + dirn * 25 * s, y - 50 * s), (x + dirn * 38 * s, y - 75 * s)], fill=a, width=max(2, int(7 * s))); d.ellipse((x + dirn * 34 * s - 7 * s, y - 84 * s, x + dirn * 34 * s + 10 * s, y - 72 * s), fill=a)
    for sg in (-1, 1): d.line([(x + dirn * 36 * s, y - 82 * s), (x + dirn * 36 * s + sg * 10 * s, y - 100 * s)], fill=a, width=max(1, int(3 * s)))
    for k, lx in enumerate((-22, -12, 14, 24)):
        sw = 6 * s * math.sin(ph + (k % 2) * math.pi); d.line([(x + lx * s, y - 40 * s), (x + lx * s + sw, y)], fill=a, width=max(1, int(4 * s)))
def _fish(d, x, y, s, col, ph, dirn):
    a = col + (220,); d.ellipse((x - 26 * s, y - 9 * s, x + 26 * s, y + 9 * s), fill=a)
    tx = x - dirn * 26 * s; wag = 8 * s * math.sin(ph * 2); d.polygon([(tx, y), (tx - dirn * 16 * s, y - 11 * s + wag), (tx - dirn * 16 * s, y + 11 * s + wag)], fill=a)
ANIMALS = {"sauropod": _sauropod, "duckbill": _duckbill, "mammoth": _mammoth, "deer": _deer, "fish": _fish}

def herd(img, env, t, xoff):
    P = PRESET.get(env)
    if not P or not P["herd"]: return
    kind, n, col = P["herd"]; r = _rnd(env, "herd"); W_ = img.size[0]
    sky = img.getpixel((W_ // 2, HZ - 30))[:3]; col = _mix(_mix(col, (30, 30, 34), 0.35), sky, 0.38)       # atmospheric perspective: far = hazy
    L = Image.new("RGBA", img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    dirn = r.choice((-1, 1)); spd = r.uniform(14, 22) * (2.2 if kind == "fish" else 1)   # px per second (far away = slow)
    span = W_ + 900
    for k in range(n):
        s = r.uniform(0.6, 0.85) if kind != "fish" else r.uniform(0.6, 1.0)
        x = (r.uniform(0, span) + dirn * spd * t) % span - 450 - xoff * 0.3
        y = HZ + 8 + r.uniform(0, 34) if kind != "fish" else r.uniform(380, 900) + 30 * math.sin(t * 0.4 + k)
        ph = t * (2.4 if kind != "fish" else 3.0) + k * 1.7
        ANIMALS[kind](d, x, y, s, col, ph, dirn)
        if kind == "fish":   # small school around the leader
            for j in range(5): ANIMALS[kind](d, x - dirn * (40 + 30 * j) * s, y + (j % 3 - 1) * 28 * s + 6 * math.sin(t * 2 + j), s * 0.7, col, ph + j, dirn)
    img.alpha_composite(L.filter(ImageFilter.GaussianBlur(1.5)))

def flyers(img, env, t, xoff):
    P = PRESET.get(env)
    if not P or not P["fly"]: return
    kind, n = P["fly"]; r = _rnd(env, "fly"); W_ = img.size[0]
    d = ImageDraw.Draw(img, "RGBA"); sky = img.getpixel((W_ // 2, HZ - 300))[:3]; col = _mix((40, 36, 40), sky, 0.45) + (230,)
    span = W_ + 600
    for k in range(n):
        s = r.uniform(0.6, 1.1) * (1.4 if kind == "ptero" else 0.8); dirn = r.choice((-1, 1)); spd = r.uniform(40, 90)
        x = (r.uniform(0, span) + dirn * spd * t) % span - 300 - xoff * 0.1; y = r.uniform(HZ - 620, HZ - 260) + 25 * math.sin(t * 0.5 + k)
        flap = math.sin(t * (3.2 if kind == "ptero" else 7) + k * 2); wy = -14 * s * flap
        span_w = 46 * s if kind == "ptero" else 22 * s
        d.line([(x - span_w, y + wy), (x - span_w * 0.4, y - 4 * s), (x, y), (x + span_w * 0.4, y - 4 * s), (x + span_w, y + wy)], fill=col, width=max(2, int(4 * s)), joint="curve")
        if kind == "ptero": d.line([(x, y), (x + dirn * 16 * s, y - 2 * s)], fill=col, width=max(2, int(4 * s)))

def grass_wave(img, env, t, xoff):
    """a strip of tall grass between the far herd and the fighters that ripples in the wind"""
    P = PRESET.get(env)
    if not P or not P["grass"]: return
    col = P["grass"]; r = _rnd(env, "grass"); W_ = img.size[0]; d = ImageDraw.Draw(img, "RGBA")
    for k in range(240):
        x = r.uniform(-20, W_ + 20) - xoff * 0.5 % 40; y = r.uniform(HZ + 40, HZ + 150); h = r.uniform(20, 46) * (0.7 + (y - HZ) / 300)
        bend = P["wind"] * 9 * math.sin(t * 1.8 - x / 160 + r.uniform(0, 0.6))
        c = _mix(col, (0, 0, 0), r.uniform(0, 0.25)) + (230,)
        d.line([(x, y), (x + bend * 0.5, y - h * 0.5), (x + bend, y - h)], fill=c, width=3)

def mid(img, env, t, xoff=0):
    """call right after the background, before the fighters"""
    if not ON or env not in PRESET: return
    if _on("LIV_ANIMALS"): flyers(img, env, t, xoff); herd(img, env, t, xoff)
    if _on("LIV_TREES"): trees(img, env, t, xoff); grass_wave(img, env, t, xoff)

# ---------------------------------------------------------------- swaying corner foliage (front layer, after the camera)
_FRONDS = {}
def _frond_set(env, under):
    if env not in _FRONDS:
        r = _rnd(env, "front"); out = []
        for side in (0, 1):
            for _ in range(14 if not under else 7):
                out.append(dict(side=side, x=r.uniform(0, 300), ln=(r.uniform(160, 360) if not under else r.uniform(300, 620)),
                                ang=r.uniform(-0.5, 0.5) + (0.35 if side == 0 else -0.35), wd=r.uniform(14, 26) if not under else r.uniform(18, 34), ph=r.uniform(0, 6.3)))
        rocks = [(side, r.uniform(-60, 260), r.uniform(-30, 40), r.uniform(110, 230), r.uniform(60, 130)) for side in (0, 1) for _ in range(3)]
        _FRONDS[env] = (out, rocks)
    return _FRONDS[env]

def front(img, env, t):
    if not _on("LIV_FRONT"): return False
    under = env in SC.UNDER; w, h = img.size; k_ = 2                      # draw at half size (it is blurred anyway)
    L = Image.new("RGBA", (w // k_, h // k_), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    col = (8, 34, 40, 235) if under else ((24, 30, 14, 240) if env not in ("tundra", "snowforest") else (40, 48, 58, 230))
    fr, rocks = _frond_set(env, under); wind = PRESET.get(env, {}).get("wind", 0.8) or 0.5
    for side, dx, dy, rx, ry in rocks:
        cx = (dx if side == 0 else w - dx) / k_; cy = (h + dy) / k_; d.ellipse((cx - rx / k_, cy - ry / k_, cx + rx / k_, cy + ry / k_), fill=col)
    for f in fr:
        x0 = (f["x"] if f["side"] == 0 else w - f["x"]); y0 = h + 10; pts = []
        sway = (0.10 * wind * math.sin(t * 1.3 + f["ph"]) + 0.05 * wind * math.sin(t * 3.1 + f["ph"] * 2)) if not under else 0.18 * math.sin(t * 0.7 + f["ph"])
        for k in range(14):
            u = k / 13; a = f["ang"] + sway * u * u
            pts.append(((x0 + math.sin(a) * f["ln"] * u) / k_, (y0 - math.cos(a) * f["ln"] * u + u * u * 60) / k_))
        for k in range(13):
            d.line([pts[k], pts[k + 1]], fill=col, width=max(2, int(f["wd"] * (1 - k / 14) / k_)))
            if not under and k % 2 == 0 and k > 2:
                px, py = pts[k]; s_ = f["wd"] * 1.6 * (1 - k / 14) / k_
                d.ellipse((px - s_ * 1.6, py - s_ * 0.5, px, py + s_ * 0.3), fill=col); d.ellipse((px, py - s_ * 0.5, px + s_ * 1.6, py + s_ * 0.3), fill=col)
    L = L.filter(ImageFilter.GaussianBlur(3.5)).resize((w, h), Image.BILINEAR)
    img.alpha_composite(L); return True
