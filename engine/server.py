# -*- coding: utf-8 -*-
"""หน้าเว็บสำหรับกดเรนเดอร์ฉากต่อสู้ไดโนเสาร์ (เปิดที่ http://localhost:8790)"""
import os, sys, json, glob, shutil, threading, traceback, webbrowser, mimetypes, subprocess, time
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, unquote
import make, jobrun

PORT = 8790
UI = os.path.join(make.ENGINE, "ui")
DIRS = {"voice": os.path.join(make.ROOT, "voice"), "music": os.path.join(make.ROOT, "music")}
OUT = os.path.join(make.ROOT, "out")
for d in list(DIRS.values()) + [OUT]: os.makedirs(d, exist_ok=True)
STATE = {"busy": False, "msg": "พร้อมใช้งาน", "pct": 0, "result": None, "error": None, "t0": None, "t1": None}

def files(kind):
    return sorted(os.path.basename(f) for f in glob.glob(os.path.join(DIRS[kind], "*")) if not os.path.basename(f).startswith("."))

def outputs():
    fs = sorted((f for f in glob.glob(os.path.join(OUT, "*")) if f.lower().endswith((".mp4", ".jpg"))), key=os.path.getmtime, reverse=True)
    return [os.path.basename(f) for f in fs[:12]]

JOBS = os.path.join(make.ROOT, "jobs"); os.makedirs(JOBS, exist_ok=True)
def job_status(jd, **kv):
    p = os.path.join(jd, "status.json")
    try: st = json.load(open(p, encoding="utf-8"))
    except Exception: st = {}
    st.update(kv); json.dump(st, open(p, "w", encoding="utf-8"), ensure_ascii=False)
def job_watcher():
    """jobs that Claude writes into the jobs folder from the chat get rendered here automatically"""
    while True:
        try:
            for jd in sorted(glob.glob(os.path.join(JOBS, "*"))):
                if not os.path.isfile(os.path.join(jd, "job.json")) or os.path.exists(os.path.join(jd, "status.json")): continue
                if STATE["busy"]: break
                time.sleep(2)   # let all files of the job finish arriving
                name = os.path.basename(jd)
                STATE.update(busy=True, msg=f"งานจาก Claude: {name}", pct=1, result=None, error=None, t0=time.time(), t1=None)
                job_status(jd, state="running", started=time.time())
                print(f"  รับงานจาก Claude: {name}", flush=True)
                def prog(m, p=None, jd=jd):
                    STATE["msg"] = f"งานจาก Claude ({os.path.basename(jd)}): {m}"
                    if p is not None: STATE["pct"] = p
                    el = time.time() - STATE["t0"]; pct = STATE["pct"] or 0
                    job_status(jd, msg=m, pct=pct, elapsed=round(el), eta=round(el * (100 - pct) / pct) if pct >= 4 else None)
                try:
                    out = jobrun.run_job(jd, prog)
                    STATE.update(result=os.path.basename(out), msg=f"งานจาก Claude เสร็จแล้ว: {os.path.basename(out)}", pct=100)
                    job_status(jd, state="done", out=os.path.basename(out), elapsed=round(time.time() - STATE["t0"]))
                    print(f"  เสร็จ: {out}", flush=True)
                except Exception as e:
                    traceback.print_exc(); STATE.update(error=str(e)[-800:], msg="งานจาก Claude ผิดพลาด")
                    job_status(jd, state="error", error=str(e)[-3000:])
                finally:
                    STATE["busy"] = False; STATE["t1"] = time.time()
        except Exception:
            traceback.print_exc()
        time.sleep(3)

def worker(a, b, test, script, captions):
    def prog(m, p=None):
        STATE["msg"] = m
        if p is not None: STATE["pct"] = p
    try:
        out = make.run(a, b, test, prog, script=script, captions=captions)
        STATE.update(result=os.path.basename(out), msg="เสร็จแล้ว!", pct=100)
    except Exception as e:
        traceback.print_exc(); STATE.update(error=str(e)[-800:], msg="เกิดข้อผิดพลาด")
    finally:
        STATE["busy"] = False; STATE["t1"] = time.time()

class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def send(self, code, body, ctype="application/json; charset=utf-8"):
        if isinstance(body, (dict, list)): body = json.dumps(body, ensure_ascii=False).encode("utf-8")
        elif isinstance(body, str): body = body.encode("utf-8")
        self.send_response(code); self.send_header("Content-Type", ctype); self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store"); self.end_headers(); self.wfile.write(body)
    def file(self, path):
        if not os.path.isfile(path): return self.send(404, {"error": "not found"})
        size = os.path.getsize(path); ctype = mimetypes.guess_type(path)[0] or "application/octet-stream"
        rng = self.headers.get("Range")
        start, end = 0, size - 1
        if rng and rng.startswith("bytes="):
            s, e = rng[6:].split("-")[:2]; start = int(s or 0); end = int(e) if e else size - 1
            self.send_response(206); self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        else:
            self.send_response(200)
        self.send_header("Content-Type", ctype); self.send_header("Accept-Ranges", "bytes"); self.send_header("Content-Length", str(end - start + 1)); self.end_headers()
        with open(path, "rb") as f:
            f.seek(start); left = end - start + 1
            while left > 0:
                chunk = f.read(min(1 << 20, left))
                if not chunk: break
                try: self.wfile.write(chunk)
                except (BrokenPipeError, ConnectionResetError): return
                left -= len(chunk)
    def do_GET(self):
        u = urlparse(self.path); p = unquote(u.path)
        if p == "/": return self.file(os.path.join(UI, "index.html"))
        if p.startswith("/ui/"):
            nm = os.path.basename(p); f = os.path.join(UI, nm)
            return self.file(f if os.path.isfile(f) else os.path.join(make.ENGINE, "fonts", nm))
        if p.startswith("/out/"): return self.file(os.path.join(OUT, os.path.basename(p)))
        if p == "/status":
            now = time.time(); t0 = STATE["t0"]; el = ((STATE["t1"] or now) - t0) if t0 else 0
            pct = STATE["pct"] or 0; eta = el * (100 - pct) / pct if (STATE["busy"] and pct >= 4 and el > 5) else None
            return self.send(200, dict(STATE, elapsed=el, eta=eta, voice=files("voice"), music=files("music"), outputs=outputs()))
        self.send(404, {"error": "not found"})
    def do_POST(self):
        u = urlparse(self.path); p = u.path; q = parse_qs(u.query)
        n = int(self.headers.get("Content-Length") or 0)
        if p == "/upload":
            kind = q.get("kind", ["voice"])[0]; name = os.path.basename(unquote(q.get("name", ["file"])[0]))
            if kind not in DIRS: return self.send(400, {"error": "kind"})
            if q.get("first", ["0"])[0] == "1":
                for f in glob.glob(os.path.join(DIRS[kind], "*")): os.remove(f)
            with open(os.path.join(DIRS[kind], name), "wb") as f:
                left = n
                while left > 0:
                    chunk = self.rfile.read(min(1 << 20, left)); f.write(chunk); left -= len(chunk)
            return self.send(200, {"ok": True})
        body = json.loads(self.rfile.read(n) or b"{}") if n else {}
        if p == "/clear":
            kind = body.get("kind")
            if kind in DIRS:
                for f in glob.glob(os.path.join(DIRS[kind], "*")):
                    if not os.path.basename(f).startswith("."): os.remove(f)
            return self.send(200, {"ok": True})
        if p == "/render":
            if STATE["busy"]: return self.send(409, {"error": "busy"})
            a, b = body.get("a"), body.get("b")
            if a not in make.NAMES or b not in make.NAMES or a == b: return self.send(400, {"error": "เลือกไดโนเสาร์ 2 ตัวที่ไม่ซ้ำกัน"})
            STATE.update(busy=True, msg="เริ่มทำงาน...", pct=1, result=None, error=None, t0=time.time(), t1=None)
            threading.Thread(target=worker, args=(a, b, bool(body.get("test")), body.get("script") or "", body.get("captions", True) is not False), daemon=True).start()
            return self.send(200, {"ok": True})
        if p == "/open":
            target = OUT
            if body.get("file"): target = os.path.join(OUT, os.path.basename(body["file"]))
            if os.name == "nt": os.startfile(target)
            return self.send(200, {"ok": True})
        self.send(404, {"error": "not found"})

def main():
    try: sys.stdout.reconfigure(encoding="utf-8")
    except Exception: pass
    try:
        srv = ThreadingHTTPServer(("127.0.0.1", PORT), H)
    except OSError:
        print("โปรแกรมเปิดอยู่แล้ว กำลังเปิดหน้าเว็บ..."); webbrowser.open(f"http://localhost:{PORT}"); return
    print(f"\n  ชุดเรนเดอร์ฉากต่อสู้ไดโนเสาร์ เปิดอยู่ที่ http://localhost:{PORT}")
    print("  ** ห้ามปิดหน้าต่างดำนี้ระหว่างใช้งาน ใช้เสร็จแล้วค่อยปิด **\n")
    threading.Thread(target=job_watcher, daemon=True).start()
    print("  พร้อมรับงานจาก Claude ในแชต (โฟลเดอร์ jobs)\n")
    if "--no-browser" not in sys.argv: webbrowser.open(f"http://localhost:{PORT}")
    srv.serve_forever()

if __name__ == "__main__":
    main()
