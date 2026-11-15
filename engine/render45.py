"""Lean stand-in for the channel's render45: land background + tag/pop helpers used by fight4."""
import os, math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1080, 1920
GROUND = 1100
DK = (16, 12, 10); YEL = (255, 214, 50); RED = (235, 45, 50); WHT = (255, 255, 255); GRN = (60, 200, 90)
FB = os.path.join(HERE, "fonts", "Kanit-ExtraBold.ttf")
def font(sz): return ImageFont.truetype(FB, sz)
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease(x): x = clamp(x); return 1 - (1 - x) ** 3
def lerp(a, b, t): return a + (b - a) * t
def pop_s(t, t0): g = clamp((t - t0) / 0.25); return 0 if g <= 0 else (1.25 - 0.25 * g if g < 1 else 1.0) * ease(g * 1.5)
def vgrad(w, h, stops):
    ys = np.linspace(0, 1, h); cols = np.zeros((h, 3))
    P_ = [s[0] for s in stops]
    for c in range(3): cols[:, c] = np.interp(ys, P_, [s[1][c] for s in stops])
    return Image.fromarray(np.repeat(cols[:, None, :], w, 1).astype(np.uint8), "RGB").convert("RGBA")
class _K: pass
K = _K(); K.vgrad = vgrad
def tag(img, x, y, txt, col=RED, sz=50, a=1.0):
    if a <= 0: return
    if a != 1.0:
        if int(sz * a) < 4: return
        L = Image.new("RGBA", img.size, (0, 0, 0, 0)); tag(L, x, y, txt, col, int(sz * a), 1.0); img.alpha_composite(L); return
    d = ImageDraw.Draw(img); f = font(sz); w = f.getlength(txt) + 50
    d.rounded_rectangle((x - w / 2, y - sz * 0.75, x + w / 2, y + sz * 0.75), 26, fill=col, outline=WHT, width=5)
    d.text((x, y), txt, font=f, fill=WHT, anchor="mm")
BGW = W + 600; BGC = {}
def cycad(d, x, y, s, rnd):
    """cycad/palm-fern: scaly trunk + arching feather leaves with leaflets"""
    th = 230 * s; tw = 26 * s
    d.polygon([(x - tw, y), (x - tw * 0.8, y - th), (x + tw * 0.8, y - th), (x + tw, y)], fill=(118, 92, 64), outline=DK)
    for k in range(int(th / (18 * s))):   # diamond scales on trunk
        yy = y - 10 * s - k * 18 * s; d.arc((x - tw * 0.9, yy - 9 * s, x + tw * 0.9, yy + 9 * s), 200, 340, fill=(84, 64, 46), width=max(2, int(3 * s)))
    top = (x, y - th)
    for j in range(9):
        a = -math.pi / 2 + (j - 4) * 0.36; L = (150 + rnd.uniform(-20, 30)) * s
        pts = [(top[0] + L * u * math.cos(a), top[1] + L * u * math.sin(a) + 90 * s * u * u) for u in [i / 10 for i in range(11)]]
        d.line(pts, fill=(58, 92, 50), width=max(3, int(5 * s)))
        for i in range(2, 10):
            px, py = pts[i]; qx, qy = pts[i + 1]; ang = math.atan2(qy - py, qx - px); ll = 34 * s * (1 - i / 12)
            for sgn in (-1, 1):
                b = ang + sgn * 1.0; d.line([(px, py), (px + ll * math.cos(b), py + ll * math.sin(b) + 6 * s)], fill=(74, 124, 62) if sgn < 0 else (90, 140, 72), width=max(3, int(7 * s)))
def frond(d, x, y, h, col):
    a = -math.pi / 2 + random.uniform(-0.5, 0.5)
    pts = [(x + h * u * math.cos(a) + 30 * u * u, y + h * u * math.sin(a)) for u in [i / 8 for i in range(9)]]
    d.line(pts, fill=shade_(col, 0.75), width=5)
    for i in range(1, 8):
        px, py = pts[i]; ll = 26 * (1 - i / 9) + 6
        for sgn in (-1, 1): d.line([(px, py), (px + sgn * ll, py - ll * 0.5)], fill=col, width=6)

def leafy(d, x, y, s, rnd, tones=((52, 92, 50), (74, 122, 62), (104, 152, 78))):
    """broadleaf tree: tapered trunk with bark lines + 2 branches + clustered foliage in 3 tones (outline only on the outside)"""
    th = 260 * s; bark, dbark = (110, 82, 58), (78, 58, 42)
    d.polygon([(x - 24 * s, y), (x - 12 * s, y - th), (x + 12 * s, y - th), (x + 24 * s, y)], fill=bark)
    for k in range(4): d.line([(x - 10 * s + k * 7 * s, y - 10 * s), (x - 6 * s + k * 5 * s, y - th * 0.9)], fill=dbark, width=max(2, int(3 * s)))
    for sgn in (-1, 1): d.line([(x, y - th * 0.6), (x + sgn * 70 * s, y - th * 0.95)], fill=bark, width=int(12 * s))
    cl = [(rnd.uniform(-130, 130) * s, -th - rnd.uniform(-60, 120) * s, rnd.uniform(60, 100) * s) for _ in range(14)]
    for (dx, dy, r) in cl: d.ellipse((x + dx - r - 6, y + dy - r - 6, x + dx + r + 6, y + dy + r + 6), fill=DK)
    for (dx, dy, r) in cl: d.ellipse((x + dx - r, y + dy - r, x + dx + r, y + dy + r), fill=tones[0])
    for (dx, dy, r) in cl: d.ellipse((x + dx - r * 0.8 - r * 0.15, y + dy - r * 0.8 - r * 0.2, x + dx + r * 0.8 - r * 0.15, y + dy + r * 0.8 - r * 0.2), fill=tones[1])
    for (dx, dy, r) in cl[:8]: d.ellipse((x + dx - r * 0.45 - r * 0.3, y + dy - r * 0.45 - r * 0.35, x + dx + r * 0.45 - r * 0.3, y + dy + r * 0.45 - r * 0.35), fill=tones[2])
def conifer(d, x, y, s, rnd, col=(50, 86, 56)):
    """araucaria-like conifer: tall trunk + tiers of drooping branch clumps"""
    th = 420 * s; d.polygon([(x - 14 * s, y), (x - 6 * s, y - th), (x + 6 * s, y - th), (x + 14 * s, y)], fill=(104, 78, 56))
    for k in range(7):
        yy = y - th * 0.35 - k * th * 0.1; ww = (150 - k * 17) * s
        for sgn in (-1, 1):
            pts = [(x, yy), (x + sgn * ww * 0.5, yy - 14 * s), (x + sgn * ww, yy + 18 * s), (x + sgn * ww * 0.6, yy + 30 * s), (x, yy + 16 * s)]
            d.polygon(pts, fill=DK); d.polygon([(px - sgn * 4, py - 3) for px, py in pts], fill=shade_(col, 1.0 + 0.04 * k))
            d.line([(x + sgn * ww * 0.15, yy + 6 * s), (x + sgn * ww * 0.85, yy + 16 * s)], fill=shade_(col, 1.3), width=max(2, int(4 * s)))
def shade_(c, k): return tuple(max(0, min(255, int(v * k))) for v in c)
def barn(d, x0, yb, w, h):
    red, dred, trim, roof = (156, 58, 46), (120, 42, 34), (236, 228, 214), (78, 72, 70)
    d.rectangle((x0, yb - h, x0 + w, yb), fill=red, outline=DK, width=7)
    for xx in range(int(x0 + 18), int(x0 + w), 22): d.line([(xx, yb - h + 6), (xx, yb - 4)], fill=dred, width=3)      # planks
    ap = (x0 + w / 2, yb - h - h * 0.55)
    d.polygon([(x0 - 26, yb - h + 6), ap, (x0 + w + 26, yb - h + 6)], fill=roof, outline=DK, width=7)
    for k in range(1, 6):   # shingle rows
        u = k / 6; d.line([(lerp(x0 - 26, ap[0], u), lerp(yb - h + 6, ap[1], u)), (lerp(x0 + w + 26, ap[0], u), lerp(yb - h + 6, ap[1], u))], fill=(98, 92, 88), width=4)
    d.polygon([(x0 + w * 0.2, yb - h), ap, (x0 + w * 0.8, yb - h)], fill=red, outline=DK, width=5)
    hx = x0 + w / 2; d.rectangle((hx - 28, yb - h - 70, hx + 28, yb - h - 20), fill=(60, 40, 34), outline=trim, width=6)   # hay window
    dx0, dx1, dy0 = x0 + w * 0.3, x0 + w * 0.7, yb - h * 0.62
    d.rectangle((dx0, dy0, dx1, yb), fill=dred, outline=trim, width=9)
    d.line([(dx0, dy0), (dx1, yb)], fill=trim, width=9); d.line([(dx1, dy0), (dx0, yb)], fill=trim, width=9); d.line([(hx, dy0), (hx, yb)], fill=trim, width=6)
    d.ellipse((x0 - 40, yb - 14, x0 + w + 40, yb + 22), fill=(80, 96, 56))   # ground shadow
def fence(d, w, y):
    wood, dw = (170, 132, 92), (126, 94, 64)
    for x in range(0, w + 90, 90):
        d.rectangle((x - 9, y - 70, x + 9, y + 34), fill=wood, outline=DK, width=4); d.polygon([(x - 9, y - 70), (x, y - 84), (x + 9, y - 70)], fill=wood, outline=DK)
    for yy in (y - 50, y - 12):
        d.rectangle((0, yy - 7, w, yy + 7), fill=wood, outline=DK, width=3); d.line([(0, yy + 3), (w, yy + 3)], fill=dw, width=3)
def build(name):
    w, h = BGW, H; rnd = random.Random(7)
    if name in ("land", "dusk", "dark", "fire"):
        sky = {"land": [(0, (120, 176, 230)), (0.4, (190, 218, 238)), (0.55, (226, 232, 222))],
               "dusk": [(0, (250, 170, 150)), (0.4, (255, 210, 170)), (0.55, (255, 230, 200))],
               "fire": [(0, (120, 40, 60)), (0.3, (230, 90, 60)), (0.55, (255, 170, 90))],
               "dark": [(0, (90, 90, 104)), (0.4, (130, 126, 130)), (0.55, (150, 144, 140))]}[name]
        img = K.vgrad(w, h, sky + [(0.56, (128, 146, 90)), (1, (96, 106, 66))] if name == "land" else sky + [(0.56, (150, 130, 110)), (1, (110, 96, 84))])
        L = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
        hill = {"land": (120, 150, 120), "dusk": (220, 170, 150), "fire": (120, 60, 60), "dark": (110, 110, 112)}[name]
        d.polygon([(0, GROUND - 40)] + [(x, GROUND - 160 - 90 * math.sin(x / 260) - 40 * math.sin(x / 90)) for x in range(0, w + 20, 20)] + [(w, GROUND - 40)], fill=hill + (255,))
        if name in ("land", "dusk"):
            img.alpha_composite(L); L = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
            for k in range(4): conifer(d, rnd.uniform(0, w), GROUND - 60, rnd.uniform(0.7, 1.0), rnd, (70, 104, 74))   # far, lighter
            for k in range(5): cycad(d, rnd.uniform(0, w), GROUND - 20, rnd.uniform(0.7, 1.1), rnd)
            for k in range(2): leafy(d, rnd.uniform(0, w), GROUND - 10, rnd.uniform(0.8, 1.0), rnd)
            random.seed(5)
            for k in range(26): frond(d, rnd.uniform(0, w), GROUND + 30, rnd.uniform(70, 140), (84, 134, 70))
        if name == "dark":
            for k in range(6):
                x = rnd.uniform(0, w); y = GROUND - 20; d.line([(x, y), (x + 20, y - 180)], fill=(90, 80, 70, 255), width=12)
                for j in range(4): d.line([(x + 20, y - 180), (x + 20 + (j - 1.5) * 60, y - 120 + 40 * j % 30)], fill=(120, 110, 90, 255), width=8)
        img.alpha_composite(L); return img
    if name == "space":
        img = K.vgrad(w, h, [(0, (40, 30, 80)), (1, (90, 60, 130))]); d = ImageDraw.Draw(img)
        for k in range(160): x, y = rnd.uniform(0, w), rnd.uniform(0, h); r = rnd.uniform(1, 3.5); d.ellipse((x - r, y - r, x + r, y + r), fill=(255, 250, 230))
        return img
    if name == "river":
        img = K.vgrad(w, h, [(0, (150, 226, 214)), (0.6, (100, 180, 190)), (1, (90, 140, 140))])
        L = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
        for k in range(8): x = 80 + k * 230; d.polygon([(x, 0), (x + 70, 0), (x + 320, h), (x + 170, h)], fill=(255, 255, 240, 34))
        d.polygon([(0, h)] + [(x, 1320 + 40 * math.sin(x / 210)) for x in range(0, w + 20, 20)] + [(w, h)], fill=(150, 130, 100, 255))
        img.alpha_composite(L); return img
    if name == "farm":
        img = K.vgrad(w, h, [(0, (120, 176, 230)), (0.5, (214, 226, 230)), (0.56, (128, 150, 90)), (1, (100, 116, 70))]); d = ImageDraw.Draw(img)
        rnd2 = random.Random(4)
        for k, x in enumerate((90, 420, 1180, 1500)): leafy(d, x, GROUND - 40, 0.85 if k % 2 else 1.0, rnd2)
        barn(d, 690, GROUND - 30, 360, 300)
        fence(d, w, GROUND - 10)
        random.seed(9)
        for k in range(60): x = random.uniform(0, w); y = random.uniform(GROUND + 30, GROUND + 260); d.line([(x, y), (x - 6, y - 26)], fill=(96, 120, 62), width=4); d.line([(x, y), (x + 8, y - 22)], fill=(110, 136, 70), width=4)
        return img
    if name == "city":
        img = K.vgrad(w, h, [(0, (170, 214, 252)), (0.55, (255, 230, 220)), (0.56, (190, 190, 200)), (1, (150, 150, 160))]); d = ImageDraw.Draw(img)
        for k in range(12):
            x = k * 140 + rnd.uniform(-20, 20); bh = rnd.uniform(250, 600); c = rnd.choice([(200, 210, 240), (240, 214, 200), (210, 230, 210)])
            d.rectangle((x, GROUND - 40 - bh, x + 120, GROUND - 40), fill=c, outline=DK, width=5)
            for r in range(int(bh // 70)):
                for cc in range(2): d.rectangle((x + 20 + cc * 50, GROUND - 40 - bh + 20 + r * 70, x + 50 + cc * 50, GROUND - 40 - bh + 55 + r * 70), fill=(255, 250, 200))
        return img
def bg(name, pan=0.0):
    if name not in BGC: BGC[name] = build(name)
    x = int(pan % 600); return BGC[name].crop((x, 0, x + W, H))
