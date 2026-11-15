# -*- coding: utf-8 -*-
"""คลังท่าต่อสู้ไดโนเสาร์ (สไตล์ช่องสัตว์ยักษ์) — Claude ใช้ประกอบตอนใหม่ได้เร็ว
    C = Choreo("trex", "spino", env="river")
    t = C.roar("a", 0.0); t = C.clash(t); t = C.gore("b", t); ...
    C.frame(t) -> PIL image ; C.sfx(path) -> effects track
A = ตัวซ้าย (หน้า ใหญ่กว่า), B = ตัวขวา (หลัง, หันซ้าย)"""
import os, sys, math, random, glob
_HERE0 = os.path.dirname(os.path.abspath(__file__))   # v19: may run from a job folder copy -> sounds/modules still come from the engine
HERE = _HERE0 if os.path.isdir(os.path.join(_HERE0, "sounds")) else (os.environ.get("ENGINE") or os.path.join(_HERE0, "..", "..", "engine")); sys.path.insert(0, HERE)
os.environ.setdefault("FIGHT_A", "trex"); os.environ.setdefault("FIGHT_B", "spino")
import fight4 as F
import scenes as SC
from PIL import ImageFilter as _IF
R, DN = F.R, F.DN
from PIL import Image, ImageDraw, ImageEnhance, ImageChops
import numpy as np
W, H = 1080, 1920
DK = R.DK; YEL = (255, 214, 50); RED = (235, 45, 50); WHT = (255, 255, 255)
clamp = R.clamp
def eout(x): x = clamp(x); return 1 - (1 - x) ** 3
for _k in DN.SP:
    if _k not in F.HIP and "L" in DN.SP[_k] and "hip_h" in DN.SP[_k]:
        F.HIP[_k] = (DN.W0 * 0.5 - 0.05 * DN.SP[_k]["L"], DN.GROUND - DN.SP[_k]["hip_h"] * DN.SP[_k]["L"])
NEUT = dict(pitch=0, neck=0.1, head=0, m=0.2, crouch=0, arm=0, tailup=0, nd=0, nl=0, fd=0, fl=0, r=0, drop=0, turn=1.0)
AH, BH = -110.0, 1150.0          # home x
CA, CB = 105.0, 1010.0           # x at body contact
HEAD_A, HEAD_B = (700, 700), (430, 700)   # where hits land on B / on A (screen space, before camera)
ENVS = ("land", "river", "sunset", "night", "rain", "volcano") + tuple(SC.SCENES)
NAME = {"trex": "ทีเร็กซ์", "spino": "สไปโนซอรัส", "tricera": "ไทรเซราทอปส์", "edmonto": "เอ็ดมอนโตซอรัส",
        "giga": "จิกาโนโตซอรัส", "carno": "คาร์โนทอรัส", "allo": "อัลโลซอรัส", "raptor": "ยูทาห์แรปเตอร์",
        "pachy": "แพคีเซฟาโลซอรัส", "anky": "แองคิโลซอรัส", "stego": "สเตโกซอรัส", "brachio": "แบรคิโอซอรัส",
        "therizino": "เทอริซิโนซอรัส", "parasaur": "พาราซอโรโลฟัส", "iguano": "อิกัวโนดอน", "dilo": "ไดโลโฟซอรัส",
        "styraco": "สไตราโคซอรัส", "kentro": "เคนโทรซอรัส", "baryonyx": "แบริออนิกซ์", "diplo": "ดิพโพลโดคัส",
        "mammoth": "แมมมอธ", "smilodon": "เสือเขี้ยวดาบ", "rhino": "แรดขนยาว", "sloth": "สลอธยักษ์", "sarco": "ซาร์โคซูคัส", "megalania": "เมกาลาเนีย", "quetzal": "เควตซัลโคแอตลัส", "paracera": "พาราเซราทีเรียม", "megalodon": "เมกาโลดอน", "mosasaurus": "โมซาซอรัส", "liopleurodon": "ไลโอพลูโรดอน", "elasmo": "อีลาสโมซอรัส", "dunkleosteus": "ดังเคิลออสเตียส", "livyatan": "ลิเวียทัน", "archelon": "อาร์คีลอน", "squid": "หมึกยักษ์"}
ROAR = {"trex": ("t-rex-dragon-reptile", 0.88), "spino": ("roar-or-scream-2", 1.04), "tricera": ("dinosaur-roar-390283", 0.8), "edmonto": ("roar-or-scream-8", 1.15),
        "giga": ("t-rex-dragon-reptile", 0.8), "carno": ("roar-or-scream-2", 0.95), "allo": ("dinosaur-roar-390283", 1.0), "raptor": ("roar-or-scream-8", 1.35),
        "pachy": ("dinosaur-growls-431298", 1.2), "anky": ("dinosaur-roar-390283", 0.7), "stego": ("dinosaur-growls-431298", 0.85), "brachio": ("dinosaur-roar-390283", 0.6),
        "therizino": ("dinosaur-growls-431298", 0.9), "parasaur": ("roar-or-scream-8", 0.8), "iguano": ("dinosaur-roar-390283", 0.85), "dilo": ("roar-or-scream-8", 1.25),
        "styraco": ("dinosaur-roar-390283", 0.78), "kentro": ("dinosaur-growls-431298", 0.9), "baryonyx": ("roar-or-scream-2", 1.12), "diplo": ("dinosaur-roar-390283", 0.55),
        "mammoth": ('dinosaur-roar-390283', 1.3), "smilodon": ('roar-or-scream-8', 1.4), "rhino": ('dinosaur-growls-431298', 1.1), "sloth": ('dinosaur-growls-431298', 0.95), "sarco": ('dinosaur-growl-487679', 0.7), "megalania": ('dinosaur-growl-487679', 1.2), "quetzal": ('roar-or-scream-8', 1.6), "paracera": ('dinosaur-roar-390283', 1.1), "megalodon": ('dinosaur-growl-487679', 0.6), "mosasaurus": ('dinosaur-growl-487679', 0.75), "liopleurodon": ('dinosaur-growls-431298', 0.7), "elasmo": ('roar-or-scream-8', 0.8), "dunkleosteus": ('dinosaur-growls-431298', 0.9), "livyatan": ('dinosaur-roar-390283', 0.5), "archelon": ('dinosaur-growls-431298', 1.1), "squid": ('roar-or-scream-8', 0.6)}
# extra synthesized voice layers per species (sfxsynth keys, gain, delay)
VOICE_EX = {"mammoth": (("mammoth-trumpet-1", 0.9, 0.0),), "paracera": (("mammoth-trumpet-2", 0.4, 0.1),), "smilodon": (("cat-snarl-1", 0.8, 0.0),),
            "sarco": (("croc-hiss-1", 0.7, 0.0),), "megalania": (("croc-hiss-2", 0.8, 0.0),), "livyatan": (("whale-moan-1", 0.9, 0.0), ("whale-clicks-1", 0.5, 0.6)),
            "megalodon": (("shark-thrash-1", 0.6, 0.0), ("deep-growl-1", 0.5, 0.1)), "mosasaurus": (("shark-thrash-2", 0.5, 0.0),), "squid": (("squid-squelch-1", 0.9, 0.0),),
            "elasmo": (("whale-moan-2", 0.4, 0.0),), "liopleurodon": (("deep-growl-1", 0.7, 0.0),), "archelon": (("croc-hiss-1", 0.6, 0.0),), "dunkleosteus": (("armor-knock-1", 0.5, 0.0), ("deep-growl-2", 0.6, 0.05)), "giga": (("monster-roar-1", 0.35, 0.05),), "carno": (("monster-roar-2", 0.35, 0.05),)}
# real recordings downloaded from Pixabay (sounds/px, credits in credits_pixabay.tsv) per sound role
REAL = {"bite-crunch": ("px-monster-bite-44538", "px-bone-crunch-152222", "px-bone-crunch-102701"),
        "flesh-tear": ("px-flesh-tear-352708", "px-flesh-tear-480118"), "blood-splat": ("px-gore-88998", "px-blood-splatter-122253"),
        "claw-slash": ("px-flesh-tear-352708",), "body-slam": ("px-heavy-punch-515251", "px-heavy-punch-634742", "px-body-fall-352725", "px-body-fall-352716"),
        "tail-whip": ("px-tail-whip-123738",), "rock-debris": ("px-rocks-falling-6375", "px-rocks-falling-515257"),
        "splash-big": ("px-water-splash-352021", "px-big-splash-467479", "px-water-splash-199583"), "splash-small": ("px-water-splash-199583",),
        "underwater-impact": ("px-underwater-explosion-423651", "px-underwater-explosion-455785", "px-underwater-521068"),
        "bubbles": ("px-bubbles-108320", "px-underwater-467471"), "thunder": ("px-thunder-192165", "px-thunder-443132"), "lava-burst": ("px-lava-103785",),
        "whale-moan": ("px-whale-382727", "px-whale-515260", "px-whale-382729", "px-whale-37270"),
        "mammoth-trumpet": ("px-elephant-trumpet-494313", "px-elephant-trumpet-482702", "px-elephant-trumpet-6047"),
        "cat-snarl": ("px-tiger-growl-193175", "px-big-cat-snarl-98468", "px-lion-roar-444190", "px-tiger-growl-502894"), "croc-hiss": ("px-crocodile-372480",),
        "deep-growl": ("px-monster-growl-401721", "px-monster-growl-90325"), "monster-roar": ("px-creature-roar-364481", "px-creature-roar-195717")}
SYNTH_TOO = ("claw-slash", "splash-small", "bubbles", "tail-whip")   # these mix synthesized variants in with the recordings
REAL_AMB = {"jungle": "px-jungle-306431", "swamp": "px-swamp-598857", "tundra": "px-blizzard-445020", "snowforest": "px-blizzard-445020",
            "beach": "px-ocean-waves-397977", "ocean": "px-ocean-waves-397977", "reef": "px-underwater-ambience-376890", "kelp": "px-underwater-ambience-376890",
            "deep": "px-deep-sea-ambience-482888", "abyss": "px-deep-sea-ambience-482888", "rain": "px-rain-ambience-208505", "storm": "px-rain-ambience-208505",
            "canyon": "px-desert-wind-350417", "savanna": "px-desert-wind-350417"}
ARMORED = ("anky", "stego", "dunkleosteus", "archelon", "styraco", "kentro", "pachy")

LCW, OX, LW_, LH_ = 2400, 660, 1920, 1080   # landscape: wide world canvas, x offset, output size
# ------------------------------------------------------------- beauty pass (v18)
BEAUTY = int(os.environ.get("BEAUTY", "1"))
try:
    import cv2 as _cv
except Exception:
    _cv = None
def _shade_layer(L, under=False, anchor=(0, 0), scaly=True, fur=False):
    """give a flat fighter layer volume: top light, belly shadow, edge occlusion and a rim light"""
    if not BEAUTY or _cv is None: return L
    bb = L.getbbox()
    if not bb: return L
    pad = 40; x0, y0 = max(0, bb[0] - pad), max(0, bb[1] - pad); x1, y1 = min(L.width, bb[2] + pad), min(L.height, bb[3] + pad)
    A = np.asarray(L.crop((x0, y0, x1, y1))).astype(np.float32)
    a = A[..., 3] / 255.0
    if a.max() < 0.5: return L
    m = (a > 0.5).astype(np.uint8)
    d = _cv.distanceTransform(m, _cv.DIST_L2, 3)
    B = _cv.GaussianBlur(a, (0, 0), 30)
    gy = _cv.Sobel(B, _cv.CV_32F, 0, 1, ksize=5); gx = _cv.Sobel(B, _cv.CV_32F, 1, 0, ksize=5)
    nrm = np.sqrt(gx * gx + gy * gy) + 1e-4
    lx, ly = (-0.35, -0.94)                                  # light from above, a little from the left
    lam = -(gx * lx + gy * ly) / nrm * np.clip(nrm * 40, 0, 1)   # +1 facing the light, -1 facing away
    inner = np.clip(d / 70.0, 0, 1)
    shade = 1.0 + 0.34 * lam * (1 - inner * 0.45) - 0.16 * (1 - np.clip(d / 18.0, 0, 1)) * (lam < 0)
    # soft vertical light falloff inside the body (upper half brighter)
    ys = np.linspace(0, 1, a.shape[0])[:, None]
    top = np.clip((ys - ys[np.argmax(m.any(1))]) , 0, 1)
    shade *= 1.04 - 0.10 * _cv.GaussianBlur(top.astype(np.float32) * np.ones_like(a), (0, 0), 30)
    ink = (A[..., :3].max(2) < 60)                         # keep black outlines and pupils pure
    shade = np.where(ink, 1.0, shade)
    rgb = A[..., :3] * shade[..., None]
    Ts, Tm, Th = _skin_tex(); ax, ay = int(anchor[0]) - x0, int(anchor[1]) - y0
    iy = (np.arange(a.shape[0]) - ay) % Ts.shape[0]; ix = (np.arange(a.shape[1]) - ax) % Ts.shape[1]
    T_ = (Ts * 0.6 + Tm) if scaly else Tm * 0.8
    if fur: T_ = Tm * 0.6 + Th * (1.1 if fur is True else float(fur))
    tex = T_[iy][:, ix] * np.clip((d - 4) / 8.0, 0, 1) * (~ink) * (A[..., :3].min(2) < 175)
    rgb = rgb * (1 + 0.10 * tex[..., None])
    rim = np.clip(1 - np.abs(d - 13) / 5.0, 0, 1) * np.clip(lam * 1.6, 0, 1)
    rc = np.array((200, 235, 255) if under else (255, 244, 214), np.float32)
    rim = rim * (~ink)
    rgb = rgb * (1 - 0.42 * rim[..., None]) + rc * 0.42 * rim[..., None]
    out = np.dstack([np.clip(rgb, 0, 255), A[..., 3]]).astype(np.uint8)
    P_ = Image.fromarray(out, "RGBA")
    L2 = L.copy(); L2.paste(P_, (x0, y0)); return L2

def _fur(P_, m, d, ink, anc):
    """shaggy coat: hanging strands along the lower edges + hair strokes inside, anchored to the animal"""
    h, w = m.shape; A = np.asarray(P_); dr = ImageDraw.Draw(P_)
    below = np.zeros_like(m); below[:-1] = m[1:]
    return P_


_TEX = None
def _skin_tex():
    """tileable 512px skin pattern: soft scales (cellular) + mottling, values around 0"""
    global _TEX
    if _TEX is None:
        rnd = np.random.RandomState(7); N = 512
        pts = rnd.rand(260, 2) * N
        yy, xx = np.mgrid[0:N, 0:N].astype(np.float32)
        d1 = np.full((N, N), 1e9, np.float32); d2 = np.full((N, N), 1e9, np.float32)
        for px, py in pts:
            for ox_ in (-N, 0, N):
                for oy_ in (-N, 0, N):
                    dd = (xx - px - ox_) ** 2 + (yy - py - oy_) ** 2
                    m = dd < d1; d2 = np.where(m, d1, np.minimum(d2, dd)); d1 = np.minimum(d1, dd)
        edge = np.sqrt(d2) - np.sqrt(d1)                     # small on scale borders
        scales = np.clip(edge / 6.0, 0, 1)                    # 0 at the crease, 1 inside a scale
        big = np.tile(rnd.rand(N, N).astype(np.float32), (3, 3)); mott = _cv.GaussianBlur(big, (0, 0), 18)[N:2 * N, N:2 * N]
        mott = (mott - mott.mean()) / (mott.std() + 1e-6)
        big2 = np.tile(rnd.rand(N, N).astype(np.float32), (3, 3)); hair = _cv.GaussianBlur(big2, (0, 0), sigmaX=1.3, sigmaY=9)[N:2 * N, N:2 * N]
        hair = (hair - hair.mean()) / (hair.std() + 1e-6)
        _TEX = ((scales - 0.75) * 0.55, mott * 0.3, hair)
    return _TEX
_FG = {}
def _foreground(env, w, h, under):
    """blurred dark silhouettes in the screen corners (ferns, grass, rocks / kelp, reef rocks) for depth"""
    key = (env, w, h)
    if key in _FG: return _FG[key]
    rnd = random.Random(hash(env) & 0xffff)
    L = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    col = (8, 34, 40, 235) if under else ((24, 30, 14, 240) if env not in ("tundra", "snowforest") else (40, 48, 58, 230))
    for side in (0, 1):
        bx = 0 if side == 0 else w
        for _ in range(3):                                     # rocks
            cx = bx + (rnd.uniform(-60, 260) if side == 0 else -rnd.uniform(-60, 260)); cy = h + rnd.uniform(-30, 40)
            rx, ry = rnd.uniform(110, 230), rnd.uniform(60, 130); d.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=col)
        for _ in range(16 if not under else 7):                # fronds / blades / kelp
            x0_ = bx + (rnd.uniform(0, 300) if side == 0 else -rnd.uniform(0, 300)); y0_ = h + 10
            ln = rnd.uniform(160, 360) if not under else rnd.uniform(300, 620); ang = rnd.uniform(-0.5, 0.5) + (0.35 if side == 0 else -0.35)
            pts = []
            for k in range(14):
                u = k / 13; x = x0_ + math.sin(ang) * ln * u + (math.sin(u * 5 + x0_) * 18 if under else 0); y = y0_ - math.cos(ang) * ln * u + (u * u * 60 * (1 if side == 0 else 1))
                pts.append((x, y))
            wdt = rnd.uniform(14, 26) if not under else rnd.uniform(18, 34)
            for k in range(len(pts) - 1):
                d.line([pts[k], pts[k + 1]], fill=col, width=max(3, int(wdt * (1 - k / 14))))
                if not under and k % 2 == 0 and k > 2:          # leaflets
                    px, py = pts[k]; s_ = wdt * 1.6 * (1 - k / 14)
                    d.ellipse((px - s_ * 1.6, py - s_ * 0.5, px, py + s_ * 0.3), fill=col); d.ellipse((px, py - s_ * 0.5, px + s_ * 1.6, py + s_ * 0.3), fill=col)
    L = L.filter(_IF.GaussianBlur(7))
    _FG[key] = L; return L
def _motes(img, t, under, env):
    """slow floating dust in the light / marine snow"""
    d = ImageDraw.Draw(img, "RGBA"); w, h = img.size; rnd = random.Random(11)
    n = 70 if under else (45 if env not in ("storm", "tundra", "snowforest") else 0)
    for i in range(n):
        x = (rnd.uniform(0, w) + t * rnd.uniform(-14, 14)) % w; y = (rnd.uniform(0, h) + (t * rnd.uniform(6, 20) if under else -t * rnd.uniform(4, 12))) % h
        r = rnd.uniform(1.5, 4.2); a = int(rnd.uniform(40, 120) * (0.6 + 0.4 * math.sin(t * rnd.uniform(0.6, 1.6) + i)))
        c = (205, 235, 245, a) if under else (255, 236, 190, a)
        d.ellipse((x - r, y - r, x + r, y + r), fill=c)

# ---------------------------------------------------------------- v19 colour grades (GRADE env or Choreo(grade=...))
GRADES = {   # contrast, saturation, shadow tint, highlight tint, matte(lifted blacks), haze colour+amount, bloom, vignette
    "natural":     dict(c=0.10, sat=1.10, sh=(0.00, 0.015, 0.04), hi=(0.05, 0.03, 0.00), matte=0.00, haze=None, bloom=0.22, vig=0.28),
    "golden":      dict(c=0.12, sat=1.12, sh=(0.02, 0.00, 0.03), hi=(0.10, 0.05, -0.03), matte=0.02, haze=((255, 205, 140), 0.07), bloom=0.30, vig=0.32),
    "ice":         dict(c=0.12, sat=1.0, sh=(-0.01, 0.02, 0.07), hi=(0.00, 0.03, 0.06), matte=0.03, haze=((205, 222, 240), 0.08), bloom=0.26, vig=0.26),
    "teal_orange": dict(c=0.16, sat=1.12, sh=(-0.03, 0.03, 0.06), hi=(0.08, 0.03, -0.04), matte=0.02, haze=None, bloom=0.24, vig=0.34),
    "dusk":        dict(c=0.14, sat=1.05, sh=(0.03, -0.01, 0.07), hi=(0.10, 0.03, 0.00), matte=0.03, haze=((240, 150, 120), 0.08), bloom=0.32, vig=0.40),
    "misty":       dict(c=0.04, sat=0.90, sh=(0.00, 0.02, 0.03), hi=(0.02, 0.03, 0.01), matte=0.06, haze=((200, 210, 200), 0.13), bloom=0.20, vig=0.24),
    "storm":       dict(c=0.18, sat=0.80, sh=(0.00, 0.01, 0.05), hi=(-0.02, 0.00, 0.02), matte=0.02, haze=((120, 130, 140), 0.08), bloom=0.14, vig=0.42),
    "vintage":     dict(c=0.06, sat=0.82, sh=(0.04, 0.02, 0.00), hi=(0.06, 0.04, -0.03), matte=0.07, haze=((235, 215, 180), 0.06), bloom=0.18, vig=0.36),
    "deepsea":     dict(c=0.10, sat=1.05, sh=(0.02, 0.03, 0.07), hi=(0.00, 0.03, 0.05), matte=0.00, haze=None, bloom=0.22, vig=0.30),
}
AUTO_GRADE = {"tundra": "ice", "snowforest": "ice", "savanna": "golden", "canyon": "golden", "beach": "teal_orange", "jungle": "misty",
              "swamp": "misty", "storm": "storm", "ocean": "teal_orange", "reef": "deepsea", "kelp": "deepsea", "deep": "deepsea", "abyss": "deepsea"}
GRADE = os.environ.get("GRADE", "auto")
def grade_for(env, g=None):
    g = g or GRADE
    if g == "none": return None
    if g == "auto" or g not in GRADES: g = AUTO_GRADE.get(env, "natural")
    return GRADES[g]

def _post(img, env, t, grade=None):
    """whole-frame finish: contrast curve, split toning, atmospheric haze, matte, bloom, vignette (per grade)"""
    if not BEAUTY or _cv is None: return img
    G = grade_for(env, grade)
    if G is None: return img
    a = np.asarray(img.convert("RGB")).astype(np.float32) / 255.0
    lum = a.mean(2, keepdims=True)
    a = a + (a - 0.5) * G["c"]
    a = lum + (a - lum) * G["sat"]
    a = a + np.array(G["sh"], np.float32) * (1 - lum) + np.array(G["hi"], np.float32) * lum
    if G["haze"]:   # thicker towards the horizon -> ties fighters into the same air as the background
        h = a.shape[0]; yy = np.linspace(0, 1, h, dtype=np.float32)[:, None, None]
        k = G["haze"][1] * (0.6 + 0.8 * np.exp(-((yy - 0.45) / 0.25) ** 2))
        a = a * (1 - k) + np.array(G["haze"][0], np.float32) / 255.0 * k
    if G["matte"]: a = G["matte"] + a * (1 - G["matte"])
    br = np.clip((a - 0.78) * 3.0, 0, 1)
    small = _cv.resize(br, (a.shape[1] // 4, a.shape[0] // 4), interpolation=_cv.INTER_AREA)
    small = _cv.GaussianBlur(small, (0, 0), 9); a = a + G["bloom"] * _cv.resize(small, (a.shape[1], a.shape[0]))
    h, w = a.shape[:2]; yy, xx = np.ogrid[:h, :w]
    r = np.sqrt(((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2)
    a = a * (1 - G["vig"] * np.clip(r - 0.55, 0, 1) ** 1.5)[..., None]
    return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8), "RGB").convert("RGBA")

BLEND = float(os.environ.get("BLEND", "1.0"))   # 0 = off, 1 = normal, up to ~1.6 = strong
def _blend_fighter(L, bg):
    """make a fighter sit IN the scene: take on the scene's ambient colour, soften the cut-out edge,
    and let the background light wrap around the silhouette"""
    if not BEAUTY or _cv is None or BLEND <= 0: return L
    bb = L.getbbox()
    if not bb: return L
    pad = 40; x0, y0, x1, y1 = max(0, bb[0] - pad), max(0, bb[1] - pad), min(L.width, bb[2] + pad), min(L.height, bb[3] + pad)
    f = np.asarray(L.crop((x0, y0, x1, y1))).astype(np.float32) / 255.0
    b = np.asarray(bg.convert("RGB").crop((x0, y0, x1, y1))).astype(np.float32) / 255.0
    al = f[..., 3:4]; rgb = f[..., :3]
    amb = np.asarray(bg.convert("RGB").resize((16, 9), Image.BILINEAR)).reshape(-1, 3).mean(0) / 255.0
    amb = amb / max(1e-3, amb.mean())                                   # normalised scene tint
    ink = (rgb.max(2, keepdims=True) < 0.24).astype(np.float32)         # keep outlines dark
    k = 0.30 * BLEND
    rgb = rgb * (1 - k * (1 - ink)) + rgb * amb * k * (1 - ink)         # ambient colour cast
    bgb = _cv.GaussianBlur(b, (0, 0), 18)
    inner = _cv.GaussianBlur(al, (0, 0), 7)[..., None] if al.ndim == 3 else al
    inner = inner.reshape(al.shape)
    rim = np.clip((al - inner) * 2.2, 0, 1) * (1 - ink)                 # band just inside the silhouette edge
    rgb = rgb + (bgb - rgb) * rim * 0.45 * BLEND                        # light wrap
    lum = rgb.mean(2, keepdims=True); bl = b.mean(2, keepdims=True).mean()
    rgb = rgb + (bl - 0.5) * 0.10 * BLEND * (1 - ink)                   # match overall exposure a little
    al2 = _cv.GaussianBlur(al, (0, 0), 0.8).reshape(al.shape)           # anti-aliased cut-out edge
    out = np.concatenate([np.clip(rgb, 0, 1), np.maximum(al2, al * 0.98)], 2)
    L = L.copy(); L.paste(Image.fromarray((out * 255).astype(np.uint8), "RGBA"), (x0, y0)); return L

def wide_bg(name, pan):
    if R.BGW < LCW + 700: R.BGW = LCW + 700; R.BGC.clear()
    if name not in R.BGC: R.BGC[name] = R.build(name)
    x = int(pan % 600); return R.BGC[name].crop((x, 0, x + LCW, H))

class Choreo:
    def __init__(s, ka="trex", kb="spino", env="land", land=False, grade=None):
        s.ka, s.kb, s.env, s.land, s.look = ka, kb, env, land, grade
        s.GB = F.GT if land else F.GS   # landscape: both fighters stand on the same ground line (no floating back lane)
        s.K = {"a": [(0.0, dict(x=AH, **NEUT))], "b": [(0.0, dict(x=BH, **NEUT))]}
        s.G = {"a": [(0.0, "pose")], "b": [(0.0, "pose")]}
        s.CAM = [(0.0, (1.0, 540, 880))]
        s.shk, s.bursts, s.slashes, s.speed, s.dusts, s.flash, s.snd, s.splash, s.couple, s.labels, s.drums = [], [], [], [], [], [], [], [], [], [], []
        s.dead = {"a": None, "b": None}; s.gone = {"a": None, "b": None}; s.pan = []
        s.envk = [(0.0, env)]
        s._tr = None
        s.kinds = []   # (t, kind, attacker) for layered impact sounds
        s.blood_lv = int(os.environ.get("BLOOD", "1"))   # 0 = no blood, 1 = normal, 2 = heavy
        s.bl = []   # (t, x, y, victim, power)
    # ------------------------------------------------------------- helpers
    def k(s, who, t, **kv): s.K[who].append((t, kv))
    def g(s, who, t, gait): s.G[who].append((t, gait))
    def cam(s, t, z, x, y): s.CAM.append((t, (z, x, y)))
    def hit(s, t, x, y, size=0.5, shake=24, victim=None, sfx=("hard-heavy-impact",), slash=False):
        s.bursts.append((t, x, y, size)); s.shk.append((t, shake, 0.6))
        if victim:
            s.flash.append((victim, t, 0.15))
            s.bl.append((t, x, y, victim[-1], max(0.5, min(1.6, size * 2 + shake / 40))))
        for k_ in sfx: s.snd.append((t, k_, 1.0, 1.0))
        if slash: s.slashes.append((t - 0.04, x - 30, y + 100))
    def sound(s, t, key, pitch=1.0, g=1.0): s.snd.append((t, key, pitch, g))
    def roar_snd(s, who, t, g=1.0, pitch=1.0):
        k = s.ka if who == "a" else s.kb; nm, p = ROAR.get(k, ROAR["trex"]); s.snd.append((t, nm, p * pitch, g))
        for key, gg, dt in VOICE_EX.get(k, ()): s.snd.append((t + dt, "SX:" + key, 1.0, g * gg))
    def fwd(s, who, d): return AH + d if who == "a" else BH - d
    def other(s, who): return "b" if who == "a" else "a"
    def biped(s, who): return DN.SP[s.ka if who == "a" else s.kb]["biped"]
    def label(s, t0, t1, txt): s.labels.append((t0, t1, txt))
    def head_xy(s, victim):
        """where a hit lands on `victim` (screen space); low four-legged animals get hit lower"""
        x, y = HEAD_A if victim == "b" else HEAD_B
        if victim == "b" and s.land: y += 150; x += 110
        k = s.kb if victim == "b" else s.ka; sp = DN.SP[k]
        if sp.get("swim"):
            y = F.GT - sp["hip_h"] * sp["L"] * 0.95 + 10
            return (x + (110 if (victim == "b" and s.land) else 0), y)
        if sp.get("mammal") and k != "paracera": y += 130 if sp["hip_h"] >= 0.28 else 250
        elif not sp["biped"]: y += 70 if sp["hip_h"] >= 0.28 else (120 if sp["hip_h"] >= 0.15 else 470)
        return x, y
    def set_env(s, t, env): s.envk.append((t, env))
    def home(s, t, who=None):
        for w in ((who,) if who else ("a", "b")):
            if s.dead[w] is None and s.gone[w] is None: s.k(w, t, x=AH if w == "a" else BH, **NEUT)
    def anchor(s, t):
        s.k("a", t); s.k("b", t); s.cam(t, *s.CAM[-1][1]) if s.CAM[-1][0] < t else None

    # ------------------------------------------------------------- moves (each returns its end time)
    def roar(s, who, t, big=False, d=2.2):
        s.anchor(t); bp = s.biped(who); p = -0.13 if bp else -0.04
        s.k(who, t + 0.15 * d, pitch=-0.04, neck=0.05, head=-0.05, m=0.1)
        s.k(who, t + 0.3 * d, pitch=(-0.18 if big else p), neck=-0.5 if big else -0.4, head=-0.3, m=1.0, tailup=-0.1, arm=-0.5)
        s.k(who, t + 0.75 * d, m=0.92, head=-0.2); s.k(who, t + d, pitch=0, neck=0.1, head=0, m=0.25, arm=0, tailup=0)
        o = s.other(who)
        if s.dead[o] is None: s.k(o, t + 0.4 * d, neck=0.22, head=0.06); s.k(o, t + d, neck=0.1, head=0)
        s.roar_snd(who, t + 0.25 * d) if not big or (s.ka if who == "a" else s.kb) != "trex" else s.sound(t + 0.25 * d, "t-rex-victory-roar", 0.9)
        s.shk.append((t + 0.3 * d, 8, 0.9))
        zx = 360 if who == "a" else 760
        s.cam(t + 0.15 * d, 1.18, zx, 770); s.cam(t + 0.85 * d, 1.18, zx, 770); s.cam(t + d, 1.0, 540, 880)
        return t + d

    def stare(s, t, d=1.8):
        s.anchor(t)
        for w, sg in (("a", 1), ("b", -1)):
            if s.dead[w] is None and s.gone[w] is None:
                base = AH if w == "a" else BH
                s.k(w, t + 0.5 * d, x=base + 40 * sg, neck=0.22, head=0.06, m=0.45); s.k(w, t + d, x=base, neck=0.1, head=0, m=0.2)
                s.g(w, t, "walk"); s.g(w, t + 0.5 * d, "pose")
        s.sound(t + 0.1, "dinosaur-growl-487679", 0.85, 0.5); s.sound(t + 0.6, "dinosaur-growls-431298", 1.1, 0.4)
        s.cam(t + 0.4 * d, 1.08, 540, 840); s.cam(t + d, 1.0, 540, 880)
        return t + d

    def stalk(s, who, t, d=2.6):
        """sneak in low and slow, head down"""
        s.anchor(t); sg = 1 if who == "a" else -1; base = AH if who == "a" else BH
        s.k(who, t + 0.2 * d, crouch=0.06, pitch=0.12, neck=0.32, head=0.22, m=0.15, tailup=0.1)
        s.k(who, t + 0.85 * d, x=base + 120 * sg); s.k(who, t + d, x=base + 120 * sg)
        s.g(who, t + 0.15 * d, "walk"); s.g(who, t + 0.85 * d, "pose")
        s.k(who, t + d + 0.6, x=base, **NEUT); s.sound(t + 0.2 * d, "dinosaur-growl-487679", 0.75, 0.45)
        for i in range(4): s.sound(t + 0.2 * d + i * 0.45, "STEP", 1.0, 0.35)
        s.cam(t + 0.3 * d, 1.15, 380 if who == "a" else 740, 840); s.cam(t + d, 1.1, 540, 860)
        return t + d + 0.6

    def clash(s, t, d=3.8):
        s.anchor(t)
        for w, sg in (("a", 1), ("b", -1)):
            base = AH if w == "a" else BH; con = CA if w == "a" else CB
            s.k(w, t + 0.25 * d, x=base - 40 * sg, crouch=0.045, pitch=0.1, neck=0.25, head=0.1, tailup=0.1, m=0.4, nd=-0.04, fd=0.05)
            s.k(w, t + 0.42 * d, x=con, pitch=0.2, neck=0.1, head=0.05, m=0.9, crouch=0)
            s.k(w, t + 0.5 * d, x=con - 30 * sg, pitch=-0.05, neck=-0.28, head=-0.3, m=0.5)
            s.k(w, t + 0.62 * d, x=con - 20 * sg, pitch=0.13, neck=0.2, head=0.1, m=0.6, nd=0.13, fd=-0.13, crouch=0.03, tailup=0.08)
            s.k(w, t + 0.75 * d, x=con + 20 * sg); s.k(w, t + 0.88 * d, x=con - 50 * sg)
            s.k(w, t + d, x=base, **NEUT)
            s.g(w, t + 0.27 * d, "run"); s.g(w, t + 0.42 * d, "pose")
        imp = t + 0.42 * d
        s.speed.append((t + 0.27 * d, imp)); s.sound(imp - 0.1, "dramatic-whoosh", 1.0, 0.8)
        for i in range(4): s.sound(t + 0.27 * d + i * 0.04, "STEP", 1.0, 0.7)
        s.hit(imp, 610, 760, 0.55, 30, "ab", ("hard-heavy-impact", "cinematic-impact-boom")); s.splash.append((imp, 1050, 1160, 0.7))
        s.dusts.append((t + 0.62 * d, t + 0.95 * d, "struggle"))
        s.sound(t + 0.62 * d, "dinosaur-growls-431298", 1.1, 0.5); s.sound(t + 0.7 * d, "dinosaur-growl-487679", 0.85, 0.5)
        s.cam(t + 0.4 * d, 1.0, 560, 880); s.cam(t + 0.5 * d, 1.22, 600, 820); s.cam(t + 0.85 * d, 1.08, 560, 860); s.cam(t + d, 1.0, 540, 880)
        s.drums.append((t, t + d))
        return t + d

    def _approach(s, who, t, d, near=True):
        """both step to striking range; returns (attacker x, victim x)"""
        o = s.other(who)
        xa_ = (CA - 25) if who == "a" else (CA - 25); xb_ = (CB + 30)
        s.k("a", t + 0.5 * d, x=xa_); s.k("b", t + 0.5 * d, x=xb_)
        s.g(who, t + 0.2 * d, "run"); s.g(who, t + 0.5 * d, "pose")
        return xa_, xb_

    def strike(s, who, t, kind="bite", d=2.4):
        """kind: bite | swipe | gore (head toss) | stomp"""
        s.anchor(t); o = s.other(who); xa_, xb_ = s._approach(who, t, d)
        sg = 1 if who == "a" else -1; xs = xa_ if who == "a" else xb_; xv = xb_ if who == "a" else xa_
        hx, hy = s.head_xy(o)
        w = who
        if kind in ("bite", "swipe"):
            s.k(w, t + 0.62 * d, x=xs - 15 * sg, pitch=-0.15, neck=-0.32, head=-0.1 if kind == "bite" else -0.22, m=1.0, arm=-0.9 if kind == "swipe" else 0)
            s.k(w, t + 0.8 * d, x=xs + 70 * sg, pitch=0.18, neck=0.32 if kind == "bite" else 0.1, head=0.3 if kind == "bite" else 0.16, m=0.1 if kind == "bite" else 0.7, arm=0.9 if kind == "swipe" else 0)
        elif kind == "gore":
            s.k(w, t + 0.62 * d, x=xs - 20 * sg, crouch=0.05, pitch=0.18, neck=0.4, head=0.35, m=0.2)
            s.k(w, t + 0.8 * d, x=xs + 80 * sg, pitch=-0.12, neck=-0.45, head=-0.3, m=0.6, crouch=0)
        else:  # stomp
            s.k(w, t + 0.62 * d, x=xs, pitch=-0.2, neck=-0.3, head=-0.2, m=0.8, nd=-0.2, nl=0.12, crouch=-0.02)
            s.k(w, t + 0.8 * d, x=xs + 40 * sg, pitch=0.16, neck=0.25, head=0.15, m=0.4, nd=0.0, nl=0.0, crouch=0.05)
        s.k(w, t + 0.9 * d, pitch=0.05, crouch=0); s.k(w, t + d + 0.5, x=s.fwd(w, 0), **NEUT)
        imp = t + 0.8 * d
        lift = 70 if kind == "gore" else 0
        s.k(o, t + 0.8 * d, x=xv); s.k(o, t + 0.9 * d, x=xv + 60 * sg, pitch=-0.18, neck=-0.32, head=-0.25, m=0.9, drop=-lift, r=-12 * sg if lift else 0, nd=-0.1, fd=0.05)
        s.k(o, t + 0.96 * d, x=xv + 80 * sg, drop=0, r=0, pitch=0, neck=0.05, head=0.1, m=0.5, nd=0, fd=0)
        if s.dead[o] is None: s.k(o, t + d + 0.5, x=s.fwd(o, 0), **NEUT)
        s.speed.append((t + 0.2 * d, t + 0.5 * d)); s.sound(t + 0.65 * d, "swing-whoosh", 1.0, 0.9)
        sf = {"bite": ("bone-crack", "body-hit-ground"), "swipe": ("body-hit-ground",), "gore": ("hard-heavy-impact", "bone-crack"), "stomp": ("hard-heavy-impact", "cinematic-impact-boom")}[kind]
        if kind == "stomp":
            s.hit(imp, (CA + 260) if who == "a" else (CB - 360), s.GB + 40, 0.5, 30, o, sf); s.dusts.append((imp, imp + 1.0, "stomp_" + who))
        else:
            s.hit(imp, hx, hy, 0.5 if kind != "gore" else 0.6, 24 if kind != "gore" else 30, o, sf, slash=(kind == "swipe"))
        s.kinds.append((imp, kind, who))
        s.roar_snd(s.other(who), imp + 0.08, 0.55, 1.1)
        zx = 640 if who == "a" else 440
        s.cam(t + 0.4 * d, 1.12, 540, 820); s.cam(t + 0.8 * d, 1.2, zx, 790); s.cam(t + d + 0.5, 1.0, 540, 880)
        return t + d + 0.5

    def dodge(s, who, t, d=2.2):
        """`who` lunges, the other hops back -> miss"""
        s.anchor(t); o = s.other(who); xa_, xb_ = s._approach(who, t, d); sg = 1 if who == "a" else -1
        xs = xa_ if who == "a" else xb_; xv = xb_ if who == "a" else xa_
        s.k(who, t + 0.62 * d, x=xs - 15 * sg, pitch=-0.15, neck=-0.32, head=-0.1, m=1.0)
        s.k(who, t + 0.8 * d, x=xs + 90 * sg, pitch=0.22, neck=0.35, head=0.3, m=0.05)
        s.k(who, t + 0.9 * d, pitch=0.1, neck=0.2); s.k(who, t + d, x=s.fwd(who, 0), **NEUT)
        s.k(o, t + 0.66 * d, x=xv, crouch=0.05); s.k(o, t + 0.76 * d, x=xv + 90 * sg, drop=-60, crouch=0, pitch=-0.12, neck=-0.2)
        s.k(o, t + 0.88 * d, x=xv + 130 * sg, drop=0, pitch=0.05, neck=0.15, m=0.6); s.k(o, t + d, x=s.fwd(o, 0), **NEUT)
        s.sound(t + 0.75 * d, "swing-whoosh", 0.9, 1.0); s.sound(t + 0.86 * d, "STEP", 1.0, 0.7); s.speed.append((t + 0.6 * d, t + 0.82 * d))
        s.cam(t + 0.6 * d, 1.15, 560, 800); s.cam(t + d, 1.0, 540, 880)
        return t + d

    def pounce(s, who, t, d=2.6):
        """leap through the air onto the other"""
        s.anchor(t); o = s.other(who); sg = 1 if who == "a" else -1; base = s.fwd(who, 0)
        con = CA if who == "a" else CB; xv = CB + 30 if who == "a" else CA - 25
        s.k(o, t + 0.3 * d, x=xv)
        s.k(who, t + 0.3 * d, x=base - 30 * sg, crouch=0.08, pitch=0.15, neck=0.3, m=0.4)
        s.k(who, t + 0.42 * d, x=base + 120 * sg, drop=-180, crouch=0, pitch=-0.1, neck=-0.1, m=1.0, nd=-0.25, fd=0.2, nl=0.15, fl=0.15)
        s.k(who, t + 0.55 * d, x=con + 40 * sg, drop=-120, pitch=0.2, neck=0.3, head=0.25)
        s.k(who, t + 0.62 * d, x=con + 20 * sg, drop=0, nd=0, fd=0, nl=0, fl=0, crouch=0.04, m=0.2)
        imp = t + 0.62 * d
        s.k(o, imp, x=xv); s.k(o, imp + 0.12, x=xv + 90 * sg, pitch=-0.2, neck=-0.35, head=-0.25, m=0.9, drop=40, r=-8 * sg)
        s.k(o, t + 0.85 * d, x=xv + 80 * sg, drop=0, r=0, pitch=0, neck=0.1, head=0, m=0.4)
        s.k(who, t + d, x=s.fwd(who, 0), **NEUT); s.k(o, t + d, x=s.fwd(o, 0), **NEUT)
        hx, hy = s.head_xy(o)
        s.hit(imp, hx, hy + 40, 0.6, 32, o, ("hard-heavy-impact", "cinematic-impact-boom", "bone-crack"))
        s.sound(t + 0.33 * d, "dramatic-whoosh", 1.0, 1.0); s.speed.append((t + 0.32 * d, imp)); s.dusts.append((imp, imp + 0.9, "land_" + o))
        s.cam(t + 0.3 * d, 1.1, 540, 760); s.cam(t + 0.5 * d, 1.0, 560, 720); s.cam(imp, 1.2, 600, 820); s.cam(t + d, 1.0, 540, 880)
        return t + d

    def shove(s, who, t, d=3.0):
        """locked together, `who` drives the other backwards"""
        s.anchor(t); o = s.other(who); sg = 1 if who == "a" else -1
        s.k("a", t + 0.3 * d, x=CA - 20, pitch=0.13, neck=0.2, head=0.1, m=0.6, nd=0.13, fd=-0.13, crouch=0.03)
        s.k("b", t + 0.3 * d, x=CB + 30, pitch=0.13, neck=0.2, head=0.1, m=0.6, nd=0.13, fd=-0.13, crouch=0.03)
        s.g("a", t, "run"); s.g("b", t, "run"); s.g("a", t + 0.3 * d, "pose"); s.g("b", t + 0.3 * d, "pose")
        for i, f in enumerate((0.45, 0.6, 0.75, 0.9)):
            push = 60 * (i + 1) * sg
            s.k("a", t + f * d, x=CA - 20 + push + (8 if i % 2 else -8)); s.k("b", t + f * d, x=CB + 30 + push + (8 if i % 2 else -8))
        s.k(who, t + d + 0.5, x=s.fwd(who, 0), **NEUT); s.k(o, t + d + 0.5, x=s.fwd(o, 0), **NEUT)
        s.g(o, t + 0.4 * d, "walk"); s.g(o, t + 0.95 * d, "pose"); s.g(who, t + 0.4 * d, "walk"); s.g(who, t + 0.95 * d, "pose")
        s.hit(t + 0.3 * d, 610, 760, 0.45, 22, None, ("hard-heavy-impact",))
        s.dusts.append((t + 0.35 * d, t + d, "struggle"))
        for i in range(5): s.sound(t + 0.4 * d + i * 0.35, "STEP", 1.0, 0.6)
        s.sound(t + 0.45 * d, "dinosaur-growls-431298", 1.0, 0.6); s.roar_snd(who, t + 0.6 * d, 0.6)
        s.cam(t + 0.3 * d, 1.15, 560, 820); s.cam(t + d, 1.12, 560 + 160 * sg, 820); s.cam(t + d + 0.5, 1.0, 540, 880)
        return t + d + 0.5

    def knockdown(s, who, t, d=4.2):
        """`who` hits hard, the other falls, then gets back up"""
        t1 = s.strike(who, t, "gore" if not s.biped(who) else "bite", d=2.2) - 0.5
        o = s.other(who); sg = 1 if who == "a" else -1; xv = s.fwd(o, 0)
        s.k(o, t1 - 0.3, x=xv); s.k(o, t1, x=xv + 40 * sg, r=-30 * sg, drop=-60, m=1.0); s.k(o, t1 + 0.3, x=xv + 70 * sg, r=-55 * sg, drop=60)
        s.k(o, t1 + 0.42, r=8 * sg, drop=170, m=0.8); s.k(o, t1 + 1.1, r=6 * sg, drop=170, m=0.4)
        s.k(o, t1 + 1.6, r=-6 * sg, drop=60, crouch=0.05, m=0.5); s.k(o, t + d, x=xv, r=0, drop=0, **{k_: v for k_, v in NEUT.items() if k_ not in ("r", "drop")})
        s.hit(t1 + 0.42, 980 if o == "b" else 300, (s.GB if o == "b" else F.GT) - 40, 0.4, 28, None, ("heavy-body-fall",)); s.dusts.append((t1 + 0.4, t1 + 1.6, "land_" + o))
        s.cam(t1 + 0.4, 1.1, 820 if o == "b" else 300, 900); s.cam(t + d, 1.0, 540, 880)
        return t + d

    def finisher(s, who, t, d=4.4):
        """bite the neck, shake, throw -> the other stays down"""
        s.anchor(t); o = s.other(who); sg = 1 if who == "a" else -1
        con = CA + 65 if who == "a" else CB - 60; xv = CB if who == "a" else CA
        s.k(who, t + 0.3 * d / 4.4, x=s.fwd(who, -30), crouch=0.05, pitch=0.16, neck=0.3, head=0.15, m=0.5, tailup=0.15)
        s.k(who, t + 0.65, x=con, pitch=0.22, neck=0.05, head=0.05, m=1.0, crouch=0, tailup=0); s.k(who, t + 0.74, m=0.22)
        s.g(who, t + 0.35, "run"); s.g(who, t + 0.65, "pose")
        tt = t + 0.95; k_ = 0
        while tt < t + 2.2:
            s.k(who, tt, neck=0.28 if k_ % 2 == 0 else -0.18, head=0.3 if k_ % 2 == 0 else -0.26, x=con + (0 if k_ % 2 == 0 else 25) * sg); tt += 0.21; k_ += 1
        s.k(who, t + 2.25, x=con + 20 * sg, neck=0.32, head=0.32, pitch=0.12); s.k(who, t + 2.7, neck=-0.58, head=-0.42, pitch=-0.1, m=0.5)
        s.k(who, t + 3.05, neck=-0.2, head=-0.15, m=0.3, pitch=0); s.k(who, t + 3.4, neck=0.05, head=0)
        s.k(o, t + 0.4, x=xv, m=0.3); s.k(o, t + 0.65, x=xv); s.k(o, t + 0.8, x=xv + 20 * sg, pitch=-0.1, neck=-0.36, head=-0.3, m=1.0)
        s.couple.append((t + 0.8, t + 2.25, who))
        land_x = 1240 if o == "b" else -60
        s.k(o, t + 2.25, x=xv + 30 * sg, r=-10 * sg); s.k(o, t + 2.5, x=xv + 120 * sg, r=-30 * sg, drop=-100)
        s.k(o, t + 2.8, x=land_x - 10 * sg, r=-55 * sg, drop=-170, m=1.0)
        s.k(o, t + 3.12, x=land_x + 5 * sg, r=-24 * sg, drop=60, nl=0.1, fl=0.12, nd=-0.05, fd=0.05); s.k(o, t + 3.26, x=land_x, r=7 * sg, drop=178, m=0.8)
        s.k(o, t + 3.4, r=2 * sg, drop=160); s.k(o, t + 3.6, r=6 * sg, drop=176, m=0.35)
        s.dead[o] = t + 3.12
        s.speed.append((t + 0.42, t + 0.67)); s.sound(t + 0.35, "dramatic-whoosh", 1.0, 0.8)
        hx, hy = s.head_xy(o)
        s.hit(t + 0.65, hx, hy, 0.5, 30, o, ("hard-heavy-impact", "bone-snap", "cinematic-impact-boom"))
        s.roar_snd(s.other(who), t + 0.8, 0.7, 1.1)
        for i in range(3): s.sound(t + 1.0 + i * 0.4, "bone-crack", 1.0 + 0.08 * i, 0.55)
        s.sound(t + 2.35, "dramatic-whoosh", 0.9, 1.0)
        lx = 980 if o == "b" else 260; ly = (s.GB if o == "b" else F.GT) - 40
        s.hit(t + 3.26, lx, ly, 0.4, 32, None, ("heavy-body-fall", "cinematic-impact-boom")); s.dusts.append((t + 3.24, t + 4.4, "land_" + o))
        s.splash.append((t + 3.26, 1000 if o == "b" else 200, 1180, 1.5))
        s.cam(t + 0.3, 1.12, 380 if who == "a" else 700, 820); s.cam(t + 0.65, 1.2, 640 if who == "a" else 440, 800)
        s.cam(t + 2.2, 1.12, 660 if who == "a" else 420, 820); s.cam(t + 2.75, 1.0, 700 if who == "a" else 380, 760)
        s.cam(t + 3.3, 1.1, 760 if who == "a" else 300, 900); s.cam(t + d, 1.0, 540, 860)
        s.drums.append((t, t + 3.3))
        return t + d

    def flee(s, who, t, d=3.0):
        """the loser turns around and runs off screen"""
        s.anchor(t); sg = 1 if who == "a" else -1; base = s.fwd(who, 0)
        s.k(who, t + 0.25 * d, turn=1.0, neck=-0.1, head=-0.1, m=0.6); s.k(who, t + 0.4 * d, turn=-1.0)
        s.k(who, t + d, x=base - 900 * sg, turn=-1.0, neck=0.2, m=0.3); s.g(who, t + 0.4 * d, "run")
        s.gone[who] = t + d; s.roar_snd(who, t + 0.15 * d, 0.5, 1.2)
        for i in range(6): s.sound(t + 0.4 * d + i * 0.3, "STEP", 1.0, 0.5 - i * 0.06)
        o = s.other(who)
        if s.dead[o] is None: s.k(o, t + 0.5 * d, x=s.fwd(o, 60), neck=0.25, m=0.6); s.g(o, t + 0.3 * d, "walk"); s.g(o, t + 0.5 * d, "pose")
        s.cam(t + 0.3 * d, 1.05, 540 - 120 * sg, 860)
        return t + d

    def limp(s, who, t, d=3.4):
        """wounded: turns away and limps off slowly"""
        s.anchor(t); sg = 1 if who == "a" else -1; base = s.fwd(who, 0)
        s.k(who, t + 0.25 * d, turn=1.0, neck=-0.05, m=0.5); s.k(who, t + 0.45 * d, turn=-1.0, pitch=0.08, neck=0.3, head=0.2)
        for i in range(6):
            tt = t + 0.45 * d + i * 0.55 * d / 6
            s.k(who, tt, x=base - (i + 1) * 110 * sg, drop=18 if i % 2 else 0, r=(3 if i % 2 else -2) * sg)
        s.g(who, t + 0.45 * d, "walk"); s.gone[who] = t + d
        s.roar_snd(who, t + 0.3 * d, 0.4, 1.25)
        return t + d

    def victory(s, who, t, d=2.8):
        s.label_win = (t, who)
        return s.roar(who, t, big=True, d=d)

    def chase(s, t, d=3.0, who="a"):
        """both run, the world scrolls past"""
        s.anchor(t); s.pan.append((t, t + d))
        s.g("a", t, "run"); s.g("b", t, "run"); s.g("a", t + d, "pose"); s.g("b", t + d, "pose")
        s.k("a", t + 0.3 * d, x=AH + 120, pitch=0.12, neck=0.2, m=0.9); s.k("b", t + 0.3 * d, x=BH - 60, turn=1.0)
        s.k("b", t + 0.32 * d, turn=-1.0); s.k("a", t + d, x=AH + 160); s.k("b", t + d, x=BH - 40, turn=-1.0)
        s.speed.append((t + 0.2 * d, t + d)); s.k("b", t + d + 0.4, turn=1.0); s.k("a", t + d + 0.4, x=AH, **NEUT); s.k("b", t + d + 0.5, x=BH, **NEUT)
        for i in range(int(d / 0.28)): s.sound(t + i * 0.28, "STEP", 1.0, 0.6)
        s.cam(t + 0.3 * d, 1.08, 600, 860); s.cam(t + d + 0.5, 1.0, 540, 880)
        return t + d + 0.5

    # ------------------------------------------------------------- rendering
    def finalize(s):
        def merge(keys):
            out = []
            for tk, v in sorted(keys, key=lambda z: z[0]):
                if out and tk - out[-1][0] < 1e-3: out[-1] = (out[-1][0], dict(out[-1][1], **v))
                else: out.append((tk, v))
            return out
        s.TA, s.TB = F.build(merge(s.K["a"])), F.build(merge(s.K["b"]))
        s.CAMk = sorted(s.CAM, key=lambda z: z[0])
        for w in ("a", "b"): s.G[w].sort(key=lambda z: z[0])
        s.envk.sort(key=lambda z: z[0])
        s._tr = True

    def camv(s, t):
        # v19.1 calm camera: low-pass the keyed camera (triangle window +-1.2 s) and halve how far it swings
        # from the shot's centre, so the background no longer slides left/right every time a fighter steps
        if not hasattr(s, "_ck"):
            s._ck = [[(k, v[i]) for k, v in s.CAMk] for i in range(3)]
            xs = [v for _, v in s._ck[1]]; s._cx0 = sum(xs) / len(xs)
        CALM = float(os.environ.get("CAM_CALM", "1"))
        if CALM > 0:
            acc = [0.0, 0.0, 0.0]; wsum = 0.0
            for j in range(-4, 5):
                w = 5 - abs(j); u = t + j * 0.3 * CALM; wsum += w
                for i in range(3): acc[i] += w * F.track(s._ck[i], u)
            z, x, y = (v / wsum for v in acc)
            x = s._cx0 + (x - s._cx0) * (1 - 0.5 * min(1, CALM)); z = 1 + (z - 1) * 0.8
        else:
            z, x, y = tuple(F.track(s._ck[i], t) for i in range(3))
        if BEAUTY:   # slow handheld-style drift so the shot never feels frozen
            z *= 1 + 0.018 * math.sin(t * 0.19); x += 16 * math.sin(t * 0.23); y += 9 * math.sin(t * 0.31 + 1)
        return z, x, y
    def shake(s, t):
        v = sum(A_ * math.exp(-(t - t0) / (d * 0.35)) for t0, A_, d in s.shk if 0 <= t - t0 < d * 2)
        if any(c0 < t < c1 for c0, c1, _ in s.couple): v += 9
        return v
    def env_at(s, t):
        e = s.envk[0][1]
        for tk, ev in s.envk:
            if t >= tk: e = ev
        return e

    def background(s, env, t):
        pan = 100 + sum(max(0, min(t, b) - a) * 260 for a, b in s.pan)
        if env in SC.SCENES:
            bw = (LCW if s.land else W) + 700; key = ("sc", env, bw)
            if key not in R.BGC: R.BGC[key] = SC.build(env, bw, H)
            x = int(pan % 600); return R.BGC[key].crop((x, 0, x + (LCW if s.land else W), H))
        if s.land:
            img = wide_bg({"sunset": "dusk", "night": "dark", "volcano": "fire"}.get(env, "land"), pan).copy()
            if env == "river": river_draw(img, OX)
            return img
        if env == "river": img = river_bg(pan)
        elif env == "sunset": img = R.bg("dusk", pan).copy()
        elif env == "night": img = R.bg("dark", pan).copy()
        elif env == "volcano": img = R.bg("fire", pan).copy()
        elif env == "rain": img = R.bg("land", pan).copy()
        else: img = R.bg("land", pan).copy()
        return img

    def grade(s, img, env, t):
        if env in SC.SCENES:
            SC.weather(img, env, t, img.size[0], img.size[1]); return img
        if env == "sunset":
            L = Image.new("RGBA", img.size, (255, 140, 60, 50)); img.alpha_composite(L)
        elif env == "night":
            img = ImageEnhance.Brightness(img.convert("RGB")).enhance(0.62).convert("RGBA")
            L = Image.new("RGBA", img.size, (40, 60, 140, 70)); img.alpha_composite(L)
            d = ImageDraw.Draw(img); mx, my = (1900, 560) if s.land else (800, 160); d.ellipse((mx, my, mx + 140, my + 140), fill=(250, 246, 220), outline=DK, width=5)
        elif env == "rain":
            img = ImageEnhance.Brightness(img.convert("RGB")).enhance(0.78).convert("RGBA")
            L = Image.new("RGBA", img.size, (70, 90, 110, 60)); img.alpha_composite(L)
            d = ImageDraw.Draw(img); rnd = random.Random(int(t * 30))
            for _ in range(260):
                x, y = rnd.uniform(-100, W), rnd.uniform(0, H); d.line([(x, y), (x + 14, y + 46)], fill=(210, 225, 240), width=2)
            if (t % 7.0) < 0.12: img.alpha_composite(Image.new("RGBA", img.size, (255, 255, 255, 120)))
        elif env == "volcano":
            L = Image.new("RGBA", img.size, (255, 80, 30, 35)); img.alpha_composite(L)
            d = ImageDraw.Draw(img); rnd = random.Random(int(t * 10))
            for _ in range(30):
                x = rnd.uniform(0, W); y = (rnd.uniform(0, H) + t * 120) % H; d.ellipse((x - 4, y - 4, x + 4, y + 4), fill=(255, 150, 60))
        return img

    # ------------------------------------------------------------- impact feel
    def warp(s, t):
        """hit-stop: animation nearly freezes for ~0.09 s on each hit, then catches up within 0.25 s (audio stays in sync)"""
        off = 0.0
        for t0, *_ in s.bl:
            u = t - t0
            if 0 <= u < 0.09: off += u * 0.9
            elif 0.09 <= u < 0.34: off += 0.081 * (1 - (u - 0.09) / 0.25)
        return t - off
    def gy(s, w): return F.GT if (w == "a" or s.land) else s.GB
    def blood_ground(s, img, t, ox):
        """droplets flying from the hit point, landing as splats that stay on the ground"""
        if not s.blood_lv: return
        if s.env_at(t) in SC.UNDER or s.env_at(t) == "ocean": return s.blood_water(img, t, ox)
        L = Image.new("RGBA", img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(L); g_ = 2600.0
        for t0, x, y, w, pw in s.bl:
            u = t - t0
            if u < 0: continue
            rnd = random.Random(int(t0 * 1000) + 7); sg = 1 if w == "b" else -1; gy = s.gy(w) + 40
            n = int((18 + 14 * pw) * (1.8 if s.blood_lv > 1 else 1.0))
            for k in range(n):
                a = math.radians(rnd.uniform(-75, 10)); sp = rnd.uniform(250, 950) * pw ** 0.5; r = rnd.uniform(4, 11) * (1.2 if s.blood_lv > 1 else 1.0)
                vx, vy = sg * sp * math.cos(a), sp * math.sin(a); x0, y0 = x + ox + rnd.uniform(-20, 20), y + rnd.uniform(-20, 20)
                yl = gy + rnd.uniform(-30, 90)   # landing depth
                # time to land: y0 + vy*T + g/2 T^2 = yl
                T = (-vy + math.sqrt(max(0, vy * vy + 2 * g_ * (yl - y0)))) / g_
                if u < T:
                    px, py = x0 + vx * u, y0 + vy * u + 0.5 * g_ * u * u; cvx, cvy = vx, vy + g_ * u; n_ = math.hypot(cvx, cvy) or 1
                    st = min(3.0, n_ / 260); ex, ey = px - cvx / n_ * r * st, py - cvy / n_ * r * st
                    d.line([(ex, ey), (px, py)], fill=(120, 6, 12, 255), width=int(r * 1.6)); d.ellipse((px - r, py - r, px + r, py + r), fill=(150, 10, 16, 255))
                else:   # splat on the ground, stays (fades a little)
                    lx = x0 + vx * T; a_ = int(235 * max(0.55, 1 - (u - T) / 10)); rr = r * rnd.uniform(1.6, 2.6)
                    d.ellipse((lx - rr * 1.6, yl - rr * 0.45, lx + rr * 1.6, yl + rr * 0.45), fill=(118, 8, 14, a_))
                    if k % 3 == 0: d.ellipse((lx - rr * 0.6 + rr, yl - rr * 0.2, lx + rr * 0.3 + rr, yl + rr * 0.2), fill=(150, 18, 22, a_))
            if u < 0.35:   # blood mist puff at the impact
                a_ = int(150 * (1 - u / 0.35)); R_ = 60 + 260 * u
                M = Image.new("RGBA", img.size, (0, 0, 0, 0)); ImageDraw.Draw(M).ellipse((x + ox + sg * 60 * u * 3 - R_, y - R_ * 0.7, x + ox + sg * 60 * u * 3 + R_, y + R_ * 0.7), fill=(170, 20, 24, a_))
                img.alpha_composite(M.filter(_IF.GaussianBlur(18)))
            if 0 < u < 1.6:   # drips from the wound area
                for j in range(int(u / 0.11) + 1):
                    v = u - j * 0.11
                    if 0 <= v < 0.5:
                        px = x + ox + sg * (20 + (j * 37) % 50); py = y + 40 + 0.5 * g_ * v * v
                        if py < gy: d.ellipse((px - 5, py - 7, px + 5, py + 7), fill=(140, 8, 14, 255))
        img.alpha_composite(L)
    def blood_water(s, img, t, ox):
        """in water blood does not fall: it blooms into drifting clouds; every hit also releases a bubble burst"""
        L = Image.new("RGBA", img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(L); B = Image.new("RGBA", img.size, (0, 0, 0, 0)); db = ImageDraw.Draw(B)
        for t0, x, y, w, pw in s.bl:
            u = t - t0
            if u < 0: continue
            rnd = random.Random(int(t0 * 1000) + 11); sg = 1 if w == "b" else -1; X = x + ox
            n = int((7 + 5 * pw) * (1.7 if s.blood_lv > 1 else 1.0))
            for k in range(n):
                vx = sg * rnd.uniform(60, 420) * pw ** 0.5; vy = rnd.uniform(-220, 120); drag = 2.2
                f_ = (1 - math.exp(-drag * u)) / drag
                px, py = X + vx * f_ + rnd.uniform(-30, 30), y + vy * f_ - 14 * u + rnd.uniform(-30, 30)   # slows down, then slowly rises
                R_ = (26 + 120 * min(1.0, u / 2.5) ** 0.6) * rnd.uniform(0.6, 1.3) * (1.2 if s.blood_lv > 1 else 1.0)
                a_ = int(215 * max(0.0, 1 - u / 9.0) * (0.7 + 0.3 * rnd.random()))
                if a_ > 0: d.ellipse((px - R_, py - R_ * 0.8, px + R_, py + R_ * 0.8), fill=(130, 10, 18, a_))
            if 0 < u < 3.0:   # thin trail from the wound
                for j in range(8):
                    v = j / 8; d.ellipse((X - 8 + sg * 30 * v * u, y + 10 - 40 * v * u - 6, X + 8 + sg * 30 * v * u, y + 10 - 40 * v * u + 6), fill=(140, 12, 20, int(160 * (1 - u / 3))))
            if u < 1.4:   # bubble burst
                for k in range(26):
                    a = rnd.uniform(0, 2 * math.pi); sp_ = rnd.uniform(80, 360); r = rnd.uniform(4, 13)
                    f_ = (1 - math.exp(-3 * u)) / 3; px = X + math.cos(a) * sp_ * f_; py = y + math.sin(a) * sp_ * f_ - 160 * u * u
                    db.ellipse((px - r, py - r, px + r, py + r), fill=(200, 236, 250, int(70 * (1 - u / 1.4))), outline=(240, 252, 255, int(240 * (1 - u / 1.4))), width=4)
        img.alpha_composite(L.filter(_IF.GaussianBlur(10))); img.alpha_composite(B)
    def wounds(s, layer, w, t, q, ox):
        """wound decals painted on the fighter, clipped to its silhouette, following its x / drop"""
        if not s.blood_lv: return layer
        evs = [e for e in s.bl if e[3] == w and t >= e[0]]
        if not evs: return layer
        M = Image.new("RGBA", layer.size, (0, 0, 0, 0)); d = ImageDraw.Draw(M)
        for t0, x, y, _, pw in evs:
            rnd = random.Random(int(t0 * 1000) + 3); u = t - t0
            q0 = F.sample(s.TA if w == "a" else s.TB, t0); dx = x - q0["x"]; cx = q["x"] + dx + (110 if (s.land and w == "b") else 0) + ox - (ox if False else 0)
            cx = q["x"] + dx + (110 if (s.land and w == "b") else 0); cy = y + (q["drop"] - q0["drop"])
            sz = 26 * pw * (1.3 if s.blood_lv > 1 else 1.0)
            for k in range(4):   # gash
                o = (k - 1.5) * sz * 0.45
                d.line([(cx - sz + o, cy - sz * 0.8), (cx + sz * 0.6 + o, cy + sz * 0.7)], fill=(110, 6, 12, 235), width=max(5, int(sz * 0.28)))
            for k in range(5):   # runs that grow downward over time
                rx = cx + rnd.uniform(-sz, sz); ln = min(1.0, u / 1.2) * rnd.uniform(40, 120) * pw
                d.line([(rx, cy), (rx + rnd.uniform(-6, 6), cy + ln)], fill=(130, 8, 14, 220), width=rnd.randint(5, 9))
        a = layer.getchannel("A"); M.putalpha(ImageChops.multiply(M.getchannel("A"), a))
        layer.alpha_composite(M); return layer

    def draw_fighter(s, img, who, t, q, gait, fl, rt):
        L = Image.new("RGBA", img.size, (0, 0, 0, 0)); s.draw_dino(L, who, t, q, gait, fl)
        env_ = s.env_at(rt); sp_ = DN.SP[s.ka if who == 'a' else s.kb]; L = _shade_layer(L, under=env_ in SC.UNDER, anchor=(q['x'] + (OX if s.land else 0), 300), scaly=not (sp_.get('swim') or sp_.get('mammal')), fur=(True if sp_.get('fur') else (0.5 if sp_.get('mammal') and not sp_.get('swim') else False)))
        bb = L.getbbox()
        if BEAUTY and bb and env_ not in SC.UNDER and env_ not in ("ocean",) and not DN.SP[s.ka if who == "a" else s.kb].get("swim"):
            gy_ = F.GT if (who == "a" or s.land) else F.GS; lift = max(0, gy_ - bb[3])          # contact shadow, fades when airborne
            if lift < 160:
                cx_ = (bb[0] + bb[2]) / 2; rw = (bb[2] - bb[0]) * 0.42 * (1 - lift / 320); al = int(110 * (1 - lift / 160))
                Sh = Image.new("L", img.size, 0); ImageDraw.Draw(Sh).ellipse((cx_ - rw, gy_ - 22, cx_ + rw, gy_ + 18), fill=al)
                Sh = Sh.filter(_IF.GaussianBlur(14)); img.paste((20, 14, 8), (0, 0), Sh)
        if s.blood_lv and any(e[3] == who and rt >= e[0] for e in s.bl): L = s.wounds(L, who, rt, q, 0)
        if env_ not in SC.UNDER: L = _blend_fighter(L, img)
        img.alpha_composite(L)
    def draw_dino(s, img, who, t, q, gait, fl):
        kind = s.ka if who == "a" else s.kb
        scale, ground = (F.ST, F.GT) if who == "a" or s.land else (F.SS, F.GS)
        if s.land and who == "b": q = dict(q); q["x"] = q["x"] + 110   # same ground line -> give the right fighter a little more room
        flip = who == "b"; turn = q.get("turn", 1.0)
        if turn < 0: flip = not flip
        sx = abs(turn)
        if sx < 0.08: return
        if sx > 0.98:
            F.dino(img, kind, gait, t, q, scale, ground, flip, fl); return
        L = Image.new("RGBA", img.size, (0, 0, 0, 0)); F.dino(L, kind, gait, t, q, scale, ground, flip, fl)
        bb = L.getbbox()
        if not bb: return
        cx = q["x"]; part = L.crop(bb); nw = max(1, int(part.width * sx))
        part = part.resize((nw, part.height), Image.BICUBIC)
        img.alpha_composite(part, (int(cx + (bb[0] - cx) * sx), bb[1]))

    def frame(s, t):
        if not s._tr: s.finalize()
        ox = OX if s.land else 0
        if s.land: F.W = LCW
        try:
            img = s._frame(t, ox)
        finally:
            F.W = W
        return img

    def _frame(s, t, ox):
        env = s.env_at(t); img = s.background(env, t)
        rt = t; t = s.warp(rt)   # t = animation time (hit-stop), rt = real time for effects
        tq = F.sample(s.TA, t); sq = F.sample(s.TB, t)
        tq["pitch"] += 0.012 * math.sin(t * 2.4); sq["pitch"] += 0.012 * math.sin(t * 2.1 + 1)
        for k_, q_ in ((s.ka, tq), (s.kb, sq)):
            if not DN.SP[k_]["biped"] and q_["pitch"] < 0: q_["pitch"] *= 0.3
        for c0, c1, w in s.couple:
            if c0 < t < c1:
                att, vic = (tq, sq) if w == "a" else (sq, tq); sg = 1 if w == "a" else -1
                ph = att["neck"]; vic["x"] += 70 * ph * sg; vic["r"] += -26 * ph * sg; vic["drop"] += -20 * abs(ph)
        tq["x"] += ox; sq["x"] += ox
        def fl(side):
            v = 0.0
            for who, t0, d in s.flash:
                if side in who and t0 <= t < t0 + d: v = max(v, 0.25 * (1 - (t - t0) / d))
            return v
        lieB = s.dead["b"] is not None and t > s.dead["b"]; lieA = s.dead["a"] is not None and t > s.dead["a"]
        s.draw_fighter(img, "b", t, sq, F.step(s.G["b"], t) if not lieB else "pose", fl("b"), rt)
        if env == "river": water_front(img, t, ox)
        if lieB: F.grass_fg(img, 700 + ox, W + ox, s.GB - 10)
        s.draw_fighter(img, "a", t + 0.2, tq, F.step(s.G["a"], t) if not lieA else "pose", fl("a"), rt)
        s.blood_ground(img, rt, ox)
        for d0, d1, kind in s.dusts:
            if d0 < t < d1:
                if kind == "struggle": F.dust(img, 560 + (tq["x"] - ox - 85) * 0.6 + ox, s.GB + 70, 0.35 + 0.1 * math.sin(t * 4), 0.8)
                elif kind.startswith("land_"): F.dust(img, (1000 if kind.endswith("b") else 260) + ox, (s.GB if kind.endswith("b") else F.GT) + 20, min(0.95, (t - d0) / (d1 - d0)), 1.1)
                elif kind.startswith("stomp_"): F.dust(img, (700 if kind.endswith("a") else 420) + ox, s.GB + 60, min(0.95, (t - d0) / (d1 - d0)), 1.0)
        if env == "river":
            for t0, x, y, big in s.splash: splash(img, x + ox, y, (t - t0) / 1.0, big)
        sp = 0.0
        for a0, a1 in s.speed: sp = max(sp, clamp((t - a0) / 0.2) * (1 - clamp((t - a1) / 0.15)))
        F.speedlines(img, sp, 500, 1400) if s.land else F.speedlines(img, sp)
        for t0, x, y, dd in s.bursts: F.burst(img, x + ox, y, (rt - t0) / dd)
        for t0, x, y in s.slashes: F.slash(img, x + ox, y, (rt - t0) / 0.7)
        for w, lie in (("b", lieB), ("a", lieA)):
            if lie and t > s.dead[w] + 0.6:
                d_ = ImageDraw.Draw(img); cx, cy = (950, s.GB - 190) if w == "b" else (260, F.GT - 230)
                for k_ in range(3): q = t * 4 + k_ * 2.1; F.star(d_, cx + ox + 80 * math.cos(q), cy + 22 * math.sin(q), 22)
        img = s.grade(img, env, rt)
        if any(0 <= rt - e[0] < 0.05 for e in s.bl): img.alpha_composite(Image.new("RGBA", img.size, (255, 250, 240, 70)))   # impact flash frame
        t = rt
        z, zx, zy = s.camv(t); sh = s.shake(t)
        z *= 1 + sum(0.055 * math.exp(-(t - e[0]) / 0.12) for e in s.bl if 0 <= t - e[0] < 0.6)   # zoom punch
        if sh: z = max(z, 1.06)
        if s.land:
            z = max(0.86, z * 0.88)   # a little wider in 16:9 so both fighters and the scene fit
            ow, oh = LW_, LH_; cw, ch = ow / z, oh / z; cx_, cy_ = zx + ox, zy + 130
            cmw, cmh = img.size
        else:
            ow, oh = W, H; cw, ch = W / z, H / z; cx_, cy_ = zx, zy; cmw, cmh = W, H
        x0 = min(max(cx_ - cw / 2 + sh * (0.6 * math.sin(t * 53) + 0.4 * math.sin(t * 31)) / z, 0), cmw - cw)
        y0 = min(max(cy_ - ch / 2 + sh * (0.6 * math.cos(t * 47) + 0.4 * math.sin(t * 29)) / z, 0), cmh - ch)
        if s.land or z > 1.001 or sh:   # v19.1: sub-pixel camera (integer crop made the background stutter while the camera moved)
            img = img.transform((ow, oh), Image.AFFINE, (cw / ow, 0, x0, 0, ch / oh, y0), resample=Image.BICUBIC)
        if BEAUTY:
            under_ = env in SC.UNDER
            _motes(img, t, under_, env)
            fg = _foreground(env, ow, oh, under_); dx_ = 0   # v19.1: foreground silhouettes no longer drift in 1-px steps
            img.alpha_composite(fg, (dx_, 0)) if dx_ >= 0 else img.alpha_composite(fg.crop((-dx_, 0, ow, oh)), (0, 0))
            img = _post(img, env, t, getattr(s, 'look', None))
        for l0, l1, txt in s.labels:
            if l0 <= t < l1: R.tag(img, ow // 2, 110 if s.land else 260, txt, RED, 58, R.pop_s(t, l0))
        return img

    def sfx(s, path, total, drums=True):
        import soundfile as sf
        from scipy.signal import resample_poly
        from sfx2 import Mixer, SR, norm, lp
        import sfxsynth as SX
        cache = {}
        def S_(key, pitch=1.0):
            k_ = (key, pitch)
            if k_ not in cache:
                if key.startswith("SX:"): x = SX.get(key[3:]).copy()
                elif key.startswith("PX:"):
                    x, sr = sf.read(os.path.join(HERE, "sounds", "px", key[3:] + ".wav"), dtype="float32")
                    if x.ndim > 1: x = x.mean(1)
                    if sr != SR: x = resample_poly(x, SR, sr).astype(np.float32)
                    x = norm(x, 1.0)
                else:
                    x, sr = sf.read(glob.glob(os.path.join(HERE, "sounds", f"*{key}*.wav"))[0], dtype="float32")
                    if x.ndim > 1: x = x.mean(1)
                if pitch != 1.0: x = resample_poly(x, 1000, int(1000 * pitch)).astype(np.float32)
                x = x.copy(); n = int(0.05 * SR); x[-n:] *= np.linspace(1, 0, n); cache[k_] = norm(x, 1.0) if not key.startswith("SX:") else x
            return cache[k_]
        def onsets(key, thr=0.35):
            x = S_(key); env_ = np.convolve(np.abs(x), np.ones(480) / 480, "same")
            idx = np.where((env_[1:] > thr * env_.max()) & (env_[:-1] <= thr * env_.max()))[0]; out = []
            for i in idx:
                if not out or i - out[-1] > SR * 0.3: out.append(i)
            return [x[i:i + int(0.5 * SR)] for i in out]
        STEPS = onsets("colossal-footsteps") + onsets("giant-footsteps")
        def px_steps(f):
            fp = os.path.join(HERE, "sounds", "px", f + ".wav")
            if not os.path.exists(fp): return []
            x = S_("PX:" + f); e_ = np.convolve(np.abs(x), np.ones(480) / 480, "same"); thr = 0.3 * e_.max()
            idx = np.where((e_[1:] > thr) & (e_[:-1] <= thr))[0]; out = []
            for i in idx:
                if not out or i - out[-1] > SR * 0.25: out.append(i)
            return [x[max(0, i - 400):i + int(0.4 * SR)] for i in out]
        TSTEP = {"step-snow": px_steps("px-snow-footsteps-335506"), "step-gravel": px_steps("px-footsteps-gravel-397986"),
                 "step-sand": px_steps("px-footsteps-gravel-357373"), "step-mud": px_steps("px-mud-footsteps-482564")}
        TERR = {"tundra": "step-snow", "snowforest": "step-snow", "canyon": "step-gravel", "savanna": "step-sand", "beach": "step-sand",
                "swamp": "step-mud", "jungle": "step-mud", "rain": "step-mud", "storm": "step-mud", "volcano": "step-gravel"}
        WATER = set(SC.UNDER)
        swim = lambda: DN.SP[s.ka].get("swim") or DN.SP[s.kb].get("swim")
        M = Mixer(total + 1.0); Mw = Mixer(total + 1.0); si = 0; rv = [0]
        def add(t0, x, g):
            (Mw if s.env_at(t0) in WATER else M).add(t0, x, g)
        def var(k, n):   # real Pixabay recordings first (rotating), synthesized variants mixed in for variety
            rv[0] += 1; pool = [f"PX:{f}" for f in REAL.get(k, ()) if os.path.exists(os.path.join(HERE, "sounds", "px", f + ".wav"))]
            pool += [f"SX:{k}-{1 + i}" for i in range(n)] if not pool or k in SYNTH_TOO else []
            return pool[rv[0] % len(pool)]
        for t0, key, pitch, g in sorted(s.snd, key=lambda z: z[0]):
            if t0 > total: continue
            env = s.env_at(t0)
            if key == "STEP":
                if env in WATER or env == "ocean" or swim():
                    add(t0, S_(var("water-swish", 3)), g * 0.6)
                    if env == "ocean": add(t0, S_(var("splash-small", 3)), g * 0.4)
                    continue
                add(t0, STEPS[si % len(STEPS)], g); si += 1
                if env in TERR:
                    ts = TSTEP.get(TERR[env]) or []
                    add(t0 + 0.01, ts[si % len(ts)] if ts else S_(var(TERR[env], 4)), g * 0.7)
            else:
                if key.startswith("SX:"):
                    base = key[3:].rsplit("-", 1)[0] if key[-1].isdigit() else key[3:]
                    if base in REAL: key = var(base, 2)
                add(t0, S_(key, pitch), g)
        # layered impacts: kind of attack, armour, blood, water
        kinds = sorted(s.kinds)
        for t0, x, y, w, pw in s.bl:
            if t0 > total: continue
            env = s.env_at(t0); kd = next((k for tk, k, _ in kinds if abs(tk - t0) < 0.05), "hit")
            victim = s.ka if w == "a" else s.kb; att = s.kb if w == "a" else s.ka
            add(t0, S_(var("hitstop-thump", 2)), 0.8 * pw)
            if env in WATER:
                add(t0, S_(var("underwater-impact", 2)), 0.9); add(t0 + 0.05, S_(var("bubbles", 3)), 0.8)
                if kd == "bite": add(t0, S_(var("bite-crunch", 3)), 0.6)
                continue
            if env == "ocean": add(t0 + 0.02, S_(var("splash-big", 2)), 0.8)
            if kd == "bite": add(t0, S_(var("bite-crunch", 3)), 0.95); add(t0 + 0.12, S_(var("flesh-tear", 2)), 0.6)
            elif kd == "swipe": add(t0 - 0.04, S_(var("claw-slash", 3)), 0.9)
            elif kd == "gore": add(t0, S_(var("horn-clack", 2)), 0.7); add(t0 + 0.08, S_(var("flesh-tear", 2)), 0.5)
            elif kd == "stomp": add(t0, S_(var("body-slam", 2)), 0.9); add(t0 + 0.05, S_(var("rock-debris", 2)), 0.6)
            else: add(t0, S_(var("body-slam", 2)), 0.7)
            if victim in ARMORED or att in ARMORED: add(t0, S_(var("armor-knock", 2)), 0.6)
            if s.blood_lv: add(t0 + 0.06, S_(var("blood-splat", 3)), 0.55 * (1.3 if s.blood_lv > 1 else 1.0))
        if s.bl:   # dramatic sting on the hardest hit
            tb = max(s.bl, key=lambda e: e[4])[0]
            if tb < total - 0.5: add(tb, S_("SX:stinger-1"), 0.45)
        # weather one-shots + looping ambience bed for each scene section
        marks = sorted([(0.0, s.env)] + list(s.envk)); bed_g = {"reef": 0.3, "kelp": 0.3, "deep": 0.36, "abyss": 0.36, "storm": 0.28, "ocean": 0.28, "beach": 0.25}
        for i, (a0, env) in enumerate(marks):
            a1 = min(total, marks[i + 1][0] if i + 1 < len(marks) else total)
            if a1 <= a0: continue
            pxb = REAL_AMB.get(env); pxp = os.path.join(HERE, "sounds", "px", (pxb or "") + ".wav")
            bed = S_("PX:" + pxb) * 0.8 if pxb and os.path.exists(pxp) else (S_("SX:amb-" + env) if env in SX.AMB else None)
            if bed is not None:
                tt_ = a0
                while tt_ < a1:
                    seg = bed[: int(min(len(bed) / SR, a1 - tt_) * SR)].copy(); f = min(len(seg), int(0.5 * SR)); seg[:f] *= np.linspace(0, 1, f); seg[-f:] *= np.linspace(1, 0, f)
                    M.add(tt_, seg, bed_g.get(env, 0.2)); tt_ += len(bed) / SR - 0.5
            if env == "storm":
                k = int(np.ceil(a0 / 3.0))
                while k * 3.0 < a1: M.add(k * 3.0, S_(var("thunder", 2)), 0.6); k += 1
            if env in ("tundra", "snowforest", "canyon"):
                tt_ = a0 + 1.0
                while tt_ < a1: M.add(tt_, S_(var("wind-gust", 2)), 0.35); tt_ += 6.5
            if env == "volcano":
                tt_ = a0 + 2.0
                while tt_ < a1: M.add(tt_, S_(var("lava-burst", 2)), 0.4); tt_ += 5.0
        if drums:
            for a0, a1 in s.drums: M.drums(a0, min(a1, total), bpm=150, inten=lambda t: 0.6, style="pop")
        M.fx += lp(Mw.fx, 1100) * 1.3   # under water everything is muffled
        M.write(path, fx_g=1.0, dr_g=0.22)

# ------------------------------------------------------------- river helpers
_RIV = {}
def river_bg(pan=100):
    key = int(pan) // 4
    if key in _RIV: return _RIV[key].copy()
    img = R.bg("land", pan).copy(); d = ImageDraw.Draw(img); rnd = random.Random(5)
    poly = [(600, 1320), (700, 1236), (790, 1172), (880, 1132), (1000, 1116), (1080, 1112), (1080, 1330)]
    d.polygon([(x - 14, y + 10) for x, y in poly], fill=(120, 96, 64)); d.polygon(poly, fill=(86, 150, 192))
    for _ in range(30):
        x = rnd.uniform(700, 1080); y = rnd.uniform(1130, 1310); d.line([(x, y), (x + rnd.uniform(30, 80), y)], fill=(150, 200, 226), width=4)
    if len(_RIV) > 200: _RIV.clear()
    _RIV[key] = img
    return img.copy()
def river_draw(img, ox=0):
    d = ImageDraw.Draw(img); rnd = random.Random(5); xe = img.width
    poly = [(600 + ox, 1320), (700 + ox, 1236), (790 + ox, 1172), (880 + ox, 1132), (1000 + ox, 1116), (xe, 1100), (xe, 1340)]
    d.polygon([(x - 14, y + 10) for x, y in poly], fill=(120, 96, 64)); d.polygon(poly, fill=(86, 150, 192))
    for _ in range(int(30 * xe / 1080)):
        x = rnd.uniform(700 + ox, xe); y = rnd.uniform(1130, 1310); d.line([(x, y), (x + rnd.uniform(30, 80), y)], fill=(150, 200, 226), width=4)
def water_front(img, t, ox=0):
    L = Image.new("RGBA", img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(L); xe = img.width
    poly = [(840 + ox, 1150), (1000 + ox, 1140), (xe, 1130), (xe, 1340), (640 + ox, 1330), (740 + ox, 1240)]
    d.polygon(poly, fill=(78, 142, 186, 165))
    for k in range(int(6 * (xe - ox) / 1080)):
        x = 860 + ox + k * 40 + 20 * math.sin(t * 1.3 + k); yy = 1152 + 4 * math.sin(t * 2 + k * 1.7)
        d.line([(x, yy), (x + 50, yy - 2)], fill=(220, 240, 250, 200), width=5)
    img.alpha_composite(L)
def splash(img, x, y, g, big=1.0):
    if not 0 <= g < 1: return
    L = Image.new("RGBA", img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(L); rnd = random.Random(int(x))
    for _ in range(int(26 * big)):
        an = rnd.uniform(math.pi * 1.05, math.pi * 1.95); sp = rnd.uniform(200, 520) * big
        px = x + math.cos(an) * sp * g; py = y + math.sin(an) * sp * g + 900 * g * g; r = rnd.uniform(8, 18) * (1 - g * 0.6) * big
        d.ellipse((px - r, py - r, px + r, py + r), fill=(200, 230, 245, int(230 * (1 - g))), outline=(60, 110, 150, int(200 * (1 - g))), width=3)
    img.alpha_composite(L)

MOVES = [  # (method, args, ชื่อไทย) — the catalogue
    ("roar", ("a",), "คำรามท้าทาย"), ("stare", (), "เผชิญหน้า จ้องตา"), ("stalk", ("a",), "ย่องเข้าหา"),
    ("clash", (), "พุ่งชน + ดันกัน"), ("strike", ("b", "swipe"), "ข่วน / ฟาดกรงเล็บ"), ("strike", ("a", "bite"), "งับ"),
    ("strike", ("b", "gore"), "ขวิด / ชนด้วยหัว"), ("strike", ("a", "stomp"), "กระทืบ"), ("dodge", ("b",), "หลบได้!"),
    ("pounce", ("a",), "กระโดดตะครุบ"), ("shove", ("a",), "ดันจนถอยกรูด"), ("knockdown", ("b",), "ล้มแล้วลุก"),
    ("chase", (), "วิ่งไล่ล่า"), ("finisher", ("a",), "งับคอ เขย่า เหวี่ยง"), ("victory", ("a",), "คำรามฉลองชัย"),
    ("flee", ("b",), "หันหลังหนี"), ("limp", ("b",), "เดินกะเผลกหนี"),
]
