# -*- coding: utf-8 -*-
"""Meshy T. rex -> toon + outline + procedural skeleton (custom distance weights) + IK planted-foot walk / idle / roar-pose.
usage: python rig_trex.py -- FBX OUTDIR MODE [frames]   MODE = check | walk"""
import bpy, math, sys, os, numpy as np
from mathutils import Euler, Vector
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
FBX, OUT, MODE = argv[0], argv[1], argv[2]; NF = int(argv[3]) if len(argv) > 3 else 120
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "meshy_toon.py")).read().split("# ---- stage")[0].split("argv = sys.argv")[0])   # imports only
FPS = 24
sc = None
def setup():
    global sc
    bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
    sc.render.engine = "BLENDER_EEVEE_NEXT"; sc.eevee.taa_render_samples = 8; sc.render.fps = FPS
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1920, 1080, int(os.environ.get("PCT", 50))
    sc.view_settings.view_transform = "Standard"
setup()
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "meshy_toon.py")).read()
body = src.split("def lin(c)")[1].split("# ---- stage")[0]
exec("def lin(c)" + body.replace("FBX", repr(FBX)))
stage = src.split("# ---- stage (same desert look as the procedural test)")[1].split("os.makedirs(OUT")[0]
exec(stage)

# ---------------- skeleton (metres; head +X, body centred at x=0, feet on z=0)
B = {  # name: (head, tail, parent)
 "pelvis": ((0.4, 0, 2.55), (0.4, 0, 2.95), None),
 "spine":  ((0.4, 0, 2.7), (1.7, 0, 2.95), "pelvis"),
 "neck":   ((1.7, 0, 2.95), (2.6, 0, 3.55), "spine"),
 "head":   ((2.6, 0, 3.55), (4.7, 0, 3.55), "neck"),
 "tail1":  ((0.4, 0, 2.7), (-0.8, 0, 2.6), "pelvis"),
 "tail2":  ((-0.8, 0, 2.6), (-2.0, 0, 2.6), "tail1"),
 "tail3":  ((-2.0, 0, 2.6), (-3.3, 0, 2.7), "tail2"),
 "tail4":  ((-3.3, 0, 2.7), (-4.75, 0, 2.5), "tail3"),
}
for sd, y in (("L", 0.77), ("R", -0.77)):
    B.update({f"thigh.{sd}": ((0.4, y, 2.3), (0.7, y, 1.35), "pelvis"), f"shin.{sd}": ((0.7, y, 1.35), (0.2, y, 0.55), f"thigh.{sd}"),
              f"meta.{sd}": ((0.2, y, 0.55), (0.6, y, 0.14), f"shin.{sd}"), f"toe.{sd}": ((0.6, y, 0.14), (1.45, y, 0.05), f"meta.{sd}")})
arm_d = bpy.data.armatures.new("rig"); arm = bpy.data.objects.new("rig", arm_d); sc.collection.objects.link(arm)
bpy.context.view_layer.objects.active = arm; bpy.ops.object.mode_set(mode="EDIT")
for n, (h, t, p) in B.items():
    eb = arm_d.edit_bones.new(n); eb.head, eb.tail = h, t; eb.align_roll(Vector((0, 1, 0)))
for n, (h, t, p) in B.items():
    if p: eb = arm_d.edit_bones[n]; eb.parent = arm_d.edit_bones[p]; eb.use_connect = (Vector(arm_d.edit_bones[p].tail) - Vector(h)).length < 1e-4
bpy.ops.object.mode_set(mode="OBJECT")

# ---------------- weights: inverse-distance to bone segments, legs restricted to their side & below the hip
ob = [o for o in sc.objects if o.type == "MESH" and o.name.startswith("Mesh")][0]
V = np.array([v.co[:] for v in ob.data.vertices]); names = list(B)
def segd(P, a, b):
    a, b = np.array(a), np.array(b); ab = b - a; t = np.clip(((P - a) @ ab) / (ab @ ab), 0, 1); return np.linalg.norm(P - (a + t[:, None] * ab), axis=1)
D = np.stack([segd(V, *B[n][:2]) for n in names], 1)
for j, n in enumerate(names):
    if "." in n:
        sd = 1 if n.endswith("L") else -1
        bad = (V[:, 1] * sd < (0.32 if n.startswith("thigh") else 0.12)); D[bad, j] = 1e9
        if n.startswith("thigh"): D[:, j] += np.clip(V[:, 2] - 1.9, 0, None) * 1.2   # fade the thigh into the hip smoothly
    if n.startswith("toe") or n.startswith("meta"): D[V[:, 2] > 0.75, j] = 1e9
W = 1.0 / (D + 0.08) ** 4; top = np.argsort(-W, 1)[:, :3]
for j, n in enumerate(names): ob.vertex_groups.new(name=n)
for i in range(len(V)):
    ws = W[i, top[i]]; s = ws.sum()
    for j, w_ in zip(top[i], ws):
        if w_ / s > 0.02: ob.vertex_groups[names[j]].add([i], float(w_ / s), "REPLACE")
md = ob.modifiers.new("arm", "ARMATURE"); md.object = arm
while ob.modifiers[0].name != "arm": bpy.ops.object.modifier_move_up({"object": ob}, modifier="arm") if False else ob.modifiers.move(ob.modifiers.find("arm"), 0)
ob.parent = arm

# ---------------- IK legs
ik = {}
for sd, y in (("L", 0.77), ("R", -0.77)):
    tgt = bpy.data.objects.new(f"foot.{sd}", None); sc.collection.objects.link(tgt); tgt.location = (0.6, y, 0.14)
    pole = bpy.data.objects.new(f"pole.{sd}", None); sc.collection.objects.link(pole); pole.parent = arm; pole.location = (3.0, y, 1.4)
    c = arm.pose.bones[f"meta.{sd}"].constraints.new("IK"); c.target = tgt; c.chain_count = 3; c.pole_target = pole; c.pole_angle = math.radians(float(os.environ.get("POLE", 0)))
    ik[sd] = tgt
for pb in arm.pose.bones: pb.rotation_mode = "XYZ"
P = arm.pose.bones

def pose(t, speed, x0, roar=0.0):
    """t seconds; speed m/s (0 = idle). returns body x."""
    cyc = 1.25 if speed > 0 else 1.0; duty = 0.62
    bx = x0 + speed * t; ph = (t / cyc) % 1.0
    bob = (0.08 * math.cos(4 * math.pi * ph) if speed > 0 else 0.03 * math.sin(2 * math.pi * t / 3.0))
    arm.location = (bx, 0, bob)
    for sd, off, y in (("L", 0.0, 0.77), ("R", 0.5, -0.77)):
        p = (t / cyc + off) % 1.0; stride = speed * cyc; n = math.floor(t / cyc + off)
        if speed == 0: fx, fz = x0 + 0.6, 0.14
        elif p < duty:            # planted
            fx = x0 + 0.6 + (n - off) * stride + stride * 0.5 - (0) ; fx = x0 + 0.6 + stride * (n - off + 0.5); fz = 0.14
        else:                     # swing: lift and move to next plant
            q = (p - duty) / (1 - duty); q2 = q * q * q * (10 - 15 * q + 6 * q * q)
            fx = x0 + 0.6 + stride * (n - off + 0.5 + q2); fz = 0.14 + 0.45 * math.sin(math.pi * q)
        ik[sd].location = (fx, y, fz)
    sw = math.sin(2 * math.pi * t / (cyc if speed > 0 else 3.2))
    for k, n in enumerate(("tail1", "tail2", "tail3", "tail4")):
        P[n].rotation_euler = (0.06 * (k + 1) * math.sin(2 * math.pi * t / (cyc * 2 if speed else 3.2) - 0.6 * k), 0, 0.02 * sw)
    P["neck"].rotation_euler = (0, 0, -0.04 * sw * (speed > 0) + 0.35 * roar)
    P["head"].rotation_euler = (0.03 * math.sin(2 * math.pi * t / 2.7), 0, 0.03 * math.cos(4 * math.pi * ph) * (speed > 0) + 0.15 * roar)
    P["spine"].rotation_euler = (0, 0, -0.08 * roar)
    return bx

cam = sc.camera; cam.data.lens = 40
os.makedirs(OUT, exist_ok=True)
if MODE == "check":
    for k, t in enumerate((0.0, 0.3, 0.6)):
        bx = pose(t, 2.2, -2.0); bpy.context.view_layer.update()
        cam.location = (bx + 0.5, -9, 1.3); cam.rotation_euler = Euler((math.radians(88), 0, 0))
        sc.render.filepath = os.path.join(OUT, f"chk{k}.png"); bpy.ops.render.render(write_still=True)
else:   # steady walk, camera glides alongside then lets it pass
    for f in range(1, NF + 1):
        t = (f - 1) / FPS
        bx = pose(t, 2.2, -6.0, roar=0.35 * max(0.0, math.sin(math.pi * min(1, max(0, (t - 2.0) / 2.0)))))
        arm.keyframe_insert("location", frame=f)
        for sd in ik: ik[sd].keyframe_insert("location", frame=f)
        for pb in P: pb.keyframe_insert("rotation_euler", frame=f)
        cam.location = (-2.5 + 1.6 * t, -13.5, 2.6); cam.rotation_euler = Euler((math.radians(86), 0, math.radians(8 - 3 * t)))
        cam.keyframe_insert("location", frame=f); cam.keyframe_insert("rotation_euler", frame=f)
    sc.frame_start, sc.frame_end = int(os.environ.get("F0", 1)), NF
    sc.render.filepath = os.path.join(OUT, "f"); bpy.ops.render.render(animation=True)
print("DONE")
