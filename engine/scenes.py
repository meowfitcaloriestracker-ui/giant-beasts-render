"""Painted, more realistic backgrounds for the 16:9 fight scenes.

Each scene is built once per render process (cached) on a wide canvas: horizon ~1060 px,
fighters stand at y=1330. Layers: sky gradient + soft clouds -> far ranges in haze ->
mid ranges -> tree / rock silhouettes -> textured ground -> foreground tufts.
Backgrounds have no black outlines, so the outlined characters stay readable on top.
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HZ = 1060          # horizon line
GY = 1330          # where the fighters' feet are

SCENES = {   # key: Thai name shown in UI / scripts
    "jungle": "ป่าดิบชื้น", "tundra": "ทุ่งน้ำแข็งยุคน้ำแข็ง", "canyon": "หุบผาหินแดง",
    "swamp": "หนองบึงหมอก", "beach": "ชายฝั่งทะเล", "savanna": "ทุ่งหญ้าแดดเย็น",
    "storm": "ทุ่งราบพายุ", "snowforest": "ป่าสนหิมะ",
    "ocean": "กลางทะเล (ผิวน้ำ)", "reef": "ใต้ทะเลน้ำตื้น แนวปะการัง", "kelp": "ป่าสาหร่ายใต้น้ำ",
    "deep": "ทะเลลึก", "abyss": "ใต้ทะเลลึกมืดมิด",
}
UNDER = ("reef", "kelp", "deep", "abyss")   # fully underwater: blood becomes clouds, bubbles, blue tint
WL = 905   # ocean waterline (creatures float half-submerged)

# ------------------------------------------------------------------ helpers

def pblur(L, r):
    """premultiplied blur: soft edges keep their own colour instead of fading to black"""
    a = np.asarray(L).astype(np.float32); al = a[..., 3:4] / 255.0
    pm = Image.fromarray(np.clip(a[..., :3] * al, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(r))
    A = L.getchannel("A").filter(ImageFilter.GaussianBlur(r))
    pa = np.asarray(pm).astype(np.float32); aa = np.asarray(A).astype(np.float32)[..., None] / 255.0
    rgb = np.where(aa > 1e-3, pa / np.maximum(aa, 1e-3), 0)
    return Image.fromarray(np.dstack([np.clip(rgb, 0, 255), aa[..., 0] * 255]).astype(np.uint8), "RGBA")

def mix(a, b, u): return tuple(int(a[i] + (b[i] - a[i]) * u) for i in range(3))

def vgrad(w, h, stops):
    ys = np.linspace(0, 1, h); cols = np.zeros((h, 3))
    for c in range(3): cols[:, c] = np.interp(ys, [s[0] for s in stops], [s[1][c] for s in stops])
    return Image.fromarray(np.repeat(cols[:, None, :], w, 1).astype(np.uint8), "RGB").convert("RGBA")

def noise(w, h, scale, seed):
    """cheap smooth value noise in [0,1]"""
    r = np.random.default_rng(seed)
    g = r.random((h // scale + 3, w // scale + 3)).astype(np.float32)
    im = Image.fromarray((g * 255).astype(np.uint8)).resize((w + 3 * scale, h + 3 * scale), Image.BICUBIC)
    return np.asarray(im, dtype=np.float32)[:h, :w] / 255.0

def ridge(w, base, amp, seed, rough=1.0, step=12):
    rnd = random.Random(seed); ph = [rnd.uniform(0, 6.28) for _ in range(4)]
    pts = []
    for x in range(-step, w + 2 * step, step):
        y = base - amp * (0.55 * math.sin(x / 520 + ph[0]) + 0.3 * math.sin(x / 210 + ph[1]) + 0.15 * rough * math.sin(x / 70 + ph[2]) + 0.06 * rough * math.sin(x / 23 + ph[3]))
        pts.append((x, y))
    return pts

def layer(img, poly, col, blur=0, alpha=255, grad=None):
    """filled polygon layer; grad=(top_col, bottom_col, y0, y1) shades it vertically"""
    w, h = img.size
    m = Image.new("L", (w, h), 0); ImageDraw.Draw(m).polygon(poly, fill=alpha)
    if blur: m = m.filter(ImageFilter.GaussianBlur(blur))
    fill = vgrad(w, h, [(0, grad[0]), (grad[2] / h, grad[0]), (grad[3] / h, grad[1]), (1, grad[1])]) if grad else Image.new("RGBA", (w, h), col + (255,))
    fill.putalpha(m); img.alpha_composite(fill)

def haze(img, y0, y1, col, a):
    w, h = img.size; L = Image.new("RGBA", (w, h), (0, 0, 0, 0)); arr = np.zeros((h, 1), np.float32)
    ys = np.arange(h); arr[:, 0] = np.clip(1 - np.abs(ys - (y0 + y1) / 2) / max(1, (y1 - y0) / 2), 0, 1) * a
    al = Image.fromarray(np.repeat(arr, w, 1).astype(np.uint8)); L = Image.new("RGBA", (w, h), col + (255,)); L.putalpha(al); img.alpha_composite(L)

def clouds(img, rnd, n, y0, y1, col, a=150, big=1.0):
    """v18: cumulus with a shaded base, lit puffy tops and a soft rim of light"""
    w, h = img.size
    sh = mix(col, (110, 105, 130), 0.22); lit = mix(col, (255, 255, 255), 0.4)
    Lb = Image.new("RGBA", (w, h), (0, 0, 0, 0)); Lm = Image.new("RGBA", (w, h), (0, 0, 0, 0)); Lt = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    db, dm, dt = ImageDraw.Draw(Lb), ImageDraw.Draw(Lm), ImageDraw.Draw(Lt)
    for _ in range(n):
        cx, cy = rnd.uniform(0, w), rnd.uniform(y0, y1); s = rnd.uniform(0.5, 1.1) * big * 0.62
        db.ellipse((cx - 230 * s, cy - 10 * s, cx + 230 * s, cy + 55 * s), fill=sh + (int(a * 0.55),))       # flat shaded base
        for k in range(9):
            u = (k - 4) / 4.0; rx = rnd.uniform(55, 120) * s * (1.15 - abs(u) * 0.4); ry = rx * rnd.uniform(0.7, 0.95)
            px, py = cx + u * 170 * s + rnd.uniform(-20, 20) * s, cy - (1 - abs(u)) * 70 * s - rnd.uniform(0, 30) * s
            dm.ellipse((px - rx, py - ry, px + rx, py + ry), fill=col + (a,))
            dt.ellipse((px - rx * 0.78, py - ry * 0.95, px + rx * 0.72, py + ry * 0.35), fill=lit + (int(a * 0.85),))   # light from above
    img.alpha_composite(pblur(Lb, 16))
    img.alpha_composite(pblur(Lm, 9))
    img.alpha_composite(pblur(Lt, 12))

def ground(img, top, bot, seed, speck=(0, 0, 0), sa=40, tex=0.22):
    """ground plane with gradient + noise texture + a few darker patches"""
    w, h = img.size
    g = vgrad(w, h - HZ, [(0, top), (1, bot)])
    n = noise(w, h - HZ, 40, seed) * 0.6 + noise(w, h - HZ, 9, seed + 1) * 0.4
    arr = np.asarray(g, dtype=np.float32).copy(); arr[..., :3] *= (1 - tex / 2 + tex * n)[..., None]
    g = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA")
    img.alpha_composite(g, (0, HZ))
    d = ImageDraw.Draw(img, "RGBA"); rnd = random.Random(seed)
    for _ in range(900):
        y = rnd.uniform(HZ + 10, h); x = rnd.uniform(0, w); s = 0.4 + (y - HZ) / (h - HZ) * 2.2
        d.ellipse((x - 3 * s, y - 1 * s, x + 3 * s, y + 1 * s), fill=speck + (sa,))

def grass_tufts(img, rnd, n, y0, y1, cols, hmax=60):
    d = ImageDraw.Draw(img, "RGBA")
    for _ in range(n):
        y = rnd.uniform(y0, y1); x = rnd.uniform(0, img.size[0]); s = 0.5 + (y - HZ) / (img.size[1] - HZ) * 1.6
        for k in range(rnd.randint(5, 9)):
            a = rnd.uniform(-0.6, 0.6); hh = rnd.uniform(0.4, 1.0) * hmax * s; c = rnd.choice(cols)
            d.line([(x + k * 3 * s, y), (x + k * 3 * s + math.sin(a) * hh, y - math.cos(a) * hh)], fill=c + (255,), width=max(2, int(3 * s)))

def rock(d, x, y, s, col, rnd):
    pts = [(x + s * math.cos(a) * rnd.uniform(0.8, 1.15), y - abs(s * 0.7 * math.sin(a)) * rnd.uniform(0.8, 1.2)) for a in np.linspace(0, math.pi, 9)]
    d.polygon(pts, fill=col + (255,)); d.polygon(pts[4:] + [(x, y)], fill=mix(col, (0, 0, 0), 0.22) + (255,))
    d.ellipse((x - s * 1.1, y - s * 0.12, x + s * 1.1, y + s * 0.18), fill=(0, 0, 0, 50))

def _clump(d, cx, cy, r, col, rnd, n=7):
    """foliage clump in three tones: dark underside, mid body, lit top"""
    dk, li = mix(col, (0, 0, 0), 0.28), mix(col, (255, 240, 200), 0.16)
    for k in range(n):
        x = cx + rnd.uniform(-r, r) * 0.8; y = cy + rnd.uniform(-r, r) * 0.4; rr = r * rnd.uniform(0.45, 0.7)
        d.ellipse((x - rr, y - rr * 0.75 + rr * 0.25, x + rr, y + rr * 0.75 + rr * 0.25), fill=dk + (255,))
    for k in range(n):
        x = cx + rnd.uniform(-r, r) * 0.75; y = cy + rnd.uniform(-r, r) * 0.35 - r * 0.12; rr = r * rnd.uniform(0.42, 0.62)
        d.ellipse((x - rr, y - rr * 0.75, x + rr, y + rr * 0.75), fill=col + (255,))
    for k in range(max(3, n // 2)):
        x = cx + rnd.uniform(-r, r) * 0.55 - r * 0.15; y = cy - r * 0.35 + rnd.uniform(-r, r) * 0.2; rr = r * rnd.uniform(0.28, 0.4)
        d.ellipse((x - rr, y - rr * 0.7, x + rr, y + rr * 0.7), fill=li + (255,))

def tree_sil(d, x, y, s, col, rnd, kind="broad"):
    """v18: trunks with branches, layered foliage clumps (dark/mid/lit)"""
    tr = mix(col, (40, 30, 20), 0.35)
    if kind == "broad":
        d.polygon([(x - 16 * s, y), (x - 8 * s, y - 250 * s), (x + 8 * s, y - 250 * s), (x + 16 * s, y)], fill=tr + (255,))
        tips = []
        for k in range(4):
            a = -math.pi / 2 + (k - 1.5) * 0.45 + rnd.uniform(-0.15, 0.15); yy = y - rnd.uniform(150, 230) * s; ln = rnd.uniform(70, 130) * s
            tip = (x + ln * math.cos(a), yy + ln * math.sin(a)); tips.append(tip)
            d.line([(x, yy), tip], fill=tr + (255,), width=max(3, int(9 * s)))
        tips.append((x, y - 300 * s))
        for tx, ty in sorted(tips, key=lambda p: p[1], reverse=True): _clump(d, tx, ty - 20 * s, rnd.uniform(70, 100) * s, col, rnd)
    elif kind == "conifer":
        d.polygon([(x - 10 * s, y), (x - 5 * s, y - 120 * s), (x + 5 * s, y - 120 * s), (x + 10 * s, y)], fill=tr + (255,))
        dk = mix(col, (0, 0, 0), 0.25)
        for k in range(9):
            yy = y - 60 * s - k * 40 * s; ww = (130 - k * 13) * s
            d.polygon([(x - ww, yy), (x, yy - 70 * s), (x + ww, yy)], fill=dk + (255,))
            d.polygon([(x - ww * 0.85, yy - 6 * s), (x, yy - 70 * s), (x + ww * 0.25, yy - 8 * s)], fill=mix(col, (255, 255, 255), 0.03 * k) + (255,))
    elif kind == "acacia":
        d.polygon([(x - 10 * s, y), (x - 6 * s, y - 180 * s), (x + 6 * s, y - 180 * s), (x + 10 * s, y)], fill=tr + (255,))
        for sgn, ln in ((-1, 1.0), (1, 0.9), (-1, 0.55), (1, 0.45)):
            d.line([(x, y - 170 * s), (x + sgn * 110 * s * ln, y - (280 + 20 * ln) * s)], fill=tr + (255,), width=max(3, int(10 * s * ln)))
        dk, li = mix(col, (0, 0, 0), 0.3), mix(col, (255, 230, 180), 0.14)
        d.ellipse((x - 235 * s, y - 330 * s, x + 235 * s, y - 268 * s), fill=dk + (255,))           # shaded underside
        for k in range(7):
            cx = x + (k - 3) * 62 * s + rnd.uniform(-15, 15) * s; r = rnd.uniform(48, 70) * s
            d.ellipse((cx - r, y - 345 * s - r * 0.35, cx + r, y - 300 * s + r * 0.15), fill=col + (255,))
        for k in range(5):
            cx = x + (k - 2.4) * 66 * s + rnd.uniform(-10, 10) * s; r = rnd.uniform(30, 44) * s
            d.ellipse((cx - r, y - 360 * s - r * 0.3, cx + r, y - 335 * s + r * 0.05), fill=li + (255,))
    elif kind == "dead":
        d.polygon([(x - 14 * s, y), (x - 7 * s, y - 280 * s), (x + 7 * s, y - 280 * s), (x + 14 * s, y)], fill=tr + (255,))
        for k in range(5):
            a = -math.pi / 2 + rnd.uniform(-0.9, 0.9); yy = y - rnd.uniform(140, 260) * s; ln = rnd.uniform(60, 130) * s
            d.line([(x, yy), (x + ln * math.cos(a), yy + ln * math.sin(a))], fill=tr + (255,), width=max(3, int(8 * s)))
    elif kind == "palm":
        top = (x + 30 * s, y - 300 * s)
        d.line([(x, y), (x + 12 * s, y - 150 * s), top], fill=tr + (255,), width=max(4, int(16 * s)), joint="curve")
        dk = mix(col, (0, 0, 0), 0.25)
        for k in range(8):
            a = -math.pi / 2 + (k - 3.5) * 0.42; pts = [(top[0] + 170 * s * u * math.cos(a), top[1] + 170 * s * u * math.sin(a) + 80 * s * u * u) for u in np.linspace(0, 1, 8)]
            d.line(pts, fill=(dk if k % 2 else col) + (255,), width=int(16 * s))

def rays(img, x, a=60, n=6, col=(255, 248, 210)):
    w, h = img.size; L = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(L); rnd = random.Random(5)
    for k in range(n):
        x0 = x + rnd.uniform(-500, 500); ww = rnd.uniform(60, 160)
        d.polygon([(x0, 300), (x0 + ww, 300), (x0 + ww + 700, h), (x0 + 500, h)], fill=col + (a,))
    img.alpha_composite(pblur(L, 30))

def vignette(img, a=90):
    w, h = img.size; yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    v = ((xx / w - 0.5) ** 2 * 1.2 + (yy / h - 0.62) ** 2 * 2.2); v = np.clip((v - 0.12) * 2.2, 0, 1) * a
    L = Image.new("RGBA", (w, h), (0, 0, 0, 255)); L.putalpha(Image.fromarray(v.astype(np.uint8))); img.alpha_composite(L)

# ------------------------------------------------------------------ scenes
def build(name, w, h):
    rnd = random.Random(hash(name) % 1000)
    if name == "jungle":
        img = vgrad(w, h, [(0, (150, 196, 200)), (0.45, (206, 224, 200)), (HZ / h, (170, 196, 150)), (1, (60, 70, 40))])
        for k, (base, col, bl) in enumerate(((HZ - 120, (120, 156, 128), 6), (HZ - 60, (88, 124, 92), 3), (HZ, (60, 92, 62), 0))):
            r2 = random.Random(k * 7 + 1); dd = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(dd)
            for _ in range(22 - k * 5): tree_sil(d, r2.uniform(-100, w + 100), base + 40, r2.uniform(0.9, 1.5) - k * 0.1, col, r2, r2.choice(("broad", "broad", "palm")))
            if bl: dd = pblur(dd, bl)
            img.alpha_composite(dd); haze(img, base - 400, base + 60, (210, 228, 206), 70 - k * 20)
        ground(img, (88, 104, 56), (52, 64, 34), 11, (30, 40, 20), 50)
        rays(img, w * 0.5, 45)
        grass_tufts(img, rnd, 260, HZ + 20, h, [(70, 110, 52), (92, 132, 62), (58, 92, 44)], 70)
        d = ImageDraw.Draw(img, "RGBA")
        for _ in range(16): rock(d, rnd.uniform(0, w), rnd.uniform(HZ + 60, h), rnd.uniform(18, 50), (96, 96, 82), rnd)
    elif name == "tundra":
        img = vgrad(w, h, [(0, (170, 190, 210)), (0.5, (220, 228, 234)), (HZ / h, (236, 240, 244)), (1, (190, 200, 212))])
        clouds(img, rnd, 10, 200, 700, (246, 248, 252), 130, 1.6)
        layer(img, ridge(w, HZ - 260, 260, 3, 1.6), None, 4, 255, ((236, 240, 248), (170, 184, 204), HZ - 520, HZ))
        layer(img, ridge(w, HZ - 120, 120, 4, 1.2), None, 2, 255, ((222, 228, 238), (150, 164, 184), HZ - 260, HZ))
        haze(img, HZ - 200, HZ + 40, (236, 240, 246), 110)
        d = ImageDraw.Draw(img, "RGBA")
        for _ in range(14): tree_sil(d, rnd.uniform(0, w), HZ + 10, rnd.uniform(0.35, 0.55), (96, 108, 112), rnd, "conifer")
        ground(img, (230, 234, 240), (196, 204, 216), 21, (150, 160, 178), 50, 0.12)
        grass_tufts(img, rnd, 140, HZ + 20, h, [(170, 156, 110), (150, 136, 96)], 46)
        d = ImageDraw.Draw(img, "RGBA")
        for _ in range(12): rock(d, rnd.uniform(0, w), rnd.uniform(HZ + 60, h), rnd.uniform(20, 60), (120, 126, 136), rnd)
    elif name == "canyon":
        img = vgrad(w, h, [(0, (120, 170, 220)), (0.5, (236, 214, 176)), (HZ / h, (240, 200, 150)), (1, (160, 96, 60))])
        for k, (base, top, bot) in enumerate(((HZ - 330, (226, 160, 120), (196, 126, 92)), (HZ - 180, (206, 120, 80), (166, 90, 60)))):
            r2 = random.Random(k + 40); pts = [(-50, HZ)]
            x = -50
            while x < w + 50:   # flat-topped mesas
                ww = r2.uniform(200, 520); hh = base + r2.uniform(-80, 120)
                pts += [(x + 40, hh), (x + ww - 40, hh), (x + ww, HZ - r2.uniform(20, 80))]; x += ww + r2.uniform(0, 160)
            pts.append((w + 50, HZ)); layer(img, pts, None, 3 - k, 255, (top, bot, base - 100, HZ))
            st = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(st)
            for yy in range(int(base) - 140, HZ, 24): d.line([(0, yy), (w, yy + 4)], fill=mix(bot, (255, 255, 255), 0.15) + (70,), width=6)   # rock strata, clipped to the mesas
            m = Image.new("L", (w, h), 0); ImageDraw.Draw(m).polygon(pts, fill=255); st.putalpha(ImageChopsMul(st.getchannel("A"), m)); img.alpha_composite(st)
            haze(img, base - 100, HZ, (246, 214, 176), 70 - k * 30)
        ground(img, (214, 150, 98), (150, 90, 56), 31, (110, 60, 40), 60)
        d = ImageDraw.Draw(img, "RGBA")
        for _ in range(40):   # cracks
            x, y = rnd.uniform(0, w), rnd.uniform(HZ + 60, h); pts = [(x, y)]
            for _ in range(5): x += rnd.uniform(-40, 40); y += rnd.uniform(-8, 14); pts.append((x, y))
            d.line(pts, fill=(110, 64, 40, 120), width=3)
        for _ in range(22): rock(d, rnd.uniform(0, w), rnd.uniform(HZ + 40, h), rnd.uniform(16, 70), (170, 104, 70), rnd)
        grass_tufts(img, rnd, 60, HZ + 20, h, [(150, 140, 80), (120, 110, 60)], 40)
    elif name == "swamp":
        img = vgrad(w, h, [(0, (120, 140, 120)), (0.5, (180, 196, 170)), (HZ / h, (150, 168, 140)), (1, (50, 62, 44))])
        d0 = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(d0)
        for _ in range(26): tree_sil(d, rnd.uniform(0, w), HZ + 20, rnd.uniform(0.7, 1.3), (70, 84, 66), rnd, rnd.choice(("dead", "broad")))
        img.alpha_composite(pblur(d0, 3)); haze(img, HZ - 380, HZ + 80, (196, 210, 186), 120)
        ground(img, (86, 98, 58), (46, 56, 34), 41, (30, 36, 20), 60)
        d = ImageDraw.Draw(img, "RGBA")
        for _ in range(9):   # murky pools
            x, y = rnd.uniform(0, w), rnd.uniform(HZ + 50, h - 100); rx, ry = rnd.uniform(140, 380), rnd.uniform(18, 60) * (1 + (y - HZ) / 600)
            d.ellipse((x - rx, y - ry, x + rx, y + ry), fill=(70, 92, 84, 230)); d.ellipse((x - rx * 0.8, y - ry * 0.7, x + rx * 0.5, y - ry * 0.2), fill=(150, 176, 160, 70))
        grass_tufts(img, rnd, 300, HZ + 10, h, [(96, 110, 50), (120, 130, 60), (74, 90, 40)], 90)
        haze(img, HZ - 40, HZ + 260, (190, 206, 180), 60)
    elif name == "beach":
        img = vgrad(w, h, [(0, (90, 160, 222)), (0.45, (180, 216, 236)), (0.53, (226, 236, 236)), (1, (196, 170, 120))])
        clouds(img, rnd, 8, 250, 650, (255, 255, 255), 170, 1.3)
        layer(img, [q for q in ridge(w, HZ - 170, 150, 8, 1.4) if q[0] < w / 3] + [(w // 3, HZ), (-20, HZ)], None, 3, 255, ((140, 150, 130), (100, 110, 90), HZ - 330, HZ))
        sea = vgrad(w, 150, [(0, (60, 130, 170)), (1, (110, 180, 196))]); img.alpha_composite(sea, (0, HZ - 60))
        d = ImageDraw.Draw(img, "RGBA")
        for k in range(30): y = HZ - 50 + k * 5; x = rnd.uniform(0, w); d.line([(x, y), (x + rnd.uniform(80, 260), y)], fill=(230, 246, 250, 120), width=2)
        sand = Image.new("RGBA", (w, h), (0, 0, 0, 0)); ground(sand, (226, 206, 160), (190, 160, 110), 51, (150, 120, 80), 50, 0.15)
        m = Image.new("L", (w, h), 0); ImageDraw.Draw(m).polygon([(0, h)] + [(x, HZ + 70 + 18 * math.sin(x / 140)) for x in range(0, w + 20, 20)] + [(w, h)], fill=255)
        sand.putalpha(ImageChopsMul(sand.getchannel("A"), m)); img.alpha_composite(sand)
        d = ImageDraw.Draw(img, "RGBA"); d.line([(x, HZ + 72 + 18 * math.sin(x / 140)) for x in range(0, w + 20, 20)], fill=(250, 252, 250, 220), width=10)
        for _ in range(6): tree_sil(d, rnd.uniform(w * 0.55, w), HZ + 90, rnd.uniform(0.9, 1.2), (60, 96, 60), rnd, "palm")
        for _ in range(10): rock(d, rnd.uniform(0, w), rnd.uniform(HZ + 120, h), rnd.uniform(20, 60), (130, 120, 110), rnd)
    elif name == "savanna":
        img = vgrad(w, h, [(0, (90, 120, 180)), (0.35, (240, 170, 110)), (0.52, (255, 214, 150)), (HZ / h, (230, 196, 130)), (1, (150, 110, 50))])
        d = ImageDraw.Draw(img, "RGBA"); d.ellipse((w * 0.62 - 90, HZ - 260, w * 0.62 + 90, HZ - 80), fill=(255, 240, 200, 255))
        L = Image.new("RGBA", (w, h), (0, 0, 0, 0)); ImageDraw.Draw(L).ellipse((w * 0.62 - 400, HZ - 560, w * 0.62 + 400, HZ + 220), fill=(255, 220, 160, 110)); img.alpha_composite(pblur(L, 80))
        clouds(img, rnd, 6, 300, 600, (250, 190, 150), 110, 1.5)
        layer(img, ridge(w, HZ - 70, 60, 61, 0.6), None, 4, 255, ((170, 120, 110), (150, 110, 90), HZ - 140, HZ))
        haze(img, HZ - 160, HZ + 30, (255, 210, 160), 90)
        d = ImageDraw.Draw(img, "RGBA")
        for _ in range(7): tree_sil(d, rnd.uniform(0, w), HZ + 30, rnd.uniform(0.6, 1.0), (70, 60, 40), rnd, "acacia")
        ground(img, (214, 170, 90), (150, 100, 40), 61, (120, 80, 30), 50)
        grass_tufts(img, rnd, 420, HZ + 10, h, [(220, 186, 110), (196, 160, 80), (170, 130, 60)], 80)
    elif name == "storm":
        img = vgrad(w, h, [(0, (50, 56, 70)), (0.45, (100, 106, 116)), (HZ / h, (130, 132, 130)), (1, (60, 66, 50))])
        clouds(img, rnd, 22, 80, 800, (70, 74, 88), 200, 2.2)
        layer(img, ridge(w, HZ - 140, 120, 71, 1.3), None, 3, 255, ((88, 96, 104), (70, 78, 80), HZ - 280, HZ))
        haze(img, HZ - 200, HZ + 40, (130, 136, 140), 90)
        d = ImageDraw.Draw(img, "RGBA")
        for _ in range(10): tree_sil(d, rnd.uniform(0, w), HZ + 20, rnd.uniform(0.6, 0.9), (50, 60, 50), rnd, "broad")
        ground(img, (90, 100, 64), (50, 56, 36), 71, (30, 30, 20), 60)
        grass_tufts(img, rnd, 260, HZ + 10, h, [(80, 96, 56), (100, 112, 64)], 70)
    elif name == "snowforest":
        img = vgrad(w, h, [(0, (120, 140, 170)), (0.5, (200, 210, 224)), (HZ / h, (226, 232, 240)), (1, (180, 190, 206))])
        for k, (col, bl, sc) in enumerate((((150, 166, 180), 5, 0.7), ((110, 128, 140), 2, 0.95), ((70, 90, 96), 0, 1.25))):
            dd = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(dd); r2 = random.Random(80 + k)
            for _ in range(26 - k * 6):
                x = r2.uniform(-80, w + 80); s = sc * r2.uniform(0.8, 1.2); tree_sil(d, x, HZ + 30 + k * 20, s, col, r2, "conifer")
                for j in range(5): yy = HZ + 30 + k * 20 - 80 * s - j * 70 * s; ww = (110 - j * 18) * s; d.polygon([(x - ww * 0.8, yy - 6), (x, yy - 40 * s), (x + ww * 0.8, yy - 6)], fill=(240, 244, 250, 230))
            if bl: dd = pblur(dd, bl)
            img.alpha_composite(dd); haze(img, HZ - 300, HZ + 60, (226, 232, 242), 70 - k * 20)
        ground(img, (238, 242, 248), (200, 208, 222), 81, (160, 170, 190), 40, 0.1)
    elif name in UNDER:
        top, mid, bot, floor = {"reef": ((120, 210, 220), (40, 150, 180), (20, 90, 130), (210, 196, 150)),
                                "kelp": ((110, 180, 160), (40, 120, 120), (16, 70, 80), (120, 120, 90)),
                                "deep": ((40, 100, 150), (14, 50, 96), (6, 22, 50), (60, 70, 80)),
                                "abyss": ((10, 30, 60), (4, 12, 30), (1, 3, 10), (24, 26, 32))}[name]
        img = vgrad(w, h, [(0, top), (0.45, mid), (1, bot)])
        if name in ("reef", "kelp", "deep"): rays(img, w * 0.5, {"reef": 55, "kelp": 45, "deep": 28}[name], 8, (210, 240, 250))
        # far seafloor ridges in haze
        layer(img, ridge(w, 1300, 120, 91, 1.2) + [(w + 20, h), (-20, h)], None, 6, 255, (mix(mid, floor, 0.25), mix(bot, floor, 0.25), 1150, 1450))
        if name == "reef":
            d = ImageDraw.Draw(img, "RGBA")
            for _ in range(26):   # coral heads + fans
                x = rnd.uniform(0, w); y = rnd.uniform(1350, 1460); c = rnd.choice([(230, 120, 110), (240, 170, 90), (180, 110, 180), (240, 210, 120), (110, 170, 150)])
                if rnd.random() < 0.5:
                    for k in range(14): a = -math.pi / 2 + rnd.uniform(-1.0, 1.0); ln = rnd.uniform(30, 110); d.line([(x, y), (x + ln * math.cos(a), y + ln * math.sin(a))], fill=c + (255,), width=rnd.randint(6, 12))
                else:
                    r = rnd.uniform(40, 90); d.ellipse((x - r, y - r * 0.7, x + r, y + r * 0.4), fill=c + (255,)); d.ellipse((x - r * 0.6, y - r * 0.6, x + r * 0.3, y - r * 0.1), fill=mix(c, (255, 255, 255), 0.25) + (255,))
        if name == "kelp":
            dd = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(dd)
            for k in range(30):
                x0 = rnd.uniform(0, w); far = k < 18; c = (40, 90, 60) if far else (70, 130, 60); hh = rnd.uniform(900, 1400)
                pts = [(x0 + 40 * math.sin(v * 6 + k), 1480 - v * hh) for v in np.linspace(0, 1, 30)]
                d.line(pts, fill=c + (200 if far else 255,), width=int(rnd.uniform(10, 18)))
                for j in range(4, 30, 3): px, py = pts[j]; sg = 1 if j % 2 else -1; d.ellipse((min(px, px + sg * 80), py - 18, max(px, px + sg * 80), py + 14), fill=c + (200 if far else 255,))
            img.alpha_composite(pblur(dd, 2))
        # sea floor
        fl = vgrad(w, h - 1400, [(0, mix(floor, mid, 0.3)), (1, mix(floor, bot, 0.5))]); img.alpha_composite(fl, (0, 1400))
        d = ImageDraw.Draw(img, "RGBA")
        for _ in range(30): rock(d, rnd.uniform(0, w), rnd.uniform(1410, h), rnd.uniform(20, 70), mix(floor, (60, 60, 60), 0.4), rnd)
        if name == "abyss":
            for _ in range(120): x, y = rnd.uniform(0, w), rnd.uniform(0, h); r = rnd.uniform(1.5, 4); d.ellipse((x - r, y - r, x + r, y + r), fill=(120, 230, 255, int(rnd.uniform(60, 180))))
        return img
    elif name == "ocean":
        img = vgrad(w, h, [(0, (80, 150, 214)), (0.42, (180, 214, 236)), (WL / h, (214, 230, 238)), (WL / h + 0.001, (40, 120, 160)), (1, (10, 50, 90))])
        clouds(img, rnd, 10, 200, 650, (255, 255, 255), 170, 1.5)
        d = ImageDraw.Draw(img, "RGBA")
        for k in range(60): y = WL + 3 + k * 2; x = rnd.uniform(0, w); d.line([(x, y), (x + rnd.uniform(60, 240), y)], fill=(220, 240, 250, 70), width=2)
        return img
    else:
        raise KeyError(name)
    vignette(img, 70)
    return img

def ImageChopsMul(a, b):
    from PIL import ImageChops
    return ImageChops.multiply(a, b)

# ------------------------------------------------------------------ animated overlays (weather)
def caustics(W, H, t, a):
    """moving light net from the water surface (cheap: two drifting noise fields)"""
    w2, h2 = W // 6, H // 6
    xs = np.linspace(0, 1, w2)[None, :]; ys = np.linspace(0, 1, h2)[:, None]
    v = np.sin(xs * 40 + t * 1.3 + np.sin(ys * 23 + t) * 2) + np.sin(ys * 36 - t * 1.1 + np.sin(xs * 19 - t * 0.7) * 2)
    v = np.clip((np.abs(v) < 0.22) * 1.0 * (1 - ys * 1.3), 0, 1) * a
    im = Image.fromarray(v.astype(np.uint8)).resize((W, H), Image.BICUBIC).filter(ImageFilter.GaussianBlur(3))
    L = Image.new("RGBA", (W, H), (230, 250, 255, 255)); L.putalpha(im); return L

def weather(img, name, t, W, H):
    d = ImageDraw.Draw(img, "RGBA"); rnd = random.Random(int(t * 30))
    if name in UNDER:
        tint = {"reef": (20, 120, 160, 46), "kelp": (20, 100, 90, 52), "deep": (8, 40, 90, 80), "abyss": (2, 8, 24, 95)}[name]
        img.alpha_composite(Image.new("RGBA", img.size, tint))   # water absorbs colour -> everything gets bluer
        if name in ("reef", "kelp"): img.alpha_composite(caustics(W, H, t, 38 if name == "reef" else 26))
        r2 = random.Random(5); d = ImageDraw.Draw(img, "RGBA")
        for k in range(160):   # marine snow / particles drifting
            x = (r2.uniform(0, W) + 12 * math.sin(t * 0.6 + k)) % W; y = (r2.uniform(0, H) - t * r2.uniform(5, 25)) % H; s = r2.uniform(1, 3.5)
            d.ellipse((x - s, y - s, x + s, y + s), fill=(220, 240, 250, 90 if name != "abyss" else 40))
        for k in range(26):   # rising bubble columns
            x0 = r2.uniform(0, W); sp = r2.uniform(80, 200); y = (r2.uniform(0, H) - t * sp) % H; x = x0 + 8 * math.sin(t * 3 + k); s = r2.uniform(4, 10)
            d.ellipse((x - s, y - s, x + s, y + s), outline=(230, 250, 255, 170), width=2)
        if name in ("deep", "abyss"): vignette(img, 120 if name == "abyss" else 70)
        return
    if name == "ocean":   # front water: lower halves of the fighters sit under a translucent surface
        L = Image.new("RGBA", img.size, (0, 0, 0, 0)); d2 = ImageDraw.Draw(L)
        wave = [(x, WL + 10 * math.sin(x / 90 + t * 2.2) + 6 * math.sin(x / 37 - t * 3)) for x in range(-20, W + 40, 20)]
        d2.polygon(wave + [(W + 40, H), (-20, H)], fill=(30, 110, 150, 150)); img.alpha_composite(L)
        d = ImageDraw.Draw(img, "RGBA"); d.line(wave, fill=(240, 250, 255, 230), width=7)
        r2 = random.Random(3)
        for k in range(40): x = (r2.uniform(0, W) + t * 30) % W; y = WL + r2.uniform(10, 400); d.line([(x, y), (x + r2.uniform(40, 120), y)], fill=(200, 236, 250, 60), width=3)
        return
    if name in ("tundra", "snowforest"):
        r2 = random.Random(4)
        for k in range(220):
            x0, y0, sp = r2.uniform(0, W), r2.uniform(0, H), r2.uniform(60, 160); s = r2.uniform(2, 6)
            x = (x0 + 40 * math.sin(t * 1.3 + k) + t * 40) % W; y = (y0 + t * sp) % H
            d.ellipse((x - s, y - s, x + s, y + s), fill=(255, 255, 255, 210))
    elif name == "storm":
        for _ in range(300):
            x, y = rnd.uniform(-100, W), rnd.uniform(0, H); d.line([(x, y), (x + 18, y + 52)], fill=(200, 210, 224, 150), width=2)
        if (t % 6.0) < 0.1 or 3.0 < (t % 6.0) < 3.06: img.alpha_composite(Image.new("RGBA", img.size, (255, 255, 255, 110)))
    elif name == "swamp":
        r2 = random.Random(9)
        for k in range(40):   # drifting insects / spores
            x = (r2.uniform(0, W) + t * r2.uniform(10, 30)) % W; y = r2.uniform(HZ - 300, HZ + 300) + 20 * math.sin(t * 2 + k)
            d.ellipse((x - 2, y - 2, x + 2, y + 2), fill=(230, 240, 200, 140))
    elif name == "savanna" or name == "canyon":
        r2 = random.Random(3)
        for k in range(30):   # dust motes in warm light
            x = (r2.uniform(0, W) + t * 50) % W; y = r2.uniform(HZ - 200, H) + 10 * math.sin(t + k)
            d.ellipse((x - 3, y - 3, x + 3, y + 3), fill=(255, 230, 180, 90))
