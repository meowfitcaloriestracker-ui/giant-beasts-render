# คลังของที่ทำไว้ใช้ซ้ำ (Giant Beasts VS)

ทุกอย่างที่สร้างให้ช่อง "สัตว์ยักษ์" / @FossyBeasts เก็บไว้ที่นี่ หยิบมาใช้กับตอนใหม่ได้ทันที

## 1. ฉาก (engine/scenes.py)
ฉากหลังวาดด้วยโค้ด ล็อกทั้งคลิป (ฉากไม่เปลี่ยน กล้องขยับได้) — ตั้งใน job ด้วย `SCENE_...` / env ของ section
| key | ฉาก | ของที่ขยับได้ (living.py v21) |
|---|---|---|
| jungle | ป่าดิบชื้น | ต้นไม้ใหญ่ไหวลม, ฝูงซอโรพอดไกลๆ, เทอโรซอร์บิน, หญ้าพลิ้ว |
| savanna | ทุ่งหญ้าแดดเย็น | ต้นอะคาเซียไหว, ฝูงซอโรพอด, เทอโรซอร์, หญ้าพลิ้ว |
| swamp | หนองบึงหมอก | ต้นไม้ตายไหว, ฝูงไดโนปากเป็ด, เทอโรซอร์ |
| canyon | หุบผาหินแดง | ต้นไม้แห้ง, ฝูงปากเป็ด, เทอโรซอร์ |
| beach | ชายฝั่งทะเล | ต้นมะพร้าวไหวแรง, ฝูงปากเป็ด, เทอโรซอร์ |
| storm | ทุ่งราบพายุ | ต้นไม้โยกแรง (ลม x2.2), ฝูงซอโรพอด, ฝน+ฟ้าแลบ |
| tundra | ทุ่งน้ำแข็ง | สนไหวเบาๆ, ฝูงแมมมอธ, นกบิน, หิมะตก |
| snowforest | ป่าสนหิมะ | สนไหว, ฝูงกวาง, นกบิน, หิมะตก |
| reef / kelp / deep | ใต้ทะเล | ฝูงปลาว่าย, ฟองอากาศ, แสงลอดน้ำ |
| abyss / ocean | ทะเลลึก / ผิวน้ำ | (ของเดิม) |

ทุกฉากบนบก: พุ่มไม้มุมจอด้านหน้าไหวตามลม (ให้ภาพมีมิติ)
ปิดได้ทีละส่วน: `LIVING=0` (ปิดหมด), `LIV_TREES=0`, `LIV_ANIMALS=0`, `LIV_FRONT=0`
เพิ่มฉาก/สัตว์ใหม่: เพิ่มใน `PRESET` และ `ANIMALS` ใน engine/living.py

## 2. ไดโนเสาร์ 2D (engine/dino45.py, v20)
37 ตัว: allo, anky, archelon, baryonyx, brachio, carno, chicken, dilo, diplo, dunkleosteus, edmonto, elasmo, giga, iguano, kentro, liopleurodon, livyatan, mammoth, megalania, megalodon, mosasaurus, pachy, paracera, parasaur, quetzal, raptor, rhino, sarco, sloth, smilodon, spino, squid, stego, styraco, therizino, trex, tricera — ดีไซน์ v20 แยกหน้าตาทีเร็กซ์ (หัวลึก ปุ่มเหนือตา) กับจิกาโนฯ (หัวยาวต่ำ สีเทาฟ้า)

## 3. แม่แบบตอน (template v4 "สู้ก่อน")
ดู jobs/ep5_th, jobs/ep6_th: ฉากชนเปิดเรื่อง → สู้รอบ 1 → หยุดภาพ+ข้อมูล → สถิติ+เทียบขนาด → สู้รอบ 2 → ทำไมชนะ → ความจริงจากฟอสซิล → ตอนหน้า
copy โฟลเดอร์ job แล้วแก้ ep.py + lines.json + voice

## 4. Shorts (tools/shorts)
- overlays.py — ป้ายชื่อคู่ชก / "ใครจะรอด?" / หน้าจอจบ "ใครชนะ? ดูคลิปเต็ม"
- make_shorts.py — ตัด 3 ช่วงจากคลิปยาว (ฉากชน, สู้รอบ 1, ไคลแมกซ์ — ตัดก่อนรู้ผล) ไทย+อังกฤษ 9:16

## 5. ปก + timeline (tools/covers, tools/make_timeline.py)

## 6. 3D Blender (tools/blender3d)
- dino3d.py — ไดโนปั้นด้วยโค้ด + เส้นขอบการ์ตูน (ต้นแบบ) + โหมด bench วัดความเร็ว GPU
- meshy_toon.py — นำเข้าโมเดล Meshy → สีการ์ตูน + เส้นขอบ
- rig_trex.py — ใส่กระดูก + ท่าเดินเท้าติดพื้น (IK) ให้ทีเร็กซ์ Meshy
- gpu_test.bat — ทดสอบบนคอม (GTX 1080 = 0.56 วิ/เฟรม 1080p)
- assets/3d/trex_meshy — โมเดล "Grumpy Little T Rex" สร้างด้วย Meshy (แพ็กฟรี CC BY 4.0 — ต้องใส่เครดิต "3D models: Meshy.ai" ในคำอธิบายคลิป)

## 7. วิเคราะห์คลิปคู่แข่ง (tools/yt)
GET_CLIP.bat + url.txt — yt-dlp + deno + ffmpeg บนคอม (โหลดมาศึกษาเท่านั้น ห้ามเอาภาพ/เสียงไปใช้ในคลิปเรา)

## 8. ไอเดียที่เก็บไว้ทำ
- ซีรีส์ "ถ้าปล่อย… 100 ตัว จะรอดกี่ตัว?" (ตัวนับค้างบนจอ, เรื่องมีหักมุม, คำถามปิดท้าย)
- Shorts "ฉากสู้ล้วน" 3D ไม่มีพากย์ ไฟล์เดียวลงได้ทุกช่อง (Part 1/2)
