# EP.6 Spinosaurus (a, left) vs Sarcosuchus (b, right) - river swamp, Spinosaurus wins
A_, B_ = "spino", "sarco"
SIZE_A, SIZE_B = 1300, 1000
LEN_A, LEN_B = 14.0, 9.5
SCENE = "swamp"
WINNER, LOSER_GONE = "a", True
B = dict(hook=1, f1=2, eyes=3, lunge=4, scream=5, pause=6, fa1=7, fa2=8, fb1=9, fb2=10, stats=11,
         back=12, drag=13, q=14, claw=15, release=16, win=17, why=18, why2=19, t1=20, t2=21, t3=22, t4=23, who=24, outro=25)
TRUTH = [("t1",), ("t2",), ("t3",), ("t4",)]
CHK = ["pause", "stats", "back", "why", "t1", "who"]

def fight1(C, r, D):
    hide(C, "b"); C.g("a", 0.0, "graze"); C.stare(0.2, 1.5)
    tin = PB("eyes", 1) - SB("f1")
    C.k("b", tin, x=FL.BH + 600); C.g("b", tin, "walk"); C.k("b", tin + 3.0, x=FL.BH); C.g("b", tin + 3.0, "pose")
    C.stalk("b", tin + 3.1, d=max(1.5, r("lunge") - tin - 3.3))
    C.g("a", r("lunge"), "pose"); C.strike("b", r("lunge") + 0.2, "bite", d=2.4)
    C.roar("a", r("scream") + 0.1, big=True)
    C.stare(r("scream") + 2.4, max(1.0, D - r("scream") - 2.8))

def fight2(C, r, D):
    C.stare(0.2, 1.0)
    C.shove("b", PB("back", 1) - SB("back"), d=min(3.0, DB("back")))
    C.shove("a", r("drag") + 0.3, d=min(3.4, DB("drag") - 0.2))
    C.stare(r("q") + 0.2, min(2.0, DB("q") - 0.5))
    s0 = r("claw") + 0.2; C.strike("a", s0, "swipe", d=2.2); closeup(C, s0 + 0.8 * 2.2, 700, 800)
    C.strike("a", s0 + 2.4, "swipe", d=2.0)
    C.limp("b", r("release") + 0.6, d=min(3.6, DB("release") - 0.6))
    C.victory("a", r("win") + 0.2)
    tt = r("why") + 0.3
    while tt < D - 0.8: tt = C.stare(tt, 2.6)
    tt = r("release") + 0.6 + min(3.6, DB("release") - 0.6)
    while tt < D + 0.5: hide(C, "b", tt); tt += 0.25

LB_, LR_ = (130, 205, 255), (255, 140, 120)
TXT = {
 "TH": dict(series="สัตว์ยักษ์ VS ใครจะชนะ?", ep="EP.6", title_a="สไปโนซอรัส", title_b="ซาร์โคซูคัส", vs="VS",
            pause="หยุดภาพ! ใครได้เปรียบ?", round2="ยกที่ 2", winner="ผู้ชนะ: สไปโนซอรัส!",
            fa=[("ยาว", "ราว 14 เมตร", ("fa1", 1)), ("หนัก", "ราว 7.4 ตัน", ("fa1", 1)), ("หาง", "แบนเหมือนใบพาย", ("fa2", 0)), ("ฟัน", "รูปกรวย งับปลา", ("fa2", 2))],
            fb=[("ยาว", "ราว 9.5 เมตร", ("fb1", 1)), ("หนัก", "ราว 4 ตัน", ("fb1", 1)), ("หัวกะโหลก", "ยาวถึง 1.6 เมตร", ("fb1", 2)), ("โตเต็มที่", "50–60 ปี", ("fb2", 0))],
            stats="สรุปสถิติ", size="เทียบขนาด", hum="คน 1.75 ม. (ซ้ายสุด)", len_a="~14 ม.", len_b="~9.5 ม.",
            rows=[("ความยาว", "~14 ม.", "~9.5 ม.", "a"), ("น้ำหนัก", "~7.4 ตัน", "~4 ตัน", "a"), ("ในน้ำ", "ว่ายได้", "ซุ่มโจมตี", "b")],
            q="คุณคิดว่าซาร์โคซูคัสจะปล่อยไหม?",
            why="ทำไมสไปโนซอรัสชนะ?", why_pts=[("หนักกว่าเกือบเท่าตัว", ("why", 1)), ("ลากขึ้นบก จระเข้เสียเปรียบ", ("why", 2)), ("แต่ในน้ำลึก จระเข้อาจชนะ", ("why2", 1))],
            truth=[("t1", "ความจริงจากฟอสซิล", [("ทั้งคู่ไม่เคยเจอกันจริง!", 1, DK), ("ซาร์โคซูคัสอยู่ก่อน ~15 ล้านปี", 2, RED)]),
                   ("t2", "สไปโนซอรัสตัวแรกของโลก", [("ขุดพบในอียิปต์", 1, DK), ("จัดแสดงที่มิวนิก เยอรมนี", 2, DK)]),
                   ("t3", "ปี 1944", [("ระเบิดในสงครามโลกครั้งที่ 2", 1, DK), ("ทำลายฟอสซิลจนหมด!", 2, RED)]),
                   ("t4", "หลายสิบปีต่อมา", [("ฟอสซิลชุดใหม่จากโมร็อกโก", 1, DK), ("หลักฐาน: น่าจะว่ายน้ำได้", 2, GRN)])],
            ch=["เปิดศึก: ซุ่มโจมตีริมแม่น้ำ", "ใครได้เปรียบ? ข้อมูลทั้งคู่", "สรุปสถิติ + เทียบขนาด", "ยกที่ 2", "ทำไมถึงชนะ", "ฟอสซิลที่หายไปในสงคราม", "ตอนต่อไป"],
            emph={"สไปโนซอรัส": LB_, "ซาร์โคซูคัส": LR_, "จระเข้ยักษ์": LR_, "อียิปต์": YEL, "มิวนิก": YEL, "โมร็อกโก": YEL, "เกือบสิบเมตร": YEL, "สิบสี่เมตร": YEL,
                  "เจ็ดตันครึ่ง": YEL, "เก้าเมตรครึ่ง": YEL, "สี่ตัน": YEL, "หนึ่งเมตรหกสิบ": YEL, "ห้าสิบถึงหกสิบปี": YEL, "เกือบเท่าตัว": YEL, "สิบห้าล้านปี": YEL,
                  "หนึ่งพันเก้าร้อยสี่สิบสี่": YEL, "สงครามโลกครั้งที่สอง": YEL, "ว่ายน้ำได้": YEL, "ผู้ชนะ": YEL, "ใบพาย": YEL},
            who="คุณคิดว่าใครชนะ? คอมเมนต์เลย!", next="ตอนหน้า: โมซาซอรัส VS ลิโอเพลอโรดอน", like="กดถูกใจ", share="แชร์", sub="ติดตาม"),
 "EN": dict(series="GIANT BEASTS VS · WHO WINS?", ep="EP.6", title_a="SPINOSAURUS", title_b="SARCOSUCHUS", vs="VS",
            pause="PAUSE! WHO HAS THE EDGE?", round2="ROUND 2", winner="WINNER: SPINOSAURUS!",
            fa=[("Length", "about 14 m", ("fa1", 1)), ("Weight", "about 7.4 t", ("fa1", 1)), ("Tail", "paddle-shaped", ("fa2", 0)), ("Teeth", "cones for fish", ("fa2", 2))],
            fb=[("Length", "about 9.5 m", ("fb1", 1)), ("Weight", "about 4 t", ("fb1", 1)), ("Skull", "up to 1.6 m", ("fb1", 2)), ("Full size", "50–60 years", ("fb2", 0))],
            stats="STATS CHECK", size="SIZE CHECK", hum="Human 1.75 m (far left)", len_a="~14 m", len_b="~9.5 m",
            rows=[("Length", "~14 m", "~9.5 m", "a"), ("Weight", "~7.4 t", "~4 t", "a"), ("In water", "swimmer", "ambusher", "b")],
            q="Do you think Sarcosuchus lets go?",
            why="Why did Spinosaurus win?", why_pts=[("Almost twice as heavy", ("why", 1)), ("Fight dragged onto land", ("why", 2)), ("In deep water, the croc might win", ("why2", 1))],
            truth=[("t1", "WHAT THE FOSSILS SAY", [("They never actually met!", 1, DK), ("Sarcosuchus: ~15 million years earlier", 2, RED)]),
                   ("t2", "THE FIRST SPINOSAURUS", [("Dug up in Egypt", 1, DK), ("Displayed in Munich, Germany", 2, DK)]),
                   ("t3", "1944", [("World War Two bombs", 1, DK), ("destroyed it completely!", 2, RED)]),
                   ("t4", "DECADES LATER", [("New fossils from Morocco", 1, DK), ("Evidence: it could probably swim", 2, GRN)])],
            ch=["Round 1: ambush at the river", "Who has the edge? The facts", "Stats + size check", "Round 2", "Why it won", "The fossil lost in a war", "Next episode"],
            emph={"Spinosaurus": LB_, "Spinosaurus's": LB_, "Sarcosuchus": LR_, "croc": LR_, "Egypt": YEL, "Munich": YEL, "Morocco": YEL, "World War Two": YEL, "winner": YEL, "swim": YEL},
            emph_re=r"\d[\d,.]*(?:\s?(?:-|to)\s?\d[\d,.]*)?(?:\s?(?:m|cm|kg|tonnes|meters|million years|years|times))?",
            who="Who wins? Tell us in the comments!", next="Next: Mosasaurus VS Liopleurodon", like="LIKE", share="SHARE", sub="SUBSCRIBE"),
}
