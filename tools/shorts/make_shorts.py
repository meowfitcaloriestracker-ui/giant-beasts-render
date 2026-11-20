import json, re, subprocess, sys
O="/mnt/user-data/outputs/"; ROAR="/home/claude/giant-beasts-render/engine/sounds/px/px-creature-roar-195717.wav"; END=3.0
def srt_starts(srt, lines):
    ts=[sum(float(x)*m for x,m in zip(re.split('[:,]',a)[:3],(3600,60,1)))+int(re.split('[:,]',a)[3])/1000 for a in re.findall(r'(\d\d:\d\d:\d\d,\d+) -->',open(srt,encoding='utf-8').read())]
    out=[];k=0
    for L in lines: out.append(ts[k]); k+=L.count('|')+1
    assert k==len(ts),(k,len(ts)); return out
EP={5:dict(segs=[(0,1),(5,7),(13,17)],TH="สัตว์ยักษ์VS_EP5_จิกาโนโตซอรัสVSทีเร็กซ์",EN="GiantBeastsVS_EP5_Giganotosaurus_vs_TRex"),
    6:dict(segs=[(0,1),(3,5),(11,15)],TH="สัตว์ยักษ์VS_EP6_สไปโนซอรัสVSซาร์โคซูคัส",EN="GiantBeastsVS_EP6_Spinosaurus_vs_Sarcosuchus")}
for ep,c in EP.items():
  for lang in ("TH","EN"):
    if lang=="TH": st=json.load(open(f"/home/claude/ep{ep}/timeline.json"))["starts"]; src=O+c["TH"]+"_แนวนอน_TH.mp4"; dst=O+"Shorts_"+c["TH"]+"_TH.mp4"
    else: st=srt_starts(O+c["EN"]+"_EN.srt", json.load(open(f"/home/claude/ep{ep}/lines_en.json"))); src=O+c["EN"]+"_EN.mp4"; dst=O+"Shorts_"+c["EN"]+"_EN.mp4"
    seg=[(max(0,st[a]-0.2) if a else 0.0, st[b]-0.15) for a,b in c["segs"]]
    durs=[b-a for a,b in seg]; T=sum(durs); n=len(seg)
    ins=[]; fc=""
    for i,(a,b) in enumerate(seg):
        ins+=["-ss",f"{a:.3f}","-t",f"{b-a:.3f}","-i",src]
        fc+=f"[{i}:a]afade=t=in:d=0.2,afade=t=out:st={durs[i]-0.3:.3f}:d=0.3[a{i}];[{i}:v]fps=30,setsar=1[v{i}];"
    fc+="".join(f"[v{i}][a{i}]" for i in range(n))+f"concat=n={n}:v=1:a=1[cv][ca];"
    fc+=(f"[cv]split[b][f];[b]scale=-2:1920,crop=1080:1920,boxblur=22:2,eq=brightness=-0.12[bg];[f]scale=1080:608[fg];[bg][fg]overlay=0:656[x1];[x1][{n}:v]overlay=0:0:shortest=1[x2];"
         f"[x2]tpad=stop_mode=clone:stop_duration={END}[x3];[x3][{n+1}:v]overlay=0:0:enable='gte(t,{T:.3f})':shortest=0,format=yuv420p,trim=duration={T+END:.3f}[v];"
         f"[{n+2}:a]atrim=0:{END},afade=t=out:st={END-0.8}:d=0.8,adelay={int(T*1000)}:all=1,volume=0.9[r];[ca]apad=whole_dur={T+END:.3f}[cp];[cp][r]amix=inputs=2:normalize=0:duration=first,alimiter=limit=0.95[a]")
    cmd=["ffmpeg","-y","-v","error",*ins,"-loop","1","-framerate","30","-i",f"ov{ep}_{lang}.png","-loop","1","-framerate","30","-i",f"end{ep}_{lang}.png","-i",ROAR,
         "-filter_complex",fc,"-map","[v]","-map","[a]","-c:v","libx264","-preset","medium","-crf","19","-r","30","-c:a","aac","-b:a","192k","-ar","48000","-movflags","+faststart","-t",f"{T+END:.3f}",dst]
    subprocess.run(cmd,check=True); print(ep,lang,round(T+END,1),[(round(a,1),round(b,1)) for a,b in seg])
