import os, sys, runpy
from PIL import Image, ImageDraw, ImageFont
ep=int(os.environ["EPN"]); os.chdir(f"/home/claude/ep{ep}"); sys.argv=["fight.py","none"]
g=runpy.run_path("fight.py",run_name="lib"); SB=g["SB"]; t0,t1,C=g["SECS"][3]
key,dur={5:("dodge",(0.6,2.6)),6:("claw",(0.2,2.2))}[ep]
tb=SB(key)+dur[0]+0.8*dur[1]-t0
if os.environ.get("MODE")=="pick":
    ims=[C.frame(tb+d).convert("RGB").resize((640,360)) for d in (-0.35,-0.15,0.0,0.15)]
    c=Image.new("RGB",(1280,720)); [c.paste(im,((i%2)*640,(i//2)*360)) for i,im in enumerate(ims)]; c.save(f"/tmp/cv{ep}.jpg"); sys.exit()
dt=float(os.environ["DT"]); fr=C.frame(tb+dt).convert("RGB").resize((1920,1080))
F="/home/claude/giant-beasts-render/engine/fonts/Kanit-ExtraBold.ttf"; W,H=1280,720
txt={5:(("จิกาโนโตซอรัส VS ทีเร็กซ์","ใครรอด?","EP.5"),("GIGANOTOSAURUS VS T. REX","WHO WINS?","EP.5")),
     6:(("สไปโนซอรัส VS จระเข้ยักษ์","ใครรอด?","EP.6"),("SPINOSAURUS VS SUPERCROC","WHO WINS?","EP.6"))}[ep]
names={5:("ปก_สัตว์ยักษ์VS_EP5_จิกาโนโตซอรัสVSทีเร็กซ์_TH.jpg","Thumbnail_GiantBeastsVS_EP5_Giganotosaurus_vs_TRex_EN.jpg"),
       6:("ปก_สัตว์ยักษ์VS_EP6_สไปโนซอรัสVSซาร์โคซูคัส_TH.jpg","Thumbnail_GiantBeastsVS_EP6_Spinosaurus_vs_Sarcosuchus_EN.jpg")}[ep]
crop=tuple(int(x) for x in os.environ.get("CROP","160,60,1760,960").split(","))
for (l1,l2,epl),nm in zip(txt,names):
    img=fr.crop(crop).resize((W,H)).convert("RGBA")
    bot=os.environ.get("TEXTPOS")=="bottom"
    grad=Image.new("L",(1,H)); [grad.putpixel((0,y), int(max(0,210*(1-((H-1-y) if bot else y)/290)))) for y in range(H)]
    img.alpha_composite(Image.merge("RGBA",[Image.new("L",(W,H),0)]*3+[grad.resize((W,H))]))
    d=ImageDraw.Draw(img)
    def fit(t,sz,mw):
        while ImageFont.truetype(F,sz).getlength(t)>mw: sz-=4
        return ImageFont.truetype(F,sz)
    def head(y,t,col,sz):
        f=fit(t,sz,1200); d.text((W/2,y),t,font=f,fill=col,anchor="mm",stroke_width=max(8,f.size//9),stroke_fill=(20,16,12))
    if bot: head(H-215,l2,(255,214,50),150); head(H-80,l1,(255,255,255),92); ey=30
    else: head(74,l1,(255,255,255),92); head(190,l2,(255,214,50),150); ey=H-100
    f=ImageFont.truetype(F,40); d.rounded_rectangle((30,ey,190,ey+70),18,fill=(20,16,12)); d.text((110,ey+35),epl,font=f,fill=(255,214,50),anchor="mm")
    img.convert("RGB").save("/mnt/user-data/outputs/"+nm,quality=92)
