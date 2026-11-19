# EP.5 Giganotosaurus (a, left) vs T. rex (b, right) - savanna, T. rex wins
A_, B_ = "giga", "trex"
SIZE_A, SIZE_B = 1320, 1250          # engine drawing size
LEN_A, LEN_B = 12.5, 12.3            # real length in metres for the size chart
SCENE = "savanna"
WINNER, LOSER_GONE = "b", True
B = dict(hook=1, f1=2, eat=3, enter=4, roar=5, cut1=6, hold=7, pause=8, fa1=9, fa2=10, fb1=11, fb2=12, stats=13,
         back=14, dodge=15, q=16, ram=17, limp=18, win=19, why=20, why2=21, t1=22, t2=23, t3=24, who=25, outro=26)
TRUTH = [("t1",), ("t2",), ("t3",)]
CHK = ["pause", "stats", "back", "why", "t1", "who"]

def fight1(C, r, D):
    hide(C, "b"); C.g("a", 0.0, "graze")   # no stare here: it would pull T. rex on screen before its entrance
    tin = PB("enter", 1) - SB("f1")
    hide(C, "b", max(0.1, tin - 0.05))   # stay off-screen until it walks in
    C.k("b", tin, x=FL.BH + 700); C.g("b", tin, "walk"); C.k("b", tin + 2.6, x=FL.BH); C.g("b", tin + 2.6, "pose")
    C.g("a", tin + 0.4, "pose")
    C.roar("a", r("roar") + 0.2, big=True); C.roar("b", PB("roar", 1) - SB("f1"), big=True)
    g0 = r("cut1") + 0.3; C.strike("a", g0, "bite", d=2.4)
    C.stare(r("hold") + 0.3, max(1.0, D - r("hold") - 0.6))

def fight2(C, r, D):
    C.stare(0.2, 1.0)
    C.dodge("a", PB("back", 1) - SB("back"), d=2.2)
    s0 = r("dodge") + 0.6; C.strike("b", s0, "bite", d=2.6); closeup(C, s0 + 0.8 * 2.6, 1300, 760)
    C.shove("a", PB("q", 1) - SB("back"), d=min(3.0, DB("q") - 1.0))
    C.knockdown("b", r("ram") + 0.2, d=min(4.2, DB("ram") + 1.0))
    C.limp("a", r("limp") + 0.3, d=min(3.6, DB("limp")))
    C.victory("b", r("win") + 0.2)
    tt = r("why") + 0.3
    while tt < D - 0.8: tt = C.stare(tt, 2.6)
    tt = r("limp") + 0.3 + min(3.6, DB("limp"))
    while tt < D + 0.5: hide(C, "a", tt); tt += 0.25

LB_, LR_ = (130, 205, 255), (255, 140, 120)
TXT = {
 "TH": dict(series="สัตว์ยักษ์ VS ใครจะชนะ?", ep="EP.5", title_a="จิกาโนโตซอรัส", title_b="ทีเร็กซ์", vs="VS",
            pause="หยุดภาพ! ใครได้เปรียบ?", round2="ยกที่ 2", winner="ผู้ชนะ: ทีเร็กซ์!",
            fa=[("ยาว", "12–13 เมตร", ("fa1", 1)), ("หัวกะโหลก", "เกือบ 2 เมตร", ("fa1", 2)), ("รูปร่าง", "เพรียวกว่า", ("fa2", 0)), ("ฟัน", "แบนคม ไว้เฉือนเนื้อ", ("fa2", 1))],
            fb=[("ยาว", "ราว 12 เมตร", ("fb1", 1)), ("หนัก", "8–9 ตัน", ("fb1", 2)), ("แรงกัด", "สูงถึง 57,000 N", ("fb2", 1)), ("ฟัน", "บดกระดูกได้", ("fb2", 2))],
            stats="สรุปสถิติ", size="เทียบขนาด", hum="คน 1.75 ม. (ซ้ายสุด)", len_a="12–13 ม.", len_b="12.3 ม.",
            rows=[("ความยาว", "12–13 ม.", "~12 ม.", "a"), ("น้ำหนัก", "เบากว่า", "8–9 ตัน", "b"), ("แรงกัด", "เฉือน", "57,000 N", "b")],
            q="คุณคิดว่าจิกาโนโตซอรัสจะรอดไหม?",
            why="ทำไมทีเร็กซ์ชนะ?", why_pts=[("แรงกัดบดกระดูก", ("why", 1)), ("งับเดียวแผลร้ายแรง", ("why", 2)), ("ฟันจิกาฯ ไว้เฉือนเหยื่อช้า ๆ", ("why2", 1))],
            truth=[("t1", "ความจริงจากฟอสซิล", [("ทั้งคู่ไม่เคยเจอกันจริง!", 1, DK), ("จิกาโนโตซอรัส: อาร์เจนตินา", 2, DK), ("ก่อนทีเร็กซ์ ~30 ล้านปี", 3, RED)]),
                   ("t2", "ญาติของมัน: มาปูซอรัส", [("ฟอสซิลอยู่รวมกัน 7–9 ตัว", 1, DK), ("อาจล่าเป็นกลุ่ม?", 2, GRN)]),
                   ("t3", "ถ้ามาเป็นฝูง...", [("ทีเร็กซ์ตัวเดียวอาจไม่รอด!", 1, RED)])],
            ch=["เปิดศึก: ปะทะยกแรก", "ใครได้เปรียบ? ข้อมูลทั้งคู่", "สรุปสถิติ + เทียบขนาด", "ยกที่ 2", "ทำไมถึงชนะ", "ความจริงจากฟอสซิล", "ตอนต่อไป"],
            emph={"จิกาโนโตซอรัส": LB_, "ทีเร็กซ์": LR_, "มาปูซอรัส": LB_, "อาร์เจนตินา": YEL, "สิบสามเมตร": YEL, "สิบสองถึงสิบสามเมตร": YEL, "เกือบสองเมตร": YEL,
                  "แปดถึงเก้าตัน": YEL, "ห้าหมื่นเจ็ดพันนิวตัน": YEL, "บดกระดูก": YEL, "เฉือนเนื้อ": YEL, "สามสิบล้านปี": YEL, "เจ็ดถึงเก้าตัว": YEL, "ล่าเป็นกลุ่ม": YEL, "ผู้ชนะ": YEL, "ราชานักล่า": YEL},
            who="คุณคิดว่าใครชนะ? คอมเมนต์เลย!", next="ตอนหน้า: สไปโนซอรัส VS ซาร์โคซูคัส", like="กดถูกใจ", share="แชร์", sub="ติดตาม"),
 "EN": dict(series="GIANT BEASTS VS · WHO WINS?", ep="EP.5", title_a="GIGANOTOSAURUS", title_b="T. REX", vs="VS",
            pause="PAUSE! WHO HAS THE EDGE?", round2="ROUND 2", winner="WINNER: T. REX!",
            fa=[("Length", "12–13 m", ("fa1", 1)), ("Skull", "almost 2 m", ("fa1", 2)), ("Build", "slimmer", ("fa2", 0)), ("Teeth", "blades for slicing", ("fa2", 1))],
            fb=[("Length", "about 12 m", ("fb1", 1)), ("Weight", "8–9 t", ("fb1", 2)), ("Bite", "up to 57,000 N", ("fb2", 1)), ("Teeth", "bone-crushing", ("fb2", 2))],
            stats="STATS CHECK", size="SIZE CHECK", hum="Human 1.75 m (far left)", len_a="12–13 m", len_b="12.3 m",
            rows=[("Length", "12–13 m", "~12 m", "a"), ("Weight", "lighter", "8–9 t", "b"), ("Bite", "slicing", "57,000 N", "b")],
            q="Do you think Giganotosaurus survives?",
            why="Why did T. rex win?", why_pts=[("Bone-crushing bite", ("why", 1)), ("One bite = a terrible wound", ("why", 2)), ("Giga's teeth: for slow prey", ("why2", 1))],
            truth=[("t1", "WHAT THE FOSSILS SAY", [("They never actually met!", 1, DK), ("Giganotosaurus: Argentina", 2, DK), ("~30 million years before T. rex", 3, RED)]),
                   ("t2", "ITS RELATIVE: MAPUSAURUS", [("7–9 skeletons found together", 1, DK), ("Hunting in groups?", 2, GRN)]),
                   ("t3", "IF THEY CAME AS A PACK...", [("A lone T. rex might not survive!", 1, RED)])],
            ch=["Round 1", "Who has the edge? The facts", "Stats + size check", "Round 2", "Why it won", "What the fossils say", "Next episode"],
            emph={"Giganotosaurus": LB_, "T. rex": LR_, "T. rex's": LR_, "Mapusaurus": LB_, "Argentina": YEL, "winner": YEL, "bone": YEL},
            emph_re=r"\d[\d,.]*(?:\s?(?:-|to)\s?\d[\d,.]*)?(?:\s?(?:m|cm|kg|tonnes|meters|newtons|million years|skeletons|times))?",
            who="Who wins? Tell us in the comments!", next="Next: Spinosaurus VS Sarcosuchus", like="LIKE", share="SHARE", sub="SUBSCRIBE"),
}
