# -*- coding: utf-8 -*-
"""สัตว์ยักษ์ VS — template v4 "fight first" (hook teaser, round 1, paused facts, round 2, fossil truth). Episode data in ep.py
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
        tot = sum(ref); acc = 0; pm = PHM[n] if PHM and len(PHM[n]) == len(ph) else None
        for j, (p, r) in enumerate(zip(ph, ref)):
            a = starts[n] + vo[n] * acc / tot; acc += r; b = starts[n] + vo[n] * acc / tot
            if pm: a = starts[n] + pm[j]; b = starts[n] + (pm[j + 1] if j + 1 < len(pm) else vo[n])   # follow the real voice
            out.append(f"{k}\n{ts(a)} --> {ts(b)}\n{p}\n"); k += 1
    open(path, "w", encoding="utf-8").write("\n".join(out))

if LANG == "EN": build_en()
TLJ = json.load(open(os.path.join(HERE, "timeline_en.json" if LANG == "EN" else "timeline.json")))
ST_, DU_, VO_ = TLJ["starts"], TLJ["durs"], TLJ["voice"]; TOTAL = TLJ["total"]
def _phrase_marks():
    """template v3: where each '|' phrase really starts, found from the pauses in the recorded voice
    (falls back to text-length proportions when a pause can't be found)"""
    cache = os.path.join(HERE, f"_phr_{LANG}.json")
    if os.path.exists(cache): return json.load(open(cache))
    src = os.path.join(HERE, "voice_en.wav" if LANG == "EN" else os.environ.get("VOICE_SRC", "voice_th.wav"))
    if not os.path.exists(src): return None
    import numpy as np
    raw = subprocess.run([os.environ.get("FFMPEG", "ffmpeg"), "-v", "error", "-i", src, "-ac", "1", "-ar", "8000", "-f", "f32le", "-"], capture_output=True).stdout
    y = np.frombuffer(raw, np.float32); FR = 160; marks = []
    for n, ln in enumerate(LINES):
        ph = [max(4, len(p.strip())) for p in ln.split("|")]; v = VO_[n]
        est = [v * sum(ph[:j]) / sum(ph) for j in range(1, len(ph))]
        seg = y[int(ST_[n] * 8000): int((ST_[n] + v) * 8000)]
        if len(ph) == 1 or len(seg) < FR * 10: marks.append([0.0] + est); continue
        rms = np.sqrt(np.convolve(seg ** 2, np.ones(FR) / FR, "same"))[::FR]; thr = max(0.006, 0.12 * np.percentile(rms, 95))
        quiet = rms < thr; gaps = []; i = 0
        while i < len(quiet):
            if quiet[i]:
                j = i
                while j < len(quiet) and quiet[j]: j += 1
                if i > 3 and j < len(quiet) - 3 and j - i >= 5: gaps.append(j * FR / 8000 - 0.04)   # speech resumes here
                i = j
            else: i += 1
        out, last = [0.0], 0.0
        for e in est:
            c = [g for g in gaps if g > last + 0.3]
            g = min(c, key=lambda g: abs(g - e)) if c else None
            out.append(g if g is not None and abs(g - e) < 0.3 * v + 0.4 else max(e, last + 0.3)); last = out[-1]
        marks.append(out)
    try: json.dump(marks, open(cache, "w"))
    except OSError: pass
    return marks
LINES = json.load(open(os.path.join(HERE, "lines_en.json" if LANG == "EN" else "lines.json"), encoding="utf-8"))
PHM = _phrase_marks()
def S(n): return ST_[n - 1]
def PS(n, k):
    """start time of phrase k (0-based) of line n: from the voice pauses when known, else proportional to text length"""
    ph = [max(4, len(p.strip())) for p in LINES[n - 1].split("|")]; k = min(k, len(ph) - 1)
    if PHM and len(PHM[n - 1]) == len(ph): return S(n) + PHM[n - 1][k]
    return S(n) + VO_[n - 1] * sum(ph[:k]) / sum(ph)
def E(n): return ST_[n - 1] + DU_[n - 1]
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
    ph = [p.strip() for p in LINES[n - 1].split("|")]
    k = max([i for i in range(len(ph)) if t >= PS(n, i) - 0.05] or [0])
    s = ph[k]; sz = fit(s, 56, 1640); w = font(sz).getlength(s)
    layer(img, lambda d: d.rounded_rectangle((960 - w / 2 - 34, 978 - sz * 0.85, 960 + w / 2 + 34, 978 + sz * 0.85), 24, fill=(0, 0, 0, 150)))
    rich(img, 960, 978, s, sz)

def rich(img, cx, cy, s, sz):
    """caption text with key words coloured (T["emph"]: word -> colour), drawn left to right"""
    import re
    keys = sorted(T.get("emph", {}), key=len, reverse=True)
    parts = re.split("(" + "|".join(map(re.escape, keys)) + ")", s) if keys else [s]
    if T.get("emph_re"):
        out = []
        for p in parts:
            out += [p] if p in T.get("emph", {}) else re.split("(" + T["emph_re"] + ")", p)
        parts = out
    f = font(sz); x = cx - f.getlength(s) / 2; sw = max(3, sz // 12)
    def draw(d):
        nonlocal x
        for p in parts:
            if not p: continue
            col = T.get("emph", {}).get(p) or (YEL if T.get("emph_re") and re.fullmatch(T["emph_re"], p) else WHT)
            d.text((x, cy), p, font=f, fill=col, anchor="lm", stroke_width=sw, stroke_fill=DK); x += f.getlength(p)
    layer(img, draw)


# ================================================================== template v4 "fight first": everything episode-specific lives in ep.py
exec(open(os.path.join(HERE, "ep.py"), encoding="utf-8").read())
T = TXT[LANG]
def SB(k): return S(B[k])
def PB(k, i): return PS(B[k], i)
def VB(k): return VO_[B[k] - 1]
def DB(k): return DU_[B[k] - 1]
FL.DN.SP[A_]["L"] = int(os.environ.get("LA", SIZE_A)); FL.DN.SP[B_]["L"] = int(os.environ.get("LB", SIZE_B))
SCENE_ = os.environ.get("SCENE", SCENE)   # one scene for the whole episode
COLD = 0.0

# ------------------------------------------------------------------ size chart: real silhouettes of both fighters + a person, on one metre scale
_SIL = {}
def _sil(kind, col):
    if (kind, col) not in _SIL:
        im = FL.DN.beast(kind, 0.0, "pose"); a = im.getchannel("A"); bb = a.getbbox(); a = a.crop(bb)
        s = Image.new("RGBA", a.size, col + (255,)); s.putalpha(a); _SIL[(kind, col)] = s
    return _SIL[(kind, col)]
def _human(d, x, g, m, col):
    d.ellipse((x - 0.12 * m, g - 1.75 * m, x + 0.12 * m, g - 1.51 * m), fill=col)
    d.rounded_rectangle((x - 0.2 * m, g - 1.5 * m, x + 0.2 * m, g - 0.85 * m), max(1, int(0.08 * m)), fill=col)
    d.rectangle((x - 0.16 * m, g - 0.9 * m, x - 0.03 * m, g), fill=col); d.rectangle((x + 0.03 * m, g - 0.9 * m, x + 0.16 * m, g), fill=col)
def size_chart(img, box, a, u):
    x0, y0, x1, y1 = box; chip(img, (x0 + x1) / 2, y0 + 8, T["size"], BLU, 44, a)
    m = (x1 - x0 - 120) / (max(LEN_A, LEN_B) + 1.2)   # px per metre
    rows = ((A_, LEN_A, BLU, T["title_a"] + f"  {T['len_a']}"), (B_, LEN_B, RED, T["title_b"] + f"  {T['len_b']}"))
    for i, (kind, ln, col, lab) in enumerate(rows):
        g = y0 + 330 + i * 330; aa = eout((u - 0.3 * i) / 0.4) * a
        layer(img, lambda d, g=g: (d.line((x0 + 30, g, x1 - 30, g), fill=DK, width=4)), a)
        layer(img, lambda d, g=g: _human(d, x0 + 60, g, m, (90, 90, 100)), aa)
        s = _sil(kind, col); w = int(ln * m); h = max(1, int(s.height * w / s.width))
        if aa > 0.01:
            sl = s.resize((w, h), Image.BICUBIC)
            if aa < 0.99: sl.putalpha(sl.getchannel("A").point(lambda v: int(v * aa)))
            img.alpha_composite(sl, (int(x0 + 100), int(g - h)))
        text(img, (x0 + 100, g + 40), lab, fit(lab, 36, x1 - x0 - 140), fill=col, anchor="lm", a=aa, sw=0)
    text(img, (x1 - 40, y1 - 40), T["hum"], 28, fill=(110, 110, 120), anchor="rm", a=a, sw=0)

def stats_table(img, t):
    u = t - SB("stats"); a = eout(u / 0.4); img.alpha_composite(Image.new("RGBA", img.size, (10, 14, 20, int(130 * a))))
    panel(img, (60, 130, 990, 900), a); size_chart(img, (60, 130, 990, 900), a, u)
    panel(img, (1020, 130, 1860, 900), a); chip(img, 1440, 140, T["stats"], RED, 52, a)
    text(img, (1480, 250), T["title_a"], fit(T["title_a"], 42, 250), fill=BLU, a=a, sw=0); text(img, (1730, 250), T["title_b"], fit(T["title_b"], 42, 250), fill=RED, a=a, sw=0)
    for i, (k, va, vb, win) in enumerate(T["rows"]):
        aa = eout((t - PB("stats", min(i + 1, len(LINES[B["stats"] - 1].split("|")) - 1)) + 0.1) / 0.35) * a; y = 360 + i * 135
        text(img, (1050, y), k, fit(k, 38, 260), fill=DK, anchor="lm", a=aa, sw=0)
        for x, v, me in ((1480, va, "a"), (1730, vb, "b")):
            good = win == me
            if good: layer(img, lambda d, x=x, y=y: d.rounded_rectangle((x - 118, y - 44, x + 118, y + 44), 22, fill=(230, 248, 230), outline=GRN, width=5), aa)
            text(img, (x, y), v, fit(v, 36, 220), fill=GRN if good else (120, 110, 100), a=aa, sw=0)

# ------------------------------------------------------------------ sections: hook teaser | fight round 1 | facts (paused) | round 2 + result | fossil truth + outro
def hide(C, who, t=0.0): C.k(who, t, x=(FL.AH - 2600) if who == "a" else (FL.BH + 2600))
def closeup(C, t, x=560, y=780, z=1.42, hold=0.9):
    C.cam(t + 0.02, z, x, y); C.cam(t + hold, z - 0.12, x, y + 20); C.cam(t + hold + 0.6, 1.0, 540, 880)
def new(): return FL.Choreo(A_, B_, SCENE_, land=True)
def sec_hook():
    t0, t1 = 0.0, SB("f1"); C = new(); C.stare(0.3, 1.2); C.clash(1.6, d=min(3.8, t1 - 2.2))   # action from second one (retention)
    tt = 1.6 + min(3.8, t1 - 2.2)
    while tt < t1: tt = C.stare(tt, 2.6)
    return t0, t1, C
def sec_f1():
    t0, t1 = SB("f1"), SB("pause"); C = new(); r = lambda k: SB(k) - t0
    fight1(C, r, t1 - t0); return t0, t1, C
def sec_facts():
    t0, t1 = SB("pause"), SB("back"); C = new(); tt = 0.3
    while tt < t1 - t0: tt = C.stare(tt, 2.6)
    return t0, t1, C
def sec_f2():
    t0, t1 = SB("back"), SB(TRUTH[0][0]); C = new(); r = lambda k: SB(k) - t0
    fight2(C, r, t1 - t0); return t0, t1, C
def sec_outro():
    t0, t1 = SB(TRUTH[0][0]), TOTAL; C = new(); tt = 0.3
    while tt < t1 - t0: tt = C.stare(tt, 2.6)
    tt = 0.0
    while LOSER_GONE and tt < t1 - t0 + 0.5: hide(C, "b" if WINNER == "a" else "a", tt); tt += 0.25   # the loser has left
    return t0, t1, C
SECS = []
for fn in (sec_hook, sec_f1, sec_facts, sec_f2, sec_outro):
    t0, t1, C = fn(); C.finalize(); SECS.append((t0, t1, C))

def fact_card(img, x0, name, col, facts, t):
    shown = [(k, v, PB(*at)) for k, v, at in facts if t >= PB(*at) - 0.05]
    if not shown: return
    a0 = eout((t - shown[0][2] + 0.05) / 0.4); w = 700; y0 = 150; h = 120 + 92 * len(facts)
    xs = x0 + (1 - a0) * (60 if x0 > 900 else -60)
    panel(img, (xs, y0, xs + w, y0 + h), a0); chip(img, xs + w / 2, y0 + 8, name, col, 50, a0)
    for i, (k, v, ts) in enumerate(shown):
        a = eout((t - ts) / 0.35); y = y0 + 100 + 92 * i
        text(img, (xs + 40, y), k, 40, fill=col, anchor="lm", a=a, sw=0)
        text(img, (xs + w - 40, y), v, fit(v, 44, w - 280), fill=DK, anchor="rm", a=a, sw=0)
        if i < len(facts) - 1: layer(img, lambda d, y=y: d.line((xs + 30, y + 46, xs + w - 30, y + 46), fill=(220, 210, 190), width=3), a)

def overlays(img, t):
    if t < SB("f1") + 1.0:   # title over the teaser
        a = eout((t - 0.2) / 0.5) * (1 - clamp((t - SB("f1") - 0.4) / 0.5))
        chip(img, 960, 90, T["series"] + "  " + T["ep"], RED, 44, a)
        text(img, (500, 260), T["title_a"], fit(T["title_a"], 104, 640), fill=WHT, a=a); text(img, (1420, 260), T["title_b"], fit(T["title_b"], 104, 680), fill=WHT, a=a)
        text(img, (960, 270), T["vs"], 150, fill=YEL, a=a)
    if SB("pause") <= t < SB("pause") + DB("pause"):   # freeze-frame moment
        u = t - SB("pause"); a = eout(u / 0.25) * (1 - clamp((u - DB("pause") + 0.6) / 0.5))
        img.alpha_composite(Image.new("RGBA", img.size, (10, 14, 20, int(90 * a))))
        chip(img, 960, 300, T["pause"], DK, 70, a)
    if SB("fa1") <= t < SB("fb1"): fact_card(img, 1140, T["title_a"], BLU, T["fa"], t)
    if SB("fb1") <= t < SB("stats"): fact_card(img, 80, T["title_b"], RED, T["fb"], t)
    if SB("stats") <= t < SB("back"): stats_table(img, t)
    if SB("back") <= t < SB("back") + 2.6: chip(img, 960, 140, T["round2"], RED, 70, eout((t - SB("back")) / 0.3) * (1 - clamp((t - SB("back") - 2.1) / 0.5)))
    if SB("q") <= t < PB("q", 1) + 0.6:
        a = eout((t - SB("q")) / 0.3) * (1 - clamp((t - PB("q", 1) - 0.2) / 0.4)); chip(img, 960, 150, T["q"], YEL, fit(T["q"], 60, 1500), a)
    if SB("win") <= t < SB("why"): chip(img, 960, 140, T["winner"], GRN, 76, eout((t - SB("win") - 0.6) / 0.4))
    if SB("why") <= t < SB(TRUTH[0][0]):
        a = eout((t - SB("why")) / 0.4); n = len(T["why_pts"]); panel(img, (1100, 180, 1860, 260 + 120 * n), a); chip(img, 1480, 188, T["why"], RED, 46, a)
        for i, (s, at) in enumerate(T["why_pts"]):
            aa = eout((t - PB(*at) + 0.1) / 0.35) * a; text(img, (1140, 320 + i * 120), "• " + s, fit(s, 44, 680), fill=DK, anchor="lm", a=aa, sw=0)
    for j, (k, title, rows) in enumerate(T["truth"]):
        nxt = SB(T["truth"][j + 1][0]) if j + 1 < len(T["truth"]) else SB("who")
        if SB(k) <= t < nxt:
            a = eout((t - SB(k)) / 0.4); img.alpha_composite(Image.new("RGBA", img.size, (10, 14, 20, int(110 * a))))
            panel(img, (300, 170, 1620, 300 + 130 * len(rows)), a); chip(img, 960, 180, title, RED, 54, a)
            for i, (s_, ph, col) in enumerate(rows):
                aa = eout((t - PB(k, ph) + 0.1) / 0.4) * a
                text(img, (960, 320 + i * 130), s_, fit(s_, 56 if col == GRN else 50, 1200), fill=col, a=aa, sw=0)
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
    fade = max(clamp(1 - u / 0.18) if i > 0 else clamp(1 - t / 0.3), clamp(1 - (t1 - t) / 0.18) if i < len(SECS) - 1 else clamp((t - (TOTAL - 0.8)) / 0.8))
    if fade > 0: img.alpha_composite(Image.new("RGBA", img.size, (0, 0, 0, int(255 * fade * 0.9))))
    return img.convert("RGB")
TOTAL_V = TOTAL
def frame_v(t): return frame(t)

def prep_audio_and_text():
    ff = os.environ.get("FFMPEG", "ffmpeg"); out = os.path.join(HERE, "..", "..", "out"); os.makedirs(out, exist_ok=True)
    src = os.path.join(HERE, "voice_en.wav" if LANG == "EN" else os.environ.get("VOICE_SRC", "voice_th.wav")); dst = os.path.join(HERE, "voice_cold.wav")
    if os.path.exists(src): subprocess.run([ff, "-v", "error", "-y", "-i", src, "-ac", "1", "-ar", "48000", dst], check=True)
    base = os.environ.get("EP_NAME", "EP")
    if LANG == "EN":
        lines = json.load(open(os.path.join(HERE, "lines_en.json"), encoding="utf-8"))
        for code in ("en", "es"):
            fp = os.path.join(HERE, f"lines_{code}.json")
            if os.path.exists(fp): srt(json.load(open(fp, encoding="utf-8")), list(ST_), VO_, os.path.join(out, f"{base}_{code.upper()}.srt"), lines_en=lines)
    def mm(x): x = int(x); return f"{x // 60}:{x % 60:02d}"
    pts = [0] + [SB(k) for k in CHK]
    open(os.path.join(out, f"{base}_chapters.txt"), "w", encoding="utf-8").write("\n".join(f"{mm(p)} {n}" for p, n in zip(pts, T["ch"])) + "\n")

def sfx(path):
    import numpy as np, soundfile as sf
    parts = []; sr = 48000
    for t0, t1, C in SECS:
        p = path + ".part.wav"; d = t1 - t0; C.sfx(p, d, drums=False); x, sr = sf.read(p, dtype="float32"); os.remove(p)
        n = int(d * sr); x = x[:n] if len(x) >= n else np.concatenate([x, np.zeros((n - len(x),) + x.shape[1:], np.float32)])
        f = int(0.15 * sr); x[:f] *= np.linspace(0, 1, f)[:, None] if x.ndim > 1 else np.linspace(0, 1, f); parts.append(x)
    sf.write(path, np.concatenate(parts) * 0.75, sr)

if __name__ == "__main__":
    m = sys.argv[1]
    if m == "info": prep_audio_and_text(); print(json.dumps({"TL": TOTAL_V, "frames": int(TOTAL_V * FPS), "lang": LANG}))
    elif m == "still":
        ims = [frame_v(float(x)) for x in sys.argv[2:]]; Sh = Image.new("RGB", (640 * min(3, len(ims)), 360 * ((len(ims) + 2) // 3)))
        for k, im in enumerate(ims): Sh.paste(im.resize((640, 360)), ((k % 3) * 640, (k // 3) * 360))
        Sh.save(os.environ.get("STILL_OUT", "stills.jpg"), quality=85)
    elif m == "sfx": sfx(sys.argv[2])
    elif m == "none": pass
    else:
        f0, f1, outp = int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]; prog = os.environ.get("PROG_FILE")
        pr = subprocess.Popen([os.environ.get("FFMPEG", "ffmpeg"), "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{OW}x{OH}", "-r", str(FPS), "-i", "-",
                               "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-threads", "2", "-pix_fmt", "yuv420p", outp], stdin=subprocess.PIPE)
        for k in range(f0, f1):
            pr.stdin.write(frame_v(k / FPS).tobytes())
            if prog and (k - f0) % 5 == 4: open(prog, "w").write(str(k - f0 + 1))
        pr.stdin.close(); pr.wait()
        if prog: open(prog, "w").write(str(f1 - f0))
