# -*- coding: utf-8 -*-
"""Procedural 3D cartoon dinosaurs for Blender (bpy 4.5): skeleton points + Skin modifier -> smooth body,
inverted-hull outline, toon shading (Shader to RGB + constant colour ramp). Prototype: T. rex.
run:  python dino3d.py still OUT.png   |  python dino3d.py anim OUTDIR FRAMES"""
import bpy, math, sys, os
from mathutils import Vector, Euler

def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_EEVEE_NEXT"; sc.eevee.taa_render_samples = 8
    sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
    sc.render.film_transparent = False
    sc.view_settings.view_transform = "Standard"
    return sc

# ------------------------------------------------------------------ materials
def toon(name, col, shadow=0.62, rim=True, belly=None):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; N = nt.nodes; Lk = nt.links
    for n in list(N): N.remove(n)
    out = N.new("ShaderNodeOutputMaterial"); dif = N.new("ShaderNodeBsdfDiffuse"); s2r = N.new("ShaderNodeShaderToRGB")
    ramp = N.new("ShaderNodeValToRGB"); ramp.color_ramp.interpolation = "CONSTANT"
    e = ramp.color_ramp.elements; e[0].position = 0.0; e[0].color = (shadow, shadow, shadow, 1); e[1].position = 0.22; e[1].color = (1, 1, 1, 1)
    hi = e.new(0.85); hi.color = (1.12, 1.12, 1.12, 1)
    mix = N.new("ShaderNodeMix"); mix.data_type = "RGBA"; mix.blend_type = "MULTIPLY"; mix.inputs[0].default_value = 1.0
    mix.inputs[6].default_value = (*[(c / 255) ** 2.2 for c in col], 1)
    if belly:   # countershading: normals pointing down get the belly colour (soft-edged band)
        geo = N.new("ShaderNodeNewGeometry"); sep = N.new("ShaderNodeSeparateXYZ"); mr = N.new("ShaderNodeMapRange")
        mr.inputs[1].default_value = -0.25; mr.inputs[2].default_value = -0.4
        bm = N.new("ShaderNodeMix"); bm.data_type = "RGBA"
        bm.inputs[6].default_value = (*[(c / 255) ** 2.2 for c in col], 1); bm.inputs[7].default_value = (*[(c / 255) ** 2.2 for c in belly], 1)
        Lk.new(geo.outputs["Normal"], sep.inputs[0]); Lk.new(sep.outputs[2], mr.inputs[0]); Lk.new(mr.outputs[0], bm.inputs[0]); Lk.new(bm.outputs[2], mix.inputs[6])
    emis = N.new("ShaderNodeEmission")
    Lk.new(dif.outputs[0], s2r.inputs[0]); Lk.new(s2r.outputs[0], ramp.inputs[0]); Lk.new(ramp.outputs[0], mix.inputs[7])
    Lk.new(mix.outputs[2], emis.inputs[0]); Lk.new(emis.outputs[0], out.inputs[0])
    return m

def outline_mat():
    m = bpy.data.materials.new("outline"); m.use_nodes = True; nt = m.node_tree; N = nt.nodes
    for n in list(N): N.remove(n)
    out = N.new("ShaderNodeOutputMaterial"); em = N.new("ShaderNodeEmission"); em.inputs[0].default_value = (0.02, 0.016, 0.012, 1)
    nt.links.new(em.outputs[0], out.inputs[0]); m.use_backface_culling = True
    return m

def add_outline(ob, thick):
    ob.data.materials.append(OUT_M)
    s = ob.modifiers.new("outline", "SOLIDIFY"); s.thickness = thick; s.offset = 1.0; s.use_flip_normals = True
    s.material_offset = len(ob.data.materials) - 1; s.use_rim = False

# ------------------------------------------------------------------ body from a skeleton
def skin_body(name, pts, edges, radii, mat, sub=2):
    me = bpy.data.meshes.new(name); me.from_pydata(pts, edges, []); ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    sk = ob.modifiers.new("skin", "SKIN"); sk.use_smooth_shade = True
    for i, r in enumerate(radii):
        v = me.skin_vertices[0].data[i]; v.radius = r if isinstance(r, tuple) else (r, r)
    me.skin_vertices[0].data[0].use_root = True
    ss = ob.modifiers.new("sub", "SUBSURF"); ss.levels = sub; ss.render_levels = sub
    ob.data.materials.append(mat)
    return ob

def sphere(name, loc, r, mat, parent=None, scale=(1, 1, 1)):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=loc, segments=24, ring_count=12); o = bpy.context.object; o.name = name
    o.scale = scale; bpy.ops.object.shade_smooth(); o.data.materials.append(mat)
    if parent: o.parent = parent
    return o

def cone(name, loc, r, h, rot, mat):
    bpy.ops.mesh.primitive_cone_add(radius1=r, radius2=0, depth=h, location=loc, rotation=rot, vertices=8); o = bpy.context.object; o.name = name
    o.data.materials.append(mat); return o

# ------------------------------------------------------------------ T. rex (metres, x forward, z up)
SPECIES = {
 "trex": dict(col=(122, 100, 72), belly=(210, 190, 152), stripe=(84, 66, 48),
   # spine from tail tip to snout: (x, z, radius_y(width), radius_z(height))
   spine=[(-6.2, 2.55, 0.05, 0.05), (-5.0, 2.75, 0.18, 0.2), (-3.6, 3.0, 0.35, 0.42), (-2.2, 3.25, 0.58, 0.7), (-1.0, 3.35, 0.82, 0.95),
          (0.2, 3.3, 0.95, 1.05), (1.3, 3.25, 0.88, 0.95), (2.1, 3.45, 0.62, 0.66), (2.6, 3.85, 0.48, 0.5), (2.95, 4.15, 0.5, 0.52)],
   head=dict(at=(3.0, 4.2), len=1.55, h=0.62, w=0.5),
   leg=dict(hip=(0.1, 3.1), knee=(0.75, 1.75), ankle=(0.05, 0.7), toe=(0.75, 0.05), r=(0.62, 0.38, 0.22, 0.14), side=0.55),
   arm=dict(sh=(1.75, 3.0), el=(2.05, 2.55), hand=(2.3, 2.6), r=(0.12, 0.08, 0.06), side=0.6)),
}

def build(kind, x0=0.0, face=1):
    sp = SPECIES[kind]; col = sp["col"]
    body_m = toon(kind + "_body", col, belly=sp["belly"]); belly_m = toon(kind + "_belly", sp["belly"]); dark_m = toon(kind + "_dark", tuple(int(c * 0.55) for c in col))
    teeth_m = toon("teeth", (250, 244, 226), 0.85); eye_m = toon("eye", (252, 250, 240), 0.9); pup_m = toon("pupil", (14, 12, 10), 1.0); mouth_m = toon("mouth", (150, 60, 58))
    root = bpy.data.objects.new(kind, None); bpy.context.collection.objects.link(root); root.location = (x0, 0, 0); root.scale = (face, 1, 1)
    parts = []
    # body: spine chain
    pts, rad = [], []
    for (x, z, ry, rz) in sp["spine"]: pts.append((x, 0, z)); rad.append((ry, rz))
    edges = [(i, i + 1) for i in range(len(pts) - 1)]
    body = skin_body(kind + "_spine", pts, edges, rad, body_m); body.parent = root; parts.append((body, 0.035))
    # head: skull block + lower jaw (separate so the mouth can open)
    h = sp["head"]; hx, hz = h["at"]; L, H, Wd = h["len"], h["h"], h["w"]
    skull = skin_body(kind + "_skull", [(hx - 0.25, 0, hz), (hx + 0.45, 0, hz + 0.18), (hx + L * 0.75, 0, hz + 0.1), (hx + L, 0, hz - 0.02)],
                      [(0, 1), (1, 2), (2, 3)], [(Wd, H * 0.85), (Wd * 1.05, H), (Wd * 0.72, H * 0.72), (Wd * 0.5, H * 0.55)], body_m)
    jaw = skin_body(kind + "_jaw", [(hx - 0.1, 0, hz - 0.35), (hx + L * 0.55, 0, hz - 0.42), (hx + L * 0.95, 0, hz - 0.38)],
                    [(0, 1), (1, 2)], [(Wd * 0.8, 0.3), (Wd * 0.62, 0.22), (Wd * 0.42, 0.16)], belly_m)
    for o in (skull, jaw): o.parent = root; parts.append((o, 0.03))
    jaw_piv = bpy.data.objects.new(kind + "_jawpivot", None); bpy.context.collection.objects.link(jaw_piv); jaw_piv.parent = root
    jaw_piv.location = (hx - 0.1, 0, hz - 0.3); jaw.parent = jaw_piv; jaw.location = (-(hx - 0.1), 0, -(hz - 0.3))
    # mouth inside + teeth
    for k in range(9):
        tx = hx + 0.25 + k * (L * 0.72 / 8)
        for sgn in (-1, 1):
            t = cone(f"tooth{k}{sgn}", (tx, sgn * Wd * 0.62, hz - 0.36), 0.05 + 0.02 * (k % 3 == 1), 0.2, (math.pi, 0, 0), teeth_m); t.parent = root
    # eyes (only the camera-side one really shows) + brow
    for sgn in (-1, 1):
        e = sphere("eye", (hx + 0.38, sgn * Wd * 0.88, hz + 0.32), 0.13, eye_m); e.parent = root
        p = sphere("pupil", (hx + 0.43, sgn * Wd * 0.98, hz + 0.33), 0.065, pup_m); p.parent = root
        b = sphere("brow", (hx + 0.32, sgn * Wd * 0.85, hz + 0.5), 0.12, dark_m, scale=(1.8, 0.7, 0.6)); b.parent = root; b.rotation_euler = (0, 0.35, 0)
        # postorbital boss
        bs = sphere("boss", (hx + 0.12, sgn * Wd * 0.7, hz + 0.6), 0.14, body_m, scale=(1.3, 0.8, 0.8)); bs.parent = root; parts.append((bs, 0.02))
    # legs (both) and arms
    lg = sp["leg"]; pivs = []
    for sgn in (-1, 1):
        P = [(lg["hip"][0], sgn * lg["side"], lg["hip"][1]), (lg["knee"][0], sgn * lg["side"], lg["knee"][1]), (lg["ankle"][0], sgn * lg["side"] * 0.95, lg["ankle"][1]), (lg["toe"][0], sgn * lg["side"] * 0.95, lg["toe"][1])]
        piv = bpy.data.objects.new(f"{kind}_hip{sgn}", None); bpy.context.collection.objects.link(piv); piv.parent = root; piv.location = (lg["hip"][0], 0, lg["hip"][1]); pivs.append(piv)
        leg = skin_body(f"{kind}_leg{sgn}", P, [(0, 1), (1, 2), (2, 3)], [(r, r) for r in lg["r"]], body_m if sgn < 0 else dark_m); leg.parent = piv; leg.location = (-lg["hip"][0], 0, -lg["hip"][1]); parts.append((leg, 0.03))
        th = sphere("thigh", (lg["hip"][0] + 0.25, sgn * lg["side"] * 0.92, lg["hip"][1] - 0.45), 0.85, body_m if sgn < 0 else dark_m, scale=(1.15, 0.62, 1.25)); th.parent = piv; th.location = (0.25, sgn * lg["side"] * 0.92, -0.45); parts.append((th, 0.03))
        ar = sp["arm"]; A = [(ar["sh"][0], sgn * ar["side"], ar["sh"][1]), (ar["el"][0], sgn * ar["side"], ar["el"][1]), (ar["hand"][0], sgn * ar["side"], ar["hand"][1])]
        arm = skin_body(f"{kind}_arm{sgn}", A, [(0, 1), (1, 2)], [(r, r) for r in ar["r"]], body_m); arm.parent = root; parts.append((arm, 0.02))
    # back stripes: dark flattened spheres along the back
    for k, (x, z, ry, rz) in enumerate(sp["spine"][2:8]):
        s = sphere("stripe", (x, 0, z + rz * 0.55), 0.5, toon("stripe", sp["stripe"]), scale=(0.16, ry * 2.04, rz * 0.9)); s.parent = root
    for o, th in parts: add_outline(o, th)
    return dict(root=root, jaw=jaw_piv, hips=pivs)

def stage(sc):
    w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True; bg = w.node_tree.nodes["Background"]; bg.inputs[0].default_value = (0.98, 0.72, 0.45, 1); bg.inputs[1].default_value = 1.0
    bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, 0)); g = bpy.context.object; g.data.materials.append(toon("ground", (214, 170, 96), 0.75))
    for i, (x, y, r) in enumerate(((-18, 40, 9), (6, 55, 14), (30, 45, 10), (-40, 60, 16))):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=(x, y, -r * 0.55)); h = bpy.context.object; h.data.materials.append(toon("hill", (176, 140, 84), 0.8)); bpy.ops.object.shade_smooth()
    bpy.ops.object.light_add(type="SUN", location=(5, -8, 12)); L = bpy.context.object; L.data.energy = 3.0; L.rotation_euler = Euler((math.radians(55), 0, math.radians(-40)))
    bpy.ops.object.camera_add(location=(5.5, -16, 4.2), rotation=(math.radians(84), 0, math.radians(18))); cam = bpy.context.object; cam.data.lens = 35; sc.camera = cam
    return cam

if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]; sys.argv = [sys.argv[0]] + argv
    mode = sys.argv[1]; sc = reset(); sc.render.resolution_percentage = int(os.environ.get("PCT", 50)); OUT_M = outline_mat(); stage(sc)
    r = build("trex", x0=-1.0)
    if mode == "anim":   # walk in, stop, roar - camera slowly orbits to show it is 3D
        out, n = sys.argv[2], int(sys.argv[3]); sc.frame_start, sc.frame_end = 1, n; sc.render.fps = 24
        cam = sc.camera; c0 = cam.location.copy()
        for f in range(1, n + 1):
            t = (f - 1) / 24; walk = min(1.0, t / 1.6); u = 1 - (1 - walk) ** 2
            r["root"].location.x = -6.0 + 5.0 * u; r["root"].keyframe_insert("location", frame=f)
            sw = math.sin(t * 2 * math.pi * 1.2) * 0.45 * (1 - walk ** 4)
            r["hips"][0].rotation_euler = (0, sw, 0); r["hips"][1].rotation_euler = (0, -sw, 0)
            for h in r["hips"]: h.keyframe_insert("rotation_euler", frame=f)
            r["root"].location.z = 0.12 * abs(math.sin(t * 2 * math.pi * 1.2)) * (1 - walk ** 4); r["root"].keyframe_insert("location", frame=f)
            m = max(0.0, min(1.0, (t - 1.8) / 0.25)) * (1 - max(0.0, min(1.0, (t - 2.9) / 0.3)))
            r["jaw"].rotation_euler = (0, 0.5 * m, 0); r["jaw"].keyframe_insert("rotation_euler", frame=f)
            a_ = math.radians(18) + 0.25 * t / (n / 24); cam.location = (c0.x * math.cos(0.25 * t / (n / 24)) , c0.y, c0.z); cam.rotation_euler = (math.radians(84), 0, a_)
            cam.keyframe_insert("location", frame=f); cam.keyframe_insert("rotation_euler", frame=f)
        os.makedirs(out, exist_ok=True); sc.render.filepath = out + "/f"; sc.render.image_settings.file_format = "PNG"
        sc.frame_start = int(os.environ.get("F0", 1)); bpy.ops.render.render(animation=True)
    if mode == "bench":   # render N frames one by one at full HD and time each (GPU test)
        import time, platform
        out, n = sys.argv[2], int(sys.argv[3]); os.makedirs(out, exist_ok=True); sc.render.resolution_percentage = 100
        try:
            import gpu; gname = gpu.platform.renderer_get() + " | " + gpu.platform.version_get()
        except Exception as e: gname = "gpu? " + str(e)
        cam = sc.camera; c0 = cam.location.copy(); log = []
        for f in range(1, n + 1):
            t = f / 24.0; r["root"].location.x = -6.0 + 5.0 * min(1, t / 1.6)
            sw = math.sin(t * 2 * math.pi * 1.2) * 0.45; r["hips"][0].rotation_euler = (0, sw, 0); r["hips"][1].rotation_euler = (0, -sw, 0)
            r["jaw"].rotation_euler = (0, 0.5 * max(0, math.sin(t * 2)), 0)
            sc.render.filepath = os.path.join(out, "f%04d.png" % f); t0 = time.time(); bpy.ops.render.render(write_still=True); log.append(time.time() - t0)
        avg = sum(log[2:]) / max(1, len(log) - 2)
        txt = ("GPU: %s\nBlender: %s\nframes: %d at 1920x1080\nfirst frame: %.2f s\naverage (after warm-up): %.3f s/frame\n7-min clip (10080 frames) estimate: %.1f min\nall: %s\n"
               % (gname, bpy.app.version_string, n, log[0], avg, avg * 10080 / 60, ", ".join("%.2f" % x for x in log)))
        open(os.path.join(out, "..", "result.txt"), "w").write(txt); print(txt)
    if mode == "still":
        sc.render.filepath = sys.argv[2]; bpy.ops.render.render(write_still=True)
