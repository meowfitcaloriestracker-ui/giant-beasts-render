# -*- coding: utf-8 -*-
"""สัตว์ยักษ์ VS EP.4 — Mammoth vs Smilodon, landscape 16:9 (v18 engine, template v2: named beats, size chart, hit close-ups)
LANG=TH uses voice.m4a + timeline.json + lines.json ; LANG=EN builds an English AI voice (Edge TTS) on first run.
CLI: info | still t1 t2 .. | sfx out.wav | render f0 f1 out.mp4"""
import os, sys, json, math, subprocess
ENGINE = os.environ.get("ENGINE") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "engine")
sys.path.insert(0, ENGINE); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # job-local fightlib (v19 look) wins
import fightlib as FL, render45 as R
from PIL import Image, ImageDraw, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__))
LANG = os.environ.get("LANG_EP", "TH").upper()
FPS, OW, OH = 30, 1920, 1080
DK = R.DK; YEL = (255, 214, 50); RED = (230, 46, 52); WHT = (255, 255, 255); BLU = (40, 120, 220); GRN = (40, 170, 90)

# ------------------------------------------------------------------ English voice (Edge TTS), built once on the PC
def build_en():
    tl = os.path.join(HERE, "timeline_en.json")
    if os.path.exists(tl) and os.path.exists(os.path.join(HERE, "voice_en.wav")): return
    import importlib
    try: import edge_tts
    except ImportError:
        subprocess.run([sys.executable, "-m", "pip", "install", "--quiet", "edge-tts"], check=True); importlib.invalidate_caches(); import edge_tts
    import asyncio, numpy as np, soundfile as sf
    lines = json.load(open(os.path.join(HERE, "lines_en.json"), encoding="utf-8"))
    ff = os.environ.get("FFMPEG", "ffmpeg"); tmp = os.path.join(HERE, "_tts"); os.makedirs(tmp, exist_ok=True); clips = []
    for i, ln in enumerate(lines):
        ph = [p.strip() for p in ln.split("|")]; txt = " ".join(p if p[-1:] in ".,!?:;" else p + "," for p in ph[:-1]) + " " + ph[-1]
        mp, wv = os.path.join(tmp, f"{i:02d}.mp3"), os.path.join(tmp, f"{i:02d}.wav")
        for attempt in range(4):
            try:
                asyncio.run(edge_tts.Communicate(txt, "en-US-GuyNeural", rate="+4%").save(mp)); break
            except Exception:
                if attempt == 3: raise
        subprocess.run([ff, "-v", "error", "-y", "-i", mp, "-ac", "1", "-ar", "48000", wv], check=True)
        x, _ = sf.read(wv, dtype="float32"); nz = np.where(np.abs(x) > 0.01)[0]
        clips.append(x[max(0, nz[0] - 800): nz[-1] + 2400] if len(nz) else x)
    st, starts, durs, vo = 0.3, [], [], []
    for x in clips:
        d = len(x) / 48000; starts.append(round(st, 3)); vo.append(round(d, 3)); durs.append(round(d + 0.5, 3)); st += d + 0.5
    total = st + 1.2; y = np.zeros(int(total * 48000), np.float32)
    for s0, x in zip(starts, clips): i = int(s0 * 48000); y[i:i + len(x)] += x
    sf.write(os.path.join(HERE, "voice_en.wav"), y, 48000)
    json.dump({"starts": starts, "durs": durs, "voice": vo, "total": round(total, 3)}, open(tl, "w"))
    out = os.path.join(HERE, "..", "..", "out"); os.makedirs(out, exist_ok=True)
    pass

def srt(lines, starts, vo, path, lines_en=None):
    """one cue per phrase; timing from the narration (phrase lengths of the English line)"""
    def ts(x): h, r = divmod(x, 3600); m, s_ = divmod(r, 60); return f"{int(h):02d}:{int(m):02d}:{int(s_):02d},{int(round((s_ % 1) * 1000)) % 1000:03d}"
    k, out = 1, []
    for n, ln in enumerate(lines):
        ph = [p.strip() for p in ln.split("|")]; ref = [max(4, len(p.strip())) for p in (lines_en[n] if lines_en else ln).split("|")]
        if len(ref) != len(ph): ref = [max(4, len(p)) for p in ph]
        tot = sum(ref); acc = 0
        for p, r in zip(ph, ref):
            a = starts[n] + vo[n] * acc / tot; acc += r; b = starts[n] + vo[n] * acc / tot
            out.append(f"{k}\n{ts(a)} --> {ts(b)}\n{p}\n"); k += 1
    open(path, "w", encoding="utf-8").write("\n".join(out))

if LANG == "EN": build_en()
TLJ = json.load(open(os.path.join(HERE, "timeline_en.json" if LANG == "EN" else "timeline.json")))
ST_, DU_, VO_ = TLJ["starts"], TLJ["durs"], TLJ["voice"]; TOTAL = TLJ["total"]
LINES = json.load(open(os.path.join(HERE, "lines_en.json" if LANG == "EN" else "lines.json"), encoding="utf-8"))
def S(n): return ST_[n - 1]
def PS(n, k):
    """start time of phrase k (0-based) of line n, proportional to text length"""
    ph = [max(4, len(p.strip())) for p in LINES[n - 1].split("|")]; k = min(k, len(ph) - 1)
    return S(n) + VO_[n - 1] * sum(ph[:k]) / sum(ph)
def E(n): return ST_[n - 1] + DU_[n - 1]
# ------------------------------------------------------------------ named beats (template v2: edit here, not in the code below)
B = dict(hook=1, coexist=2, a1=3, a2=4, a3=5, b1=6, b2=7, b3=8, stats=9, sim=10, dawn=11, stalk=12, alarm=13, pounce=14, stab=15,
         throw=16, again=17, gore=18, flung=19, limp=20, win=21, why=22, calf=23, truth1=24, truth2=25, who=26, outro=27)
def SB(k): return S(B[k])
def PB(k, i): return PS(B[k], i)
def VB(k): return VO_[B[k] - 1]
def DB(k): return DU_[B[k] - 1]

T = {
 "TH": dict(series="สัตว์ยักษ์ VS ใครจะชนะ?", ep="EP.4", title_a="แมมมอธ", title_b="เสือเขี้ยวดาบ", vs="VS",
            sim="จำลองการต่อสู้", dawn="ทุ่งหิมะยุคน้ำแข็ง อเมริกาเหนือ", winner="ผู้ชนะ: แมมมอธ!",
            ra=[("สูงถึงไหล่", "ราว 3 เมตร", ("a1", 1)), ("หนัก", "4–6 ตัน", ("a1", 1)), ("ขนาด", "≈ ช้างเอเชีย", ("a1", 2)),
                ("งา", "ยาวถึง 4 เมตร", ("a2", 0)), ("ใช้งา", "ขุดหิมะ + ป้องกันตัว", ("a2", 1)), ("ขน", "2 ชั้น + ไขมันหนา", ("a3", 0))],
            rb=[("หนัก", "200–300 กก.", ("b1", 1)), ("รูปร่าง", "ล่ำกว่าสิงโต", ("b1", 2)), ("เขี้ยวบน", "ยาวถึง 28 ซม.", ("b2", 0)),
                ("อ้าปาก", "กว้างเกือบ 2 เท่าสิงโต", ("b2", 1)), ("แรงกัด", "อ่อนกว่าสิงโต", ("b3", 0)), ("วิธีฆ่า", "เฉือนคอ", ("b3", 1))],
            stats="สรุปสถิติ", size="เทียบขนาด", hum="คน 1.75 ม.", sa="3 ม.", sb="1.1 ม.",
            rows=[("น้ำหนัก", "4–6 ตัน", "200–300 กก.", "a"), ("ความสูง", "3 ม.", "1.1 ม.", "a"), ("อาวุธ", "งา 4 ม.", "เขี้ยว 28 ซม.", "-"), ("ความว่องไว", "ช้า", "ว่องไว", "b")],
            q="คุณคิดว่ามันจะยอมแพ้ไหม?",
            why="ทำไมแมมมอธชนะ?", why1="หนักกว่าราว 20 เท่า", why2="ขน + หนังหนา กันเขี้ยวดาบ", deep="ถ้าเป็นลูกแมมมอธล่ะ?", deep2="เสือเขี้ยวดาบมีโอกาสชนะ",
            deep3="(ลูกแมมมอธที่พลัดหลงจากฝูง)",
            never="ความจริงจากฟอสซิล", f1="บ่อน้ำมันดินลาเบรีย ลอสแองเจลิส", f2="พบเสือเขี้ยวดาบหลายพันตัว", f3="อยู่ร่วมกับฟอสซิลแมมมอธ",
            real="นักล่าลูกแมมมอธตัวจริง", g1="โฮโมเธอเรียม (แมวเขี้ยวดาบอีกชนิด)", g2="ถ้ำฟรีเซนฮาน รัฐเท็กซัส", g3="กระดูกลูกแมมมอธวัย ~2 ขวบ จำนวนมาก!",
            cold="ใครจะรอด?", cold2="แมมมอธ VS เสือเขี้ยวดาบ", count="ฉากต่อสู้เริ่มใน",
            ch=["เปิดเรื่อง", "ข้อมูลแมมมอธ", "ข้อมูลเสือเขี้ยวดาบ", "สรุปสถิติ + เทียบขนาด", "การต่อสู้", "ทำไมถึงชนะ", "ความจริงจากฟอสซิล", "ตอนต่อไป"],
            who="คุณคิดว่าใครชนะ? คอมเมนต์เลย!", next="ตอนหน้า: จิกาโนโตซอรัส VS ทีเร็กซ์", like="กดถูกใจ", share="แชร์", sub="ติดตาม"),
 "EN": dict(series="GIANT BEASTS VS · WHO WINS?", ep="EP.4", title_a="MAMMOTH", title_b="SABER-TOOTH", vs="VS",
            sim="FIGHT SIMULATION", dawn="Ice Age North America", winner="WINNER: MAMMOTH!",
            ra=[("Shoulder", "about 3 m", ("a1", 1)), ("Weight", "4–6 t", ("a1", 1)), ("Size", "≈ Asian elephant", ("a1", 2)),
                ("Tusks", "up to 4 m", ("a2", 0)), ("Tusk use", "snow + defense", ("a2", 1)), ("Coat", "2 layers + fat", ("a3", 0))],
            rb=[("Weight", "200–300 kg", ("b1", 1)), ("Build", "bulkier than a lion", ("b1", 2)), ("Sabers", "up to 28 cm", ("b2", 0)),
                ("Gape", "~2x a lion's", ("b2", 1)), ("Bite", "weaker than a lion", ("b3", 0)), ("Kill", "throat slice", ("b3", 1))],
            stats="STATS CHECK", size="SIZE CHECK", hum="Human 1.75 m", sa="3 m", sb="1.1 m",
            rows=[("Weight", "4–6 t", "200–300 kg", "a"), ("Height", "3 m", "1.1 m", "a"), ("Weapons", "4 m tusks", "28 cm sabers", "-"), ("Speed", "slow", "agile", "b")],
            q="Do you think it gives up?",
            why="Why did the mammoth win?", why1="About 20x heavier", why2="Fur + thick hide block the sabers", deep="What about a calf?", deep2="The saber-tooth could win",
            deep3="(a calf lost from its herd)",
            never="WHAT THE FOSSILS SAY", f1="La Brea Tar Pits, Los Angeles", f2="Thousands of saber-tooth cats", f3="...found alongside mammoth fossils",
            real="THE REAL CALF HUNTER", g1="Homotherium (another sabertooth cat)", g2="Friesenhahn Cave, Texas", g3="Many bones of ~2-year-old mammoth calves!",
            cold="WHO SURVIVES?", cold2="MAMMOTH VS SABER-TOOTH", count="FIGHT STARTS IN",
            ch=["Intro", "Mammoth profile", "Saber-tooth profile", "Stats + size check", "The fight", "Why it won", "What the fossils say", "Next episode"],
            who="Who wins? Tell us in the comments!", next="Next: Giganotosaurus VS T. rex", like="LIKE", share="SHARE", sub="SUBSCRIBE"),
}[LANG]
_FC = {}
def font(sz):
    if sz not in _FC: _FC[sz] = R.font(sz)
    return _FC[sz]
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def eout(x): x = clamp(x); return 1 - (1 - x) ** 3
def layer(img, fn, a=1.0):
    if a <= 0.01: return
    L = Image.new("RGBA", img.size, (0, 0, 0, 0)); fn(ImageDraw.Draw(L))
    if a < 0.99: L.putalpha(L.getchannel("A").point(lambda v: int(v * a)))
    img.alpha_composite(L)
def text(img, xy, s, sz, fill=WHT, anchor="mm", a=1.0, sw=None):
    layer(img, lambda d: d.text(xy, s, font=font(sz), fill=fill, anchor=anchor, stroke_width=sw if sw is not None else max(4, sz // 9), stroke_fill=DK), a)
def chip(img, x, y, s, col=RED, sz=46, a=1.0, anchor="m"):
    w = font(sz).getlength(s) + 56; x0 = x - w / 2 if anchor == "m" else x
    def f(d):
        d.rounded_rectangle((x0, y - sz * 0.8, x0 + w, y + sz * 0.8), 26, fill=col, outline=WHT, width=5); d.text((x0 + w / 2, y), s, font=font(sz), fill=WHT, anchor="mm")
    layer(img, f, a)
def panel(img, box, a=1.0, fill=(255, 250, 238)):
    def f(d):
        d.rounded_rectangle((box[0] + 8, box[1] + 10, box[2] + 8, box[3] + 10), 30, fill=(0, 0, 0, 80))
        d.rounded_rectangle(box, 30, fill=fill + (240,), outline=DK, width=6)
    layer(img, f, a)
def fit(s, sz, maxw):
    while sz > 26 and font(sz).getlength(s) > maxw: sz -= 2
    return sz
def caption(img, t):
    for n in range(1, len(LINES) + 1):
        if S(n) - 0.1 <= t < S(n) + VO_[n - 1] + 0.25: break
    else: return
    ph = [p.strip() for p in LINES[n - 1].split("|")]; L_ = [max(4, len(p)) for p in ph]; tot = sum(L_); u = (t - S(n)) / max(0.1, VO_[n - 1])
    acc = 0; k = 0
    for i, l in enumerate(L_):
        if u >= acc / tot: k = i
        acc += l
    s = ph[k]; sz = fit(s, 56, 1640); w = font(sz).getlength(s)
    layer(img, lambda d: d.rounded_rectangle((960 - w / 2 - 34, 978 - sz * 0.85, 960 + w / 2 + 34, 978 + sz * 0.85), 24, fill=(0, 0, 0, 150)))
    text(img, (960, 978), s, sz, sw=max(3, sz // 12))

def fact_card(img, x0, name, col, facts, t):
    shown = [(k, v, PB(*at)) for k, v, at in facts if t >= PB(*at) - 0.05]
    if not shown: return
    a0 = eout((t - shown[0][2] + 0.05) / 0.4); w = 680; y0 = 150; h = 120 + 92 * len(facts)
    xs = x0 + (1 - a0) * (60 if x0 > 900 else -60)
    panel(img, (xs, y0, xs + w, y0 + h), a0); chip(img, xs + w / 2, y0 + 8, name, col, 50, a0)
    for i, (k, v, ts) in enumerate(shown):
        a = eout((t - ts - 0.12 * i) / 0.35); y = y0 + 100 + 92 * i
        text(img, (xs + 40, y), k, 40, fill=col, anchor="lm", a=a, sw=0)
        text(img, (xs + w - 40, y), v, fit(v, 44, w - 280), fill=DK, anchor="rm", a=a, sw=0)
        if i < len(facts) - 1: layer(img, lambda d, y=y: d.line((xs + 30, y + 46, xs + w - 30, y + 46), fill=(220, 210, 190), width=3), a)

# ------------------------------------------------------------------ size chart (template v2): silhouettes on a metre grid
def _sil_human(d, x, g, m, col):
    d.ellipse((x - 0.12 * m, g - 1.75 * m, x + 0.12 * m, g - 1.51 * m), fill=col)
    d.rounded_rectangle((x - 0.2 * m, g - 1.5 * m, x + 0.2 * m, g - 0.85 * m), int(0.08 * m), fill=col)
    for s_ in (-1, 1):
        d.rounded_rectangle((x + s_ * 0.04 * m - 0.08 * m, g - 0.9 * m, x + s_ * 0.04 * m + 0.08 * m + s_ * 0.04 * m, g), int(0.05 * m), fill=col)
        d.line((x + s_ * 0.22 * m, g - 1.42 * m, x + s_ * 0.3 * m, g - 0.85 * m), fill=col, width=max(3, int(0.08 * m)))
def _sil_mammoth(d, x, g, m, col, tusk):
    for lx in (-1.25, -0.8, 0.75, 1.15): d.rounded_rectangle((x + (lx - 0.22) * m, g - 1.7 * m, x + (lx + 0.22) * m, g), int(0.1 * m), fill=col)
    d.ellipse((x - 1.75 * m, g - 2.85 * m, x + 1.55 * m, g - 1.15 * m), fill=col)
    d.ellipse((x + 0.75 * m, g - 3.3 * m, x + 2.0 * m, g - 2.0 * m), fill=col)
    d.polygon([(x + 1.75 * m, g - 2.3 * m), (x + 2.1 * m, g - 1.6 * m), (x + 2.05 * m, g - 0.5 * m), (x + 1.85 * m, g - 0.45 * m), (x + 1.8 * m, g - 1.5 * m), (x + 1.4 * m, g - 2.0 * m)], fill=col)
    d.arc((x + 1.55 * m, g - 1.95 * m, x + 2.75 * m, g - 0.75 * m), -30, 190, fill=tusk, width=max(4, int(0.13 * m)))
def _sil_cat(d, x, g, m, col, tusk):
    for lx in (-0.6, -0.35, 0.45, 0.7): d.rounded_rectangle((x + (lx - 0.09) * m, g - 0.75 * m, x + (lx + 0.09) * m, g), int(0.05 * m), fill=col)
    d.ellipse((x - 0.85 * m, g - 1.15 * m, x + 0.95 * m, g - 0.55 * m), fill=col)
    d.ellipse((x + 0.75 * m, g - 1.3 * m, x + 1.25 * m, g - 0.85 * m), fill=col)
    d.line((x - 0.8 * m, g - 0.95 * m, x - 1.05 * m, g - 0.75 * m), fill=col, width=max(3, int(0.08 * m)))
    d.line((x + 1.1 * m, g - 0.95 * m, x + 1.12 * m, g - 0.78 * m), fill=tusk, width=max(3, int(0.04 * m)))
def size_chart(img, box, a, t0):
    x0, y0, x1, y1 = box; g = y1 - 90; m = min((g - y0 - 120) / 3.5, (x1 - x0 - 60) / 8.4)   # px per metre
    chip(img, (x0 + x1) / 2, y0 + 8, T["size"], BLU, 44, a)
    def grid(d):
        for k in range(1, 4):
            y = g - k * m
            if y < y0 + 70: continue; d.line((x0 + 30, y, x1 - 30, y), fill=(210, 200, 180), width=2); d.text((x0 + 40, y - 6), f"{k} m", font=font(26), fill=(150, 140, 120), anchor="ls")
        d.line((x0 + 20, g, x1 - 20, g), fill=DK, width=5)
    layer(img, grid, a)
    items = ((lambda d: _sil_human(d, x0 + 30 + 0.6 * m, g, m, (90, 90, 100)), x0 + 30 + 0.6 * m, T["hum"], 1.75, (90, 90, 100)),
             (lambda d: _sil_cat(d, x0 + 30 + 2.4 * m, g, m, RED, WHT), x0 + 30 + 2.5 * m, T["sb"], 1.1, RED),
             (lambda d: _sil_mammoth(d, x0 + 30 + 5.4 * m, g, m, BLU, (250, 245, 225)), x0 + 30 + 5.6 * m, T["sa"], 3.0, BLU))
    for i, (fn, lx, lab, hgt, col) in enumerate(items):
        aa = eout((t0 - 0.25 * i) / 0.4) * a; layer(img, fn, aa)
        text(img, (max(x0 + 110, lx), g + 45), lab, fit(lab, 34, 200), fill=col, a=aa, sw=0)

def stats_table(img, t):
    u = t - SB("stats"); a = eout(u / 0.4); img.alpha_composite(Image.new("RGBA", img.size, (10, 14, 20, int(130 * a))))
    panel(img, (60, 130, 990, 900), a); size_chart(img, (60, 130, 990, 900), a, u)
    box = (1020, 130, 1860, 900); panel(img, box, a); chip(img, 1440, 140, T["stats"], RED, 52, a)
    text(img, (1480, 250), T["title_a"], fit(T["title_a"], 42, 250), fill=BLU, a=a, sw=0); text(img, (1730, 250), T["title_b"], fit(T["title_b"], 42, 250), fill=RED, a=a, sw=0)
    for i, (k, va, vb, win) in enumerate(T["rows"]):
        aa = eout((t - PB("stats", i + 1) + 0.1) / 0.35) * a; y = 360 + i * 135
        text(img, (1050, y), k, fit(k, 38, 260), fill=DK, anchor="lm", a=aa, sw=0)
        for x, v, me in ((1480, va, "a"), (1730, vb, "b")):
            good = win == me
            if good: layer(img, lambda d, x=x, y=y: d.rounded_rectangle((x - 118, y - 44, x + 118, y + 44), 22, fill=(230, 248, 230), outline=GRN, width=5), aa)
            text(img, (x, y), v, fit(v, 36, 220), fill=GRN if good else (120, 110, 100), a=aa, sw=0)

# ------------------------------------------------------------------ sections
def hide(C, who, t=0.0): C.k(who, t, x=(FL.AH - 2600) if who == "a" else (FL.BH + 2600))
A_, B_ = "mammoth", "smilodon"
FL.DN.SP["mammoth"]["L"] = int(os.environ.get("LA", 1050)); FL.DN.SP["smilodon"]["L"] = int(os.environ.get("LB", 760))
def closeup(C, t, x=560, y=780, z=1.42, hold=0.9):
    """template v2: hard push-in on a big hit, then ease back out"""
    C.cam(t + 0.02, z, x, y); C.cam(t + hold, z - 0.12, x, y + 20); C.cam(t + hold + 0.6, 1.0, 540, 880)

def sec_intro():
    t0, t1 = 0.0, SB("a1"); C = FL.Choreo(A_, B_, "tundra", land=True)
    C.stare(0.5); C.roar("a", PB("hook", 0) + 0.6, big=True); C.roar("b", PB("hook", 1) + 0.6, big=True); C.stare(SB("coexist") + 0.2)
    return t0, t1, C
def sec_a():
    t0, t1 = SB("a1"), SB("b1"); C = FL.Choreo(A_, B_, "snowforest", land=True); hide(C, "b")
    C.k("a", 0, x=FL.AH - 500); C.g("a", 0, "walk"); C.k("a", 1.8, x=FL.AH); C.g("a", 1.8, "pose")
    C.roar("a", SB("a2") - t0 + 0.4, big=True); C.roar("a", SB("a3") - t0 + 0.6)
    for k in ("a1", "a2", "a3"): hide(C, "b", SB(k) - t0)
    return t0, t1, C
def sec_b():
    t0, t1 = SB("b1"), SB("stats"); C = FL.Choreo(A_, B_, "snowforest", land=True); hide(C, "a")
    C.k("b", 0, x=FL.BH + 500); C.g("b", 0, "walk"); C.k("b", 1.8, x=FL.BH); C.g("b", 1.8, "pose")
    C.roar("b", SB("b2") - t0 + 0.4, big=True); C.roar("b", SB("b3") - t0 + 0.6)
    for k in ("b1", "b2", "b3"): hide(C, "a", SB(k) - t0)
    return t0, t1, C
def sec_stats():
    t0, t1 = SB("stats"), SB("sim"); C = FL.Choreo(A_, B_, "tundra", land=True); tt = 0.3
    while tt < t1 - t0: tt = C.stare(tt, 2.4)
    return t0, t1, C
def sec_fight():
    t0, t1 = SB("sim"), SB("truth1"); C = FL.Choreo(A_, B_, "tundra", land=True); r = lambda k: SB(k) - t0
    hide(C, "b"); C.stare(0.4, 2.0)
    b_in = PB("dawn", 2) - t0; C.k("b", b_in, x=FL.BH + 700); C.g("b", b_in, "walk"); C.k("b", b_in + 2.4, x=FL.BH); C.g("b", b_in + 2.4, "pose")
    C.stalk("b", r("stalk") + 0.2, d=min(3.2, DB("stalk") - 0.4))
    C.roar("a", r("alarm") + 0.5, big=True)
    C.pounce("b", r("pounce") + 0.2)
    C.strike("b", r("stab") + 0.1, "bite", d=2.2)
    C.knockdown("a", r("throw") + 0.1, d=min(4.2, DB("throw") + DB("again") * 0.3))
    C.strike("b", PB("again", 2) - t0, "swipe", d=2.0)
    g0 = r("gore") + 0.4; d = 2.6; C.strike("a", g0, "gore", d=d); closeup(C, g0 + 0.8 * d, 600, 760)
    C.stare(r("flung") + 0.3, min(2.4, DB("flung") - 0.5))
    C.limp("b", r("limp") + 0.2, d=min(3.6, DB("limp") + 0.2))
    C.victory("a", r("win") + 0.2)
    tt = r("why") + 0.3
    while tt < t1 - t0 - 1.0: tt = C.roar("a", tt, d=2.4) + 2.2
    tt = r("limp") + 0.2 + min(3.6, DB("limp") + 0.2)
    while tt < t1 - t0 + 0.5: hide(C, "b", tt); tt += 0.25
    return t0, t1, C
def sec_outro():
    t0, t1 = SB("truth1"), TOTAL; C = FL.Choreo(A_, B_, "snowforest", land=True); r = lambda k: SB(k) - t0
    tt = 0.3
    while tt < r("who"): tt = C.stare(tt, 2.6)
    C.roar("a", r("who") + 0.6); C.roar("b", r("who") + 3.2)
    tt = r("outro")
    while tt < t1 - t0: tt = C.stare(tt, 2.6)
    return t0, t1, C

SECS = []
for fn in (sec_intro, sec_a, sec_b, sec_stats, sec_fight, sec_outro):
    t0, t1, C = fn(); C.finalize(); SECS.append((t0, t1, C))

def truth_panel(img, t, key, title, rows):
    a = eout((t - SB(key)) / 0.4); img.alpha_composite(Image.new("RGBA", img.size, (10, 14, 20, int(110 * a))))
    panel(img, (300, 170, 1620, 720), a); chip(img, 960, 180, title, RED, 54, a)
    for i, (s_, k, col) in enumerate(rows):
        aa = eout((t - PB(key, k) + 0.1) / 0.4) * a
        text(img, (960, 340 + i * 130), s_, fit(s_, 58 if col == GRN else 52, 1200), fill=col, a=aa, sw=0)

def overlays(img, t):
    if t < SB("a1"):
        a = eout((t - 0.2) / 0.5) * (1 - clamp((t - (SB("coexist") + DB("coexist") - 0.6)) / 0.5))
        chip(img, 960, 90, T["series"] + "  " + T["ep"], RED, 44, a)
        y = 260 + (1 - a) * -60
        text(img, (500, y), T["title_a"], fit(T["title_a"], 110, 620), fill=WHT, a=a); text(img, (1420, y), T["title_b"], fit(T["title_b"], 110, 680), fill=WHT, a=a)
        text(img, (960, y + 10), T["vs"], 150, fill=YEL, a=a)
    if SB("a1") <= t < SB("sim") - 0.3:
        left = max(0, int(SB("dawn") - t + 0.999)); a = eout((t - SB("a1")) / 0.5) * (1 - clamp((t - (SB("sim") - 0.8)) / 0.5))
        chip(img, 40, 62, f"{T['count']} {left // 60}:{left % 60:02d}", DK, 38, a, anchor="l")
    if SB("a1") <= t < SB("b1"): fact_card(img, 1160, T["title_a"], BLU, T["ra"], t)
    if SB("b1") <= t < SB("stats"): fact_card(img, 80, T["title_b"], RED, T["rb"], t)
    if SB("stats") <= t < SB("sim"): stats_table(img, t)
    if SB("sim") <= t < SB("dawn"): a = eout((t - SB("sim")) / 0.4); chip(img, 960, 300, T["sim"], RED, 86, a)
    if SB("dawn") <= t < SB("dawn") + 4: chip(img, 960, 120, T["dawn"], BLU, 46, eout((t - SB("dawn")) / 0.4) * (1 - clamp((t - SB("dawn") - 3.5) / 0.5)))
    if SB("again") <= t < PB("again", 1) + 0.6:   # mid-fight question to the viewer
        a = eout((t - SB("again")) / 0.3) * (1 - clamp((t - PB("again", 1) - 0.2) / 0.4)); chip(img, 960, 150, T["q"], YEL, 60, a)
    if SB("win") <= t < SB("why"): a = eout((t - SB("win") - 0.6) / 0.4); chip(img, 960, 140, T["winner"], GRN, 76, a)
    if SB("why") <= t < SB("calf"):
        a = eout((t - SB("why")) / 0.4); panel(img, (1180, 180, 1860, 560), a); chip(img, 1520, 188, T["why"], RED, 46, a)
        for i, s in enumerate((T["why1"], T["why2"])):
            aa = eout((t - PB("why", i + 1) + 0.1) / 0.35) * a; text(img, (1220, 330 + i * 120), "• " + s, fit(s, 46, 600), fill=DK, anchor="lm", a=aa, sw=0)
    if SB("calf") <= t < SB("truth1"):
        a = eout((t - SB("calf")) / 0.4); panel(img, (1100, 180, 1860, 560), a, fill=(252, 236, 226)); chip(img, 1480, 188, T["deep"], RED, 46, a)
        text(img, (1480, 320), T["deep3"], fit(T["deep3"], 40, 700), fill=DK, a=eout((t - SB("calf") - 0.5) / 0.4) * a, sw=0)
        text(img, (1480, 450), T["deep2"], fit(T["deep2"], 50, 680), fill=RED, a=eout((t - PB("calf", 1)) / 0.4) * a, sw=0)
    if SB("truth1") <= t < SB("truth2"): truth_panel(img, t, "truth1", T["never"], ((T["f1"], 1, DK), (T["f2"], 2, DK), (T["f3"], 3, DK)))
    if SB("truth2") <= t < SB("who"): truth_panel(img, t, "truth2", T["real"], ((T["g1"], 1, DK), (T["g2"], 2, DK), (T["g3"], 3, GRN)))
    if SB("who") <= t < SB("outro"):
        a = eout((t - SB("who")) / 0.4); chip(img, 960, 160, T["who"], RED, fit(T["who"], 56, 1500), a)
        chip(img, 960, 300, T["next"], BLU, fit(T["next"], 46, 1500), eout((t - PB("who", 2)) / 0.4))
    if t >= SB("outro"):
        u = t - SB("outro")
        for i, (s, col) in enumerate(((T["like"], BLU), (T["share"], GRN), (T["sub"], RED))):
            chip(img, 600 + i * 360, 220, s, col, 54, eout((u - VB("outro") * (0.15 + 0.2 * i)) / 0.35))
def frame(t):
    for i, (t0, t1, C) in enumerate(SECS):
        if t < t1 or i == len(SECS) - 1: break
    u = t - t0; img = C.frame(max(0.0, u)).convert("RGBA")
    if img.size != (OW, OH): img = img.resize((OW, OH))
    overlays(img, t); caption(img, t)
    fade = max(clamp(1 - u / 0.18), clamp(1 - (t1 - t) / 0.18) if i < len(SECS) - 1 else clamp((t - (TOTAL - 0.8)) / 0.8))
    if fade > 0: img.alpha_composite(Image.new("RGBA", img.size, (0, 0, 0, int(255 * fade * 0.9))))
    return img.convert("RGB")

COLD = 7.0
FS_ = SECS[4]; CS = SB("pounce") - FS_[0] - 0.2   # cold open = the pounce + saber stab
TOTAL_V = TOTAL + COLD
def cold_frame(t):
    img = FS_[2].frame(CS + t).convert("RGBA")
    if img.size != (OW, OH): img = img.resize((OW, OH))
    a = eout((t - 0.3) / 0.4)
    layer(img, lambda d: (d.rectangle((0, 0, OW, 90), fill=(0, 0, 0, 255)), d.rectangle((0, OH - 90, OW, OH), fill=(0, 0, 0, 255))))
    text(img, (960, 190), T["cold"], 130, fill=YEL, a=a)
    chip(img, 960, OH - 160, T["cold2"], RED, 52, eout((t - 0.9) / 0.4))
    fade = max(clamp(1 - t / 0.15), clamp((t - (COLD - 0.35)) / 0.35))
    if fade > 0: img.alpha_composite(Image.new("RGBA", img.size, (0, 0, 0, int(255 * fade))))
    return img.convert("RGB")
def frame_v(t): return cold_frame(t) if t < COLD else frame(t - COLD)

def prep_audio_and_text():
    """voice padded by COLD seconds (jobrun mixes the file from 0), srt + YouTube chapters shifted to video time"""
    ff = os.environ.get("FFMPEG", "ffmpeg"); out = os.path.join(HERE, "..", "..", "out"); os.makedirs(out, exist_ok=True)
    src = os.path.join(HERE, "voice_en.wav" if LANG == "EN" else os.environ.get("VOICE_SRC", "voice_th.wav")); dst = os.path.join(HERE, "voice_cold.wav")
    if os.path.exists(src):
        ms = int(COLD * 1000); subprocess.run([ff, "-v", "error", "-y", "-i", src, "-af", f"adelay={ms}:all=1", "-ac", "1", "-ar", "48000", dst], check=True)
    base = os.environ.get("EP_NAME", "EP4")
    if LANG == "EN":
        lines = json.load(open(os.path.join(HERE, "lines_en.json"), encoding="utf-8")); st = [x + COLD for x in ST_]
        for code in ("en", "es"):
            fp = os.path.join(HERE, f"lines_{code}.json")
            if os.path.exists(fp): srt(json.load(open(fp, encoding="utf-8")), st, VO_, os.path.join(out, f"{base}_{code.upper()}.srt"), lines_en=lines)
    def mm(x): x = int(x); return f"{x // 60}:{x % 60:02d}"
    pts = [0] + [SB(k) + COLD for k in ("a1", "b1", "stats", "sim", "why", "truth1", "who")]
    open(os.path.join(out, f"{base}_chapters.txt"), "w", encoding="utf-8").write("\n".join(f"{mm(p)} {n}" for p, n in zip(pts, T["ch"])) + "\n")

def sfx(path):
    import numpy as np, soundfile as sf
    parts = []; sr = 48000; cold = None
    for t0, t1, C in SECS:
        p = path + ".part.wav"; d = t1 - t0; C.sfx(p, d, drums=False); x, sr = sf.read(p, dtype="float32"); os.remove(p)
        n = int(d * sr); x = x[:n] if len(x) >= n else np.concatenate([x, np.zeros((n - len(x),) + x.shape[1:], np.float32)])
        if C is FS_[2]:
            a0 = int(CS * sr); cold = x[a0:a0 + int(COLD * sr)].copy(); g = int(0.35 * sr)
            env = np.linspace(1, 0, g); cold[-g:] *= env[:, None] if cold.ndim > 1 else env
        f = int(0.15 * sr); x[:f] *= np.linspace(0, 1, f)[:, None] if x.ndim > 1 else np.linspace(0, 1, f); parts.append(x)
    sf.write(path, np.concatenate([cold * 1.15] + parts) * 0.75, sr)

if __name__ == "__main__":
    m = sys.argv[1]
    if m == "info": prep_audio_and_text(); print(json.dumps({"TL": TOTAL_V, "frames": int(TOTAL_V * FPS), "lang": LANG}))
    elif m == "still":
        ims = [frame_v(float(x)) for x in sys.argv[2:]]; Sh = Image.new("RGB", (640 * min(3, len(ims)), 360 * ((len(ims) + 2) // 3)))
        for k, im in enumerate(ims): Sh.paste(im.resize((640, 360)), ((k % 3) * 640, (k // 3) * 360))
        Sh.save(os.environ.get("STILL_OUT", "stills.jpg"), quality=85)
    elif m == "sfx": sfx(sys.argv[2])
    else:
        f0, f1, outp = int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]; prog = os.environ.get("PROG_FILE")
        pr = subprocess.Popen([os.environ.get("FFMPEG", "ffmpeg"), "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{OW}x{OH}", "-r", str(FPS), "-i", "-",
                               "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-threads", "2", "-pix_fmt", "yuv420p", outp], stdin=subprocess.PIPE)
        for k in range(f0, f1):
            pr.stdin.write(frame_v(k / FPS).tobytes())
            if prog and (k - f0) % 5 == 4: open(prog, "w").write(str(k - f0 + 1))
        pr.stdin.close(); pr.wait()
        if prog: open(prog, "w").write(str(f1 - f0))
