from PIL import Image, ImageDraw, ImageFont, ImageFilter
F="/home/claude/fonts/Kanit-ExtraBold.ttf"; R="/home/claude/fonts/Kanit-Regular.ttf"
W,H=1080,1920; VY0,VY1=656,1264
def fit(d,txt,font,maxw,size):
    while size>20:
        f=ImageFont.truetype(font,size)
        if d.textlength(txt,font=f)<=maxw: return f
        size-=4
    return ImageFont.truetype(font,size)
def text(img,y,txt,font,size,fill,stroke=8,maxw=1000,shadow=True):
    d=ImageDraw.Draw(img); f=fit(d,txt,font,maxw,size)
    w=d.textlength(txt,font=f); x=(W-w)/2
    if shadow:
        sh=Image.new("RGBA",img.size,(0,0,0,0)); ImageDraw.Draw(sh).text((x+6,y+8),txt,font=f,fill=(0,0,0,170),stroke_width=stroke,stroke_fill=(0,0,0,170))
        img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(6)))
    d.text((x,y),txt,font=f,fill=fill,stroke_width=stroke,stroke_fill=(10,10,10))
    return f.size
def pill(img,y0,y1,col):
    d=ImageDraw.Draw(img); d.rounded_rectangle((70,y0,W-70,y1),radius=36,fill=col)
def overlay(lang):
    im=Image.new("RGBA",(W,H),(0,0,0,0)); d=ImageDraw.Draw(im)
    # thin frame lines around video
EPS = {
 5: dict(TH=("จิกาโนโตซอรัส","ทีเร็กซ์","ใครจะรอด?","ฟันเฉือน ปะทะ ฟันบดกระดูก","คอมเมนต์ทีม: จิกาโนฯ หรือ ทีเร็กซ์?"),
         EN=("GIGANOTOSAURUS","T. REX","WHO SURVIVES?","Slicing teeth vs bone-crushing bite","Comment your team: Giga or T. rex?")),
 6: dict(TH=("สไปโนซอรัส","ซาร์โคซูคัส","ใครจะรอด?","บนบก ปะทะ ในน้ำ","คอมเมนต์ทีม: สไปโน หรือ ซาร์โคซูคัส?"),
         EN=("SPINOSAURUS","SARCOSUCHUS","WHO SURVIVES?","Land vs water - who has the edge?","Comment your team: Spino or Sarco?")),
}
def overlay(ep, lang):
    a,b,q,pt,cm = EPS[ep][lang]
    im=Image.new("RGBA",(W,H),(0,0,0,0)); d=ImageDraw.Draw(im)
    d.rectangle((0,VY0-8,W,VY0),fill=(255,190,40,255)); d.rectangle((0,VY1,W,VY1+8),fill=(255,190,40,255))
    text(im,170,a,F,150,(255,255,255)); text(im,335,"VS",F,90,(255,60,40)); text(im,425,b,F,150,(255,255,255))
    pill(im,1330,1470,(220,30,30,235)); text(im,1338,q,F,96,(255,255,255),stroke=0,shadow=False,maxw=860)
    text(im,1530,("ตอนจบ + ความจริงจากฟอสซิล" if lang=="TH" else "The ending + real fossil facts"),R,64,(255,230,120),stroke=6)
    text(im,1620,("ดูคลิปเต็มที่หน้าช่อง" if lang=="TH" else "Full video on the channel"),F,78,(255,255,255),stroke=7)
    im.save(f"ov{ep}_{lang}.png")
    im=Image.new("RGBA",(W,H),(0,0,0,205))
    if lang=="TH":
        text(im,560,"ใครชนะ?",F,230,(255,200,40)); text(im,860,"ดูตอนจบในคลิปเต็มที่หน้าช่อง",F,80,(255,255,255),stroke=7)
    else:
        text(im,560,"WHO WINS?",F,210,(255,200,40)); text(im,860,"See the ending in the full video",F,76,(255,255,255),stroke=7)
    pill(im,1020,1170,(220,30,30,240)); text(im,1034,(pt if lang=="TH" else "Watch it on @FossyBeasts"),F,82,(255,255,255),stroke=0,shadow=False,maxw=860)
    text(im,1260,cm,R,58,(255,255,255),stroke=5)
    im.save(f"end{ep}_{lang}.png")
for e in (5,6):
    for L in ("TH","EN"): overlay(e,L)
