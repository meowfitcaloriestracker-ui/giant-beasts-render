"""Swimming rig for prehistoric sea creatures (same canvas / anchor conventions as dino45.beast).

A body is described along its length u (0 = tail tip, 1 = snout) by half-thickness tables above/below
a centre line. The centre line undulates (swim wave), pitches with P["pitch"], and the long-necked
species bend the neck with P["neck"]. Fins are polygons in the body's local frame (s along body, n up),
attached at a u position and rotated with the local tangent. The lower jaw is a separate piece hinged
at u_hinge and opened by `mouth`.
"""
import math, random
from PIL import Image, ImageDraw
import dino45 as DN
from dino45 import Canvas, shade, DK, W0, H0, GROUND, S

def interp(tab, u):
    """Catmull-Rom through the table -> smooth, rounded body outline"""
    if u <= tab[0][0]: return tab[0][1]
    for i in range(len(tab) - 1):
        u0, v1 = tab[i]; u1, v2 = tab[i + 1]
        if u <= u1:
            v0 = tab[i - 1][1] if i > 0 else v1; v3 = tab[i + 2][1] if i + 2 < len(tab) else v2
            f = (u - u0) / max(1e-6, u1 - u0)
            r = 0.5 * ((2 * v1) + (-v0 + v2) * f + (2 * v0 - 5 * v1 + 4 * v2 - v3) * f * f + (-v0 + 3 * v1 - 3 * v2 + v3) * f ** 3)
            return max(0.0, r)
    return tab[-1][1]

# ------------------------------------------------------------------ species
# top/bot: half thickness (in L) along u ; jaw: (u_hinge, mouth line offset at hinge, at tip, tip u) ; eye: (u, n)
SEA = {
 "megalodon": dict(L=1250, hip_h=0.38, col=(98, 116, 132), belly=(226, 230, 228), name="เมกาโลดอน",
     top=[(0, 0.004), (0.06, 0.018), (0.2, 0.05), (0.42, 0.105), (0.6, 0.125), (0.78, 0.11), (0.9, 0.08), (0.97, 0.045), (1.0, 0.0)],
     bot=[(0, 0.004), (0.06, 0.016), (0.2, 0.045), (0.42, 0.095), (0.6, 0.115), (0.76, 0.1), (0.86, 0.07), (0.94, 0.04), (1.0, 0.0)],
     jaw=(0.74, -0.01, 0.02, 0.93), teeth="shark", eye=(0.89, 0.035), gills=(0.70, 0.78, 5),
     fins=[("caudal_shark", 0.03, 1.0), ("dorsal", 0.56, 1.0), ("pectoral", 0.68, 1.15), ("pelvic", 0.34, 0.6), ("dorsal2", 0.17, 0.35), ("anal", 0.16, 0.35)], wave=0.022),
 "mosasaurus": dict(L=1350, hip_h=0.36, col=(78, 96, 92), belly=(214, 210, 186), name="โมซาซอรัส",
     top=[(0, 0.004), (0.05, 0.012), (0.25, 0.03), (0.45, 0.06), (0.62, 0.07), (0.8, 0.055), (0.86, 0.05), (0.93, 0.04), (1.0, 0.012)],
     bot=[(0, 0.004), (0.05, 0.01), (0.25, 0.028), (0.45, 0.058), (0.62, 0.068), (0.8, 0.05), (0.86, 0.04), (0.95, 0.025), (1.0, 0.008)],
     jaw=(0.86, 0.0, 0.0, 0.995), teeth="cone", eye=(0.9, 0.028), scales=True,
     fins=[("caudal_mosa", 0.02, 1.0), ("paddle", 0.7, 1.0), ("paddle", 0.43, 0.8)], wave=0.03),
 "liopleurodon": dict(L=1050, hip_h=0.38, col=(86, 92, 110), belly=(210, 210, 206), name="ไลโอพลูโรดอน",
     top=[(0, 0.004), (0.08, 0.02), (0.25, 0.07), (0.45, 0.115), (0.62, 0.105), (0.72, 0.075), (0.78, 0.07), (0.9, 0.055), (1.0, 0.015)],
     bot=[(0, 0.004), (0.08, 0.02), (0.25, 0.065), (0.45, 0.11), (0.62, 0.1), (0.72, 0.07), (0.78, 0.06), (0.92, 0.035), (1.0, 0.01)],
     jaw=(0.75, 0.0, 0.0, 0.995), teeth="cone", eye=(0.82, 0.04),
     fins=[("tailfin_small", 0.02, 1.0), ("flipper", 0.58, 1.25), ("flipper", 0.3, 1.1)], wave=0.015),
 "elasmo":   dict(L=1350, hip_h=0.34, col=(104, 120, 112), belly=(214, 214, 196), name="อีลาสโมซอรัส",
     top=[(0, 0.004), (0.06, 0.012), (0.14, 0.04), (0.26, 0.085), (0.38, 0.08), (0.45, 0.04), (0.5, 0.024), (0.9, 0.018), (0.93, 0.022), (0.97, 0.02), (1.0, 0.006)],
     bot=[(0, 0.004), (0.06, 0.012), (0.14, 0.04), (0.26, 0.085), (0.38, 0.075), (0.45, 0.035), (0.5, 0.022), (0.9, 0.016), (0.93, 0.018), (0.97, 0.012), (1.0, 0.004)],
     jaw=(0.94, 0.0, 0.0, 0.998), teeth="cone_small", eye=(0.95, 0.012), neck=(0.44, 0.92),
     fins=[("flipper", 0.34, 1.0), ("flipper", 0.17, 0.85)], wave=0.012),
 "dunkleosteus": dict(L=820, hip_h=0.38, col=(96, 104, 92), belly=(206, 204, 184), name="ดังเคิลออสเตียส",
     top=[(0, 0.004), (0.08, 0.025), (0.2, 0.06), (0.4, 0.12), (0.6, 0.16), (0.78, 0.16), (0.9, 0.13), (0.97, 0.08), (1.0, 0.03)],
     bot=[(0, 0.004), (0.08, 0.022), (0.2, 0.055), (0.4, 0.11), (0.6, 0.14), (0.72, 0.13), (0.86, 0.1), (0.96, 0.05), (1.0, 0.0)],
     jaw=(0.74, -0.02, -0.01, 0.99), teeth="blades", eye=(0.88, 0.07), armor=(0.58, 1.0),
     fins=[("caudal_shark", 0.03, 0.9), ("dorsal", 0.45, 0.8), ("pectoral", 0.56, 0.9), ("anal", 0.2, 0.4)], wave=0.02),
 "livyatan": dict(L=1400, hip_h=0.38, col=(74, 80, 92), belly=(150, 156, 166), name="ลิเวียทัน",
     top=[(0, 0.004), (0.05, 0.012), (0.18, 0.04), (0.35, 0.09), (0.55, 0.12), (0.72, 0.125), (0.86, 0.115), (0.95, 0.09), (1.0, 0.04)],
     bot=[(0, 0.004), (0.05, 0.012), (0.18, 0.04), (0.35, 0.085), (0.55, 0.11), (0.72, 0.1), (0.85, 0.085), (0.97, 0.05), (1.0, 0.02)],
     jaw=(0.7, -0.035, -0.02, 0.975), teeth="whale", eye=(0.78, 0.0), scars=True,
     fins=[("fluke", 0.0, 1.0), ("pectoral_small", 0.66, 0.7), ("hump", 0.42, 0.6)], wave=0.03),
 "archelon": dict(L=800, hip_h=0.36, col=(96, 104, 82), belly=(196, 190, 150), name="อาร์คีลอน",
     top=[(0, 0.004), (0.12, 0.03), (0.2, 0.12), (0.4, 0.21), (0.58, 0.2), (0.72, 0.1), (0.78, 0.05), (0.92, 0.055), (1.0, 0.02)],
     bot=[(0, 0.004), (0.12, 0.02), (0.2, 0.06), (0.4, 0.08), (0.62, 0.075), (0.74, 0.04), (0.8, 0.035), (0.92, 0.04), (1.0, 0.0)],
     jaw=(0.86, 0.005, 0.01, 0.99), teeth="beak", eye=(0.9, 0.025), shell=(0.18, 0.74),
     fins=[("turtle_front", 0.66, 1.0), ("turtle_back", 0.22, 0.7)], wave=0.006),
 "squid":    dict(L=1300, hip_h=0.38, col=(176, 70, 60), belly=(220, 140, 120), name="หมึกยักษ์",
     top=[(0, 0.004), (0.05, 0.03), (0.2, 0.065), (0.38, 0.07), (0.48, 0.06), (0.52, 0.065), (0.58, 0.05), (0.6, 0.03)],
     bot=[(0, 0.004), (0.05, 0.03), (0.2, 0.06), (0.38, 0.065), (0.48, 0.055), (0.52, 0.06), (0.58, 0.045), (0.6, 0.03)],
     jaw=None, teeth=None, eye=(0.53, 0.01), arms=(0.6, 1.0),
     fins=[("squid_fin", 0.06, 1.0)], wave=0.006),
}
SWIM = list(SEA)

def register():
    """expose sea creatures in dino45.SP so the fight engine (HIP, names, head points) treats them like any fighter"""
    for k, v in SEA.items():
        DN.SP[k] = dict(L=v["L"], biped=False, swim=True, hip_h=v["hip_h"], col=v["col"], belly=v["belly"], hs=0.1, head="sea")

# ------------------------------------------------------------------ fins (local frame: s along body towards head, n up; units of L)
FIN = {
 "caudal_shark": [(0.0, 0.0), (-0.06, 0.07), (-0.12, 0.2), (-0.08, 0.19), (-0.03, 0.08), (0.02, 0.01), (-0.03, -0.07), (-0.07, -0.15), (-0.03, -0.13), (0.03, -0.02)],
 "caudal_mosa": [(0.02, 0.0), (-0.03, 0.03), (-0.06, 0.05), (-0.05, 0.02), (-0.02, -0.01), (-0.07, -0.11), (-0.03, -0.14), (0.02, -0.07), (0.04, -0.01)],
 "tailfin_small": [(0.02, 0.0), (-0.03, 0.04), (-0.05, 0.0), (-0.03, -0.04)],
 "fluke": [(0.03, 0.0), (-0.02, 0.025), (-0.09, 0.03), (-0.05, 0.0), (-0.09, -0.03), (-0.02, -0.025)],
 "dorsal": [(0.05, 0.0), (-0.0, 0.13), (-0.035, 0.12), (-0.06, 0.0)],
 "dorsal2": [(0.02, 0.0), (-0.01, 0.06), (-0.03, 0.0)],
 "hump": [(0.03, 0.0), (0.0, 0.03), (-0.03, 0.0)],
 "anal": [(0.02, 0.0), (-0.01, -0.06), (-0.03, 0.0)],
 "pectoral": [(0.04, 0.0), (-0.06, -0.16), (-0.1, -0.17), (-0.04, -0.03)],
 "pectoral_small": [(0.03, 0.0), (-0.04, -0.07), (-0.07, -0.07), (-0.02, 0.0)],
 "pelvic": [(0.03, 0.0), (-0.03, -0.07), (-0.05, -0.06), (-0.02, 0.0)],
 "paddle": [(0.03, 0.0), (-0.02, -0.1), (-0.07, -0.13), (-0.08, -0.1), (-0.03, -0.01)],
 "flipper": [(0.04, 0.0), (0.0, -0.08), (-0.1, -0.2), (-0.15, -0.21), (-0.08, -0.08), (-0.03, 0.0)],
 "turtle_front": [(0.05, 0.0), (0.02, -0.1), (-0.15, -0.3), (-0.22, -0.32), (-0.1, -0.12), (-0.03, -0.01)],
 "turtle_back": [(0.03, 0.0), (-0.02, -0.06), (-0.09, -0.09), (-0.08, -0.03), (-0.02, 0.0)],
 "squid_fin": [(0.08, 0.0), (0.0, 0.08), (-0.06, 0.0), (0.0, -0.08)],
}
FLAP = {"pectoral": 0.25, "paddle": 0.45, "flipper": 0.5, "turtle_front": 0.55, "turtle_back": 0.35, "pelvic": 0.2, "pectoral_small": 0.3}

def swimmer(kind, t, gait="walk", mouth=0.0, P=None):
    P = P or {}; sp = SEA[kind]; L = sp["L"]; col = sp["col"]; cv = Canvas(); rnd = random.Random(7)
    moving = gait in ("walk", "run"); fr = 1.6 if gait == "run" else 1.0 if moving else 0.55
    ph = 2 * math.pi * fr * t
    cx, cy = W0 * 0.5 - 0.05 * L, GROUND - sp["hip_h"] * L
    cy += 0.012 * L * math.sin(ph * 0.5)   # gentle bob
    pitch = 0.6 * P.get("pitch", 0.0); neckb = P.get("neck", 0.0); headp = P.get("head", 0.0)
    amp = sp["wave"] * (1.5 if gait == "run" else 1.0)
    N = 90; us = [i / (N - 1) for i in range(N)]
    # centre line in body frame (x along body, y up), then rotate by pitch about the centre
    pts = []; x = -0.5 * L; y = 0.0; ang = 0.0; ds = L / (N - 1)
    nk = sp.get("neck")
    for i, u in enumerate(us):
        if i:
            a_ = 0.0
            if nk and nk[0] < u <= nk[1]: a_ = (neckb * 1.4 + headp * 0.4) / ((nk[1] - nk[0]) * (N - 1)) - (0.002 if neckb == 0 else 0)
            elif not nk and u > 0.72: a_ = headp * 0.25 / ((1 - 0.72) * (N - 1))
            ang += a_; x += ds * math.cos(ang); y += ds * math.sin(ang)
        w_ = amp * L * (1 - u) ** 2 * math.sin(ph - u * 5.5)
        pts.append((x, y + w_))
    def to_canvas(p):
        c, s_ = math.cos(-pitch), math.sin(-pitch)
        return (cx + p[0] * c - p[1] * s_, cy - (p[0] * s_ + p[1] * c))
    C = [to_canvas(p) for p in pts]
    def frame_at(u):
        i = min(N - 2, max(0, int(u * (N - 1)))); a, b = C[i], C[i + 1]; f = u * (N - 1) - i
        p = (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f); dx, dy = b[0] - a[0], b[1] - a[1]; n = math.hypot(dx, dy) or 1
        return p, (dx / n, dy / n), (dy / n, -dx / n)   # point, tangent (towards head), normal (up on screen)
    def loc(u, s_, n_):
        p, tg, nm = frame_at(u); return (p[0] + tg[0] * s_ * L + nm[0] * n_ * L, p[1] + tg[1] * s_ * L + nm[1] * n_ * L)
    top = [loc(u, 0, interp(sp["top"], u)) for u in us]; bot = [loc(u, 0, -interp(sp["bot"], u)) for u in us]
    jaw = sp.get("jaw"); gape = max(0.0, min(1.0, mouth))
    # ---- far fins (behind body)
    def fin(name, u, sc, far, flapk=0.0):
        p, tg, nm = frame_at(u); poly = FIN[name]; fl = FLAP.get(name, 0.0) * math.sin(ph + u * 3 + (1.2 if far else 0)) if (moving or flapk) else 0.0
        out = []
        for s_, n_ in poly:
            s2, n2 = s_ * sc, n_ * sc
            if fl: s2, n2 = s2 * math.cos(fl) - n2 * math.sin(fl), s2 * math.sin(fl) + n2 * math.cos(fl)
            out.append((p[0] + (tg[0] * s2 + nm[0] * n2) * L, p[1] + (tg[1] * s2 + nm[1] * n2) * L))
        return out
    farc = shade(col, 0.72)
    for name, u, sc in sp["fins"]:
        if name in ("pectoral", "paddle", "flipper", "turtle_front", "turtle_back", "pelvic", "pectoral_small"):
            cv.piece([fin(name, u - 0.02, sc * 0.9, True)], farc, smooth=2)
    if sp.get("arms"):   # far arms
        _arms(cv, sp, frame_at, loc, L, ph, gape, far=True)
    # ---- mouth interior + lower jaw
    if jaw:
        uh, oh, ot, ut = jaw
        hp = loc(uh, 0, oh)
        def J(q): # rotate about hinge by gape (opens downward)
            a = -0.55 * gape if sp["teeth"] != "whale" else -0.42 * gape
            dx, dy = q[0] - hp[0], q[1] - hp[1]; _, tg, _ = frame_at(uh); sgn = 1 if tg[0] >= 0 else -1
            c, s_ = math.cos(-a * sgn), math.sin(-a * sgn); return (hp[0] + dx * c - dy * s_, hp[1] + dx * s_ + dy * c)
        juv = [u for u in us if uh <= u <= ut]
        mo = lambda u: oh + (ot - oh) * (u - uh) / max(1e-6, ut - uh)
        mline = [loc(u, 0, mo(u)) for u in juv]
        TW = 0.085   # v18: rounded jaw - the underside curves up into the hinge instead of a boxy step
        def cdep(u):
            g = min(1.0, max(0.0, (u - uh) / TW)); g = g * g * (3 - 2 * g); g = math.sqrt(g)
            f = min(1.0, max(0.0, (ut - u) / 0.07)); g *= math.sqrt(f * (2 - f)) * 0.75 + 0.25   # rounded chin
            return mo(u) * (1 - g) + (-interp(sp["bot"], u)) * g
        lower = [J(q) for q in mline] + [J(loc(u, 0, cdep(u))) for u in juv[::-1]]
        if gape > 0.05:
            throat = [hp] + mline + [J(q) for q in mline[::-1]]
            d = cv.draw(); d.polygon([cv.P(q) for q in throat], fill=(70, 30, 34))
            mid = [((a[0] + J(a)[0]) / 2, (a[1] + J(a)[1]) / 2) for a in mline[: len(mline) * 2 // 3]]
            d.line([cv.P(q) for q in mid], fill=(170, 90, 96), width=int(0.012 * L * S))
        cv.piece([lower], shade(col, 0.95), smooth=0)
        _teeth(cv, sp, mline, J, L, lower_only=True)
        iu = us.index(juv[0])
        body = top + [loc(u, 0, oh + (ot - oh) * (u - uh) / max(1e-6, ut - uh)) for u in juv[::-1] if u < 1.0][:0]   # placeholder (kept simple)
        body = top + [loc(u, 0, oh + (ot - oh) * (u - uh) / max(1e-6, ut - uh)) for u in us[::-1] if uh <= u <= ut] + bot[:iu + 1][::-1]
        if ut < 1.0: body = top + [loc(1.0, 0, 0)] + [loc(u, 0, oh + (ot - oh) * (u - uh) / max(1e-6, ut - uh)) for u in us[::-1] if uh <= u <= ut] + bot[:iu + 1][::-1]
        throat = [loc(u, 0, cdep(u)) for u in us if uh < u <= uh + TW]
        if throat:
            ie = max(i for i, u in enumerate(us) if u <= uh + TW)
            body = body[:len(body) - (iu + 1)] + throat + [loc(us[ie], 0, -interp(sp["bot"], us[ie]))] + bot[:ie + 1][::-1]
    else:
        body = top + bot[::-1]; mline = []
    # ---- tail fins that sit behind the body outline
    for name, u, sc in sp["fins"]:
        if name.startswith("caudal") or name in ("fluke", "tailfin_small", "squid_fin"):
            cv.piece([fin(name, u, sc, False)], shade(col, 0.92), smooth=2)
    # ---- body
    cv.piece([body], col, smooth=0); d = cv.draw()
    # belly countershading (lower band, clipped by drawing as polygon inside)
    bl = [loc(u, 0, -interp(sp["bot"], u) * 0.15) for u in us if 0.04 < u < (jaw[0] if jaw else 0.99)]
    bb = [loc(u, 0, -interp(sp["bot"], u) * 0.88) for u in us if 0.04 < u < (jaw[0] if jaw else 0.99)]
    if bl: d.polygon([cv.P(q) for q in bl + bb[::-1]], fill=sp["belly"])
    d.line([cv.P(q) for q in bl], fill=shade(sp["belly"], 0.9), width=int(0.004 * L * S))
    _details(cv, sp, kind, us, loc, frame_at, L, ph, rnd, mline)
    # ---- near fins
    for name, u, sc in sp["fins"]:
        if name in ("dorsal", "dorsal2", "anal", "hump"):
            cv.piece([fin(name, u, sc, False)], shade(col, 0.95), smooth=2)
        elif name in ("pectoral", "paddle", "flipper", "turtle_front", "turtle_back", "pelvic", "pectoral_small"):
            cv.piece([fin(name, u, sc, False)], shade(col, 1.04), smooth=2)
    if sp.get("arms"): _arms(cv, sp, frame_at, loc, L, ph, gape, far=False)
    if jaw: _teeth(cv, sp, mline, None, L, lower_only=False)
    # ---- eye
    eu, en = sp["eye"]; e = loc(eu, 0, en); r = (0.016 if kind != "squid" else 0.03) * L
    d = cv.draw()
    if kind == "squid":
        d.ellipse([cv.P((e[0] - r, e[1] - r)), cv.P((e[0] + r, e[1] + r))], fill=(250, 240, 210), outline=DK, width=6)
        d.ellipse([cv.P((e[0] - r * 0.55, e[1] - r * 0.55)), cv.P((e[0] + r * 0.55, e[1] + r * 0.55))], fill=DK)
    else:
        d.ellipse([cv.P((e[0] - r, e[1] - r)), cv.P((e[0] + r, e[1] + r))], fill=(250, 246, 226), outline=DK, width=5)
        q = r * 0.6; ex = e[0] + r * 0.25; d.ellipse([cv.P((ex - q, e[1] - q)), cv.P((ex + q, e[1] + q))], fill=DK)
        d.ellipse([cv.P((ex - q * 0.2, e[1] - q * 0.7)), cv.P((ex + q * 0.4, e[1] - q * 0.15))], fill=(255, 255, 255))
        d.line([cv.P((e[0] - r * 1.4, e[1] - r * 1.5)), cv.P((e[0] + r * 1.3, e[1] - r * 0.9))], fill=DK, width=int(0.006 * L * S))   # brow (angry)
    return cv.im.resize((W0, H0), Image.LANCZOS)

def _teeth(cv, sp, mline, J, L, lower_only):
    kind = sp["teeth"]; d = cv.draw()
    if not mline or kind in (None, "beak"): return
    if kind == "blades":   # Dunkleosteus: bony fang plates instead of teeth
        tip = mline[-1]; a = mline[-4] if len(mline) > 4 else mline[0]
        if lower_only and J:
            t0 = J(tip); t1 = J(a); d.polygon([cv.P(t1), cv.P(t0), cv.P((t0[0] - 0.005 * L, t0[1] - 0.05 * L)), cv.P(((t0[0] + t1[0]) / 2, t1[1] - 0.02 * L))], fill=(232, 224, 200), outline=DK, width=5)
        elif not lower_only:
            d.polygon([cv.P(a), cv.P(tip), cv.P((tip[0] - 0.004 * L, tip[1] + 0.05 * L)), cv.P(((tip[0] + a[0]) / 2, a[1] + 0.02 * L))], fill=(240, 232, 210), outline=DK, width=5)
        return
    step = {"shark": 3, "cone": 3, "cone_small": 2, "whale": 4}[kind]; hgt = {"shark": 0.03, "cone": 0.026, "cone_small": 0.01, "whale": 0.04}[kind] * L
    sel = mline[2::step]
    for i, q in enumerate(sel):
        if lower_only and J:
            if kind == "whale" or kind != "shark" or True:
                b = J(q); d.polygon([cv.P((b[0] - hgt * 0.3, b[1])), cv.P((b[0], b[1] - hgt)), cv.P((b[0] + hgt * 0.3, b[1]))], fill=(250, 246, 232), outline=DK, width=3)
        elif not lower_only:
            if kind == "whale": continue   # Livyatan: big teeth in both jaws, but upper ones hidden behind the lip line
            d.polygon([cv.P((q[0] - hgt * 0.3, q[1])), cv.P((q[0], q[1] + hgt)), cv.P((q[0] + hgt * 0.3, q[1]))], fill=(250, 246, 232), outline=DK, width=3)

def _details(cv, sp, kind, us, loc, frame_at, L, ph, rnd, mline):
    d = cv.draw(); col = sp["col"]
    if sp.get("gills"):
        g0, g1, n = sp["gills"]
        for k in range(n):
            u = g0 + (g1 - g0) * k / (n - 1); a = loc(u, 0, 0.05); b = loc(u - 0.012, 0, -0.04)
            d.line([cv.P(a), cv.P(b)], fill=shade(col, 0.6), width=int(0.006 * L * S))
    if sp.get("scales"):
        for k in range(60):
            u = rnd.uniform(0.15, 0.84); n_ = rnd.uniform(0.0, 1.0) * interp(sp["top"], u); q = loc(u, 0, n_); r = 0.006 * L
            d.ellipse([cv.P((q[0] - r, q[1] - r * 0.7)), cv.P((q[0] + r, q[1] + r * 0.7))], fill=shade(col, 0.82))
    if sp.get("scars"):
        for k in range(9):
            u = rnd.uniform(0.6, 0.95); n_ = rnd.uniform(-0.02, 0.09); a = loc(u, 0, n_); b = loc(u - 0.03, 0, n_ - 0.015)
            d.line([cv.P(a), cv.P(b)], fill=shade(col, 1.35), width=int(0.004 * L * S))
    if sp.get("armor"):   # bony head / thorax shield with plate seams
        a0, a1 = sp["armor"]; uu = [u for u in us if a0 <= u <= a1]
        shield = [loc(u, 0, interp(sp["top"], u) + 0.004) for u in uu] + [loc(u, 0, -interp(sp["bot"], u) * 0.35) for u in uu[::-1]]
        cv.piece([shield], (150, 146, 128), smooth=0); d = cv.draw()
        for u in (a0 + 0.08, a0 + 0.2, a0 + 0.3):
            d.line([cv.P(loc(u, 0, interp(sp["top"], u))), cv.P(loc(u + 0.02, 0, -interp(sp["bot"], u) * 0.3))], fill=(100, 96, 84), width=int(0.006 * L * S))
        for k in range(30):
            u = rnd.uniform(a0 + 0.02, a1 - 0.08); n_ = rnd.uniform(-0.02, interp(sp["top"], u) * 0.9); q = loc(u, 0, n_); r = 0.004 * L
            d.ellipse([cv.P((q[0] - r, q[1] - r)), cv.P((q[0] + r, q[1] + r))], fill=(124, 120, 104))
    if sp.get("shell"):   # Archelon leathery shell with ridges
        s0, s1 = sp["shell"]; uu = [u for u in us if s0 <= u <= s1]
        shell = [loc(u, 0, interp(sp["top"], u) + 0.006) for u in uu] + [loc(u, 0, -0.02) for u in uu[::-1]]
        cv.piece([shell], (80, 88, 70), smooth=0); d = cv.draw()
        for k in range(1, 4):
            f = k / 4; d.line([cv.P(loc(u, 0, interp(sp["top"], u) * f)) for u in uu[2:-2]], fill=(110, 118, 92), width=int(0.007 * L * S))
        for u in uu[3:-3:3]:
            q = loc(u, 0, interp(sp["top"], u)); d.ellipse([cv.P((q[0] - 0.008 * L, q[1] - 0.008 * L)), cv.P((q[0] + 0.008 * L, q[1] + 0.008 * L))], fill=(120, 128, 100), outline=DK, width=3)
        hk = loc(1.0, 0, -0.005); d.polygon([cv.P(hk), cv.P(loc(0.985, 0, -0.04)), cv.P(loc(0.96, 0, -0.01))], fill=(220, 210, 170), outline=DK, width=4)   # hooked beak

def _arms(cv, sp, frame_at, loc, L, ph, gape, far):
    a0, a1 = sp["arms"]; base = frame_at(a0)[0]; col = shade(sp["col"], 0.75 if far else 1.0)
    spread = 0.08 + 0.25 * gape
    idx = (0, 2, 4, 6, 8) if far else (1, 3, 5, 7, 9)
    for k in idx:
        long = k in (8, 9); ln = (0.62 if long else 0.4) * L; off = (k / 9 - 0.5) * spread * 2
        pts = []; p = base; _, tg, nm = frame_at(a0); ang = math.atan2(tg[1], tg[0]) + off
        for j in range(16):
            v = j / 15; a = ang + 0.25 * math.sin(ph * 1.3 + k + v * 4) * v + off * v
            p = (p[0] + math.cos(a) * ln / 15, p[1] + math.sin(a) * ln / 15); pts.append(p)
        w0 = (0.03 if not long else 0.018) * L
        poly = DN.taper(base, pts[len(pts) // 2], w0, w0 * 0.55) + DN.taper(pts[len(pts) // 2], pts[-1], w0 * 0.55, w0 * 0.1)
        cv.piece([DN.taper(base, pts[7], w0, w0 * 0.6), DN.taper(pts[7], pts[-1], w0 * 0.6, w0 * 0.08)], col, smooth=0)
        if long:   # club with suckers
            d = cv.draw(); c = pts[-2]; d.ellipse([cv.P((c[0] - 0.025 * L, c[1] - 0.015 * L)), cv.P((c[0] + 0.025 * L, c[1] + 0.015 * L))], fill=shade(col, 1.1), outline=DK, width=4)
        if not far:
            d = cv.draw()
            for j in range(3, 14, 2):
                q = pts[j]; r = 0.006 * L; d.ellipse([cv.P((q[0] - r, q[1] - r)), cv.P((q[0] + r, q[1] + r))], fill=(236, 200, 180), outline=shade(col, 0.6), width=2)
