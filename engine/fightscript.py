# -*- coding: utf-8 -*-
"""ฉากต่อสู้ตามบท: แต่ละบรรทัดของบท = 1 ฉาก เลือกท่าจากคำในบรรทัด (คำราม / ปะทะ / กัด / ข่วน / ล้ม / ชนะ ...)
ใช้ท่าและเอฟเฟกต์ชุด v4 ของช่อง (fight4.py) มาต่อกันตามบท
env: FIGHT_A (ผู้ชนะ ซ้าย) FIGHT_B (ผู้แพ้ ขวา) SCRIPT_JSON = {"lines": [...], "durs": [วินาทีต่อบรรทัด หรือ null], "captions": true}
python fightscript.py info | still t1 t2 .. | render f0 f1 out.mp4 | sfx out.wav"""
import sys, os, json, math, random, subprocess, re, glob
ALIAS = {"trex": ["ทีเร็กซ์", "ที-เร็กซ์", "เร็กซ์", "ไทรันโน", "t-rex", "trex", "t. rex"],
         "spino": ["สไปโน", "spino"], "tricera": ["ไทรเซรา", "สามเขา", "tricera"], "edmonto": ["เอ็ดมอนโต", "ปากเป็ด", "edmonto"],
         "giga": ["จิกาโนโต", "กิกาโนโต", "giga"], "carno": ["คาร์โน", "carno"], "allo": ["อัลโล", "allo"], "raptor": ["แรปเตอร์", "ยูทาห์", "raptor"],
         "pachy": ["แพคี", "หัวโหนก", "pachy"], "anky": ["แองคิโล", "แองคี", "anky"], "stego": ["สเตโก", "stego"], "brachio": ["แบรคิโอ", "brachio"],
         "therizino": ["เทอริซิโน", "therizino"], "parasaur": ["พาราซอ", "parasaur"], "iguano": ["อิกัวโน", "iguano"], "dilo": ["ไดโลโฟ", "dilo"],
         "styraco": ["สไตราโค", "styraco"], "kentro": ["เคนโทร", "kentro"], "baryonyx": ["แบริออ", "baryonyx"], "diplo": ["ดิพโพล", "ดิปโพล", "diplo"], "mammoth": ["แมมมอธ", "mammoth"], "smilodon": ["เขี้ยวดาบ", "สมิโลดอน", "smilodon"], "rhino": ["แรด", "rhino"], "sloth": ["สลอธ", "sloth"], "sarco": ["ซาร์โค", "จระเข้", "sarco"], "megalania": ["เมกาลาเนีย", "megalania"], "quetzal": ["เควตซัล", "quetzal"], "paracera": ["พาราเซรา", "paracera"], "megalodon": ["เมกาโลดอน", "ฉลาม", "megalodon"], "mosasaurus": ["โมซา", "mosasaurus"], "liopleurodon": ["ไลโอ", "liopleurodon"], "elasmo": ["อีลาสโม", "elasmo"], "dunkleosteus": ["ดังเคิล", "dunkleosteus"], "livyatan": ["ลิเวียทัน", "วาฬ", "livyatan"], "archelon": ["อาร์คีลอน", "เต่า", "archelon"], "squid": ["หมึก", "squid"]}
def _first_kind(line, kinds):
    low = line.lower(); best = None
    for k in kinds:
        for al in ALIAS.get(k, []):
            i = low.find(al.lower())
            if i >= 0 and (best is None or i < best[0]): best = (i, k)
    return best[1] if best else None
def script_winner(lines, ka, kb):
    """who wins according to the script: 'X ชนะ' -> X ; 'X ล้ม/ตาย' -> the other one ; 'X ทุ่ม/เหวี่ยง/ฆ่า Y' -> X"""
    for ln in lines:
        ln2 = re.sub(r"ไม่(ยอม)?(แพ้|ล้ม|ตาย|ถอย|หนี)|ไม่ยอม", " ", ln)
        if re.search(r"ชนะ|ผู้ชนะ|ราชา|เจ้าแห่ง", ln2):
            k = _first_kind(ln2, (ka, kb))
            if k: return k
        if re.search(r"ล้ม|ตาย|พ่าย|แพ้|สิ้นใจ|น็อก|ปิดฉาก|ทุ่ม|เหวี่ยง|ฆ่า", ln2):
            k = _first_kind(ln2, (ka, kb))
            if k:
                active = re.search(r"ทุ่ม|เหวี่ยง|ฆ่า|ปิดฉาก", ln2)
                return k if active else (kb if k == ka else ka)
    return ka
_p = os.environ.get("SCRIPT_JSON")
if _p and os.path.exists(_p):
    _ls = [l for l in json.load(open(_p, encoding="utf-8")).get("lines", []) if l.strip()]
    _a, _b = os.environ.get("FIGHT_A", "trex"), os.environ.get("FIGHT_B", "spino")
    if _ls and script_winner(_ls, _a, _b) == _b:     # the winner always takes the left (winner) role
        os.environ["FIGHT_A"], os.environ["FIGHT_B"] = _b, _a
import fight4 as F
R, DN = F.R, F.DN
from PIL import Image, ImageDraw
import numpy as np
W, H, FPS = 1080, 1920, 30
KA, KB = F.KA, F.KB
NAME = F.NAME
clamp = R.clamp
HERE = os.path.dirname(os.path.abspath(__file__))

KW = [("finale", r"ล้ม|ตาย|พ่าย|แพ้|ปิดฉาก|สิ้นใจ|ทุ่ม|เหวี่ยงลง|ฆ่า|จบชีวิต|ล้มลง|น็อก"),
      ("victory", r"ชนะ|ผู้ชนะ|ราชา|เจ้าแห่ง|ประกาศศักดา|ฉลอง"),
      ("roar", r"คำราม|แผด|ขู่|ร้อง|ตะโกน|ส่งเสียง"),
      ("clash", r"ปะทะ|พุ่งชน|ชนกัน|ชน|พุ่งเข้า|ดัน|ผลัก|ประจัญ|ห้ำหั่น|ต่อสู้|สู้กัน|บุก"),
      ("bite", r"กัด|งับ|ขย้ำ|ฟัน"),
      ("swipe", r"ข่วน|ฟาด|พาด|ฟัด|ตบ|สะบัด|ตี|โจมตี|แทง|ขวิด|ตะปบ|เล็บ|หาง|ทิ่ม|ต่อย|เตะ")]

def actor_of(line, default):
    low = line.lower(); best = None
    for side, k in (("a", KA), ("b", KB)):
        for al in ALIAS.get(k, []):
            i = low.find(al.lower())
            if i >= 0 and (best is None or i < best[0]): best = (i, side)
    return best[1] if best else default

def classify(lines):
    """-> list of (move, actor) per line"""
    out = []; dead = False; turn = "a"
    for i, ln in enumerate(lines):
        mv = "stare"
        clean = re.sub(r"ไม่(ยอม)?(แพ้|ล้ม|ตาย|ถอย|หนี)|ไม่ยอม", " ", ln)   # "ไม่ยอมแพ้" is not a knockout
        for name, rx in KW:
            if re.search(rx, clean): mv = name; break
        who = actor_of(ln, turn)
        if mv == "victory" and not dead: mv = "finale"
        if mv == "finale":
            if dead: mv = "victory"
            else: dead = True
        if dead and mv in ("roar", "clash", "bite", "swipe"): mv = "victory" if mv == "roar" else "stare"
        if mv in ("bite", "swipe"): turn = "b" if who == "a" else "a"
        out.append((mv, who))
    if lines and not dead:   # every fight needs an ending: the last line becomes the knockout
        out[-1] = ("finale", "a")
    return out

BASE = {"stare": 1.8, "roar": 2.2, "clash": 3.8, "bite": 2.4, "swipe": 2.4, "finale": 4.4, "victory": 2.8}
NEUT = dict(pitch=0, neck=0.1, head=0, m=0.2, crouch=0, arm=0, tailup=0, nd=0, nl=0, fd=0, fl=0)
AH, BH = -110, 1150     # home x of the two fighters
DEFCAM = (1.0, 540, 880)

class TL:
    def __init__(s):
        s.ka, s.kb, s.ga, s.gb, s.cam = [(0, dict(x=AH, **NEUT))], [(0, dict(x=BH, **NEUT))], [(0, "pose")], [(0, "pose")], [(0, DEFCAM)]
        s.shk, s.bursts, s.slashes, s.speed, s.dust, s.flash, s.sfx, s.couple, s.lines = [], [], [], [], [], [], [], [], []
        s.dead_t = None; s.victory_t = None; s.drums = []

def roar_snd(k):
    return {"trex": ("t-rex-dragon-reptile", 0.88), "spino": ("roar-or-scream-2", 1.04), "tricera": ("dinosaur-roar-390283", 0.8),
            "edmonto": ("roar-or-scream-8", 1.15)}.get(k, ("dinosaur-roar-390283", 1.0))

def add_move(T, mv, who, t0, s):
    """append keys of one move starting at t0, time scale s"""
    def at(r): return t0 + r * s
    KA_, KB_ = T.ka, T.kb
    def ka(r_t, **kv): KA_.append((at(r_t), kv))
    def kb(r_t, **kv): KB_.append((at(r_t), kv))
    def cam(r, z, x, y): T.cam.append((at(r), (z, x, y)))
    def snd(r, key, pitch=1.0, g=1.0, a=0.0, b=None): T.sfx.append((at(r), key, pitch, g, a, b))
    ka(0); kb(0); cam(0, *T.cam[-1][1])
    dead = T.dead_t is not None
    if mv == "stare":
        f = who
        if not dead:
            ka(0.9, x=AH + 30, neck=0.2, head=0.05, m=0.4); ka(1.8, x=AH, neck=0.1, head=0, m=0.2)
            kb(0.9, x=BH - 30, neck=0.2, m=0.4); kb(1.8, x=BH, neck=0.1, m=0.2)
            T.ga.append((at(0), "walk")); T.ga.append((at(0.9), "pose")); T.gb.append((at(0), "walk")); T.gb.append((at(0.9), "pose"))
            snd(0.1, "dinosaur-growl-487679", 0.85, 0.5, 0, 1.2); snd(0.6, "dinosaur-growls-431298", 1.1, 0.35, 0, 1.2)
            cam(0.4, 1.12, 380 if f == "a" else 700, 800); cam(1.6, 1.12, 380 if f == "a" else 700, 800); cam(1.8, *DEFCAM)
        else:
            ka(0.9, neck=0.2, head=0.05, m=0.4); ka(1.8, neck=0.1, head=0, m=0.2); cam(0.5, 1.08, 540, 820); cam(1.8, 1.0, 560, 860)
    elif mv in ("roar", "victory"):
        side = "a" if (mv == "victory" or dead) else who
        k_ = ka if side == "a" else kb; kind = KA if side == "a" else KB
        big = mv == "victory"
        if big:
            ka(0.3, x=210); T.ga.append((at(0), "walk")); T.ga.append((at(0.3), "pose"))
            if T.victory_t is None: T.victory_t = at(0.4)
        k_(0.2 + 0.3 * big, pitch=-0.04, neck=0.05, head=-0.05, m=0.1, crouch=-0.005)
        k_(0.5 + 0.2 * big, pitch=-0.16 if big else (-0.25 if kind == "spino" else -0.13), neck=-0.52 if big else -0.42, head=-0.32 if big else -0.26,
           m=1.0, tailup=-0.1, arm=-0.5 if big else -0.6)
        k_(1.1 + 0.9 * big, m=0.92, head=-0.2)
        k_(1.5 + 1.0 * big, pitch=0, neck=0.1, head=0, m=0.25, arm=0, tailup=0, crouch=0)
        if not big:
            (kb if side == "a" else ka)(0.6, neck=0.22, head=0.06); (kb if side == "a" else ka)(1.6, neck=0.1, head=0)
        name, pt = ("t-rex-victory-roar", 0.9) if (big and KA == "trex") else roar_snd(kind)
        snd(0.4 + 0.2 * big, name, pt, 1.0)
        T.shk.append((at(0.5 + 0.2 * big), 8, 0.8 + 0.6 * big))
        zx = (360 if side == "a" else 760) if not big else 540
        cam(0.35, 1.18 if not big else 1.1, zx, 760 if not big else 780); cam(1.5 + big, 1.18 if not big else 1.1, zx, 760 if not big else 780)
        cam(2.2 + 0.6 * big, *(DEFCAM if not big else (1.08, 560, 800)))
    elif mv == "clash":
        for k_, home, sgn, g in ((ka, AH, 1, T.ga), (kb, BH, -1, T.gb)):
            k_(0.5, x=home - 40 * sgn, crouch=0.045, pitch=0.1, neck=0.25, head=0.1, tailup=0.1, m=0.4, nd=-0.04, fd=0.05)
            k_(1.1, x=105 if sgn > 0 else 1010, pitch=0.2, neck=0.1, head=0.05, m=0.9, crouch=0)
            k_(1.4, x=75 if sgn > 0 else 1045, pitch=-0.05, neck=-0.28 if sgn > 0 else -0.3, head=-0.32 if sgn > 0 else -0.3, m=0.5)
            k_(1.75, x=85 if sgn > 0 else 1040, pitch=0.13, neck=0.2, head=0.1, m=0.6, nd=0.13, fd=-0.13, crouch=0.03, tailup=0.08)
            for r_, xa, xb in ((2.25, 125, 1080), (2.75, 55, 1010), (3.1, 110, 1065)): k_(r_, x=xa if sgn > 0 else xb)
            k_(3.8, x=home, **NEUT)
            g.append((at(0.55), "run")); g.append((at(1.1), "pose"))
        T.speed.append((at(0.6), at(1.1))); snd(0.9, "dramatic-whoosh", 1.0, 0.8)
        for k in range(4): snd(0.6 + k * 0.13, "STEP", 1.0, 0.75)
        snd(1.1, "hard-heavy-impact", 1.0, 1.0); snd(1.1, "cinematic-impact-boom", 1.0, 0.9)
        snd(1.8, "dinosaur-growls-431298", 1.1, 0.6); snd(2.0, "dinosaur-growl-487679", 0.85, 0.6)
        T.bursts.append((at(1.1), 610, 760, 0.55)); T.shk.append((at(1.1), 30, 0.7)); T.flash.append(("ab", at(1.1), 0.15))
        T.dust.append((at(1.75), at(3.1), "struggle"))
        cam(0.5, *DEFCAM); cam(1.1, 1.0, 560, 880); cam(1.25, 1.22, 600, 820); cam(1.9, 1.08, 560, 860); cam(3.1, 1.08, 600, 860); cam(3.8, *DEFCAM)
        T.drums.append((at(0.5), at(3.8)))
    elif mv in ("bite", "swipe"):
        bite = mv == "bite"
        if who == "a":
            ka(0.15, x=AH - 40, crouch=0.04, pitch=0.12, neck=0.25, m=0.4); T.ga.append((at(0.2), "run")); T.ga.append((at(0.5), "pose"))
            ka(0.5, x=130, pitch=0.2, neck=0.1, m=0.9, crouch=0)
            ka(0.62, x=120, pitch=-0.08, neck=-0.32, head=-0.1 if bite else 0.45, m=0.95)
            ka(0.8, x=175, pitch=0.12, neck=0.32, head=0.3 if bite else -0.2, m=0.1 if bite else 0.6)
            ka(1.4, x=100, pitch=0.05, neck=0.12, head=0, m=0.5); ka(2.4, x=AH, **NEUT)
            kb(0.5, x=1040); kb(0.8, x=1040)
            kb(0.92, x=1110, pitch=-0.2, neck=-0.3, head=-0.25, m=0.9); kb(1.2, x=1120, pitch=0, neck=0.05, head=0, m=0.4); kb(2.4, x=BH, **NEUT)
            hx, hy = 700, 700; vic = "b"
            cam(0.4, 1.12, 560, 820); cam(0.8, 1.16, 640, 800); cam(1.6, 1.08, 560, 860); cam(2.4, *DEFCAM)
        else:
            kb(0.15, x=BH + 40, crouch=0.04, pitch=0.12, neck=0.25, m=0.4); T.gb.append((at(0.2), "run")); T.gb.append((at(0.5), "pose"))
            kb(0.5, x=1040, pitch=0.2, m=0.9, crouch=0)
            kb(0.62, x=1085, pitch=-0.22, neck=-0.32, head=-0.22, m=1.0, arm=-0.9)
            kb(0.8, x=985, pitch=0.22, neck=0.1 if not bite else 0.3, head=0.16 if not bite else 0.3, arm=0.9, m=0.8 if not bite else 0.1)
            kb(0.95, x=960, m=0.3, arm=0.5); kb(1.4, x=1000, pitch=0, neck=-0.12, head=-0.1, m=0.9, arm=0); kb(2.4, x=BH, **NEUT)
            ka(0.5, x=80); ka(0.8, x=80)
            ka(0.92, x=0, head=-0.2, neck=-0.12, pitch=-0.05, nd=-0.12, nl=0.04, fd=0.04, m=0.9)
            ka(1.12, x=-30, head=0.25, nl=0.0); ka(1.32, head=-0.15); ka(1.52, head=0.06); ka(2.4, x=AH, **NEUT)
            hx, hy = 430, 700; vic = "a"
            cam(0.4, 1.12, 520, 820); cam(0.8, 1.16, 430, 800); cam(1.6, 1.05, 500, 860); cam(2.4, *DEFCAM)
        T.speed.append((at(0.25), at(0.5))); snd(0.6, "swing-whoosh", 1.0, 0.9)
        snd(0.8, "bone-crack", 1.0, 0.9); snd(0.8, "body-hit-ground", 1.0, 0.7)
        if bite: snd(0.8, "bone-snap", 1.0, 0.6)
        vk = KB if vic == "b" else KA; nm, pt = roar_snd(vk); snd(0.9, nm, pt * 1.08, 0.6, 0, 1.0)
        T.bursts.append((at(0.8), hx, hy, 0.45)); T.shk.append((at(0.8), 22, 0.55)); T.flash.append((vic, at(0.8), 0.25))
        if not bite: T.slashes.append((at(0.76), hx - (30 if vic == "a" else -30), hy + 100))
    elif mv == "finale":
        ka(0.3, x=-140, crouch=0.05, pitch=0.16, neck=0.3, head=0.15, m=0.5, tailup=0.15, nd=-0.06, fd=0.08)
        ka(0.65, x=170, pitch=0.22, neck=0.05, head=0.05, m=1.0, crouch=0); ka(0.74, m=0.22)
        for r_, n_, h_, x_ in ((0.95, 0.28, 0.3, 160), (1.15, -0.18, -0.26, 185), (1.35, 0.26, 0.3, 158), (1.55, -0.2, -0.28, 186), (1.75, 0.24, 0.28, 160), (1.95, -0.15, -0.2, 182)):
            ka(r_, neck=n_, head=h_, x=x_)
        ka(2.25, x=180, neck=0.32, head=0.32, pitch=0.12); ka(2.7, neck=-0.58, head=-0.42, pitch=-0.1, m=0.5)
        ka(3.05, neck=-0.2, head=-0.15, m=0.3, pitch=0); ka(3.4, x=150, neck=0.05, head=0, nd=0, fd=0, tailup=0); ka(4.4, x=170)
        T.ga.append((at(0.0), "pose")); T.ga.append((at(0.35), "run")); T.ga.append((at(0.65), "pose"))
        kb(0.4, x=1000, m=0.3); kb(0.65, x=1000); kb(0.8, x=1030, pitch=-0.1, neck=-0.36, head=-0.3, m=1.0)
        kb(2.25, x=1040, r=-10); kb(2.5, x=1130, r=-30, drop=-100); kb(2.8, x=1230, r=-55, drop=-170, m=1.0)
        kb(3.12, x=1250, r=-24, drop=60, nl=0.1, fl=0.12, nd=-0.05, fd=0.05); kb(3.26, x=1240, r=7, drop=178, m=0.8)
        kb(3.4, r=2, drop=160); kb(3.6, r=6, drop=176, m=0.35)
        T.couple.append((at(0.8), at(2.25))); T.dead_t = at(3.12)
        T.speed.append((at(0.42), at(0.67))); snd(0.35, "dramatic-whoosh", 1.0, 0.8)
        for k in range(2): snd(0.42 + k * 0.11, "STEP", 1.0, 0.8)
        snd(0.65, "hard-heavy-impact", 1.0, 1.0); snd(0.65, "bone-snap", 1.0, 1.0); snd(0.65, "cinematic-impact-boom", 1.0, 0.6)
        nm, pt = roar_snd(KB); snd(0.8, nm, pt * 1.1, 0.7)
        for k in range(3): snd(1.0 + k * 0.4, "bone-crack", 1.0 + 0.08 * k, 0.5)
        snd(2.35, "dramatic-whoosh", 0.9, 1.0); snd(3.26, "heavy-body-fall", 0.85, 1.0); snd(3.26, "cinematic-impact-boom", 0.8, 0.9)
        T.bursts.append((at(0.65), 700, 700, 0.5)); T.bursts.append((at(3.26), 980, F.GS - 40, 0.4))
        T.shk += [(at(0.65), 30, 0.7), (at(3.26), 32, 0.8)]; T.flash.append(("b", at(0.65), 0.25))
        T.dust.append((at(3.24), at(4.44), "fall"))
        cam(0.3, 1.12, 380, 820); cam(0.65, 1.2, 640, 800); cam(2.2, 1.12, 660, 820); cam(2.75, 1.0, 700, 760); cam(3.3, 1.1, 760, 900); cam(4.4, 1.0, 540, 860)
        T.drums.append((at(0.0), at(3.3)))

def load_cfg():
    p = os.environ.get("SCRIPT_JSON")
    cfg = json.load(open(p, encoding="utf-8")) if p and os.path.exists(p) else {}
    lines = [l.strip() for l in cfg.get("lines", []) if l.strip()]
    if not lines:
        lines = [f"{NAME[KA]} คำรามท้าทาย", f"{NAME[KB]} คำรามตอบโต้", "ทั้งสองพุ่งเข้าปะทะกันอย่างรุนแรง", f"{NAME[KB]} ฟาดกลับเต็มแรง",
                 f"{NAME[KA]} งับเข้าที่คอ", f"สุดท้าย {NAME[KB]} ล้มลง", f"{NAME[KA]} คือผู้ชนะ"]
    durs = cfg.get("durs") or []
    return lines, durs, cfg.get("captions", True)

LINES, DURS, CAPS = load_cfg()
MOVES = classify(LINES)
T = TL(); t = 0.0; STARTS = []
for i, (ln, (mv, who)) in enumerate(zip(LINES, MOVES)):
    base = BASE[mv]; want = DURS[i] if i < len(DURS) and DURS[i] else None
    dur = max(want + 0.35, 1.2) if want else base
    s = clamp(dur / base, 0.75, 1.5)
    STARTS.append(t); add_move(T, mv, who, t, s)
    T.lines.append((t, t + max(dur, base * s), ln))
    t += max(dur, base * s)
TOTAL = t + 0.6
def merge(keys, dict_vals=True):
    out = []
    for tk, v in sorted(keys, key=lambda k: k[0]):
        if out and tk - out[-1][0] < 1e-3:
            out[-1] = (out[-1][0], dict(out[-1][1], **v) if dict_vals else v)
        else: out.append((tk, v))
    return out
T.ka, T.kb, T.cam = merge(T.ka), merge(T.kb), merge(T.cam, False)
TA, TB = F.build(T.ka), F.build(T.kb)
CAMK = T.cam
def cam(a): return tuple(F.track([(k, v[i]) for k, v in CAMK], a) for i in range(3))
def shake(a):
    v = sum(A_ * math.exp(-(a - t0) / (d * 0.35)) for t0, A_, d in T.shk if 0 <= a - t0 < d * 2)
    if any(c0 < a < c1 for c0, c1 in T.couple): v += 9
    return v

def caption(img, txt, a, t0):
    f = R.font(58); words = txt.split(" "); rows = [""]
    for w_ in words:
        cand = (rows[-1] + " " + w_).strip()
        if f.getlength(cand) > 900 and rows[-1]: rows.append(w_)
        else: rows[-1] = cand
    rows = rows[:3]; lh = 74; y0 = 1530 - len(rows) * lh / 2
    g = R.pop_s(a, t0);
    if g <= 0: return
    d = ImageDraw.Draw(img)
    for k, r in enumerate(rows):
        d.text((540, y0 + k * lh), r, font=f, fill=(255, 255, 255), anchor="mm", stroke_width=8, stroke_fill=R.DK)

def frame(a):
    img = F.BG.copy()
    tq = F.sample(TA, a); sq = F.sample(TB, a)
    tq["pitch"] += 0.012 * math.sin(a * 2.4); sq["pitch"] += 0.012 * math.sin(a * 2.1 + 1)
    for k_, q_ in ((KA, tq), (KB, sq)):
        if not DN.SP[k_]["biped"] and q_["pitch"] < 0: q_["pitch"] *= 0.3
    for c0, c1 in T.couple:
        if c0 < a < c1: ph = tq["neck"]; sq["x"] += 70 * ph; sq["r"] += -26 * ph; sq["drop"] += -20 * abs(ph)
    lie = T.dead_t is not None and a > T.dead_t
    def fl(side):
        v = 0.0
        for who, t0, d in T.flash:
            if side in who and t0 <= a < t0 + d: v = max(v, 0.25 * (1 - (a - t0) / d))
        return v
    F.dino(img, KB, F.step(T.gb, a) if not lie else "pose", a, sq, F.SS, F.GS, True, fl("b"))
    if lie: F.grass_fg(img, 700, W, F.GS - 10)
    F.dino(img, KA, F.step(T.ga, a), a + 0.2, tq, F.ST, F.GT, False, fl("a"))
    for d0, d1, kind in T.dust:
        if kind == "struggle" and d0 < a < d1: F.dust(img, 560 + (tq["x"] - 85) * 0.6, F.GS + 70, 0.35 + 0.1 * math.sin(a * 4), 0.8)
        if kind == "fall" and a > d0: F.dust(img, 1000, F.GS + 20, min(0.95, (a - d0) / 1.2), 1.1)
    sp = 0.0
    for s0, s1 in T.speed: sp = max(sp, clamp((a - s0) / 0.2) * (1 - clamp((a - s1) / 0.15)))
    F.speedlines(img, sp)
    for t0, x, y, d in T.bursts: F.burst(img, x, y, (a - t0) / d)
    for t0, x, y in T.slashes: F.slash(img, x, y, (a - t0) / 0.7)
    if lie and a > T.dead_t + 0.5:
        d_ = ImageDraw.Draw(img)
        for k in range(3): q = a * 4 + k * 2.1; F.star(d_, 950 + 80 * math.cos(q), F.GS - 190 + 22 * math.sin(q), 22)
    z, zx, zy = cam(a); sh = shake(a)
    if sh: z = max(z, 1.06)
    cw, ch = W / z, H / z
    x0 = min(max(zx - cw / 2 + sh * (0.6 * math.sin(a * 53) + 0.4 * math.sin(a * 31)) / z, 0), W - cw)
    y0 = min(max(zy - ch / 2 + sh * (0.6 * math.cos(a * 47) + 0.4 * math.sin(a * 29)) / z, 0), H - ch)
    if z > 1.001 or sh: img = img.crop((int(x0), int(y0), int(x0 + cw), int(y0 + ch))).resize((W, H), Image.BICUBIC)
    vt = T.victory_t
    R.tag(img, 540, 260, f"{NAME[KA]} VS {NAME[KB]}" if (vt is None or a < vt) else "ใครชนะ? คอมเมนต์!", R.RED, 66, R.pop_s(a, 0.2 if (vt is None or a < vt) else vt + 0.2))
    if CAPS:
        for l0, l1, txt in T.lines:
            if l0 <= a < l1 - 0.05: caption(img, txt, a, l0 + 0.05)
    if a > TOTAL - 0.4:
        img = Image.blend(img.convert("RGB"), Image.new("RGB", img.size, (0, 0, 0)), clamp((a - (TOTAL - 0.4)) / 0.4)).convert("RGBA")
    return img.convert("RGB")

# ---------------------------------------------------------------- sound
def make_sfx(path):
    import soundfile as sf
    from scipy.signal import resample_poly
    sys.path.insert(0, HERE)
    from sfx2 import Mixer, SR, norm
    cache = {}
    def S(key, pitch=1.0, a=0.0, b=None):
        k = (key, pitch, a, b)
        if k in cache: return cache[k]
        f = glob.glob(os.path.join(HERE, "sounds", f"*{key}*.wav"))[0]; x, sr = sf.read(f, dtype="float32")
        if x.ndim > 1: x = x.mean(1)
        x = x[int(a * sr): int(b * sr) if b else None]
        if pitch != 1.0: x = resample_poly(x, 1000, int(1000 * pitch)).astype(np.float32)
        n = int(0.05 * SR); x = x.copy(); x[-n:] *= np.linspace(1, 0, n); cache[k] = norm(x, 1.0); return cache[k]
    def onsets(key, thr=0.35):
        x = S(key); env = np.convolve(np.abs(x), np.ones(480) / 480, "same")
        idx = np.where((env[1:] > thr * env.max()) & (env[:-1] <= thr * env.max()))[0]; out = []
        for i in idx:
            if not out or i - out[-1] > SR * 0.3: out.append(i)
        return [x[i:i + int(0.5 * SR)] for i in out]
    STEPS = onsets("colossal-footsteps") + onsets("giant-footsteps")
    M = Mixer(TOTAL + 1.0); si = 0
    M.add(0.0, S("dinosaur-growl-487679", 0.85), 0.45)
    for d0, d1 in T.drums: M.drums(d0, d1, bpm=150, inten=lambda t: 0.6, style="pop")
    for t0, key, pitch, g, a, b in T.sfx:
        if key == "STEP": M.add(t0, STEPS[si % len(STEPS)], g); si += 1
        else: M.add(t0, S(key, pitch, a, b), g)
    M.write(path, fx_g=1.0, dr_g=0.25)

if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "info":
        print(json.dumps({"TL": TOTAL, "frames": int(TOTAL * FPS), "starts": STARTS, "moves": MOVES}, ensure_ascii=False))
    elif mode == "still":
        ims = [frame(float(x)) for x in sys.argv[2:]]
        S_ = Image.new("RGB", (270 * len(ims), 480))
        for k, im in enumerate(ims): S_.paste(im.resize((270, 480)), (k * 270, 0))
        S_.save(os.environ.get("STILL_OUT", "stills.jpg"), quality=85)
    elif mode == "sfx":
        make_sfx(sys.argv[2])
    else:
        f0, f1, outp = int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
        prog = os.environ.get("PROG_FILE")
        pr = subprocess.Popen([os.environ.get("FFMPEG", "ffmpeg"), "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                               "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-threads", "2", "-pix_fmt", "yuv420p", outp], stdin=subprocess.PIPE)
        for k in range(f0, f1):
            pr.stdin.write(frame(k / FPS).tobytes())
            if prog and (k - f0) % 5 == 4: open(prog, "w").write(str(k - f0 + 1))
        pr.stdin.close(); pr.wait()
        if prog: open(prog, "w").write(str(f1 - f0))
