# -*- coding: utf-8 -*-
"""ชุดเรนเดอร์ฉากต่อสู้ไดโนเสาร์ (สไตล์ช่องสัตว์ยักษ์) — เรนเดอร์ทั้งคลิปบนคอม
python make.py                      -> เมนูเลือกตัวละคร
python make.py trex spino           -> ผู้ชนะ (ซ้าย) / ผู้แพ้ (ขวา)
python make.py trex spino --test    -> ภาพตัวอย่าง 6 ภาพ (เร็ว)
เสียงพากย์: วางไฟล์เสียงหรือ zip จากแอปเสียงพากย์ไทยในโฟลเดอร์ voice
เพลง:      วางไฟล์ mp3 1 ไฟล์ในโฟลเดอร์ music
"""
import os, sys, glob, json, shutil, subprocess, tempfile, time, zipfile
from concurrent.futures import ThreadPoolExecutor

ENGINE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(ENGINE)
PY = sys.executable
FIGHTERS = [("trex", "ทีเร็กซ์"), ("spino", "สไปโนซอรัส"), ("tricera", "ไทรเซราทอปส์"), ("edmonto", "เอ็ดมอนโตซอรัส (ปากเป็ด)"),
            ("giga", "จิกาโนโตซอรัส"), ("carno", "คาร์โนทอรัส"), ("allo", "อัลโลซอรัส"), ("raptor", "ยูทาห์แรปเตอร์"),
            ("pachy", "แพคีเซฟาโลซอรัส"), ("anky", "แองคิโลซอรัส"), ("stego", "สเตโกซอรัส"), ("brachio", "แบรคิโอซอรัส"),
            ("therizino", "เทอริซิโนซอรัส"), ("parasaur", "พาราซอโรโลฟัส"), ("iguano", "อิกัวโนดอน"), ("dilo", "ไดโลโฟซอรัส"), ("styraco", "สไตราโคซอรัส"), ("kentro", "เคนโทรซอรัส"), ("baryonyx", "แบริออนิกซ์"), ("diplo", "ดิพโพลโดคัส"), ("mammoth", "แมมมอธ"), ("smilodon", "เสือเขี้ยวดาบ"), ("rhino", "แรดขนยาว"), ("sloth", "สลอธยักษ์"), ("sarco", "ซาร์โคซูคัส"), ("megalania", "เมกาลาเนีย"), ("quetzal", "เควตซัลโคแอตลัส"), ("paracera", "พาราเซราทีเรียม"), ("megalodon", "เมกาโลดอน"), ("mosasaurus", "โมซาซอรัส"), ("liopleurodon", "ไลโอพลูโรดอน"), ("elasmo", "อีลาสโมซอรัส"), ("dunkleosteus", "ดังเคิลออสเตียส"), ("livyatan", "ลิเวียทัน"), ("archelon", "อาร์คีลอน"), ("squid", "หมึกยักษ์")]
NAMES = dict(FIGHTERS)
AUD = (".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac")

def say(*a): print(*a, flush=True)

def find_tool(name):
    p = shutil.which(name)
    if p: return p
    pats = [os.path.join(ROOT, "ffmpeg", "**", name + ".exe"),
            os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg*\**\bin\\" + name + ".exe"),
            r"C:\ffmpeg\**\bin\\" + name + ".exe"]
    for pat in pats:
        hits = glob.glob(pat, recursive=True)
        if hits: return hits[0]
    say(f"ไม่พบ {name} — ดับเบิลคลิก ติดตั้ง.bat ก่อน"); input("กด Enter เพื่อปิด"); sys.exit(1)

def dur(ffprobe, path):
    r = subprocess.run([ffprobe, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path], capture_output=True, text=True)
    try: return float(r.stdout.strip())
    except ValueError: return 0.0

def collect_voice(ffmpeg, tmp, vdir=None):
    vdir = vdir or os.path.join(ROOT, "voice"); files = []
    for z in sorted(glob.glob(os.path.join(vdir, "*.zip"))):
        with zipfile.ZipFile(z) as zf:
            for nm in sorted(zf.namelist()):
                if nm.lower().endswith(AUD) and not nm.startswith("__MACOSX"):
                    out = os.path.join(tmp, f"vz{len(files):03d}" + os.path.splitext(nm)[1]); open(out, "wb").write(zf.read(nm)); files.append(out)
    files += sorted(f for f in glob.glob(os.path.join(vdir, "*")) if f.lower().endswith(AUD))
    if not files: return None
    lst = os.path.join(tmp, "v.txt")
    with open(lst, "w", encoding="utf-8") as f:
        for i, fn in enumerate(files):
            n = os.path.join(tmp, f"vn{i:03d}.wav")
            subprocess.run([ffmpeg, "-y", "-v", "error", "-i", fn, "-af", "silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse,apad=pad_dur=0.2",
                            "-ar", "48000", "-ac", "2", n], check=True)
            f.write(f"file '{n.replace(os.sep, '/')}'\n")
    out = os.path.join(tmp, "voice.wav")
    subprocess.run([ffmpeg, "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", out], check=True)
    return out

def voice_files(ffmpeg, tmp, vdir=None):
    """each voice file normalised to 48k stereo wav, trimmed of silence; order = script lines"""
    vdir = vdir or os.path.join(ROOT, "voice"); src = []
    for z in sorted(glob.glob(os.path.join(vdir, "*.zip"))):
        with zipfile.ZipFile(z) as zf:
            for nm in sorted(zf.namelist()):
                if nm.lower().endswith(AUD) and not nm.startswith("__MACOSX"):
                    out = os.path.join(tmp, f"lz{len(src):03d}" + os.path.splitext(nm)[1]); open(out, "wb").write(zf.read(nm)); src.append(out)
    src += sorted(f for f in glob.glob(os.path.join(vdir, "*")) if f.lower().endswith(AUD))
    outs = []
    for i, fn in enumerate(src):
        n = os.path.join(tmp, f"line{i:03d}.wav")
        subprocess.run([ffmpeg, "-y", "-v", "error", "-i", fn, "-af", "silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse",
                        "-ar", "48000", "-ac", "2", n], check=True)
        outs.append(n)
    return outs

def place_voice(files, starts, total, tmp):
    import numpy as np, soundfile as sf
    buf = np.zeros((int((total + 2) * 48000), 2), np.float32)
    for f, t in zip(files, starts):
        x, sr = sf.read(f, dtype="float32")
        if x.ndim == 1: x = np.stack([x, x], 1)
        o = int((t + 0.15) * 48000); m = min(len(x), len(buf) - o)
        if m > 0: buf[o:o + m] += x[:m]
    out = os.path.join(tmp, "voice_placed.wav"); sf.write(out, buf, 48000); return out

def menu():
    say("\n=== ชุดเรนเดอร์ฉากต่อสู้ไดโนเสาร์ (สไตล์ช่องสัตว์ยักษ์) ===\n")
    for i, (_, n) in enumerate(FIGHTERS, 1): say(f"  {i}. {n}")
    def pick(msg, default):
        s = input(msg).strip()
        return FIGHTERS[int(s) - 1][0] if s.isdigit() and 1 <= int(s) <= len(FIGHTERS) else default
    a = pick("\nตัวที่ชนะ (ยืนซ้าย) เลือกเลข [Enter = 1 ทีเร็กซ์]: ", "trex")
    b = pick("ตัวที่แพ้ (ยืนขวา) เลือกเลข [Enter = 2 สไปโนซอรัส]: ", "spino")
    if a == b:
        b = "spino" if a != "spino" else "trex"; say(f"เลือกตัวเดียวกันไม่ได้ เปลี่ยนตัวขวาเป็น {NAMES[b]}")
    t = input("ทำภาพตัวอย่างก่อน (เร็ว) พิมพ์ y / เรนเดอร์คลิปเต็ม กด Enter: ").strip().lower() == "y"
    return a, b, t

def run(a, b, test=False, progress=None, voice_dir=None, music_dir=None, script=None, captions=True):
    """renders one fight; progress(msg, pct). returns output path"""
    P = progress or (lambda m, p=None: say(m))
    ffmpeg, ffprobe = find_tool("ffmpeg"), find_tool("ffprobe")
    out_dir = os.path.join(ROOT, "out"); os.makedirs(out_dir, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    base = f"{a}_vs_{b}_{stamp}"
    tmp = tempfile.mkdtemp(prefix="dinofight_")
    env = dict(os.environ, FIGHT_A=a, FIGHT_B=b, FFMPEG=ffmpeg, TMAP=os.path.join(tmp, "tmap.json"), PYTHONIOENCODING="utf-8")
    t0 = time.time()
    lines = [l.strip() for l in (script or "").splitlines() if l.strip()]
    prog = "fightscript.py" if lines else "fight4.py"
    vfiles = []
    if lines:
        vfiles = voice_files(ffmpeg, tmp, voice_dir)
        durs = [dur(ffprobe, f) for f in vfiles] if len(vfiles) == len(lines) else []
        if vfiles and not durs: P(f"เสียงพากย์มี {len(vfiles)} ไฟล์ แต่บทมี {len(lines)} บรรทัด จะต่อเสียงรวดเดียวแทน (ฉากจะไม่ตรงทีละบรรทัด)", 1)
        sj = os.path.join(tmp, "script.json")
        json.dump({"lines": lines, "durs": durs, "captions": captions}, open(sj, "w", encoding="utf-8"), ensure_ascii=False)
        env["SCRIPT_JSON"] = sj
    if test:
        P("กำลังทำภาพตัวอย่าง 6 ภาพ...", 30)
        p = os.path.join(out_dir, base + "_preview.jpg")
        if lines:
            inf = json.loads(subprocess.run([PY, prog, "info"], cwd=ENGINE, env=env, capture_output=True, text=True, check=True).stdout.strip().splitlines()[-1])
            st = inf["starts"] + [inf["TL"]]
            ts = [str(round(min(st[i] + 1.0, (st[i] + st[i + 1]) / 2), 2)) for i in range(len(inf["starts"]))][:8]
        else:
            ts = ["2.2", "5.2", "8.2", "10.6", "12.9", "15"]
        subprocess.run([PY, prog, "still", *ts], cwd=ENGINE, env=dict(env, STILL_OUT=p), check=True, capture_output=True)
        P("ภาพตัวอย่างเสร็จแล้ว", 100); return p
    info = json.loads(subprocess.run([PY, prog, "info"], cwd=ENGINE, env=env, capture_output=True, text=True, check=True).stdout.strip().splitlines()[-1])
    nfr = info["frames"]; TL = info["TL"]
    cores = max(1, (os.cpu_count() or 2) - 1); parts = max(2, min(cores, 12))
    P(f"เรนเดอร์ {NAMES[a]} VS {NAMES[b]} ({nfr} เฟรม แบ่งทำพร้อมกัน {parts} ส่วน)", 2)
    bounds = [(nfr * i // parts, nfr * (i + 1) // parts) for i in range(parts)]
    stop = [False]
    def monitor():
        while not stop[0]:
            n = 0
            for i in range(parts):
                try: n += int(open(os.path.join(tmp, f"prog{i:02d}.txt")).read() or 0)
                except (OSError, ValueError): pass
            P(f"กำลังวาดภาพ {n}/{nfr} เฟรม", 2 + 83 * n // max(1, nfr)); time.sleep(1)
    def job(i):
        f0, f1 = bounds[i]; outp = os.path.join(tmp, f"part{i:02d}.mp4")
        r = subprocess.run([PY, prog, "render", str(f0), str(f1), outp], cwd=ENGINE, env=dict(env, PROG_FILE=os.path.join(tmp, f"prog{i:02d}.txt")), capture_output=True, text=True)
        if r.returncode != 0: raise RuntimeError(r.stderr[-1500:])
        return outp
    import threading
    mt = threading.Thread(target=monitor, daemon=True); mt.start()
    try:
        with ThreadPoolExecutor(parts) as ex: outs = list(ex.map(job, range(parts)))
    finally:
        stop[0] = True
    lst = os.path.join(tmp, "parts.txt")
    with open(lst, "w", encoding="utf-8") as f:
        for o in outs: f.write(f"file '{o.replace(os.sep, '/')}'\n")
    video = os.path.join(tmp, "video.mp4")
    subprocess.run([ffmpeg, "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", video], check=True)
    P("ใส่เสียงเอฟเฟกต์...", 88)
    sfx = os.path.join(tmp, "sfx.wav")
    if lines:
        subprocess.run([PY, prog, "sfx", sfx], cwd=ENGINE, env=env, check=True, capture_output=True)
    else:
        subprocess.run([PY, "fight_sfx_real.py"], cwd=ENGINE, env=dict(env, SFX_OUT=sfx), check=True, capture_output=True)
    if lines and vfiles and len(vfiles) == len(lines):
        voice = place_voice(vfiles, info["starts"], TL, tmp)
    else:
        voice = collect_voice(ffmpeg, tmp, voice_dir)
    mdir = music_dir or os.path.join(ROOT, "music")
    music = next((f for f in sorted(glob.glob(os.path.join(mdir, "*"))) if f.lower().endswith(AUD)), None)
    total = TL
    if voice:
        vd = dur(ffprobe, voice); total = TL if (lines and len(vfiles) == len(lines)) else max(TL, vd + 0.8)
    P("รวมภาพกับเสียง...", 93)
    cmd = [ffmpeg, "-y", "-v", "error", "-i", video, "-i", sfx]
    fl = [f"[0:v]tpad=stop_mode=clone:stop_duration={max(0, total - TL) + 0.1:.2f}[v]",
          f"[1:a]volume={0.7 if voice else 1.0}[s]"]; mix = ["[s]"]; n = 2
    if voice:
        cmd += ["-i", voice]; fl.append(f"[{n}:a]adelay={0 if lines and len(vfiles) == len(lines) else 300}|{0 if lines and len(vfiles) == len(lines) else 300},volume=1.5[vo]"); mix.append("[vo]"); n += 1
    if music:
        cmd += ["-stream_loop", "-1", "-i", music]
        fl.append(f"[{n}:a]volume={0.25 if voice else 0.45},afade=t=out:st={max(0, total - 1.5):.2f}:d=1.5[m]"); mix.append("[m]"); n += 1
    fl.append("".join(mix) + f"amix=inputs={len(mix)}:normalize=0:duration=longest,alimiter=limit=0.95[a]")
    out = os.path.join(out_dir, base + ".mp4")
    cmd += ["-filter_complex", ";".join(fl), "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "veryfast", "-crf", "19",
            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-t", f"{total:.2f}", "-movflags", "+faststart", out]
    subprocess.run(cmd, check=True)
    shutil.rmtree(tmp, ignore_errors=True)
    P(f"เสร็จแล้ว! ใช้เวลา {time.time() - t0:.0f} วินาที", 100)
    return out

def main():
    try: sys.stdout.reconfigure(encoding="utf-8")
    except Exception: pass
    args = [x for x in sys.argv[1:] if not x.startswith("--")]
    test = "--test" in sys.argv
    if len(args) >= 2: a, b = args[0], args[1]
    else: a, b, test = menu()
    out = run(a, b, test)
    say(f"\n{out}")
    if os.name == "nt": os.startfile(os.path.dirname(out))

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        say(f"\nเกิดข้อผิดพลาด: {e}\nถ่ายรูปหน้าจอนี้ส่งให้ Claude ได้เลย")
    if os.name == "nt": input("\nกด Enter เพื่อปิด")
