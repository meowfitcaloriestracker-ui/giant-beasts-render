import numpy as np, soundfile as sf, json, sys
from math import gcd
from scipy.signal import resample_poly
src, n, outd = sys.argv[1], int(sys.argv[2]), sys.argv[3]
segs=[]
for i in range(1,n+1):
    a,sr=sf.read(f"{src}/{i:02d}.wav",dtype='float32')
    if a.ndim>1: a=a.mean(1)
    if sr!=48000: g=gcd(sr,48000); a=resample_poly(a,48000//g,sr//g).astype('float32')
    idx=np.where(np.abs(a)>0.01)[0]; a=a[max(0,idx[0]-480):idx[-1]+2400]; segs.append(a)
st=0.3; starts=[];durs=[];vo=[]
for a in segs:
    d=len(a)/48000; starts.append(round(st,3)); vo.append(round(d,3)); durs.append(round(d+0.5,3)); st+=d+0.5
total=round(st+1.2,3); out=np.zeros(int(total*48000)+10,'float32')
for s,a in zip(starts,segs): i=int(s*48000); out[i:i+len(a)]+=a
sf.write(f"{outd}/voice_th.wav",out,48000)
json.dump({"starts":starts,"durs":durs,"voice":vo,"total":total},open(f"{outd}/timeline.json","w"))
print(outd, round(total/60,2),"min", [round(v,1) for v in vo])
