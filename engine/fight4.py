"""T. rex vs Spinosaurus v4 — keyframed per-joint acting (dino45 pose P), smooth Catmull-Rom tracks, camera keys, slow-mo.
python3 fight4.py render START END PART.mp4   |  python3 fight4.py still a1 a2 ...  |  python3 fight4.py info"""
import sys, os, math, random, subprocess, json
_a = sys.argv[:]; sys.argv = [sys.argv[0]]
import render45 as R
sys.argv = _a
import dino45 as DN
from PIL import Image, ImageDraw, ImageFilter
W, H, FPS = 1080, 1920, 30; DK = R.DK
clamp = R.clamp
def sstep(u): u = clamp(u); return u * u * (3 - 2 * u)

# ---------------------------------------------------------------- keyframe tracks
def track(keys, t):
    """keys: sorted [(t, v)]. Catmull-Rom (uniform) between keys, eased in time -> smooth velocity, no overshoot at holds"""
    if t <= keys[0][0]: return keys[0][1]
    if t >= keys[-1][0]: return keys[-1][1]
    for i in range(len(keys) - 1):
        if keys[i][0] <= t <= keys[i + 1][0]: break
    t0, v1 = keys[i]; t1, v2 = keys[i + 1]; v0 = keys[i - 1][1] if i > 0 else v1; v3 = keys[i + 2][1] if i + 2 < len(keys) else v2
    u = sstep((t - t0) / (t1 - t0)) * 0.5 + (t - t0) / (t1 - t0) * 0.5
    u2, u3 = u * u, u * u * u
    return 0.5 * (2 * v1 + (-v0 + v2) * u + (2 * v0 - 5 * v1 + 4 * v2 - v3) * u2 + (-v0 + 3 * v1 - 3 * v2 + v3) * u3)
CH = ("x", "r", "drop", "m", "pitch", "neck", "head", "tailup", "crouch", "arm", "nd", "nl", "fd", "fl")
DEF = dict(r=0, drop=0, m=0.15, pitch=0, neck=0, head=0, tailup=0, crouch=0, arm=0, nd=0, nl=0, fd=0, fl=0)
def build(keys):
    """keys: [(t, {ch: v})] -> per-channel track lists (a channel holds its last value until it is keyed again)"""
    cur = dict(DEF); tr = {c: [] for c in CH}
    for t, kv in keys:
        cur.update(kv)
        for c in CH:
            if c in cur: tr[c].append((t, cur[c]))
    return tr
def sample(tr, t): return {c: track(v, t) for c, v in tr.items() if v}
def step(seq, t):
    g = seq[0][1]
    for t0, v in seq:
        if t >= t0: g = v
    return g

TREX = build([
 (0.0, dict(x=-170, pitch=0.05, neck=0.15, head=0.05, m=0.15)),
 (1.5, dict(x=-110)),
 (1.75, dict(pitch=-0.04, neck=0.05, head=-0.05, m=0.1, crouch=-0.005)),
 (2.05, dict(pitch=-0.13, neck=-0.38, head=-0.28, m=1.0, tailup=-0.1, arm=-0.45)),
 (2.65, dict(m=0.92, head=-0.2)),
 (2.95, dict(pitch=0.0, neck=0.1, head=0.0, m=0.25, arm=0.0, tailup=0.0, crouch=0.0)),
 (3.25, dict(neck=0.2, head=0.1)),
 (4.0, dict(crouch=0.03, pitch=0.1, neck=0.25, head=0.1, tailup=0.1, m=0.4, nd=-0.04, fd=0.05)),
 (4.5, dict(x=-150, pitch=0.03, crouch=0.045)),
 (5.1, dict(x=105, pitch=0.2, neck=0.1, head=0.05, m=0.9, crouch=0.0)),
 (5.4, dict(x=75, pitch=-0.05, neck=-0.28, head=-0.32, m=0.5)),
 (5.75, dict(x=85, pitch=0.13, neck=0.2, head=0.1, m=0.6, nd=0.13, fd=-0.13, crouch=0.03, tailup=0.08)),
 (6.25, dict(x=125)), (6.75, dict(x=55)), (7.2, dict(x=110)),
 (7.45, dict(x=90, pitch=0.08, neck=0.12)),
 (7.95, dict(x=80)),
 (8.12, dict(x=40, pitch=-0.08, neck=-0.32, head=0.45, m=0.9)),
 (8.5, dict(x=-40, head=-0.2, neck=-0.12, pitch=-0.05, nd=-0.12, nl=0.04, fd=0.04)),
 (8.75, dict(x=-70, head=0.25, nl=0.0)), (8.95, dict(head=-0.15)), (9.15, dict(head=0.06)),
 (9.9, dict(x=-140, crouch=0.05, pitch=0.16, neck=0.3, head=0.15, m=0.5, tailup=0.15, nd=-0.06, fd=0.08)),
 (10.25, dict(x=170, pitch=0.22, neck=0.05, head=0.05, m=1.0, crouch=0.0)),
 (10.34, dict(m=0.22)),
 (10.55, dict(neck=0.28, head=0.3, x=160)), (10.75, dict(neck=-0.18, head=-0.26, x=185)), (10.95, dict(neck=0.26, head=0.3, x=158)),
 (11.15, dict(neck=-0.2, head=-0.28, x=186)), (11.35, dict(neck=0.24, head=0.28, x=160)), (11.55, dict(neck=-0.15, head=-0.2, x=182)),
 (11.85, dict(x=180, neck=0.32, head=0.32, pitch=0.12)),
 (12.3, dict(neck=-0.58, head=-0.42, pitch=-0.1, m=0.5)),
 (12.65, dict(neck=-0.2, head=-0.15, m=0.3, pitch=0.0)),
 (13.0, dict(x=150, neck=0.05, head=0.0)),
 (13.75, dict(x=210)),
 (14.1, dict(pitch=-0.16, neck=-0.52, head=-0.32, m=1.0, arm=-0.5, tailup=-0.1)),
 (15.7, dict(m=0.9)),
 (16.3, dict(m=0.2, neck=0.0, head=0.0, pitch=0.0, arm=0.0, tailup=0.0)),
])
TREX_G = [(0, "walk"), (1.5, "pose"), (4.55, "run"), (5.1, "pose"), (10.0, "run"), (10.25, "pose"), (13.0, "walk"), (13.75, "pose")]
SPINO = build([
 (0.0, dict(x=1225, neck=0.1, m=0.2)),
 (1.5, dict(x=1150)),
 (2.05, dict(neck=-0.15, head=-0.1, pitch=-0.05)),
 (2.9, dict(neck=0.05, head=0.0, pitch=0.0)),
 (3.2, dict(pitch=-0.25, neck=-0.45, head=-0.22, m=1.0, arm=-0.9, tailup=-0.15)),
 (3.85, dict(m=0.9)),
 (4.05, dict(pitch=0.1, neck=0.25, head=0.1, crouch=0.03, m=0.4, arm=0.0, tailup=0.08, nd=-0.04, fd=0.05)),
 (4.5, dict(x=1190, crouch=0.045)),
 (5.1, dict(x=1010, pitch=0.2, m=0.9, crouch=0.0)),
 (5.4, dict(x=1045, neck=-0.3, head=-0.3, pitch=-0.05)),
 (5.75, dict(x=1040, pitch=0.13, neck=0.2, head=0.1, m=0.7, nd=0.13, fd=-0.13, crouch=0.03)),
 (6.25, dict(x=1080)), (6.75, dict(x=1010)), (7.2, dict(x=1065)),
 (7.45, dict(x=1085, pitch=-0.22, neck=-0.32, head=-0.22, m=1.0, arm=-0.9, nd=0.0, fd=0.0)),
 (7.95, dict(x=985, pitch=0.22, neck=0.1, head=0.16, arm=0.9, m=0.8)),
 (8.12, dict(x=960, m=0.3, arm=0.5)),
 (8.6, dict(x=1000, pitch=0.0, neck=-0.12, head=-0.1, m=0.9, arm=0.0)),
 (9.6, dict(m=0.3, neck=0.1, head=0.0)),
 (10.25, dict(x=1000, m=0.3)),
 (10.4, dict(x=1030, pitch=-0.1, neck=-0.36, head=-0.3, m=1.0)),
 (11.85, dict(x=1040, r=-10)),
 (12.1, dict(x=1130, r=-30, drop=-100)),
 (12.4, dict(x=1230, r=-55, drop=-170, m=1.0)),
 (12.72, dict(x=1250, r=-24, drop=60, nl=0.1, fl=0.12, nd=-0.05, fd=0.05)),
 (12.86, dict(x=1240, r=7, drop=178, m=0.8)),
 (13.0, dict(r=2, drop=160)),
 (13.2, dict(r=6, drop=176, m=0.35)),
 (14.6, dict(tailup=-0.25)), (14.9, dict(tailup=0.05)), (15.6, dict(tailup=-0.15, m=0.2)), (16.4, dict(tailup=0.0)),
])
SPINO_G = [(0, "walk"), (1.5, "pose"), (4.55, "run"), (5.1, "pose")]
CAM = build([])   # unused container
CAMK = [(0, (1.0, 540, 900)), (1.5, (1.05, 540, 880)), (1.95, (1.18, 360, 760)), (2.8, (1.18, 360, 760)), (3.15, (1.18, 760, 780)), (3.9, (1.18, 760, 780)),
        (4.35, (1.0, 540, 880)), (5.1, (1.0, 560, 880)), (5.25, (1.22, 600, 820)), (5.9, (1.08, 560, 860)), (7.4, (1.08, 600, 860)), (8.15, (1.16, 430, 800)),
        (8.7, (1.05, 500, 860)), (9.7, (1.12, 380, 820)), (10.25, (1.2, 640, 800)), (11.8, (1.12, 660, 820)), (12.35, (1.0, 700, 760)), (12.9, (1.1, 760, 900)),
        (13.6, (1.0, 540, 860)), (14.15, (1.1, 540, 780)), (16.8, (1.08, 560, 800))]
def cam(t): return tuple(track([(k, v[i]) for k, v in CAMK], t) for i in range(3))
SHK = [(2.05, 8, 0.8), (3.2, 7, 0.8), (5.15, 30, 0.7), (8.12, 22, 0.55), (10.25, 30, 0.7), (12.86, 32, 0.8), (14.1, 9, 1.4)]
def shake(t):
    a = sum(A * math.exp(-(t - t0) / (d * 0.35)) for t0, A, d in SHK if 0 <= t - t0 < d * 2)
    if 10.4 < t < 11.85: a += 9
    return a
# slow motion (anim time a runs at speed v inside [a0, a1])
SLOW = [(5.08, 5.7, 0.35), (10.15, 10.55, 0.35), (12.75, 13.0, 0.5)]; AT = 16.8
def a2w(a):
    w = a
    for a0, a1, v in SLOW: w += (min(max(a, a0), a1) - a0) * (1 / v - 1)
    return w
TL = a2w(AT)
def w2a(w):
    lo, hi = 0.0, AT
    for _ in range(40):
        m = (lo + hi) / 2
        if a2w(m) < w: lo = m
        else: hi = m
    return lo

# ---------------------------------------------------------------- drawing
ST, SS = 0.95, 0.8; GT, GS = 1330, 1170
KA = os.environ.get("FIGHT_A", "trex"); KB = os.environ.get("FIGHT_B", "spino")
NAME = {"trex": "ทีเร็กซ์", "spino": "สไปโนซอรัส", "tricera": "ไทรเซราทอปส์", "edmonto": "เอ็ดมอนโตซอรัส",
        "giga": "จิกาโนโตซอรัส", "carno": "คาร์โนทอรัส", "allo": "อัลโลซอรัส", "raptor": "ยูทาห์แรปเตอร์",
        "pachy": "แพคีเซฟาโลซอรัส", "anky": "แองคิโลซอรัส", "stego": "สเตโกซอรัส", "brachio": "แบรคิโอซอรัส", "therizino": "เทอริซิโนซอรัส", "parasaur": "พาราซอโรโลฟัส", "iguano": "อิกัวโนดอน", "dilo": "ไดโลโฟซอรัส", "styraco": "สไตราโคซอรัส", "kentro": "เคนโทรซอรัส", "baryonyx": "แบริออนิกซ์", "diplo": "ดิพโพลโดคัส", "mammoth": "แมมมอธ", "smilodon": "เสือเขี้ยวดาบ", "rhino": "แรดขนยาว", "sloth": "สลอธยักษ์", "sarco": "ซาร์โคซูคัส", "megalania": "เมกาลาเนีย", "quetzal": "เควตซัลโคแอตลัส", "paracera": "พาราเซราทีเรียม", "megalodon": "เมกาโลดอน", "mosasaurus": "โมซาซอรัส", "liopleurodon": "ไลโอพลูโรดอน", "elasmo": "อีลาสโมซอรัส", "dunkleosteus": "ดังเคิลออสเตียส", "livyatan": "ลิเวียทัน", "archelon": "อาร์คีลอน", "squid": "หมึกยักษ์"}
HIP = {k: (DN.W0 * 0.5 - 0.05 * DN.SP[k]["L"], DN.GROUND - DN.SP[k]["hip_h"] * DN.SP[k]["L"]) for k in set((KA, KB))}
def dino(img, kind, gait, t, q, scale, ground, flip, fl=0.0):
    P = dict(pitch=q["pitch"], neck=q["neck"], head=q["head"], tailup=q["tailup"], crouch=q["crouch"], arm=q["arm"], feet={"near": (q["nd"], q["nl"]), "far": (q["fd"], q["fl"])})
    s = DN.beast(kind, t, gait, max(0.0, min(1.0, q["m"])), P=P, walkd=(-q["x"] if flip else q["x"]) / scale); hx, hy = HIP[kind]
    if abs(q["r"]) > 0.05: s = s.rotate(-q["r"], resample=Image.BICUBIC, center=(hx, hy))
    s = s.resize((int(1600 * scale), int(1000 * scale)), Image.BICUBIC)
    if flip: s = s.transpose(Image.FLIP_LEFT_RIGHT); hx = 1600 - hx
    if fl > 0:
        wq = Image.new("RGBA", s.size, (255, 255, 255, 255)); wq.putalpha(s.getchannel("A").point(lambda v: int(v * fl))); s.alpha_composite(wq)
    img.alpha_composite(s, (int(q["x"] - hx * scale), int(ground + q["drop"] - 900 * scale)))
def star(d, x, y, r, col=(255, 230, 80)):
    pts = [(x + (r if k % 2 == 0 else r * 0.45) * math.cos(k * math.pi / 8 + 0.2), y + (r if k % 2 == 0 else r * 0.45) * math.sin(k * math.pi / 8 + 0.2)) for k in range(16)]
    d.polygon(pts, fill=col, outline=DK, width=6)
def burst(img, x, y, g):
    """impact: expanding star + ring + spark lines, fades out"""
    if not 0 <= g < 1: return
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(L); a = int(255 * (1 - g) ** 0.7)
    r = 60 + 160 * g ** 0.5; d.ellipse((x - r * 1.6, y - r * 1.6, x + r * 1.6, y + r * 1.6), outline=(255, 255, 255, a), width=max(2, int(14 * (1 - g))))
    for k in range(10):
        an = k * math.pi / 5 + 0.3; r0, r1 = r * 0.9, r * (1.5 + 0.4 * (k % 2)); d.line([(x + r0 * math.cos(an), y + r0 * math.sin(an)), (x + r1 * math.cos(an), y + r1 * math.sin(an))], fill=(255, 240, 160, a), width=8)
    star(d, x, y, r * 0.75 * (1 - 0.3 * g)); L.putalpha(L.getchannel("A").point(lambda v: min(v, a)))
    img.alpha_composite(L)
def slash(img, x, y, g):
    if not 0 <= g < 1: return
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(L); grow = min(1, g * 4); a = int(255 * (1 - g))
    for k in range(3):
        o = (k - 1) * 42; p0 = (x - 130 + o, y - 120 + o * 0.3); p1 = (p0[0] + 260 * grow, p0[1] + 240 * grow)
        d.line([p0, p1], fill=(255, 255, 255, a), width=14 - 3 * abs(k - 1))
    img.alpha_composite(L.filter(ImageFilter.GaussianBlur(1)))
def speedlines(img, g, y0=500, y1=1300):
    if g <= 0: return
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(L); rnd = random.Random(int(g * 1000) % 7)
    for k in range(22):
        y = rnd.uniform(y0, y1); x = rnd.uniform(-200, W); ln = rnd.uniform(160, 420); d.line([(x, y), (x + ln, y)], fill=(255, 255, 255, int(150 * g)), width=rnd.choice((3, 4, 6)))
    img.alpha_composite(L)
def dust(img, x, y, g, w=1.0):
    if g <= 0 or g >= 1: return
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(L); rnd = random.Random(3)
    for k in range(16):
        an = rnd.uniform(math.pi, 2 * math.pi); r = (60 + 300 * g * rnd.uniform(0.6, 1.2)) * w; rr = (50 + 60 * g) * w
        cx, cy = x + r * math.cos(an), y + 0.35 * r * math.sin(an); d.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), fill=(206, 188, 150, int(190 * (1 - g))))
    img.alpha_composite(L.filter(ImageFilter.GaussianBlur(7)))
def grass_fg(img, x0, x1, y):
    d = ImageDraw.Draw(img); rnd = random.Random(11)
    for r_ in range(3):
        for k in range(int((x1 - x0) / 7)):
            x = x0 + k * 7 + rnd.uniform(-4, 4); h = rnd.uniform(40, 90) * (1 - r_ * 0.2); yy = y + 30 + r_ * 18
            d.line([(x, yy), (x + rnd.uniform(-14, 14), yy - h)], fill=((88, 112, 58), (110, 134, 72), (126, 148, 84))[(k + r_) % 3], width=7)
BG = R.bg("land", 100).copy()
def frame(w):
    a = w2a(w); img = BG.copy()
    tq = sample(TREX, a); sq = sample(SPINO, a)
    tq["pitch"] += 0.012 * math.sin(a * 2.4); sq["pitch"] += 0.012 * math.sin(a * 2.1 + 1)   # breathing
    for k_, q_ in ((KA, tq), (KB, sq)):   # four-legged fighters do not rear up like a theropod
        if not DN.SP[k_]["biped"] and q_["pitch"] < 0: q_["pitch"] *= 0.3
    if 10.4 < a < 11.85:   # Spino is shaken by the bite: follows the T. rex head
        ph = (tq["neck"]); sq["x"] += 70 * ph; sq["r"] += -26 * ph; sq["drop"] += -20 * abs(ph)
    lie = a > 12.72
    flS = 0.25 * (1 - clamp((a - 10.25) / 0.12)) if 10.25 <= a else 0.0
    flT = 0.25 * (1 - clamp((a - 8.12) / 0.15)) if 8.12 <= a else 0.0
    if 5.15 <= a < 5.3: flS = flT = 0.15 * (1 - (a - 5.15) / 0.15)
    dino(img, KB, step(SPINO_G, a) if not lie else "pose", a, sq, SS, GS, True, flS)
    if lie: grass_fg(img, 700, W, GS - 10)
    dino(img, KA, step(TREX_G, a), a + 0.2, tq, ST, GT, False, flT)
    if 5.75 < a < 7.4: dust(img, 560 + (tq["x"] - 85) * 0.6, GS + 70, 0.35 + 0.1 * math.sin(a * 4), 0.8)
    if a > 12.84: dust(img, 1000, GS + 20, min(0.95, (a - 12.84) / 1.2), 1.1)
    speedlines(img, max(clamp((a - 4.6) / 0.2) * (1 - clamp((a - 5.1) / 0.15)), clamp((a - 10.02) / 0.1) * (1 - clamp((a - 10.27) / 0.12))))
    burst(img, 610, 760, (a - 5.15) / 0.55); burst(img, 430, 700, (a - 8.12) / 0.45); burst(img, 700, 700, (a - 10.25) / 0.5); burst(img, 980, GS - 40, (a - 12.86) / 0.4)
    slash(img, 400, 800, (a - 8.08) / 0.7)
    if a > 13.2:
        d = ImageDraw.Draw(img)
        for k in range(3): q = a * 4 + k * 2.1; star(d, 950 + 80 * math.cos(q), GS - 190 + 22 * math.sin(q), 22)
    z, zx, zy = cam(a); sh = shake(a)
    if sh: z = max(z, 1.06)
    cw, ch = W / z, H / z
    x0 = min(max(zx - cw / 2 + sh * (0.6 * math.sin(w * 53) + 0.4 * math.sin(w * 31)) / z, 0), W - cw)
    y0 = min(max(zy - ch / 2 + sh * (0.6 * math.cos(w * 47) + 0.4 * math.sin(w * 29)) / z, 0), H - ch)
    if z > 1.001 or sh: img = img.crop((int(x0), int(y0), int(x0 + cw), int(y0 + ch))).resize((W, H), Image.BICUBIC)
    R.tag(img, 540, 260, f"{NAME[KA]} VS {NAME[KB]}" if a < 14.0 else "ใครชนะ? คอมเมนต์!", R.RED, 66, R.pop_s(a, 0.2 if a < 14.0 else 14.2))
    return img.convert("RGB")

if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "info": print(json.dumps({"TL": TL, "frames": int(TL * FPS)})); json.dump({"TL": TL, "ev": {str(round(x / 20, 2)): a2w(x / 20) for x in range(0, int(AT * 20) + 1)}}, open(os.environ.get("TMAP", "fight_tmap.json"), "w"))
    elif mode == "still":
        ims = [frame(a2w(float(x))) for x in sys.argv[2:]]
        S = Image.new("RGB", (270 * len(ims), 480))
        for k, im in enumerate(ims): S.paste(im.resize((270, 480)), (k * 270, 0))
        S.save(os.environ.get("STILL_OUT", "stills.jpg"), quality=85)
    else:
        f0, f1, outp = int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
        pr = subprocess.Popen([os.environ.get("FFMPEG", "ffmpeg"), "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-threads", "2", "-pix_fmt", "yuv420p", outp], stdin=subprocess.PIPE)
        prog = os.environ.get("PROG_FILE")
        for k in range(f0, f1):
            pr.stdin.write(frame(k / FPS).tobytes())
            if prog and (k - f0) % 5 == 4: open(prog, "w").write(str(k - f0 + 1))
        pr.stdin.close(); pr.wait(); print("done", f0, f1)
