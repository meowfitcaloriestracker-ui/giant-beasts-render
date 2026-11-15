# -*- coding: utf-8 -*-
"""render jobs that Claude writes into the jobs folder from the chat"""
import os, json, time, shutil, tempfile, subprocess
from concurrent.futures import ThreadPoolExecutor
from make import ENGINE, ROOT, PY, say, find_tool

def run_job(jobdir, progress=None):
    """render a job that Claude dropped into ROOT/jobs/<id>/:
       job.json {"name": "...", "fight": "fight.py", "sfx": "sfx.py" | null, "voice": "voice.wav" | null, "music": null | "file", "music_gain": 0.3}
       fight.py: same CLI as fight4.py (info / render f0 f1 out.mp4), may sys.path-insert ENGINE
       sfx.py  : writes the effects track to $SFX_OUT"""
    P = progress or (lambda m, p=None: say(m))
    cfg = json.load(open(os.path.join(jobdir, "job.json"), encoding="utf-8"))
    ffmpeg, ffprobe = find_tool("ffmpeg"), find_tool("ffprobe")
    out_dir = os.path.join(ROOT, "out"); os.makedirs(out_dir, exist_ok=True)
    tmp = tempfile.mkdtemp(prefix="dinojob_"); t0 = time.time()
    env = dict(os.environ, FFMPEG=ffmpeg, ENGINE=ENGINE, TMAP=os.path.join(tmp, "tmap.json"), PYTHONIOENCODING="utf-8", PYTHONPATH=ENGINE)
    env.update({k: str(v) for k, v in cfg.get("env", {}).items()})
    fight = cfg.get("fight", "fight.py")
    info = json.loads(subprocess.run([PY, fight, "info"], cwd=jobdir, env=env, capture_output=True, text=True, check=True).stdout.strip().splitlines()[-1])
    nfr = info["frames"]; TL = info["TL"]
    parts = max(2, min(max(1, (os.cpu_count() or 2) - 1), int(os.environ.get("MAXPARTS", 12))))
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
        r = subprocess.run([PY, fight, "render", str(f0), str(f1), outp], cwd=jobdir, env=dict(env, PROG_FILE=os.path.join(tmp, f"prog{i:02d}.txt")), capture_output=True, text=True)
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
    P("ใส่เสียง...", 90)
    cmd = [ffmpeg, "-y", "-v", "error", "-i", video]; fl, mix, n = [], [], 1
    if cfg.get("sfx"):
        sfx = os.path.join(tmp, "sfx.wav")
        subprocess.run([PY, cfg["sfx"]], cwd=jobdir, env=dict(env, SFX_OUT=sfx), check=True, capture_output=True)
        cmd += ["-i", sfx]; fl.append(f"[{n}:a]volume={cfg.get('sfx_gain', 1.0)}[s]"); mix.append("[s]"); n += 1
    if cfg.get("voice"):
        cmd += ["-i", os.path.join(jobdir, cfg["voice"])]; fl.append(f"[{n}:a]volume={cfg.get('voice_gain', 1.5)}[vo]"); mix.append("[vo]"); n += 1
    if cfg.get("music"):
        mp = cfg["music"] if os.path.isabs(cfg["music"]) else os.path.join(jobdir, cfg["music"])
        cmd += ["-stream_loop", "-1", "-i", mp]; fl.append(f"[{n}:a]volume={cfg.get('music_gain', 0.3)},afade=t=out:st={max(0, TL - 1.5):.2f}:d=1.5[m]"); mix.append("[m]"); n += 1
    out = os.path.join(out_dir, cfg.get("name", os.path.basename(jobdir)) + ".mp4")
    if mix:
        fl.append("".join(mix) + f"amix=inputs={len(mix)}:normalize=0:duration=longest,alimiter=limit=0.95[a]")
        cmd += ["-filter_complex", ";".join(fl), "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-t", f"{TL:.2f}", "-movflags", "+faststart", out]
    else:
        cmd += ["-c", "copy", "-movflags", "+faststart", out]
    subprocess.run(cmd, check=True)
    shutil.rmtree(tmp, ignore_errors=True)
    P(f"เสร็จแล้ว! ใช้เวลา {time.time() - t0:.0f} วินาที", 100)
    return out

