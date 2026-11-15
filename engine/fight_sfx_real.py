"""fight SFX from real Pixabay recordings (in /home/claude/sfxreal), timed through the slow-mo map"""
import sys, os, json, glob, numpy as np, soundfile as sf
from scipy.signal import resample_poly
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from sfx2 import Mixer, SR, verb, norm, lp
TM = json.load(open(os.environ.get("TMAP", "fight_tmap.json"))); TL = TM["TL"]
def W_(a): return TM["ev"][str(round(a * 20) / 20)]
def S(key, pitch=1.0, a=0.0, b=None, fade=0.05):
    f = glob.glob(os.path.join(HERE, "sounds", f"*{key}*.wav"))[0]; x, sr = sf.read(f, dtype="float32")
    x = x[int(a * sr): int(b * sr) if b else None]
    if pitch != 1.0: x = resample_poly(x, 1000, int(1000 * pitch)).astype(np.float32)   # slower playback = deeper
    n = int(fade * SR); x[-n:] *= np.linspace(1, 0, n); return norm(x, 1.0)
def onsets(key, thr=0.35):
    x = S(key); env = np.convolve(np.abs(x), np.ones(480) / 480, "same"); idx = np.where((env[1:] > thr * env.max()) & (env[:-1] <= thr * env.max()))[0]
    out = [];
    for i in idx:
        if not out or i - out[-1] > SR * 0.3: out.append(i)
    return [x[i:i + int(0.5 * SR)] for i in out]
STEPS = onsets("colossal-footsteps") + onsets("giant-footsteps")
M = Mixer(TL + 1.0)
M.drums(W_(4.0), W_(12.9), bpm=150, inten=lambda t: 0.6, style="pop")
TREX_G, SPINO_G = S("dinosaur-growl-487679", 0.85), S("dinosaur-growls-431298", 1.1)
M.add(0.0, TREX_G, 0.55); M.add(0.4, SPINO_G[:int(2.5 * SR)], 0.35)
for k in range(5): M.add(W_(0.15 + k * 0.3), STEPS[k % len(STEPS)], 0.5)
M.add(W_(1.95), S("t-rex-dragon-reptile", 0.88), 1.0)                      # T. rex roar: deep
M.add(W_(3.1), S("roar-or-scream-2", 1.04), 0.95)                           # Spino answers: higher
M.add(W_(4.0), TREX_G[:int(1.0 * SR)], 0.6); M.add(W_(4.1), SPINO_G[:int(0.9 * SR)], 0.4)
for k in range(4): M.add(W_(4.6 + k * 0.13), STEPS[(k + 2) % len(STEPS)], 0.75)
M.add(W_(4.9), S("dramatic-whoosh"), 0.8)
M.add(W_(5.15), S("hard-heavy-impact"), 1.0); M.add(W_(5.15), S("cinematic-impact-boom"), 0.9)
M.add(W_(5.8), SPINO_G, 0.6); M.add(W_(6.0), TREX_G, 0.6)
M.add(W_(7.45), S("roar-or-scream-8", 1.1, 0, 1.2), 0.75)
M.add(W_(7.9), S("swing-whoosh"), 0.9); M.add(W_(8.1), S("bone-crack"), 0.9); M.add(W_(8.1), S("body-hit-ground"), 0.7)
M.add(W_(8.25), S("dinosaur-roar-390283", 0.8, 0.2, 1.6), 0.8)
M.add(W_(9.3), TREX_G[:int(1.4 * SR)], 0.85); M.add(W_(9.95), S("dramatic-whoosh"), 0.8)
for k in range(2): M.add(W_(10.02 + k * 0.11), STEPS[k % len(STEPS)], 0.8)
M.add(W_(10.25), S("hard-heavy-impact"), 1.0); M.add(W_(10.25), S("bone-snap"), 1.0); M.add(W_(10.25), S("cinematic-impact-boom"), 0.6)
M.add(W_(10.4), S("roar-or-scream-8", 1.15), 0.7)                          # Spino in pain
for k in range(3): M.add(W_(10.6 + k * 0.4), S("bone-crack", 1.0 + 0.08 * k), 0.5)
M.add(W_(11.95), S("dramatic-whoosh", 0.9), 1.0)
M.add(W_(12.86), S("heavy-body-fall", 0.85), 1.0); M.add(W_(12.86), S("cinematic-impact-boom", 0.8), 0.9)
M.add(W_(14.05), S("t-rex-victory-roar", 0.9), 1.0)
M.write(os.environ.get("SFX_OUT", "fight_sfx.wav"), fx_g=1.0, dr_g=0.25); print("ok", TL, len(STEPS))
