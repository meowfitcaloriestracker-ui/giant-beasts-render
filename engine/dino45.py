"""dino45: jointed cartoon dinosaurs — every piece is a connected bone segment with a real joint.
spine chain (head-neck-torso-tail) with travelling waves, legs solved with 2-bone IK (hip-knee-ankle) + metatarsus + toes,
arms 3 segments, hinged jaw. Bold outline, pastel-cartoon colours, far limbs darker.
beast(kind, t, gait="walk"|"idle"|"graze"|"run"|"roar", mouth=0..1) -> RGBA 1600x1000, feet on y=GROUND."""
import math
from PIL import Image, ImageDraw, ImageFilter, ImageChops, ImageOps
def dilate(m, r):
    """fast round-ish dilation of an L mask by ~r px (two box passes + threshold, soft edge)"""
    return m.filter(ImageFilter.BoxBlur(max(1, r * 0.6))).filter(ImageFilter.BoxBlur(max(1, r * 0.6))).point(lambda v: min(255, v * 14))
def erode(m, r): return ImageOps.invert(dilate(ImageOps.invert(m), r))
DK = (34, 26, 22); W0, H0 = 1600, 1000; GROUND = 900; S = 2
FLAT = False
HIRES = False   # return the 2x canvas (for big close-up covers)   # flat-vector look like the user's reference: no inner outlines, no gradient shading

def lerp(a, b, u): return a + (b - a) * u
def rot(v, a): c, s = math.cos(a), math.sin(a); return (v[0] * c - v[1] * s, v[0] * s + v[1] * c)
def add(p, v): return (p[0] + v[0], p[1] + v[1])
def taper(p1, p2, r1, r2, n=10):
    """hull of two circles (a tapered bone/capsule)"""
    dx, dy = p2[0] - p1[0], p2[1] - p1[1]; a = math.atan2(dy, dx); pts = []
    for k in range(n + 1): b = a + math.pi / 2 + math.pi * k / n; pts.append((p1[0] + r1 * math.cos(b), p1[1] + r1 * math.sin(b)))
    for k in range(n + 1): b = a - math.pi / 2 + math.pi * k / n; pts.append((p2[0] + r2 * math.cos(b), p2[1] + r2 * math.sin(b)))
    return pts
def ik(hip, target, l1, l2, bend=1):
    """2-bone IK: returns knee point. bend=+1 knee forward (to +x), -1 backward"""
    dx, dy = target[0] - hip[0], target[1] - hip[1]; d = min(math.hypot(dx, dy), l1 + l2 - 1e-3); d = max(d, abs(l1 - l2) + 1e-3)
    a = math.atan2(dy, dx); c = (l1 * l1 + d * d - l2 * l2) / (2 * l1 * d); c = max(-1, min(1, c)); b = math.acos(c)
    ang = a - b * bend
    return (hip[0] + l1 * math.cos(ang), hip[1] + l1 * math.sin(ang))
def smooth(pts, th, k=4):
    out, ot = [], []
    n = len(pts)
    for i in range(n - 1):
        p0 = pts[max(0, i - 1)]; p1 = pts[i]; p2 = pts[i + 1]; p3 = pts[min(n - 1, i + 2)]
        for j in range(k):
            u = j / k; u2, u3 = u * u, u * u * u
            f = lambda a, b, c, d: 0.5 * (2 * b + (-a + c) * u + (2 * a - 5 * b + 4 * c - d) * u2 + (-a + 3 * b - 3 * c + d) * u3)
            out.append((f(p0[0], p1[0], p2[0], p3[0]), f(p0[1], p1[1], p2[1], p3[1])))
            ot.append((lerp(th[i][0], th[i + 1][0], u), lerp(th[i][1], th[i + 1][1], u)))
    out.append(pts[-1]); ot.append(th[-1]); return out, ot
def chaikin(poly, it=2):
    for _ in range(it):
        n = len(poly); out = []
        for i in range(n):
            p, q = poly[i], poly[(i + 1) % n]
            out += [(0.75 * p[0] + 0.25 * q[0], 0.75 * p[1] + 0.25 * q[1]), (0.25 * p[0] + 0.75 * q[0], 0.25 * p[1] + 0.75 * q[1])]
        poly = out
    return poly
def shade(c, k): return tuple(max(0, min(255, int(v * k))) for v in c)

class Canvas:
    def __init__(s): s.im = Image.new("RGBA", (W0 * S, H0 * S), (0, 0, 0, 0))
    def piece(s, polys, fill, edge=True, dark=0.82, lw=5, smooth=2):
        """draw a connected piece (union of polygons) with bottom shading + its own outline"""
        pts = [p for poly in polys for p in poly]
        x0 = int(min(p[0] for p in pts) * S) - 20; y0 = int(min(p[1] for p in pts) * S) - 20
        x1 = int(max(p[0] for p in pts) * S) + 20; y1 = int(max(p[1] for p in pts) * S) + 20
        w, h = max(2, x1 - x0), max(2, y1 - y0)
        m = Image.new("L", (w, h), 0); md = ImageDraw.Draw(m)
        for poly in polys: md.polygon([(p[0] * S - x0, p[1] * S - y0) for p in (chaikin(poly, smooth) if len(poly) < 60 and smooth else poly)], fill=255)
        L = Image.new("RGBA", (w, h), fill + (255,))
        if FLAT: edge = False; dark = 1.0
        sh = Image.new("RGBA", (w, h), shade(fill, dark) + (255,)); sm = ImageChops.offset(m, 0, -int(16 * S)); sm = ImageChops.subtract(m, sm)
        L.paste(sh, (0, 0), sm.filter(ImageFilter.GaussianBlur(6)))
        hi = Image.new("RGBA", (w, h), shade(fill, 1.12) + (255,)); hm = ImageChops.subtract(m, ImageChops.offset(m, 0, int(10 * S)))
        if not FLAT: L.paste(hi, (0, 0), hm.filter(ImageFilter.GaussianBlur(5)).point(lambda v: v // 2))
        L.putalpha(m)
        if edge:
            o = Image.new("RGBA", (w, h), DK + (255,)); o.putalpha(dilate(m, lw * 2))
            o.alpha_composite(L); L = o
        s.im.alpha_composite(L, (x0, y0))
    def draw(s): return ImageDraw.Draw(s.im)
    def P(s, p): return (p[0] * S, p[1] * S)

# ------------------------------------------------------------------ species
SP = {
 "trex":   dict(L=1250, biped=True, col=(122, 106, 80), belly=(204, 188, 156), stripe=(88, 74, 56), spot=(150, 116, 82), hip_h=0.265, tail_bend=0.035,
                torso=[(0.085, 0.1, 0.105), (0.08, 0.1, 0.11), (0.05, 0.085, 0.09)], torso_ang=-0.28,
                neck=[(0.035, 0.068, 0.068), (0.03, 0.064, 0.064)], neck_ang=-0.45,
                tail=[(0.05, 0.085, 0.08)] + [(0.054, 0.062 * (1 - k / 9) ** 1.8 + 0.005, 0.055 * (1 - k / 9) ** 1.8 + 0.005) for k in range(9)], tail_ang=-0.16,
                leg=(0.125, 0.125, 0.065, 0.05, 0.085, 0.042, 0.03), arm=(0.042, 0.042, 0.018, 0.015), head="trex", hs=0.2, hdeco=["boss", "jawmuscle", "angry"]),
 "edmonto":dict(L=1250, biped=False, col=(132, 128, 92), belly=(206, 196, 160), stripe=(98, 94, 66), spot=(160, 140, 96), hip_h=0.29, tail_bend=0.02,
                torso=[(0.09, 0.12, 0.13), (0.09, 0.11, 0.12), (0.07, 0.08, 0.085)], torso_ang=0.10,
                neck=[(0.05, 0.07, 0.07), (0.05, 0.06, 0.06), (0.045, 0.055, 0.055)], neck_ang=-0.25,
                tail=[(0.06, 0.08, 0.075)] + [(0.055, 0.07 * (1 - k / 9) + 0.01, 0.065 * (1 - k / 9) + 0.01) for k in range(9)], tail_ang=0.02,
                leg=(0.13, 0.13, 0.07, 0.06, 0.09, 0.05, 0.036), fleg=(0.1, 0.095, 0.045, 0.045, 0.035, 0.028), head="duck", hs=0.2),
 "tricera":dict(L=1150, biped=False, col=(124, 112, 96), belly=(196, 186, 164), stripe=(92, 82, 70), spot=(170, 130, 90), hip_h=0.29,
                torso=[(0.1, 0.13, 0.13), (0.1, 0.13, 0.125), (0.07, 0.10, 0.10)], torso_ang=0.12,
                neck=[(0.05, 0.075, 0.075)], neck_ang=0.05,
                tail=[(0.06, 0.08, 0.075)] + [(0.05, 0.065 * (1 - k / 7) + 0.01, 0.06 * (1 - k / 7) + 0.01) for k in range(7)], tail_ang=0.08,
                leg=(0.13, 0.12, 0.06, 0.06, 0.085, 0.052, 0.04), fleg=(0.11, 0.095, 0.04, 0.055, 0.045, 0.036), head="trike", hs=0.24),
 "spino":  dict(L=1300, biped=True, col=(96, 102, 84), belly=(198, 190, 158), stripe=(72, 78, 62), spot=(132, 102, 78), hip_h=0.215, tail_bend=0.02,
                torso=[(0.09, 0.09, 0.1), (0.09, 0.09, 0.105), (0.07, 0.08, 0.085)], torso_ang=-0.1,
                neck=[(0.045, 0.06, 0.06), (0.045, 0.052, 0.052), (0.04, 0.045, 0.045)], neck_ang=-0.18,
                tail=[(0.05, 0.075, 0.07)] + [(0.05, 0.056 * (1 - k / 10) ** 1.4 + 0.006, 0.05 * (1 - k / 10) ** 1.4 + 0.006) for k in range(10)], tail_ang=-0.06,
                leg=(0.1, 0.1, 0.055, 0.045, 0.075, 0.04, 0.028), arm=(0.046, 0.046, 0.03, 0.018), head="spino", hs=0.17, sail=(150, 86, 60)),
 "chicken":dict(L=900, biped=True, col=(250, 246, 236), belly=(250, 246, 236), stripe=(236, 226, 210), hip_h=0.42,
                torso=[(0.12, 0.17, 0.19), (0.1, 0.15, 0.15)], torso_ang=-0.25,
                neck=[(0.07, 0.07, 0.07), (0.07, 0.06, 0.06)], neck_ang=-1.15,
                tail=[(0.07, 0.12, 0.1), (0.06, 0.08, 0.06)], tail_ang=-0.7,
                leg=(0.13, 0.15, 0.13, 0.05, 0.045, 0.022, 0.02), arm=None, head="chick", hs=0.12, legcol=(250, 178, 70)),
}
_TH = lambda n, a, p=1.8: [(0.05, a, a * 0.9)] + [(0.054, a * 0.75 * (1 - k / n) ** p + 0.005, a * 0.68 * (1 - k / n) ** p + 0.005) for k in range(n)]
SP.update({
 "giga":   dict(L=1320, biped=True, col=(104, 110, 116), belly=(214, 210, 198), stripe=(64, 68, 76), spot=(146, 124, 98), hip_h=0.25, tail_bend=0.03,
                torso=[(0.085, 0.095, 0.1), (0.08, 0.095, 0.105), (0.05, 0.08, 0.085)], torso_ang=-0.24,
                neck=[(0.04, 0.064, 0.064), (0.035, 0.06, 0.06)], neck_ang=-0.4, tail=_TH(10, 0.085), tail_ang=-0.14,
                leg=(0.12, 0.12, 0.062, 0.048, 0.08, 0.04, 0.03), arm=(0.05, 0.05, 0.024, 0.016), head="giga", hs=0.21, hdeco=["ridge", "angry", "jawmuscle"]),
 "carno":  dict(L=1050, biped=True, col=(156, 100, 74), belly=(218, 190, 150), stripe=(112, 70, 52), spot=(98, 62, 46), hip_h=0.28, tail_bend=0.03,
                torso=[(0.085, 0.1, 0.1), (0.08, 0.1, 0.105), (0.05, 0.085, 0.085)], torso_ang=-0.24,
                neck=[(0.04, 0.07, 0.07), (0.035, 0.066, 0.066)], neck_ang=-0.42, tail=_TH(9, 0.085), tail_ang=-0.12,
                leg=(0.13, 0.13, 0.07, 0.05, 0.08, 0.04, 0.03), arm=(0.024, 0.02, 0.01, 0.013), head="carno", hs=0.18, hdeco=["brow_horns", "angry"], osteo_rows=True),
 "allo":   dict(L=1000, biped=True, col=(158, 134, 90), belly=(222, 206, 166), stripe=(118, 92, 60), spot=(128, 100, 70), hip_h=0.27, tail_bend=0.03,
                torso=[(0.085, 0.09, 0.095), (0.08, 0.09, 0.1), (0.05, 0.075, 0.08)], torso_ang=-0.22,
                neck=[(0.04, 0.06, 0.06), (0.04, 0.056, 0.056)], neck_ang=-0.42, tail=_TH(10, 0.08), tail_ang=-0.12,
                leg=(0.125, 0.125, 0.068, 0.05, 0.075, 0.038, 0.028), arm=(0.055, 0.05, 0.028, 0.017), head="allo", hs=0.19, hdeco=["lacrimal", "angry"]),
 "raptor": dict(L=760, biped=True, col=(150, 96, 62), belly=(224, 200, 160), stripe=(92, 56, 38), spot=(176, 128, 84), hip_h=0.31, tail_bend=0.0,
                torso=[(0.09, 0.085, 0.09), (0.085, 0.08, 0.09), (0.05, 0.065, 0.07)], torso_ang=-0.2,
                neck=[(0.05, 0.05, 0.05), (0.045, 0.045, 0.045)], neck_ang=-0.7, tail=_TH(10, 0.07, 1.2), tail_ang=-0.05,
                leg=(0.14, 0.15, 0.08, 0.05, 0.07, 0.035, 0.025), arm=(0.075, 0.07, 0.04, 0.017), head="raptor", hs=0.17, hdeco=["angry", "feathers"], sickle=True),
 "pachy":  dict(L=700, biped=True, col=(132, 120, 98), belly=(208, 196, 168), stripe=(96, 86, 68), spot=(160, 132, 96), hip_h=0.3, tail_bend=0.02,
                torso=[(0.1, 0.12, 0.13), (0.09, 0.12, 0.125), (0.06, 0.09, 0.09)], torso_ang=-0.12,
                neck=[(0.05, 0.065, 0.065), (0.045, 0.06, 0.06)], neck_ang=-0.55, tail=_TH(9, 0.09, 1.4), tail_ang=-0.05,
                leg=(0.13, 0.13, 0.07, 0.05, 0.085, 0.045, 0.032), arm=(0.035, 0.03, 0.015, 0.013), head="pachy", hs=0.2, hdeco=["dome_knobs"], dome=(206, 172, 120)),
 "anky":   dict(L=1050, biped=False, col=(130, 112, 82), belly=(206, 190, 154), stripe=(98, 84, 62), spot=(160, 134, 96), hip_h=0.2, tail_bend=0.02,
                torso=[(0.1, 0.13, 0.12), (0.11, 0.135, 0.12), (0.08, 0.11, 0.1)], torso_ang=0.04,
                neck=[(0.05, 0.075, 0.075)], neck_ang=0.15, tail=[(0.06, 0.08, 0.075)] + [(0.055, 0.05 * (1 - k / 8) + 0.02, 0.045 * (1 - k / 8) + 0.02) for k in range(8)], tail_ang=0.02,
                leg=(0.08, 0.08, 0.04, 0.05, 0.075, 0.045, 0.038), fleg=(0.07, 0.065, 0.03, 0.055, 0.045, 0.038), head="anky", hs=0.17, hdeco=["corner_horns"], osteo=True, club=True),
 "stego":  dict(L=1150, biped=False, col=(124, 128, 88), belly=(206, 200, 160), stripe=(94, 98, 66), spot=(150, 140, 96), hip_h=0.31, tail_bend=0.02,
                torso=[(0.1, 0.13, 0.13), (0.1, 0.12, 0.12), (0.08, 0.09, 0.09)], torso_ang=0.22,
                neck=[(0.05, 0.055, 0.06), (0.045, 0.045, 0.05)], neck_ang=0.25, tail=[(0.06, 0.08, 0.075)] + [(0.055, 0.06 * (1 - k / 8) + 0.012, 0.055 * (1 - k / 8) + 0.012) for k in range(8)], tail_ang=-0.2,
                leg=(0.13, 0.12, 0.05, 0.05, 0.085, 0.05, 0.04), fleg=(0.085, 0.075, 0.035, 0.05, 0.04, 0.034), head="stego", hs=0.12, plates=(190, 112, 72), thago=True),
 "brachio":dict(L=1000, biped=False, col=(122, 128, 116), belly=(200, 200, 182), stripe=(92, 98, 88), spot=(150, 150, 130), hip_h=0.32, tail_bend=0.02,
                torso=[(0.1, 0.13, 0.13), (0.1, 0.13, 0.13), (0.08, 0.11, 0.11)], torso_ang=-0.22,
                neck=[(0.08, 0.06, 0.06), (0.08, 0.05, 0.05), (0.08, 0.042, 0.042), (0.075, 0.036, 0.036)], neck_ang=-1.05, tail=_TH(8, 0.08, 1.3), tail_ang=0.1,
                leg=(0.13, 0.12, 0.05, 0.05, 0.08, 0.06, 0.045), fleg=(0.15, 0.14, 0.05, 0.065, 0.055, 0.05), head="brachio", hs=0.1),
})

SP.update({
 "therizino":dict(L=1050, biped=True, col=(150, 140, 110), belly=(214, 204, 176), stripe=(116, 104, 80), spot=(170, 150, 110), hip_h=0.3, tail_bend=0.04,
                torso=[(0.09, 0.14, 0.15), (0.09, 0.13, 0.13), (0.06, 0.09, 0.09)], torso_ang=-0.45,
                neck=[(0.06, 0.05, 0.05), (0.06, 0.042, 0.042), (0.05, 0.036, 0.036)], neck_ang=-0.75, tail=_TH(7, 0.08, 1.4), tail_ang=0.05,
                leg=(0.12, 0.12, 0.05, 0.05, 0.08, 0.045, 0.034), arm=(0.09, 0.085, 0.04, 0.022), head="therizino", hs=0.11, bigclaws=0.2, hdeco=["feathers"]),
 "parasaur": dict(L=1150, biped=False, col=(140, 120, 92), belly=(214, 200, 168), stripe=(150, 70, 52), spot=(170, 140, 100), hip_h=0.29, tail_bend=0.02,
                torso=[(0.09, 0.12, 0.13), (0.09, 0.11, 0.12), (0.07, 0.08, 0.085)], torso_ang=0.10,
                neck=[(0.05, 0.07, 0.07), (0.05, 0.06, 0.06), (0.045, 0.055, 0.055)], neck_ang=-0.3,
                tail=[(0.06, 0.08, 0.075)] + [(0.055, 0.07 * (1 - k / 9) + 0.01, 0.065 * (1 - k / 9) + 0.01) for k in range(9)], tail_ang=0.02,
                leg=(0.13, 0.13, 0.07, 0.06, 0.09, 0.05, 0.036), fleg=(0.1, 0.095, 0.045, 0.045, 0.035, 0.028), head="duck", hs=0.2, hdeco=["tube_crest"], crest=(200, 96, 66)),
 "iguano":   dict(L=1150, biped=False, col=(118, 124, 92), belly=(204, 200, 168), stripe=(88, 94, 68), spot=(150, 146, 104), hip_h=0.3, tail_bend=0.02,
                torso=[(0.09, 0.125, 0.13), (0.09, 0.115, 0.12), (0.07, 0.085, 0.09)], torso_ang=0.08,
                neck=[(0.05, 0.07, 0.07), (0.05, 0.06, 0.06)], neck_ang=-0.3,
                tail=[(0.06, 0.08, 0.075)] + [(0.055, 0.07 * (1 - k / 9) + 0.01, 0.065 * (1 - k / 9) + 0.01) for k in range(9)], tail_ang=0.02,
                leg=(0.13, 0.13, 0.07, 0.06, 0.09, 0.05, 0.036), fleg=(0.105, 0.1, 0.045, 0.05, 0.04, 0.032), head="iguano", hs=0.19, thumb=True),
 "dilo":     dict(L=950, biped=True, col=(170, 150, 80), belly=(230, 216, 170), stripe=(70, 90, 70), spot=(110, 120, 80), hip_h=0.28, tail_bend=0.03,
                torso=[(0.085, 0.085, 0.09), (0.08, 0.085, 0.09), (0.05, 0.07, 0.075)], torso_ang=-0.22,
                neck=[(0.045, 0.055, 0.055), (0.04, 0.05, 0.05)], neck_ang=-0.5, tail=_TH(10, 0.075), tail_ang=-0.1,
                leg=(0.125, 0.125, 0.068, 0.05, 0.072, 0.036, 0.027), arm=(0.05, 0.048, 0.026, 0.015), head="dilo", hs=0.17, hdeco=["twin_crest", "angry"], crest=(204, 70, 54)),
 "styraco":  dict(L=1050, biped=False, col=(132, 110, 86), belly=(204, 190, 162), stripe=(98, 80, 64), spot=(176, 132, 92), hip_h=0.29,
                torso=[(0.1, 0.13, 0.13), (0.1, 0.13, 0.125), (0.07, 0.10, 0.10)], torso_ang=0.12, neck=[(0.05, 0.075, 0.075)], neck_ang=0.05,
                tail=[(0.06, 0.08, 0.075)] + [(0.05, 0.065 * (1 - k / 7) + 0.01, 0.06 * (1 - k / 7) + 0.01) for k in range(7)], tail_ang=0.08,
                leg=(0.13, 0.12, 0.06, 0.06, 0.085, 0.052, 0.04), fleg=(0.11, 0.095, 0.04, 0.055, 0.045, 0.036), head="styraco", hs=0.24),
 "kentro":   dict(L=950, biped=False, col=(150, 128, 82), belly=(214, 200, 160), stripe=(110, 92, 60), spot=(170, 140, 96), hip_h=0.3, tail_bend=0.02,
                torso=[(0.1, 0.12, 0.12), (0.1, 0.11, 0.11), (0.08, 0.085, 0.085)], torso_ang=0.2,
                neck=[(0.05, 0.05, 0.055), (0.045, 0.042, 0.046)], neck_ang=0.25, tail=[(0.06, 0.075, 0.07)] + [(0.055, 0.058 * (1 - k / 8) + 0.012, 0.052 * (1 - k / 8) + 0.012) for k in range(8)], tail_ang=-0.18,
                leg=(0.13, 0.12, 0.05, 0.05, 0.085, 0.05, 0.04), fleg=(0.085, 0.075, 0.035, 0.05, 0.04, 0.034), head="stego", hs=0.12, plates=(200, 150, 80), spiky=True, thago=True),
 "baryonyx": dict(L=1050, biped=True, col=(110, 116, 98), belly=(206, 200, 172), stripe=(78, 84, 70), spot=(140, 112, 86), hip_h=0.25, tail_bend=0.02,
                torso=[(0.09, 0.09, 0.1), (0.09, 0.09, 0.105), (0.07, 0.08, 0.085)], torso_ang=-0.16,
                neck=[(0.045, 0.06, 0.06), (0.045, 0.052, 0.052), (0.04, 0.045, 0.045)], neck_ang=-0.25, tail=_TH(10, 0.075, 1.4), tail_ang=-0.08,
                leg=(0.11, 0.11, 0.058, 0.046, 0.075, 0.04, 0.028), arm=(0.055, 0.055, 0.032, 0.019), head="spino", hs=0.16, bigclaws=0.07, hdeco=["angry"]),
 "diplo":    dict(L=980, biped=False, col=(136, 128, 104), belly=(210, 202, 178), stripe=(104, 96, 78), spot=(160, 150, 120), hip_h=0.27, tail_bend=0.015,
                torso=[(0.1, 0.12, 0.12), (0.1, 0.12, 0.12), (0.08, 0.1, 0.1)], torso_ang=-0.04,
                neck=[(0.08, 0.06, 0.06), (0.08, 0.05, 0.05), (0.075, 0.042, 0.042), (0.07, 0.035, 0.035)], neck_ang=-0.62,
                tail=[(0.06, 0.07, 0.065)] + [(0.06, 0.06 * (1 - k / 12) ** 1.5 + 0.004, 0.055 * (1 - k / 12) ** 1.5 + 0.004) for k in range(12)], tail_ang=-0.05,
                leg=(0.12, 0.11, 0.05, 0.05, 0.075, 0.055, 0.045), fleg=(0.1, 0.095, 0.045, 0.05, 0.045, 0.04), head="brachio", hs=0.085),
})

_SHORT = lambda a, n=3, l=0.03: [(l, a, a)] + [(l * 0.8, a * (1 - (k + 1) / (n + 1)) + 0.006, a * (1 - (k + 1) / (n + 1)) + 0.006) for k in range(n)]
SP.update({
 "mammoth": dict(L=1050, biped=False, mammal=True, pillar=True, fur=True, col=(112, 74, 48), belly=(140, 98, 66), stripe=(84, 54, 34), hip_h=0.30, tail_bend=0.0,
                prof=dict(top=[(-0.09, -0.12), (-0.11, -0.02), (-0.08, 0.07), (0.0, 0.12), (0.12, 0.16), (0.24, 0.21), (0.33, 0.25), (0.40, 0.23), (0.45, 0.16)],
                          bot=[(0.47, -0.03), (0.44, -0.11), (0.37, -0.16), (0.25, -0.18), (0.12, -0.16), (0.02, -0.14), (-0.06, -0.14)],
                          neck=(0.44, 0.06), hl=(0.0, -0.02), fl=(0.36, 0.0), tail=[(-0.09, 0.02), (-0.12, -0.06), (-0.12, -0.13)], tailw=(0.018, 0.012)),
                torso=[(0.1, 0.1, 0.1)], torso_ang=0.0, neck=[(0.05, 0.11, 0.11)], neck_ang=0.3, tail=[(0.03, 0.02, 0.02)], tail_ang=1.2,
                leg=(0.15, 0.13, 0.03, 0.03, 0.068, 0.058, 0.056), fleg=(0.16, 0.15, 0.03, 0.072, 0.062, 0.058),
                head="mammoth", hs=0.22, hdeco=["ear_round", "trunk", "tusks"]),
 "smilodon": dict(L=760, biped=False, mammal=True, col=(176, 126, 74), belly=(238, 216, 176), stripe=(128, 84, 44), hip_h=0.30, tail_bend=0.0,
                prof=dict(top=[(-0.06, -0.06), (-0.06, 0.03), (-0.01, 0.08), (0.10, 0.075), (0.20, 0.09), (0.28, 0.12), (0.35, 0.115), (0.40, 0.08)],
                          bot=[(0.41, -0.01), (0.37, -0.09), (0.29, -0.115), (0.17, -0.09), (0.07, -0.075), (-0.02, -0.085)],
                          neck=(0.39, 0.04), hl=(0.0, -0.01), fl=(0.31, 0.0), tail=[(-0.05, 0.05), (-0.09, 0.02), (-0.11, -0.02)], tailw=(0.025, 0.016), bellyh=0.05),
                torso=[(0.1, 0.1, 0.1)], torso_ang=0.0, neck=[(0.06, 0.065, 0.06), (0.05, 0.055, 0.05)], neck_ang=-0.25, tail=[(0.03, 0.02, 0.02)], tail_ang=1.0,
                leg=(0.12, 0.11, 0.075, 0.03, 0.058, 0.04, 0.032), fleg=(0.15, 0.12, 0.05, 0.07, 0.052, 0.042),
                head="cat", hs=0.23, hdeco=["ear_tri", "sabers", "angry"]),
 "rhino":   dict(L=950, biped=False, mammal=True, pillar=True, fur=True, col=(118, 86, 58), belly=(150, 114, 82), stripe=(88, 62, 42), hip_h=0.22, tail_bend=0.0,
                prof=dict(top=[(-0.08, -0.08), (-0.09, 0.01), (-0.05, 0.08), (0.05, 0.11), (0.17, 0.13), (0.27, 0.17), (0.35, 0.215), (0.42, 0.19), (0.46, 0.10)],
                          bot=[(0.48, -0.03), (0.42, -0.12), (0.30, -0.155), (0.16, -0.15), (0.03, -0.125), (-0.06, -0.115)],
                          neck=(0.46, 0.02), hl=(0.0, -0.02), fl=(0.37, 0.0), tail=[(-0.08, 0.01), (-0.10, -0.06), (-0.10, -0.11)], tailw=(0.016, 0.01)),
                torso=[(0.1, 0.1, 0.1)], torso_ang=0.0, neck=[(0.04, 0.1, 0.095)], neck_ang=0.6, tail=[(0.03, 0.02, 0.02)], tail_ang=1.2,
                leg=(0.1, 0.085, 0.03, 0.03, 0.058, 0.048, 0.046), fleg=(0.11, 0.095, 0.03, 0.062, 0.05, 0.048),
                head="rhino", hs=0.22, hdeco=["ear_tri", "rhino_horns"]),
 "sloth":   dict(L=1000, biped=False, mammal=True, pillar=True, fur=True, col=(120, 94, 68), belly=(156, 128, 96), stripe=(92, 70, 50), hip_h=0.30, tail_bend=0.0,
                prof=dict(top=[(-0.10, -0.05), (-0.09, 0.07), (-0.02, 0.14), (0.10, 0.155), (0.22, 0.13), (0.31, 0.08), (0.36, 0.03)],
                          bot=[(0.38, -0.07), (0.33, -0.14), (0.22, -0.19), (0.09, -0.2), (-0.03, -0.18), (-0.09, -0.13)],
                          neck=(0.36, -0.01), hl=(0.0, -0.04), fl=(0.31, -0.07), tail=[(-0.08, -0.02), (-0.16, -0.12), (-0.21, -0.25)], tailw=(0.06, 0.03)),
                torso=[(0.1, 0.1, 0.1)], torso_ang=0.0, neck=[(0.07, 0.065, 0.06)], neck_ang=0.2, tail=[(0.03, 0.02, 0.02)], tail_ang=1.2,
                leg=(0.12, 0.11, 0.03, 0.03, 0.08, 0.066, 0.06), fleg=(0.1, 0.09, 0.03, 0.058, 0.048, 0.044),
                head="sloth", hs=0.16, front_claws=True),
 "sarco":   dict(L=1000, biped=False, col=(88, 98, 72), belly=(186, 182, 142), stripe=(62, 70, 52), spot=(110, 118, 84), hip_h=0.1, tail_bend=0.015,
                torso=[(0.11, 0.07, 0.055), (0.12, 0.075, 0.06), (0.08, 0.06, 0.05)], torso_ang=0.02, neck=[(0.05, 0.05, 0.05)], neck_ang=0.02,
                tail=[(0.06, 0.07, 0.06)] + [(0.055, 0.06 * (1 - k / 10) + 0.008, 0.05 * (1 - k / 10) + 0.008) for k in range(10)], tail_ang=-0.01,
                leg=(0.06, 0.058, 0.04, 0.036, 0.03, 0.025, 0.02), fleg=(0.055, 0.05, 0.035, 0.03, 0.025, 0.02), head="croc", hs=0.24, osteo_rows=True, hdeco=["angry"]),
 "megalania":dict(L=900, biped=False, col=(132, 118, 86), belly=(206, 196, 162), stripe=(92, 82, 60), spot=(160, 140, 96), hip_h=0.12, tail_bend=0.015,
                torso=[(0.11, 0.07, 0.065), (0.11, 0.075, 0.07), (0.07, 0.06, 0.055)], torso_ang=0.02, neck=[(0.07, 0.05, 0.05)], neck_ang=-0.06,
                tail=[(0.06, 0.065, 0.06)] + [(0.055, 0.055 * (1 - k / 10) + 0.006, 0.05 * (1 - k / 10) + 0.006) for k in range(10)], tail_ang=0.0,
                leg=(0.065, 0.06, 0.04, 0.04, 0.035, 0.028, 0.022), fleg=(0.06, 0.055, 0.035, 0.034, 0.028, 0.022), head="lizard", hs=0.17, hdeco=["angry"]),
 "quetzal": dict(L=900, biped=False, mammal=True, col=(196, 194, 184), belly=(236, 232, 220), stripe=(150, 140, 130), hip_h=0.2, tail_bend=0.0,
                prof=dict(top=[(-0.06, -0.02), (-0.05, 0.05), (0.01, 0.12), (0.08, 0.19), (0.14, 0.23), (0.19, 0.22), (0.20, 0.17)],
                          bot=[(0.19, 0.09), (0.14, 0.03), (0.07, -0.03), (0.0, -0.06), (-0.05, -0.05)],
                          neck=(0.18, 0.18), hl=(0.0, -0.02), fl=(0.16, 0.11), tail=[(-0.05, 0.01), (-0.08, 0.0)], tailw=(0.012, 0.006), bellyh=0.05),
                torso=[(0.1, 0.1, 0.1)], torso_ang=0.0, neck=[(0.09, 0.036, 0.036), (0.09, 0.032, 0.032), (0.08, 0.03, 0.03)], neck_ang=-0.75, tail=[(0.02, 0.01, 0.01)], tail_ang=0.6,
                leg=(0.1, 0.09, 0.035, 0.03, 0.04, 0.028, 0.022), fleg=(0.17, 0.15, 0.03, 0.036, 0.028, 0.022),
                head="ptero", hs=0.28, hdeco=["ptero_crest"], wing=(160, 152, 146)),
 "paracera":dict(L=1100, biped=False, mammal=True, pillar=True, col=(150, 130, 104), belly=(204, 190, 164), stripe=(116, 98, 78), hip_h=0.40, tail_bend=0.0,
                prof=dict(top=[(-0.07, -0.06), (-0.07, 0.03), (-0.02, 0.08), (0.10, 0.09), (0.22, 0.115), (0.31, 0.13), (0.37, 0.11)],
                          bot=[(0.39, 0.0), (0.35, -0.075), (0.23, -0.10), (0.10, -0.095), (0.0, -0.085), (-0.06, -0.075)],
                          neck=(0.36, 0.07), hl=(0.0, -0.02), fl=(0.31, -0.01), tail=[(-0.06, 0.02), (-0.08, -0.05), (-0.08, -0.12)], tailw=(0.012, 0.008)),
                torso=[(0.1, 0.1, 0.1)], torso_ang=0.0, neck=[(0.1, 0.065, 0.06), (0.09, 0.055, 0.05)], neck_ang=-0.8, tail=[(0.03, 0.02, 0.02)], tail_ang=1.2,
                leg=(0.18, 0.17, 0.04, 0.03, 0.055, 0.042, 0.038), fleg=(0.19, 0.18, 0.04, 0.055, 0.042, 0.038),
                head="paracera", hs=0.2, hdeco=["ear_tri"]),
})
SP_FIXED = True

def chain(start, ang0, segs, bends, dyn):
    pts = [start]; th = []; a = ang0
    for k, (l, tt, tb) in enumerate(segs):
        a += bends + dyn[k]; p = add(pts[-1], (l * math.cos(a), l * math.sin(a))); pts.append(p); th.append((tt, tb))
    return pts, th, a

def head_shape(kind, gape):
    """local coords: x forward from neck joint (units of head scale), y down. returns (skull, jaw, hinge, eye, extras)"""
    if kind == "trex":
        skull = [(-0.26, -0.28), (-0.08, -0.5), (0.26, -0.55), (0.44, -0.58), (0.58, -0.5), (0.86, -0.44), (1.0, -0.38), (1.06, -0.24), (1.06, -0.06), (1.03, 0.03), (0.9, 0.045), (0.6, 0.05), (0.2, 0.06), (0.05, 0.08), (-0.22, 0.22)]   # v20: deep, broad, rounded snout
        jaw = [(0.12, 0.03), (0.98, 0.03), (0.96, 0.15), (0.6, 0.2), (0.3, 0.27), (0.0, 0.25)]
        return skull, jaw, (0.06, 0.05), (0.42, -0.3), ("teeth", 0.25, 0.95)
    if kind == "spino":   # long, low crocodile-like snout with a notch and a rosette tip
        skull = [(-0.22, -0.22), (0.0, -0.33), (0.22, -0.32), (0.38, -0.2), (0.7, -0.13), (1.05, -0.1), (1.22, -0.14), (1.36, -0.12), (1.42, -0.03), (1.36, 0.04), (1.1, 0.02), (0.95, 0.04), (0.5, 0.04), (0.1, 0.06), (-0.2, 0.18)]
        jaw = [(0.05, 0.03), (1.34, 0.03), (1.32, 0.1), (0.9, 0.1), (0.4, 0.14), (0.0, 0.18)]
        return skull, jaw, (0.05, 0.05), (0.2, -0.2), ("teeth", 0.4, 1.38)
    if kind == "duck":
        skull = [(-0.2, -0.22), (0.1, -0.36), (0.35, -0.32), (0.62, -0.18), (0.98, -0.12), (1.06, 0.0), (1.0, 0.07), (0.3, 0.1), (-0.15, 0.2)]
        jaw = [(0.3, 0.05), (0.98, 0.06), (0.94, 0.14), (0.4, 0.2), (0.25, 0.14)]
        return skull, jaw, (0.3, 0.07), (0.32, -0.16), ("bill", 0.7, 1.05)
    if kind == "trike":   # v18: long wedge skull, hooked parrot beak, short nose horn, frill rising behind
        skull = [(-0.18, -0.26), (0.12, -0.36), (0.45, -0.34), (0.74, -0.24), (0.96, -0.12), (1.1, 0.0), (1.12, 0.08), (1.04, 0.13), (0.94, 0.07), (0.6, 0.11), (0.2, 0.16), (-0.18, 0.18)]
        jaw = [(0.28, 0.1), (0.9, 0.08), (1.02, 0.12), (0.9, 0.21), (0.45, 0.25), (0.3, 0.2)]
        return skull, jaw, (0.28, 0.1), (0.46, -0.19), ("horns", 0, 0)
    if kind == "giga":
        skull = [(-0.24, -0.22), (-0.04, -0.36), (0.3, -0.38), (0.66, -0.33), (1.0, -0.25), (1.24, -0.17), (1.32, -0.07), (1.3, 0.02), (1.08, 0.04), (0.6, 0.05), (0.2, 0.06), (0.05, 0.08), (-0.2, 0.18)]   # v20: long, low, narrow
        jaw = [(0.12, 0.03), (1.26, 0.03), (1.2, 0.12), (0.6, 0.15), (0.3, 0.2), (0.0, 0.2)]
        return skull, jaw, (0.06, 0.05), (0.38, -0.25), ("teeth", 0.25, 1.24)
    if kind == "carno":
        skull = [(-0.22, -0.3), (0.0, -0.5), (0.3, -0.52), (0.6, -0.42), (0.78, -0.3), (0.86, -0.1), (0.84, 0.03), (0.6, 0.05), (0.2, 0.06), (0.04, 0.08), (-0.2, 0.2)]
        jaw = [(0.1, 0.03), (0.82, 0.03), (0.78, 0.12), (0.4, 0.18), (0.0, 0.2)]
        return skull, jaw, (0.05, 0.05), (0.33, -0.3), ("teeth", 0.2, 0.82)
    if kind == "allo":
        skull = [(-0.22, -0.24), (-0.04, -0.4), (0.3, -0.42), (0.6, -0.36), (0.9, -0.28), (1.06, -0.18), (1.1, -0.04), (1.06, 0.03), (0.6, 0.05), (0.2, 0.06), (0.04, 0.08), (-0.2, 0.18)]
        jaw = [(0.1, 0.03), (1.04, 0.03), (1.0, 0.11), (0.6, 0.15), (0.3, 0.2), (0.0, 0.2)]
        return skull, jaw, (0.05, 0.05), (0.36, -0.27), ("teeth", 0.22, 1.04)
    if kind == "raptor":
        skull = [(-0.2, -0.2), (0.05, -0.32), (0.4, -0.28), (0.8, -0.16), (1.0, -0.08), (1.03, 0.0), (0.85, 0.03), (0.3, 0.05), (0.0, 0.07), (-0.18, 0.16)]
        jaw = [(0.1, 0.03), (0.98, 0.02), (0.9, 0.09), (0.4, 0.12), (0.0, 0.15)]
        return skull, jaw, (0.05, 0.05), (0.3, -0.18), ("teeth", 0.2, 0.96)
    if kind == "pachy":
        skull = [(-0.22, -0.25), (-0.12, -0.55), (0.12, -0.74), (0.4, -0.7), (0.56, -0.46), (0.75, -0.22), (0.86, -0.05), (0.8, 0.05), (0.3, 0.08), (-0.15, 0.18)]
        jaw = [(0.25, 0.05), (0.8, 0.04), (0.75, 0.12), (0.35, 0.16)]
        return skull, jaw, (0.25, 0.06), (0.44, -0.26), ("beak", 0.7, 0.86)
    if kind == "anky":
        skull = [(-0.15, -0.3), (0.3, -0.36), (0.75, -0.25), (0.92, -0.05), (0.86, 0.1), (0.2, 0.15), (-0.15, 0.15)]
        jaw = [(0.3, 0.1), (0.84, 0.1), (0.76, 0.2), (0.35, 0.22)]
        return skull, jaw, (0.3, 0.1), (0.44, -0.15), ("beak", 0.72, 0.92)
    if kind == "stego":
        skull = [(-0.15, -0.22), (0.3, -0.27), (0.7, -0.17), (0.96, -0.04), (0.92, 0.06), (0.3, 0.1), (-0.15, 0.14)]
        jaw = [(0.3, 0.05), (0.9, 0.05), (0.85, 0.12), (0.35, 0.15)]
        return skull, jaw, (0.3, 0.06), (0.34, -0.12), ("beak", 0.75, 0.96)
    if kind == "brachio":
        skull = [(-0.2, -0.2), (0.02, -0.44), (0.3, -0.5), (0.46, -0.32), (0.75, -0.2), (0.96, -0.08), (0.96, 0.04), (0.4, 0.08), (-0.15, 0.15)]
        jaw = [(0.3, 0.05), (0.92, 0.05), (0.88, 0.12), (0.35, 0.15)]
        return skull, jaw, (0.3, 0.06), (0.36, -0.15), ("beak", 0.0, 0.0)
    if kind == "therizino":
        skull = [(-0.2, -0.22), (0.1, -0.36), (0.45, -0.3), (0.85, -0.12), (0.95, 0.0), (0.8, 0.06), (0.3, 0.1), (-0.15, 0.16)]
        jaw = [(0.3, 0.05), (0.85, 0.04), (0.78, 0.12), (0.35, 0.15)]
        return skull, jaw, (0.3, 0.06), (0.36, -0.15), ("beak", 0.7, 0.95)
    if kind == "iguano":
        skull = [(-0.2, -0.24), (0.1, -0.36), (0.5, -0.3), (0.9, -0.16), (1.06, -0.02), (1.0, 0.07), (0.3, 0.1), (-0.15, 0.2)]
        jaw = [(0.3, 0.05), (0.98, 0.06), (0.94, 0.14), (0.4, 0.2), (0.25, 0.14)]
        return skull, jaw, (0.3, 0.07), (0.3, -0.17), ("beak", 0.85, 1.06)
    if kind == "dilo":
        skull = [(-0.2, -0.22), (0.02, -0.36), (0.4, -0.34), (0.7, -0.24), (0.86, -0.22), (0.98, -0.16), (1.02, -0.04), (0.98, 0.03), (0.6, 0.05), (0.2, 0.06), (0.04, 0.08), (-0.18, 0.16)]
        jaw = [(0.1, 0.03), (0.98, 0.03), (0.94, 0.11), (0.5, 0.15), (0.0, 0.17)]
        return skull, jaw, (0.05, 0.05), (0.32, -0.22), ("teeth", 0.2, 0.98)
    if kind == "styraco":
        skull = [(-0.1, -0.3), (0.35, -0.32), (0.85, -0.2), (1.0, 0.05), (0.85, 0.15), (0.2, 0.17), (-0.15, 0.2)]
        jaw = [(0.25, 0.12), (0.88, 0.14), (0.8, 0.26), (0.3, 0.3)]
        return skull, jaw, (0.25, 0.14), (0.38, -0.2), ("spikefrill", 0, 0)
    if kind == "mammoth":
        skull = [(-0.3, -0.2), (-0.22, -0.7), (0.1, -0.86), (0.42, -0.62), (0.58, -0.25), (0.62, 0.02), (0.45, 0.2), (0.1, 0.25), (-0.25, 0.15)]
        jaw = [(0.1, 0.15), (0.36, 0.18), (0.3, 0.3), (0.1, 0.28)]
        return skull, jaw, (0.15, 0.18), (0.24, -0.3), ("beak", 0, 0)
    if kind == "cat":   # v18: rounder cat skull, short deep muzzle, heavy chin for the sabers
        skull = [(-0.28, -0.2), (-0.12, -0.42), (0.12, -0.52), (0.38, -0.48), (0.56, -0.34), (0.7, -0.24), (0.8, -0.12), (0.82, 0.0), (0.74, 0.08), (0.5, 0.1), (0.2, 0.14), (-0.22, 0.2)]
        jaw = [(0.1, 0.08), (0.66, 0.08), (0.64, 0.18), (0.5, 0.26), (0.22, 0.26)]
        return skull, jaw, (0.1, 0.1), (0.42, -0.24), ("teeth", 0.35, 0.72)
    if kind == "rhino":
        skull = [(-0.25, -0.25), (0.1, -0.35), (0.6, -0.3), (1.0, -0.15), (1.1, 0.05), (0.9, 0.15), (0.3, 0.2), (-0.2, 0.2)]
        jaw = [(0.4, 0.15), (1.0, 0.12), (0.95, 0.25), (0.45, 0.28)]
        return skull, jaw, (0.4, 0.16), (0.42, -0.15), ("beak", 0, 0)
    if kind == "sloth":
        skull = [(-0.2, -0.2), (0.15, -0.32), (0.5, -0.2), (0.7, -0.02), (0.6, 0.1), (0.1, 0.15), (-0.2, 0.15)]
        jaw = [(0.25, 0.08), (0.62, 0.06), (0.55, 0.16), (0.3, 0.18)]
        return skull, jaw, (0.25, 0.08), (0.32, -0.12), ("beak", 0, 0)
    if kind == "croc":
        skull = [(-0.2, -0.15), (0.1, -0.24), (0.5, -0.15), (1.0, -0.1), (1.25, -0.08), (1.36, -0.02), (1.3, 0.03), (0.2, 0.05), (-0.15, 0.08)]
        jaw = [(0.1, 0.03), (1.3, 0.03), (1.25, 0.1), (0.2, 0.13), (-0.1, 0.12)]
        return skull, jaw, (0.0, 0.04), (0.2, -0.2), ("teeth", 0.2, 1.3)
    if kind == "lizard":
        skull = [(-0.2, -0.18), (0.15, -0.28), (0.6, -0.22), (0.95, -0.1), (1.0, 0.0), (0.9, 0.05), (0.2, 0.07), (-0.15, 0.12)]
        jaw = [(0.1, 0.04), (0.95, 0.04), (0.9, 0.12), (0.2, 0.15), (-0.05, 0.13)]
        return skull, jaw, (0.05, 0.05), (0.32, -0.14), ("teeth", 0.2, 0.95)
    if kind == "ptero":
        skull = [(-0.15, -0.2), (0.1, -0.3), (0.4, -0.22), (1.2, -0.06), (1.62, 0.0), (1.2, 0.04), (0.3, 0.08), (-0.1, 0.1)]
        jaw = [(0.25, 0.04), (1.56, 0.01), (1.2, 0.1), (0.3, 0.12)]
        return skull, jaw, (0.2, 0.05), (0.16, -0.12), ("beak", 0, 0)
    if kind == "paracera":
        skull = [(-0.25, -0.25), (0.05, -0.38), (0.5, -0.3), (0.9, -0.18), (1.02, 0.0), (0.95, 0.12), (0.4, 0.16), (-0.2, 0.18)]
        jaw = [(0.4, 0.12), (0.95, 0.12), (0.9, 0.22), (0.45, 0.24)]
        return skull, jaw, (0.4, 0.12), (0.3, -0.18), ("beak", 0, 0)
    if kind == "chick":
        skull = [(-0.1, -0.3), (0.3, -0.42), (0.62, -0.3), (0.72, -0.08), (0.55, 0.12), (0.1, 0.2), (-0.15, 0.1)]
        jaw = [(0.58, -0.02), (1.0, 0.04), (0.6, 0.12)]
        return skull, jaw, (0.58, 0.0), (0.38, -0.15), ("comb", 0, 0)

def beast(kind, t, gait="walk", mouth=0.0, freq=None, look=0.0, P=None, walkd=None):
    """P (optional pose, all additive): pitch, neck, head, tailup, tailbend, crouch, arm, feet={"near":(dx,lift),"far":(dx,lift)} (gait "pose" = feet planted from P)"""
    P = P or {}
    if SP[kind].get("swim"):
        import sea; return sea.swimmer(kind, t, gait, mouth, P)
    _low = SP[kind]["hip_h"] < 0.15   # crocs / monitor lizards: keep the body flat, swing the head instead
    _mam = SP[kind].get("mammal") and not _low
    G = lambda k, d=0.0: P.get(k, d) * (0.25 if _low and k in ("pitch", "crouch") else 0.45 if _mam and k == "pitch" else 0.35 if _mam and k == "crouch" else 0.6 if _mam and k == "neck" and P.get(k, 0) < 0 else 1.0) + (0.6 * P.get("pitch", 0) if _low and k == "head" else 0)
    sp = SP[kind]; L = sp["L"]; cv = Canvas(); col = sp["col"]
    fr = freq or {"walk": 0.8, "run": 1.5, "idle": 0.4, "graze": 0.4, "roar": 0.5, "pose": 0.4}[gait]
    moving = gait in ("walk", "run")
    stride = (0.16 if gait == "walk" else 0.26 if gait == "run" else 0.0) * L; lift = (0.05 if gait == "walk" else 0.09) * L
    duty = 0.62 if gait == "walk" else 0.42   # share of the cycle a foot is planted
    # v20 planted feet (gait solver idea from line-art-animation): when the caller passes the distance walked (walkd,
    # in this canvas' units, + = forward) the step cycle is driven by distance, so a planted foot moves back exactly
    # as fast as the body moves forward - no sliding. Without walkd the cycle runs on time as before.
    if moving and walkd is not None: p = 2 * math.pi * walkd / (stride / duty)
    else: p = 2 * math.pi * fr * t
    hipx = W0 * 0.5 - 0.05 * L
    bob = (0.012 * L * math.cos(2 * p)) if moving else 0.006 * L * math.sin(p)
    hip = (hipx, GROUND - sp["hip_h"] * L + bob + G("crouch") * L)
    graze = gait == "graze"
    # ---- spine chains
    tdyn = [0.06 * math.sin(p - k * 0.55) * (0.3 + k / len(sp["tail"])) for k in range(len(sp["tail"]))]
    tail, tth, _ = chain(hip, math.pi + sp["tail_ang"] + G("tailup") + 0.6 * G("pitch"), [(l * L, a, b) for l, a, b in sp["tail"]], sp.get("tail_bend", 0.02) + G("tailbend"), tdyn)
    tor, oth, ta = chain(hip, sp["torso_ang"] + G("pitch") + (0.12 if graze else 0) + (0.02 * math.sin(2 * p) if moving else 0), [(l * L, a, b) for l, a, b in sp["torso"]], 0.0, [0] * 9)
    nang = sp["neck_ang"] + G("neck") + (0.85 if graze else 0) + (-0.12 if gait == "roar" else 0) + look + 0.04 * math.sin(p + 1)
    ndyn = [0.05 * math.sin(p * (2 if moving else 1) + k) for k in range(len(sp["neck"]))]
    neck, nth, na = chain(tor[-1], nang - (len(sp["neck"]) - 1) * 0.0, [(l * L, a, b) for l, a, b in sp["neck"]], 0.0, ndyn)
    if graze: na += 0.5
    if gait == "roar": na -= 0.08
    centre = tail[::-1] + tor[1:] + neck[1:]
    thick = [(x * L, y * L) for x, y in (tth[::-1] + [(sp["tail"][0][1], sp["tail"][0][2])] + oth + nth)]
    thick = thick[:len(centre)]
    while len(thick) < len(centre): thick.append(thick[-1])
    thick[0] = (0.004 * L, 0.004 * L)
    centre, thick = smooth(centre, thick, 4)
    # normals
    top, bot = [], []
    for i, c in enumerate(centre):
        a = centre[max(0, i - 1)]; b = centre[min(len(centre) - 1, i + 1)]; dx, dy = b[0] - a[0], b[1] - a[1]; n = math.hypot(dx, dy) or 1
        nx, ny = dy / n, -dx / n
        top.append((c[0] + nx * thick[i][0], c[1] + ny * thick[i][0])); bot.append((c[0] - nx * thick[i][1], c[1] - ny * thick[i][1]))
    body = top + bot[::-1]
    PR = sp.get("prof"); xbody = []
    if PR:   # silhouette species (mammals / pterosaur): body drawn from a reference-proportion outline, not the dino spine tube
        a0 = G("pitch") + (0.02 * math.sin(2 * p) if moving else 0)
        def B(q): return add(hip, rot((q[0] * L, -q[1] * L), a0))
        nb = B(PR["neck"])
        neck, nth, na = chain(nb, nang, [(l * L, a, b) for l, a, b in sp["neck"]], 0.0, ndyn)
        if graze: na += 0.5
        if gait == "roar": na -= 0.08
        ncen = [nb] + neck[1:]; nthk = [(x * L, y * L) for x, y in nth][:len(ncen)]
        while len(nthk) < len(ncen): nthk.append(nthk[-1])
        ntop, nbot = [], []
        for i, c in enumerate(ncen):
            a_ = ncen[max(0, i - 1)]; b_ = ncen[min(len(ncen) - 1, i + 1)]; dx, dy = b_[0] - a_[0], b_[1] - a_[1]; n = math.hypot(dx, dy) or 1; nx, ny = dy / n, -dx / n
            ntop.append((c[0] + nx * nthk[i][0], c[1] + ny * nthk[i][0])); nbot.append((c[0] - nx * nthk[i][1], c[1] - ny * nthk[i][1]))
        topP = [B(q) for q in PR["top"]]; botP = [B(q) for q in PR["bot"]]
        body = topP + ntop[1:] + nbot[1:][::-1] + botP
        tw = PR.get("tailw", (0.02, 0.01)); tp0 = [B(q) for q in PR["tail"]]
        sw = 0.04 * math.sin(p) if moving else 0.0
        tp0 = [add(q, (0, sw * L * k / max(1, len(tp0) - 1))) for k, q in enumerate(tp0)]
        if len(tp0) > 1: xbody = [taper(tp0[k], tp0[k + 1], lerp(tw[0], tw[1], k / (len(tp0) - 1)) * L, lerp(tw[0], tw[1], (k + 1) / (len(tp0) - 1)) * L) for k in range(len(tp0) - 1)]
        centre, top, bot = ncen, ntop, nbot
        tor = [B(PR["hl"]), B(PR["fl"]), nb]; PRtop, PRbot = topP, botP
    if sp.get("sail"):   # neural-spine sail along the back, anchored to the moving spine points
        x0, x1 = hip[0] - 0.14 * L, tor[-1][0] - 0.02 * L
        idx = [i for i, c in enumerate(centre) if x0 <= c[0] <= x1 and i < len(centre) - 2]
        if len(idx) > 3:
            base_, tips = [], []
            for j, i in enumerate(idx):
                u = j / (len(idx) - 1); c = centre[i]; tp = top[i]; vx, vy = tp[0] - c[0], tp[1] - c[1]; n = math.hypot(vx, vy) or 1
                hgt = 0.2 * L * math.sin(math.pi * u) ** 0.7 * (0.85 + 0.25 * u)
                base_.append((c[0] + vx * 0.6, c[1] + vy * 0.6)); tips.append((tp[0] + vx / n * hgt, tp[1] + vy / n * hgt))
            sl = base_ + tips[::-1]; scol = sp["sail"]
            cv.piece([sl], scol, smooth=2); d0 = cv.draw()
            for j in range(1, len(idx) - 1, 3):
                d0.line([cv.P(base_[j]), cv.P(tips[j])], fill=shade(scol, 0.7), width=6)
            d0.line([cv.P(q) for q in tips[2:-2]], fill=shade(scol, 1.25), width=10, joint="curve")
    if sp.get("plates"):   # stegosaur plates in two rows, anchored on the spine
        idx = [i for i, c in enumerate(centre) if hip[0] - 0.42 * L <= c[0] <= tor[-1][0] + 0.02 * L and 2 < i < len(centre) - 3]
        pc = sp["plates"]
        for row in (0, 1):
            for j, i in enumerate(idx[row::4]):
                u = (idx.index(i)) / max(1, len(idx) - 1); c = centre[i]; tp = top[i]; vx, vy = tp[0] - c[0], tp[1] - c[1]; n = math.hypot(vx, vy) or 1
                hgt = (0.06 + 0.1 * math.sin(math.pi * u) ** 1.2) * L * (0.85 if row else 1.0); w = hgt * 0.42
                tx, ty = vx / n, vy / n; bx, by = -ty, tx; b0 = (tp[0] - tx * 0.02 * L, tp[1] - ty * 0.02 * L)
                plate = [add(b0, (bx * w * 0.6, by * w * 0.6)), add(b0, (tx * hgt * 0.55 + bx * w, ty * hgt * 0.55 + by * w)), add(b0, (tx * hgt, ty * hgt)),
                         add(b0, (tx * hgt * 0.55 - bx * w, ty * hgt * 0.55 - by * w)), add(b0, (-bx * w * 0.6, -by * w * 0.6))]
                if sp.get("spiky") and u < 0.55:   # rear half: long thin spikes instead of plates
                    plate = [add(b0, (bx * w * 0.35, by * w * 0.35)), add(b0, (tx * hgt * 1.25, ty * hgt * 1.25)), add(b0, (-bx * w * 0.35, -by * w * 0.35))]
                if row: plate = [add(q, (0.025 * L, -0.005 * L)) for q in plate]
                cv.piece([plate], shade(pc, 0.8 if row else 1.0), smooth=1)
    # ---- legs
    def leg(base, phase, dims, far, front=False):
        if front: l1, l2, l3, r1, r2, r3 = dims; l4 = 0.03
        else: l1, l2, l3, l4, r1, r2, r3 = dims
        l1, l2, l3, l4 = l1 * L, l2 * L, l3 * L, l4 * L
        ph = p + phase
        sw = 0.0   # 0 planted .. 1 mid-swing
        if moving:
            u = (ph / (2 * math.pi)) % 1.0
            if u < duty: rx = stride * 0.5 - stride * u / duty; fy = GROUND   # planted: slides back at body speed
            else:
                q_ = (u - duty) / (1 - duty); mj = q_ ** 3 * (10 - 15 * q_ + 6 * q_ * q_)   # minimum-jerk swing
                sw = math.sin(math.pi * q_); rx = -stride * 0.5 + stride * mj; fy = GROUND - lift * sw ** 1.2
            fx = base[0] + 0.06 * L + rx
        elif gait == "pose":
            fdx, flift = P.get("feet", {}).get("far" if far else "near", (0.0, 0.0))
            fx, fy = base[0] + (0.05 + fdx) * L + (0.03 * L if far else 0), GROUND - flift * L
        else: fx, fy = base[0] + (0.05 if not front else 0.02) * L + (0.03 * L if far else 0), GROUND
        toe = (fx + (0.05 * L if not front else 0.02 * L), fy)
        ma = -2.0 + 0.5 * sw   # metatarsus angle from toe back up to ankle (lifts while the foot swings)
        if sp.get("pillar"): ma = -1.62 + 0.3 * sw; toe = (fx + 0.035 * L, fy)
        ankle = (toe[0] + l3 * math.cos(ma) - 0.02 * L, toe[1] + l3 * math.sin(ma))
        knee = ik(base, ankle, l1, l2, bend=-1 if front else 1)
        polys = [taper(base, knee, r1 * L, r2 * L * 0.8), taper(knee, ankle, r2 * L * 0.8, r3 * L * 0.7), taper(ankle, (toe[0] - 0.01 * L, toe[1] - 0.012 * L), r3 * L * 0.7, r3 * L * 0.55)]
        # toes (3 for theropod/hadrosaur, hoof-like pads for front)
        for k, da in enumerate(() if sp.get("mammal") else (-0.25, 0.0, 0.25) if not front else (-0.2, 0.2)):
            tip = (toe[0] + l4 * math.cos(da * 0.6) * (0.8 if k != 1 else 1.0), toe[1] - 0.004 * L + l4 * 0.1 * k)
            polys.append(taper((toe[0] - 0.012 * L, toe[1] - 0.012 * L), tip, r3 * L * 0.42, r3 * L * 0.22))
        if sp.get("mammal"):   # rounded foot / paw instead of dinosaur toes
            fw = r3 * L * (1.08 if sp.get("pillar") else 1.0); fh = r3 * L * (0.55 if sp.get("pillar") else 0.5); fc = ((ankle[0] + toe[0]) / 2 + 0.006 * L, toe[1] - fh * 0.85)
            polys[-1] = taper(ankle, fc, r3 * L * 0.7, r3 * L * 0.7)
            polys.append([(fc[0] + fw * math.cos(a), fc[1] + fh * (0.9 if math.sin(a) > 0 else 1.0) * math.sin(a)) for a in [k * math.pi / 10 for k in range(20)]])
        if PR:
            polys.insert(0, taper((base[0] - 0.01 * L, base[1] - 0.05 * L), knee, r1 * L * 1.3, r2 * L * 0.85)); return polys, (base, knee, ankle, toe)
        thigh = [(base[0] + r1 * L * (1.05 if sp.get("mammal") else 1.25) * math.cos(a) * (1 - 0.25 * max(0, -math.sin(a))), base[1] - 0.15 * r1 * L + r1 * L * (1.2 if math.sin(a) < 0 else 1.0) * math.sin(a)) for a in [k * math.pi / 12 for k in range(24)]]
        polys.insert(0, thigh)
        return polys, (base, knee, ankle, toe)
    legcol = sp.get("legcol", col)
    hipP = (hip[0] + 0.01 * L, hip[1] + 0.02 * L)
    shP = tor[-2] if len(tor) > 2 else tor[-1]; shP = (shP[0] + 0.02 * L, shP[1] + 0.03 * L) if not sp.get("mammal") or sp.get("wing") else (shP[0] - 0.035 * L, shP[1] + 0.05 * L)
    if PR: hipP = B(PR["hl"]); shP = B(PR["fl"])
    legs = [("hind", hipP, math.pi, True), ("hind", hipP, 0.0, False)]
    if not sp["biped"]: legs = [("front", shP, 0.0, True), ("hind", hipP, math.pi, True), ("front", shP, math.pi, False), ("hind", hipP, 0.0, False)]
    drawn = {}
    for (kindleg, base, ph0, far) in legs:
        if not far: continue
        polys, js = leg(base, ph0 + (0.5 if kindleg == "front" else 0), sp["fleg"] if kindleg == "front" else sp["leg"], True, kindleg == "front")
        cv.piece(polys, shade(legcol if kindleg == "hind" or kind != "chicken" else legcol, 0.78))
    # arms (far)
    if sp.get("arm"):
        a1, a2, a3, r = [v * L for v in sp["arm"]]; sh = (tor[-1][0] - 0.03 * L, tor[-1][1] + 0.07 * L)
        def arm(off, c):
            e = add(sh, rot((a1, 0), 1.35 + G("arm") + 0.15 * math.sin(p + off))); h = add(e, rot((a2, 0), 0.2 + 0.7 * G("arm") + 0.15 * math.sin(p + off + 1))); f = add(h, rot((a3, 0), 0.9))
            cv.piece([taper(sh, e, r * 1.3, r), taper(e, h, r, r * 0.8), taper(h, f, r * 0.7, r * 0.3)], c)
            if sp.get("bigclaws"):
                dd = cv.draw(); cl = sp["bigclaws"] * L
                for j_, da in enumerate((-0.35, 0.0, 0.35)):
                    a0 = 1.0 + da * 0.6; cw_ = 0.012 * L * (1.6 if cl > 0.15 * L else 1.0); b0 = add(f, rot((cw_, 0), a0 + 1.57))
                    pts_ = [b0] + [add(f, rot((cl * u_, 0), a0 + 0.9 * u_ * u_)) for u_ in (0.35, 0.65, 0.9, 1.0)] + [add(f, rot((cl * 0.55, 0), a0 + 0.35)), add(f, rot((cw_, 0), a0 - 1.57))]
                    dd.polygon([cv.P(q) for q in pts_], fill=(246, 238, 216), outline=DK, width=4)
            if kind == "spino":
                dd = cv.draw(); k_ = add(f, rot((0.03 * L, 0), 1.6)); dd.polygon([cv.P(add(f, (-0.01 * L, 0))), cv.P(k_), cv.P(add(f, (0.01 * L, 0)))], fill=(250, 244, 226), outline=DK, width=3)
        arm(1.5, shade(col, 0.78))
    # body
    cv.piece([body] + xbody, col)
    d = cv.draw()
    # belly countershade (clipped to body)
    bl = [(c[0] - (top[i][0] - c[0]) * 0.05, c[1] - (top[i][1] - c[1]) * 0.05) for i, c in enumerate(centre)]
    bm = Image.new("L", cv.im.size, 0)
    if PR:
        up_ = [B((x, y + PR.get("bellyh", 0.07))) for x, y in PR["bot"]]
        ImageDraw.Draw(bm).polygon([cv.P(q) for q in PRbot + up_[::-1]], fill=255)
        if len(nbot) > 2: ImageDraw.Draw(bm).polygon([cv.P(q) for q in [(ncen[i][0] * 0.55 + nbot[i][0] * 0.45, ncen[i][1] * 0.55 + nbot[i][1] * 0.45) for i in range(len(ncen))] + nbot[::-1]], fill=255)
    else: ImageDraw.Draw(bm).polygon([cv.P(q) for q in bl[2:-1] + bot[2:-1][::-1]], fill=255)
    m = Image.new("L", cv.im.size, 0); ImageDraw.Draw(m).polygon([cv.P(q) for q in body], fill=255)
    bm = ImageChops.multiply(bm, erode(m, 6)).filter(ImageFilter.GaussianBlur(30 if PR else 14))
    bc_ = sp["belly"] if not PR else tuple(int(lerp(col[i], sp["belly"][i], 0.55)) for i in range(3))
    be = Image.new("RGBA", cv.im.size, bc_ + (255,)); be.putalpha(bm); cv.im.alpha_composite(be); d = cv.draw()
    # back stripes / scale spots (follow the spine -> move with joints)
    for i in range(6, len(centre) - 6, 4 if kind != "trex" else 3):
        c = centre[i]; tp = top[i]; vx, vy = tp[0] - c[0], tp[1] - c[1]
        if kind == "chicken": continue
        if sp.get("mammal"):
            if sp.get("fur"):
                for f_ in (0.85, 0.45, 0.05):
                    q = (c[0] + vx * f_, c[1] + vy * f_); d.arc([cv.P((q[0] - 0.03 * L, q[1] - 0.02 * L)), cv.P((q[0] + 0.03 * L, q[1] + 0.03 * L))], 20, 150, fill=sp["stripe"], width=max(3, int(0.005 * L * S)))
            continue
        if kind in ("trex", "edmonto", "tricera", "spino"):
            sa_ = (c[0] + vx * 0.98, c[1] + vy * 0.98); sb_ = (c[0] + vx * 0.25, c[1] + vy * 0.25); wv = max(6, int(0.13 * math.hypot(vx, vy) * S))
            d.line([cv.P(sa_), cv.P(sb_)], fill=sp["stripe"], width=wv)
        else:
            q = (c[0] + vx * 0.62, c[1] + vy * 0.62); r = max(4, 0.16 * math.hypot(vx, vy))
            d.ellipse([cv.P((q[0] - r * 1.3, q[1] - r)), cv.P((q[0] + r * 1.3, q[1] + r))], fill=sp["stripe"])
    if PR and sp.get("fur"):   # shaggy coat: hair strokes under the back line + ragged fringe hanging off the belly
        hc = shade(col, 0.72); wv = max(3, int(0.005 * L * S))
        for k in range(1, len(PRtop) - 1):
            a_, b_ = PRtop[k], PRtop[k + 1]
            for u in (0.2, 0.7):
                q = (lerp(a_[0], b_[0], u), lerp(a_[1], b_[1], u) + 0.035 * L)
                d.line([cv.P(q), cv.P((q[0] - 0.018 * L, q[1] + 0.045 * L))], fill=hc, width=wv)
        fr_ = []
        for k in range(len(PRbot) - 1):
            a_, b_ = PRbot[k], PRbot[k + 1]
            for u in (0.0, 0.25, 0.5, 0.75):
                q = (lerp(a_[0], b_[0], u), lerp(a_[1], b_[1], u)); j_ = len(fr_)
                fr_.append((q[0] - (0.012 * L if j_ % 2 else 0), q[1] + ((0.055 + 0.02 * ((j_ // 2) % 3 == 1)) if j_ % 2 else -0.004) * L))   # v18: longer shaggy skirt
        fr_ = fr_[2:-2]
        for k in range(1, len(fr_) - 1, 2):   # hanging hair tufts (outlined only on the hanging edge)
            a_, t_, b_ = fr_[k - 1], fr_[k], fr_[k + 1]
            d.polygon([cv.P((a_[0], a_[1] - 0.03 * L)), cv.P(t_), cv.P((b_[0], b_[1] - 0.03 * L))], fill=col)
            d.line([cv.P(a_), cv.P(t_), cv.P(b_)], fill=DK, width=max(4, int(0.004 * L * S)), joint="curve")
    elif sp.get("fur"):   # shaggy fur fringe under the belly / neck
        dk_ = shade(col, 0.82)
        i0 = len(centre) // 3; i1 = len(centre) - 3; rim = []
        for j_, i in enumerate(range(i0, i1)):
            q = bot[i]; c = centre[i]; vx, vy = q[0] - c[0], q[1] - c[1]; n = math.hypot(vx, vy) or 1
            k_ = (0.022 if j_ % 2 else -0.004) * L; rim.append((q[0] + vx / n * k_, q[1] + vy / n * k_))
        inner = [(centre[i][0] + (bot[i][0] - centre[i][0]) * 0.8, centre[i][1] + (bot[i][1] - centre[i][1]) * 0.8) for i in range(i0, i1)]
        if len(rim) > 3: cv.piece([rim + inner[::-1]], shade(col, 0.9), smooth=0); d = cv.draw()
    if sp.get("wing"):   # folded wing membrane from shoulder down the long fore limb
        if PR:
            cv.piece([[B((0.17, 0.16)), B((0.02, 0.06)), B((0.0, -0.02)), B((0.12, -0.04)), B((0.19, -0.06)), B((0.21, 0.06))]], sp["wing"], smooth=2); d = cv.draw()
        sh_ = tor[-1]; hp_ = tor[0]
        if not PR: cv.piece([[ (sh_[0] + 0.01 * L, sh_[1] + 0.0 * L), (hp_[0] + 0.0 * L, hp_[1] + 0.02 * L), (hp_[0] + 0.05 * L, hp_[1] + 0.08 * L), (sh_[0] + 0.03 * L, sh_[1] + 0.2 * L), (sh_[0] + 0.05 * L, sh_[1] + 0.06 * L)]], sp["wing"], smooth=1); d = cv.draw()
    if sp.get("osteo") or sp.get("osteo_rows"):   # armour: rows of bony studs/spikes following the spine
        big = bool(sp.get("osteo"))
        for i in range(5, len(centre) - (8 if big else 14), 3 if big else 4):
            c = centre[i]; tp = top[i]; vx, vy = tp[0] - c[0], tp[1] - c[1]; n = math.hypot(vx, vy) or 1; tx, ty = vx / n, vy / n
            for frac, sz in ((0.95, 1.0), (0.55, 0.7)) if big else ((0.9, 0.6),):
                q = (c[0] + vx * frac, c[1] + vy * frac); h_ = (0.035 if big else 0.016) * L * sz; w_ = h_ * 0.7
                d.polygon([cv.P((q[0] - ty * w_, q[1] + tx * w_)), cv.P((q[0] + tx * h_, q[1] + ty * h_)), cv.P((q[0] + ty * w_, q[1] - tx * w_))], fill=(222, 210, 180) if big else shade(col, 1.15), outline=DK, width=4)
        if big:   # flank spikes along the lower body edge
            for i in range(len(centre) // 2 - 6, len(centre) - 10, 4):
                q = bot[i]; d.polygon([cv.P((q[0] - 0.014 * L, q[1] - 0.01 * L)), cv.P((q[0] - 0.004 * L, q[1] + 0.04 * L)), cv.P((q[0] + 0.012 * L, q[1] - 0.01 * L))], fill=(222, 210, 180), outline=DK, width=4)
    if sp.get("club"):   # tail club
        q = centre[1]; r = 0.055 * L
        cv.piece([[(q[0] + r * 1.15 * math.cos(a), q[1] + r * 0.85 * math.sin(a)) for a in [k * math.pi / 10 for k in range(20)]]], shade(col, 1.08)); d = cv.draw()
        for k in range(3): a = k * 2.1 + 0.4; d.ellipse([cv.P((q[0] + r * 0.5 * math.cos(a) - 0.012 * L, q[1] + r * 0.4 * math.sin(a) - 0.01 * L)), cv.P((q[0] + r * 0.5 * math.cos(a) + 0.012 * L, q[1] + r * 0.4 * math.sin(a) + 0.01 * L))], fill=(222, 210, 180))
    if sp.get("thago"):   # tail spikes
        for k, (fi, ang) in enumerate(((5, -0.6), (7, -0.9), (5, 0.5), (8, 0.8))):
            c = centre[fi]; tp = top[fi] if ang < 0 else bot[fi]; vx, vy = tp[0] - c[0], tp[1] - c[1]; n = math.hypot(vx, vy) or 1
            dirx, diry = rot((vx / n, vy / n), 0.5 if ang < 0 else -0.5); h_ = 0.085 * L; w_ = 0.012 * L
            d.polygon([cv.P((tp[0] - diry * w_, tp[1] + dirx * w_)), cv.P((tp[0] + dirx * h_, tp[1] + diry * h_)), cv.P((tp[0] + diry * w_, tp[1] - dirx * w_))], fill=(240, 232, 210), outline=DK, width=4)
    if kind == "chicken":   # wing (folded, hinged at shoulder)
        w0 = tor[0]; w1 = add(w0, (0.16 * L, -0.02 * L)); fl = 0.08 * math.sin(p * 2) if moving else 0
        wing = [w1, add(w1, (0.02 * L, 0.08 * L)), add(w0, rot((-0.12 * L, 0.06 * L), fl)), add(w0, (-0.1 * L, -0.02 * L))]
        cv.piece([wing], (240, 234, 222)); d = cv.draw()
        for k in range(3): d.line([cv.P(add(w0, (-0.02 * L * k, 0.0))), cv.P(add(w0, (-0.09 * L - 0.01 * k * L, 0.05 * L)))], fill=(214, 204, 190), width=6)
    # near limbs
    for (kindleg, base, ph0, far) in legs:
        if far: continue
        polys, (b, kn, an, to) = leg(base, ph0 + (0.5 if kindleg == "front" else 0), sp["fleg"] if kindleg == "front" else sp["leg"], False, kindleg == "front")
        cv.piece(polys[1:], legcol, lw=3); cv.piece(polys[:1], legcol, edge=False, dark=0.96); d = cv.draw()
        if kindleg == "hind" and sp["biped"] and kind not in ("raptor", "dilo", "chicken"):   # v20: muscle lines on big theropod thighs, no polka dots
            d.arc([cv.P((b[0] - 0.06 * L, b[1] - 0.06 * L)), cv.P((b[0] + 0.05 * L, b[1] + 0.05 * L))], 120, 230, fill=shade(legcol, 0.72), width=max(4, int(0.004 * L * S)))
            d.arc([cv.P((b[0] - 0.035 * L, b[1] - 0.075 * L)), cv.P((b[0] + 0.07 * L, b[1] + 0.03 * L))], 300, 20, fill=shade(legcol, 0.78), width=max(3, int(0.003 * L * S)))
        elif sp.get("spot") and kindleg == "hind" and not sp.get("mammal"):
            for (dx, dy, rr) in ((-0.03, -0.03, 0.018), (0.02, -0.05, 0.014), (0.0, 0.01, 0.012), (0.04, -0.0, 0.01), (-0.05, 0.02, 0.01)):
                q = (b[0] + dx * L, b[1] + dy * L); r = rr * L; d.ellipse([cv.P((q[0] - r, q[1] - r)), cv.P((q[0] + r, q[1] + r))], fill=sp["spot"])
        for j in (kn, an):   # joint creases
            d.arc([cv.P((j[0] - 0.02 * L, j[1] - 0.02 * L)), cv.P((j[0] + 0.02 * L, j[1] + 0.02 * L))], 200, 320, fill=shade(legcol, 0.6), width=5)
        if sp.get("front_claws") and kindleg == "front":   # huge curved claws (walks on its knuckles)
            for j_ in range(3):
                c0 = (an[0] + (0.01 + j_ * 0.012) * L, an[1] + 0.01 * L); pts_ = [c0, (c0[0] + 0.05 * L, c0[1] + 0.01 * L), (c0[0] + 0.07 * L, c0[1] - 0.03 * L), (c0[0] + 0.045 * L, c0[1] - 0.004 * L), (c0[0], c0[1] - 0.01 * L)]
                d.polygon([cv.P(q) for q in pts_], fill=(240, 232, 214), outline=DK, width=4)
        if sp.get("thumb") and kindleg == "front":   # thumb spike
            c0 = (an[0] + 0.02 * L, an[1] - 0.005 * L); d.polygon([cv.P((c0[0] - 0.012 * L, c0[1])), cv.P((c0[0] + 0.035 * L, c0[1] - 0.035 * L)), cv.P((c0[0] + 0.012 * L, c0[1] + 0.012 * L))], fill=(246, 238, 216), outline=DK, width=4)
        if sp.get("sickle") and kindleg == "hind":   # raised killing claw
            c0 = (an[0] + 0.03 * L, an[1] + 0.02 * L); d.line([cv.P(c0), cv.P((c0[0] + 0.02 * L, c0[1] - 0.035 * L)), cv.P((c0[0] + 0.05 * L, c0[1] - 0.025 * L))], fill=DK, width=16, joint="curve")
            d.line([cv.P(c0), cv.P((c0[0] + 0.02 * L, c0[1] - 0.035 * L)), cv.P((c0[0] + 0.05 * L, c0[1] - 0.025 * L))], fill=(250, 244, 226), width=9, joint="curve")
        if kind != "chicken" and kindleg == "hind" and not sp.get("mammal"):   # claws
            for da in (-0.25, 0.0, 0.25):
                tip = (to[0] + 0.065 * L * math.cos(da * 0.6) * (0.8 if da else 1.0) + 0.012 * L, to[1] - 0.002 * L)
                d.polygon([cv.P((tip[0] - 0.012 * L, tip[1] - 0.01 * L)), cv.P((tip[0] + 0.012 * L, tip[1])), cv.P((tip[0] - 0.01 * L, tip[1] + 0.004 * L))], fill=(250, 244, 226))
    if sp.get("arm"):
        arm(0.0, col); d = cv.draw()
    # ---- head (hinged at neck end)
    hs = sp["hs"] * L; skull, jaw, hinge, eye, extra = head_shape(sp["head"], mouth)
    hp = neck[-1]; ang = na + 0.15 + G("head")
    def T(q): return add(hp, rot((q[0] * hs, q[1] * hs), ang))
    g = mouth * (0.5 if sp["head"] == "trex" else 0.65 if sp["head"] == "duck" else 0.45)
    def J(q): return T(add(hinge, rot((q[0] - hinge[0], q[1] - hinge[1]), g)))
    jawp = [J(q) for q in jaw]
    if mouth > 0.05:   # mouth interior: dark throat wedge + tongue lying in the lower jaw
        if sp["head"] == "trex":
            mu, ml = T((0.45, 0.06)), J((0.45, 0.05)); mid = ((mu[0] + ml[0]) / 2, (mu[1] + ml[1]) / 2)   # throat depth: open notch at the front
            d.polygon([cv.P(T(q)) for q in ((0.0, 0.0), (0.5, 0.0), (0.97, 0.02))] + [cv.P(mid)] + [cv.P(J(q)) for q in ((0.95, 0.05), (0.4, 0.06), (0.05, 0.08))], fill=(74, 40, 40))
            d.line([cv.P(T(q)) for q in ((0.1, 0.06), (0.5, 0.055), (0.97, 0.05))], fill=(196, 120, 116), width=int(0.035 * hs * S))   # upper gum
            d.line([cv.P(J(q)) for q in ((0.12, 0.05), (0.5, 0.035), (0.95, 0.03))], fill=(196, 120, 116), width=int(0.035 * hs * S))  # lower gum
            d.polygon([cv.P(J(q)) for q in ((0.1, 0.04), (0.3, 0.0), (0.48, 0.01), (0.5, 0.05), (0.12, 0.07))], fill=(176, 96, 100))   # short tongue at the back
        else:
            jx_ = min(0.95, max(q[0] for q in jaw) - 0.03); d.polygon([cv.P(T(hinge)), cv.P(T((jx_, 0.05))), cv.P(J((jx_, 0.06)))], fill=(74, 40, 40))
    cv.piece([jawp], shade(col, 0.95), smooth=1 if sp["head"] == "trex" else 2); d = cv.draw()
    if extra[0] == "spikefrill":
        fr_ = [T((-0.05 + 0.7 * math.cos(a), -0.35 - 0.7 * math.sin(a))) for a in [math.pi * (0.15 + 0.9 * k / 16) for k in range(17)]] + [T((-0.3, 0.05)), T((0.2, -0.1))]
        for k in range(1, 16, 3):
            a = math.pi * (0.15 + 0.9 * k / 16); b1 = T((-0.05 + 0.62 * math.cos(a), -0.35 - 0.62 * math.sin(a))); b2 = T((-0.05 + 1.15 * math.cos(a), -0.35 - 1.15 * math.sin(a)))
            vx, vy = b2[0] - b1[0], b2[1] - b1[1]; n = math.hypot(vx, vy) or 1; px, py = -vy / n * 0.06 * hs, vx / n * 0.06 * hs
            d.polygon([cv.P((b1[0] + px, b1[1] + py)), cv.P(b2), cv.P((b1[0] - px, b1[1] - py))], fill=(244, 232, 206), outline=DK, width=5)
        cv.piece([fr_], shade(col, 1.05)); d = cv.draw()
    if extra[0] == "horns":   # frill: a solid shield sweeping up and back from the rear of the skull, scalloped edge
        cx_, cy_, rx_, ry_ = -0.1, -0.42, 0.52, 0.62
        angs = [math.pi * (0.32 + 0.86 * k / 20) for k in range(21)]
        rim_ = [(cx_ + rx_ * math.cos(a), cy_ - ry_ * math.sin(a)) for a in angs]
        fr_ = [T(q) for q in rim_] + [T((-0.3, 0.06)), T((0.05, -0.05)), T((0.3, -0.3))]
        cv.piece([fr_], shade(col, 1.08)); d = cv.draw()
        inner = [T((cx_ + rx_ * 0.72 * math.cos(a), cy_ + 0.05 - ry_ * 0.72 * math.sin(a))) for a in angs[2:-2]]
        d.line([cv.P(q) for q in inner], fill=shade(col, 0.82), width=max(3, int(0.03 * hs * S)))
        for k in range(1, 20, 2):
            a = angs[k]; q = T((cx_ + (rx_ + 0.02) * math.cos(a), cy_ - (ry_ + 0.02) * math.sin(a))); r = 0.04 * hs
            d.polygon([cv.P((q[0] - r, q[1] + r * 0.4)), cv.P((q[0], q[1] - r * 1.1)), cv.P((q[0] + r, q[1] + r * 0.4))], fill=(236, 222, 190), outline=DK, width=3)
    cv.piece([[T(q) for q in skull]], col, smooth=1 if sp["head"] == "trex" else 2); d = cv.draw()
    hd = sp.get("hdeco", [])
    def cone(b1, tip, w, col_=(250, 244, 226)):
        b1, b2 = T(b1), T(tip); vx, vy = b2[0] - b1[0], b2[1] - b1[1]; n = math.hypot(vx, vy) or 1; px, py = -vy / n * w * hs, vx / n * w * hs
        d.polygon([cv.P((b1[0] + px, b1[1] + py)), cv.P(b2), cv.P((b1[0] - px, b1[1] - py))], fill=col_, outline=DK, width=5)
    if "boss" in hd:   # v20: rough horn-like boss behind / above the eye (T. rex postorbital)
        cv.piece([[T(q) for q in ((0.3, -0.56), (0.4, -0.66), (0.5, -0.64), (0.58, -0.56))]], shade(col, 1.12), smooth=1); d = cv.draw()
    if "jawmuscle" in hd:   # v20: bulging jaw muscle behind the eye
        d.arc([cv.P(T((-0.12, -0.4))), cv.P(T((0.24, -0.02)))], 250, 20, fill=shade(col, 0.72), width=max(4, int(0.03 * hs * S)))
    if "ridge" in hd:
        for k in range(6): q = T((0.32 + k * 0.13, -0.41 + 0.015 * k * k * 0.3)); r = 0.035 * hs; d.ellipse([cv.P((q[0] - r, q[1] - r)), cv.P((q[0] + r, q[1] + r))], fill=shade(col, 1.15), outline=DK, width=4)
    if "brow_horns" in hd:
        cone((0.26, -0.46), (0.05, -0.78), 0.09, shade(col, 1.05)); cone((0.36, -0.46), (0.3, -0.76), 0.08, shade(col, 1.15))
    if "lacrimal" in hd:
        cone((0.3, -0.4), (0.36, -0.58), 0.07, shade(col, 1.1))
        for k in range(4): q = T((0.55 + k * 0.12, -0.36 + k * 0.02)); r = 0.025 * hs; d.ellipse([cv.P((q[0] - r, q[1] - r)), cv.P((q[0] + r, q[1] + r))], fill=shade(col, 1.15), outline=DK, width=3)
    if sp.get("dome"):
        cv.piece([[T(q) for q in ((-0.14, -0.5), (0.08, -0.72), (0.38, -0.7), (0.52, -0.48), (0.2, -0.42))]], sp["dome"], smooth=2); d = cv.draw()
    if "dome_knobs" in hd:
        for q0 in ((-0.2, -0.4), (-0.14, -0.55), (-0.04, -0.66), (0.6, -0.38), (0.7, -0.24)):
            q = T(q0); r = 0.04 * hs; d.ellipse([cv.P((q[0] - r, q[1] - r)), cv.P((q[0] + r, q[1] + r))], fill=(226, 214, 186), outline=DK, width=4)
    if "corner_horns" in hd:
        cone((-0.08, -0.26), (-0.32, -0.5), 0.09); cone((-0.06, 0.1), (-0.3, 0.3), 0.08)
    if "ear_round" in hd:
        q = T((-0.08, -0.32)); r = 0.24 * hs; d.ellipse([cv.P((q[0] - r * 0.8, q[1] - r)), cv.P((q[0] + r * 0.8, q[1] + r))], fill=shade(col, 0.9), outline=DK, width=5)
    if "ear_tri" in hd:
        d.polygon([cv.P(T(q)) for q in ((-0.12, -0.3), (-0.06, -0.62), (0.12, -0.36))], fill=shade(col, 0.92), outline=DK, width=5)
    if "trunk" in hd:
        bz = lambda a, b, c, e, u: tuple((1 - u) ** 3 * a[i] + 3 * (1 - u) ** 2 * u * b[i] + 3 * (1 - u) * u * u * c[i] + u ** 3 * e[i] for i in range(2))
        pts_ = [T(bz((0.6, -0.02), (1.05, 0.2), (1.0, 1.0), (1.22, 1.15), k / 14)) for k in range(15)]
        d.line([cv.P(q) for q in pts_], fill=DK, width=int(0.24 * hs * S) + 10, joint="curve"); d.line([cv.P(q) for q in pts_], fill=col, width=int(0.24 * hs * S), joint="curve")
        for k_ in range(3, 13, 2): q = pts_[k_]; d.line([cv.P((q[0] - 0.07 * hs, q[1])), cv.P((q[0] + 0.07 * hs, q[1]))], fill=shade(col, 0.72), width=4)
    if "tusks" in hd:
        bz = lambda a, b, c, e, u: tuple((1 - u) ** 3 * a[i] + 3 * (1 - u) ** 2 * u * b[i] + 3 * (1 - u) * u * u * c[i] + u ** 3 * e[i] for i in range(2))
        pts_ = [T(bz((0.42, 0.18), (0.7, 0.9), (1.35, 0.85), (1.5, 0.3), k / 16)) for k in range(17)]
        d.line([cv.P(q) for q in pts_], fill=DK, width=int(0.13 * hs * S) + 10, joint="curve"); d.line([cv.P(q) for q in pts_], fill=(246, 238, 214), width=int(0.13 * hs * S), joint="curve")
    if "sabers" in hd:
        for off, sc_ in ((0.0, 1.0),):
            d.polygon([cv.P(T(q)) for q in ((0.56 + off, 0.06), (0.66 + off, 0.06), (0.6 + off, 0.62 * sc_), (0.55 + off, 0.5 * sc_))], fill=(250, 244, 226), outline=DK, width=5)
    if "rhino_horns" in hd:
        cone((0.92, -0.14), (1.12, -0.9), 0.13, (214, 196, 160)); cone((0.66, -0.28), (0.72, -0.62), 0.08, (214, 196, 160))
    if "ptero_crest" in hd:
        d.polygon([cv.P(T(q)) for q in ((0.1, -0.24), (-0.42, -0.62), (-0.3, -0.4), (0.35, -0.2))], fill=(206, 96, 66), outline=DK, width=5)
    if "tube_crest" in hd:
        cv.piece([[T(q) for q in ((0.15, -0.3), (-0.2, -0.62), (-0.62, -0.86), (-0.74, -0.8), (-0.58, -0.66), (-0.14, -0.4), (0.25, -0.2))]], sp.get("crest", shade(col, 1.1)), smooth=2); d = cv.draw()
    if "twin_crest" in hd:
        for off in (0.12, 0.0):
            cv.piece([[T(q) for q in ((0.1 + off, -0.3), (0.16 + off, -0.82), (0.32 + off, -0.84), (0.64 + off, -0.4))]], shade(sp.get("crest", col), 1.0 - off * 2.5), smooth=2); d = cv.draw()
            for k_ in range(3): d.line([cv.P(T((0.2 + off + k_ * 0.16, -0.36))), cv.P(T((0.22 + off + k_ * 0.14, -0.66 + k_ * 0.1)))], fill=(250, 220, 190), width=6)
    if "feathers" in hd:
        for k in range(5): a_ = T((-0.2 - k * 0.05, -0.22 + k * 0.07)); b_ = T((-0.42 - k * 0.04, -0.38 + k * 0.12)); d.line([cv.P(a_), cv.P(b_)], fill=shade(col, 0.75), width=9)
    if extra[0] == "beak" and extra[2] > 0:
        d.polygon([cv.P(T(q)) for q in [(extra[1], -0.14), (extra[2], -0.04), (extra[2] - 0.02, 0.07), (extra[1], 0.07)]], fill=(70, 62, 54), outline=DK, width=4)
    if extra[0] == "teeth" and mouth < 0.1:
        d.line([cv.P(T(q)) for q in ((0.05, -0.02), (0.15, 0.03), (0.5, 0.04), (0.98, 0.02))], fill=shade(col, 0.55) if FLAT else DK, width=7, joint="curve")
    if extra[0] == "teeth":
        for k in range(9):
            u = extra[1] + (extra[2] - extra[1] - 0.04) * k / 8; th_ = 0.06 + 0.04 * mouth; a = T((u, 0.04)); b2 = T((u + 0.02, 0.04 + th_)); c2 = T((u + 0.04, 0.04))
            d.polygon([cv.P(a), cv.P(b2), cv.P(c2)], fill=(252, 250, 236), outline=None if FLAT else DK)
            if mouth > 0.2:
                a = J((u, 0.04)); b2 = J((u + 0.02, -0.03)); c2 = J((u + 0.04, 0.04)); d.polygon([cv.P(a), cv.P(b2), cv.P(c2)], fill=(252, 250, 236), outline=None if FLAT else DK)
        q = T((min(0.9, max(p_[0] for p_ in skull) - 0.07), -0.12)); d.ellipse([cv.P((q[0] - 0.025 * hs, q[1] - 0.02 * hs)), cv.P((q[0] + 0.025 * hs, q[1] + 0.02 * hs))], fill=DK)   # nostril
    if extra[0] == "bill":
        d.polygon([cv.P(T(q)) for q in [(0.62, -0.18), (1.06, -0.04), (1.06, 0.06), (0.62, 0.08)]], fill=(244, 220, 150), outline=DK)
    if extra[0] == "spikefrill":
        b1, b2 = T((0.75, -0.2)), T((1.05, -0.75)); vx, vy = b2[0] - b1[0], b2[1] - b1[1]; n = math.hypot(vx, vy) or 1; px, py = -vy / n * 0.08 * hs, vx / n * 0.08 * hs
        d.polygon([cv.P((b1[0] + px, b1[1] + py)), cv.P(b2), cv.P((b1[0] - px, b1[1] - py))], fill=(250, 244, 226), outline=DK, width=5)
    if extra[0] == "horns":   # two long brow horns above the eye (far one a touch behind), short nose horn
        for base_, tip_ in (((0.4, -0.33), (0.9, -0.98)), ((0.5, -0.31), (1.08, -0.86)), ((0.86, -0.17), (0.97, -0.38))):
            b1, b2 = T(base_), T(tip_); vx, vy = b2[0] - b1[0], b2[1] - b1[1]; n = math.hypot(vx, vy) or 1; px, py = -vy / n * 0.06 * hs, vx / n * 0.06 * hs
            d.polygon([cv.P((b1[0] + px, b1[1] + py)), cv.P(b2), cv.P((b1[0] - px, b1[1] - py))], fill=(250, 244, 226), outline=DK, width=5)
    if extra[0] == "comb":
        for k in range(4):
            q = T((0.12 + k * 0.13, -0.42 + 0.02 * k)); r = 0.08 * hs
            d.ellipse([cv.P((q[0] - r, q[1] - r * 1.4)), cv.P((q[0] + r, q[1] + r * 0.5))], fill=(232, 60, 60), outline=DK, width=4)
        q = T((0.6, 0.18)); d.ellipse([cv.P((q[0] - 0.07 * hs, q[1] - 0.04 * hs)), cv.P((q[0] + 0.05 * hs, q[1] + 0.16 * hs))], fill=(232, 60, 60), outline=DK, width=4)
        d.polygon([cv.P(T(q)) for q in [(0.58, -0.12), (1.0, 0.03), (0.6, 0.06)]], fill=(250, 190, 60), outline=DK, width=4)
    # eye (blinks)
    e = T(eye); r = 0.075 * hs if sp["head"] != "chick" else 0.1 * hs; blink = (t % 3.7) < 0.12
    if FLAT:
        q = r * 0.5; d.ellipse([cv.P((e[0] - q, e[1] - q * (0.25 if blink else 1))), cv.P((e[0] + q, e[1] + q * (0.25 if blink else 1)))], fill=(60, 44, 36))
        d.line([cv.P((e[0] - r * 1.3, e[1] - r * 1.2)), cv.P((e[0] + r * 1.2, e[1] - r * 1.0))], fill=shade(col, 0.7), width=9)
    elif blink: d.line([cv.P((e[0] - r, e[1])), cv.P((e[0] + r, e[1]))], fill=DK, width=7)
    else:
        d.ellipse([cv.P((e[0] - r, e[1] - r)), cv.P((e[0] + r, e[1] + r))], fill=(255, 250, 230), outline=DK, width=5)
        q = r * 0.55; ex = e[0] + r * 0.25; d.ellipse([cv.P((ex - q, e[1] - q)), cv.P((ex + q, e[1] + q))], fill=DK)
        d.ellipse([cv.P((ex - q * 0.2, e[1] - q * 0.7)), cv.P((ex + q * 0.4, e[1] - q * 0.1))], fill=(255, 255, 255))
        if sp["head"] in ("trex", "spino") or "angry" in sp.get("hdeco", []): d.line([cv.P((e[0] - r * 1.4, e[1] - r * 1.3)), cv.P((e[0] + r * 1.3, e[1] - r * 1.0))], fill=DK, width=8)
    if HIRES:
        big = cv.im; a = big.getchannel("A").filter(ImageFilter.GaussianBlur(6)).point(lambda v: 255 if v > 20 else 0)
        o = Image.new("RGBA", big.size, DK + (255,)); o.putalpha(a); o.alpha_composite(big); return o
    small = cv.im.resize((W0, H0), Image.LANCZOS)
    if FLAT: return small
    a = small.getchannel("A").filter(ImageFilter.GaussianBlur(3)).point(lambda v: 255 if v > 20 else 0)
    o = Image.new("RGBA", (W0, H0), DK + (255,)); o.putalpha(a); o.alpha_composite(small)
    return o

if __name__ == "__main__":
    out = Image.new("RGB", (W0 * 2, H0 * 2), (220, 236, 246))
    for k, (kd, g, m) in enumerate((("trex", "walk", 0.0), ("trex", "roar", 1.0), ("edmonto", "graze", 0.3), ("tricera", "walk", 0.0))):
        im = beast(kd, 0.35, g, m); out.paste(im, ((k % 2) * W0, (k // 2) * H0), im)
    out.resize((1600, 1000)).save("/tmp/rig.jpg", quality=85)
    o2 = Image.new("RGB", (W0 * 4, H0), (220, 236, 246))
    for k in range(4):
        im = beast("trex", k * 0.31, "walk"); o2.paste(im, (k * W0, 0), im)
    o2.resize((1600, 250)).save("/tmp/walk.jpg", quality=85)
    im = beast("chicken", 0.2, "walk"); o3 = Image.new("RGB", (W0, H0), (220, 236, 246)); o3.paste(im, (0, 0), im); o3.resize((800, 500)).save("/tmp/chick.jpg")

def chicken(t, gait="walk", peck=0.0):
    """realistic-ish hen (Rhode-Island red): jointed legs (IK), layered feathers, fan tail, serrated comb."""
    cv = Canvas(); L = 700; p = 2 * math.pi * 1.4 * t; moving = gait == "walk"
    cx, cy = W0 * 0.5, GROUND - 0.55 * L + (0.015 * L * math.cos(2 * p) if moving else 0)
    def egg(c, rx, ry, a, n=40): return [add(c, rot((rx * math.cos(k * 2 * math.pi / n) * (1 + 0.12 * math.cos(k * 2 * math.pi / n)), ry * math.sin(k * 2 * math.pi / n)), a)) for k in range(n)]
    body, dark, light = (168, 84, 44), (110, 50, 28), (204, 118, 64)
    legc = (226, 182, 70)
    def leg(ph, far):
        hip = (cx + 0.02 * L, cy + 0.12 * L); fx = cx + 0.05 * L + (0.12 * L * math.cos(ph) if moving else (0.04 * L if far else -0.02 * L))
        fy = GROUND - (0.06 * L * max(0, math.sin(ph)) if moving else 0)
        ankle = (fx - 0.03 * L, fy - 0.17 * L); knee = ik(hip, ankle, 0.17 * L, 0.2 * L, 1)
        toe = (fx, fy); polys = [taper(knee, ankle, 0.018 * L, 0.014 * L), taper(ankle, toe, 0.014 * L, 0.012 * L)]
        for da in (-0.1, 0.0, 0.1): polys.append(taper(toe, (toe[0] + 0.075 * L * math.cos(da), toe[1] + 0.075 * L * da * 0.2), 0.011 * L, 0.005 * L))
        polys.append(taper(toe, (toe[0] - 0.05 * L, toe[1]), 0.01 * L, 0.005 * L))
        cv.piece(polys, shade(legc, 0.8) if far else legc, lw=4)
        d = cv.draw()
        for k in range(5):   # scales on the shank
            q = (lerp(knee[0], ankle[0], 0.5 + k * 0.1) + lerp(0, toe[0] - ankle[0], k * 0.2), lerp(knee[1], ankle[1], 0.5 + k * 0.1) + lerp(0, toe[1] - ankle[1], k * 0.2))
            d.line([cv.P((q[0] - 0.01 * L, q[1])), cv.P((q[0] + 0.01 * L, q[1]))], fill=shade(legc, 0.7), width=3)
        cv.piece([taper(hip, knee, 0.05 * L, 0.03 * L)], shade(body, 0.85 if far else 1.0))   # feathered thigh
    leg(p + math.pi, True)
    # tail: fan of sickle feathers
    for k in range(6):
        a = -1.9 + k * 0.17; base = (cx - 0.24 * L, cy - 0.08 * L); tip = add(base, rot((0.0, -0.3 * L), a + 1.57))
        cv.piece([taper(base, tip, 0.05 * L, 0.02 * L)], (60, 34, 22) if k % 2 else (90, 48, 26), lw=4)
    cv.piece([egg((cx, cy), 0.3 * L, 0.21 * L, -0.15)], body)
    d = cv.draw()
    for r_ in range(4):   # layered breast/back feathers
        for k in range(7):
            x = cx - 0.18 * L + k * 0.06 * L + (r_ % 2) * 0.03 * L; y = cy - 0.1 * L + r_ * 0.06 * L
            d.arc([cv.P((x - 0.035 * L, y - 0.03 * L)), cv.P((x + 0.035 * L, y + 0.03 * L))], 20, 160, fill=dark, width=5)
    bobx = 0.04 * L * math.sin(2 * p) if moving else 0.0
    nb = (cx + 0.2 * L, cy - 0.1 * L); hd = (cx + 0.3 * L + bobx + 0.12 * L * peck, cy - 0.38 * L + 0.3 * L * peck)
    cv.piece([taper(nb, hd, 0.11 * L, 0.07 * L), egg(hd, 0.09 * L, 0.08 * L, 0.0, 24)], light)
    d = cv.draw()
    for k in range(4):   # neck hackle feathers
        y = lerp(nb[1], hd[1], 0.2 + k * 0.18); x = lerp(nb[0], hd[0], 0.2 + k * 0.18)
        d.arc([cv.P((x - 0.05 * L, y - 0.03 * L)), cv.P((x + 0.05 * L, y + 0.03 * L))], 30, 150, fill=body, width=5)
    comb = [(hd[0] - 0.07 * L, hd[1] - 0.07 * L)]
    for k in range(5): comb += [(hd[0] - 0.06 * L + k * 0.03 * L, hd[1] - 0.14 * L + (k % 2) * 0.0), (hd[0] - 0.045 * L + k * 0.03 * L, hd[1] - 0.095 * L)]
    comb += [(hd[0] + 0.08 * L, hd[1] - 0.06 * L)]
    d.polygon([cv.P(q) for q in comb], fill=(206, 40, 44), outline=DK, width=4)
    bk = [(hd[0] + 0.075 * L, hd[1] - 0.025 * L), (hd[0] + 0.15 * L, hd[1] + 0.01 * L), (hd[0] + 0.075 * L, hd[1] + 0.03 * L)]
    d.polygon([cv.P(q) for q in bk], fill=(232, 196, 110), outline=DK, width=4)
    q = (hd[0] + 0.065 * L, hd[1] + 0.075 * L); d.ellipse([cv.P((q[0] - 0.022 * L, q[1] - 0.03 * L)), cv.P((q[0] + 0.022 * L, q[1] + 0.035 * L))], fill=(206, 40, 44), outline=DK, width=4)
    q = (hd[0] + 0.0, hd[1] + 0.02 * L); d.ellipse([cv.P((q[0] - 0.018 * L, q[1] - 0.015 * L)), cv.P((q[0] + 0.018 * L, q[1] + 0.015 * L))], fill=(240, 220, 200))   # ear lobe
    e = (hd[0] + 0.03 * L, hd[1] - 0.02 * L); r = 0.018 * L
    if (t % 3.1) < 0.12: d.line([cv.P((e[0] - r, e[1])), cv.P((e[0] + r, e[1]))], fill=DK, width=6)
    else:
        d.ellipse([cv.P((e[0] - r, e[1] - r)), cv.P((e[0] + r, e[1] + r))], fill=(232, 150, 40), outline=DK, width=3)
        d.ellipse([cv.P((e[0] - r * 0.5, e[1] - r * 0.5)), cv.P((e[0] + r * 0.5, e[1] + r * 0.5))], fill=DK)
    sh = (cx + 0.08 * L, cy - 0.06 * L); fl = 0.12 * math.sin(4 * p) if moving else 0
    wing = [sh, add(sh, rot((-0.3 * L, 0.04 * L), fl)), add(sh, rot((-0.26 * L, 0.13 * L), fl)), add(sh, (-0.05 * L, 0.12 * L))]
    cv.piece([wing], shade(body, 0.9)); d = cv.draw()
    for k in range(4): d.line([cv.P(add(sh, rot((-0.07 * L - k * 0.055 * L, 0.05 * L), fl))), cv.P(add(sh, rot((-0.12 * L - k * 0.05 * L, 0.12 * L), fl)))], fill=dark, width=6)
    leg(p, False)
    if HIRES:
        big = cv.im; a = big.getchannel("A").filter(ImageFilter.GaussianBlur(6)).point(lambda v: 255 if v > 20 else 0)
        o = Image.new("RGBA", big.size, DK + (255,)); o.putalpha(a); o.alpha_composite(big); return o
    small = cv.im.resize((W0, H0), Image.LANCZOS)
    if FLAT: return small
    a = small.getchannel("A").filter(ImageFilter.GaussianBlur(3)).point(lambda v: 255 if v > 20 else 0)
    o = Image.new("RGBA", (W0, H0), DK + (255,)); o.putalpha(a); o.alpha_composite(small)
    return o

# sea creatures (swimming rig) register themselves into SP
import sea as _sea
_sea.register()
