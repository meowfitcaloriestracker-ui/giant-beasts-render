# -*- coding: utf-8 -*-
"""GitHub Actions renderer: prep (info + voice/srt) -> render (one slice per runner, all cores) -> merge (concat + audio)
python engine/gha.py prep JOB | render JOB SLICE NSLICES | merge JOB | assets JOB DIR"""
import os, sys, json, glob, shutil, subprocess
from concurrent.futures import ThreadPoolExecutor
ENGINE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(ENGINE); PY = sys.executable
PARTS = os.path.join(ROOT, "parts"); OUT = os.path.join(ROOT, "out")


def setup(job):
    jd = os.path.join(ROOT, "jobs", job); cfg = json.load(open(os.path.join(jd, "job.json"), encoding="utf-8"))
    env = dict(os.environ, FFMPEG="ffmpeg", ENGINE=ENGINE, TMAP=os.path.join(jd, "_tmap.json"), PYTHONIOENCODING="utf-8", PYTHONPATH=ENGINE)
    env.update({k: str(v) for k, v in cfg.get("env", {}).items()})
    return jd, cfg, env


def prep(job):
    jd, cfg, env = setup(job)
    r = subprocess.run([PY, cfg.get("fight", "fight.py"), "info"], cwd=jd, env=env, capture_output=True, text=True)
    if r.returncode:
        print(r.stdout[-3000:], r.stderr[-3000:]); sys.exit(1)
    info = json.loads(r.stdout.strip().splitlines()[-1]); json.dump(info, open(os.path.join(jd, "_info.json"), "w"))
    print(info)


def render(job, s, n):
    jd, cfg, env = setup(job); info = json.load(open(os.path.join(jd, "_info.json")))
    nfr, sub = info["frames"], os.cpu_count() or 4; tot = n * sub; os.makedirs(PARTS, exist_ok=True)

    def one(k):
        g = s * sub + k; f0, f1 = nfr * g // tot, nfr * (g + 1) // tot; outp = os.path.join(PARTS, f"part{g:04d}.mp4")
        if f1 <= f0: return None
        r = subprocess.run([PY, cfg.get("fight", "fight.py"), "render", str(f0), str(f1), outp], cwd=jd, env=env, capture_output=True, text=True)
        if r.returncode: raise RuntimeError(r.stderr[-3000:])
        return outp
    with ThreadPoolExecutor(sub) as ex:
        print([p for p in ex.map(one, range(sub)) if p])


def merge(job):
    jd, cfg, env = setup(job); info = json.load(open(os.path.join(jd, "_info.json"))); TL = info["TL"]
    parts = sorted(glob.glob(os.path.join(PARTS, "part*.mp4"))); os.makedirs(OUT, exist_ok=True)
    lst = os.path.join(PARTS, "parts.txt")
    with open(lst, "w") as f:
        for p in parts: f.write(f"file '{p}'\n")
    video = os.path.join(PARTS, "video.mp4")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", video], check=True)
    cmd = ["ffmpeg", "-y", "-v", "error", "-i", video]; fl, mix, n = [], [], 1
    if cfg.get("sfx"):
        sfx = os.path.join(PARTS, "sfx.wav")
        subprocess.run([PY, cfg["sfx"]], cwd=jd, env=dict(env, SFX_OUT=sfx), check=True)
        cmd += ["-i", sfx]; fl.append(f"[{n}:a]volume={cfg.get('sfx_gain', 1.0)}[s]"); mix.append("[s]"); n += 1
    if cfg.get("voice"):
        cmd += ["-i", os.path.join(jd, cfg["voice"])]; fl.append(f"[{n}:a]volume={cfg.get('voice_gain', 1.5)}[vo]"); mix.append("[vo]"); n += 1
    out = os.path.join(OUT, cfg.get("name", job) + ".mp4")
    if mix:
        fl.append("".join(mix) + f"amix=inputs={len(mix)}:normalize=0:duration=longest,alimiter=limit=0.95[a]")
        cmd += ["-filter_complex", ";".join(fl), "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-t", f"{TL:.2f}", "-movflags", "+faststart", out]
    else:
        cmd += ["-c", "copy", "-movflags", "+faststart", out]
    subprocess.run(cmd, check=True); print("->", out)


def assets(job, dst):
    """copy out/ files to ASCII names (GitHub mangles non-ASCII release asset names)"""
    os.makedirs(dst, exist_ok=True)
    for f in sorted(os.listdir(OUT)):
        if f.startswith("."): continue
        if f.isascii(): name = f
        else:
            stem, ext = os.path.splitext(f); tag = "_chapters" if stem.endswith("_chapters") else ""
            name = f"{job}{tag}{ext}"
        shutil.copy(os.path.join(OUT, f), os.path.join(dst, name)); print(f, "->", name)


if __name__ == "__main__":
    a = sys.argv[1:]
    {"prep": lambda: prep(a[1]), "render": lambda: render(a[1], int(a[2]), int(a[3])),
     "merge": lambda: merge(a[1]), "assets": lambda: assets(a[1], a[2])}[a[0]]()
