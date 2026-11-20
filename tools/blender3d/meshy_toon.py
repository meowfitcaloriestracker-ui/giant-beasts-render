# -*- coding: utf-8 -*-
"""Import a Meshy FBX dinosaur, make it a cartoon (toon shading from its own texture + black outline), render test views."""
import bpy, math, sys, os
from mathutils import Euler, Vector
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
FBX, OUT = argv[0], argv[1]; PCT = int(os.environ.get("PCT", 50))
bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
sc.render.engine = "BLENDER_EEVEE_NEXT"; sc.eevee.taa_render_samples = 8
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1920, 1080, PCT
sc.view_settings.view_transform = "Standard"

def lin(c): return (*[(x / 255) ** 2.2 for x in c], 1)
def flat(name, col, shadow=0.75):
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    for n in list(N): N.remove(n)
    o = N.new("ShaderNodeOutputMaterial"); d = N.new("ShaderNodeBsdfDiffuse"); s = N.new("ShaderNodeShaderToRGB"); r = N.new("ShaderNodeValToRGB")
    r.color_ramp.interpolation = "CONSTANT"; e = r.color_ramp.elements; e[0].color = (shadow,) * 3 + (1,); e[1].position = 0.2
    mx = N.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = "MULTIPLY"; mx.inputs[0].default_value = 1; mx.inputs[6].default_value = lin(col)
    em = N.new("ShaderNodeEmission")
    L.new(d.outputs[0], s.inputs[0]); L.new(s.outputs[0], r.inputs[0]); L.new(r.outputs[0], mx.inputs[7]); L.new(mx.outputs[2], em.inputs[0]); L.new(em.outputs[0], o.inputs[0])
    return m

# ---- import + normalise: head toward +X, feet on the ground, ~4.4 m tall
bpy.ops.import_scene.fbx(filepath=FBX)
ob = [o for o in bpy.context.scene.objects if o.type == "MESH"][0]
bpy.context.view_layer.objects.active = ob; ob.select_set(True)
ob.rotation_euler = Euler((0, 0, math.radians(90))); bpy.ops.object.transform_apply(rotation=True, scale=True)
zs = [v.co.z for v in ob.data.vertices]; s = 4.4 / (max(zs) - min(zs)); ob.scale = (s, s, s); bpy.ops.object.transform_apply(scale=True)
zmin = min(v.co.z for v in ob.data.vertices); xs = [v.co.x for v in ob.data.vertices]
for v in ob.data.vertices: v.co.z -= zmin; v.co.x -= (max(xs) + min(xs)) / 2
bpy.ops.object.shade_smooth()

# ---- toon material driven by the Meshy colour texture
img = None
for m in ob.data.materials:
    for n in m.node_tree.nodes:
        if n.type == "TEX_IMAGE" and n.image and "metal" not in n.image.name and "rough" not in n.image.name and img is None: img = n.image
m = bpy.data.materials.new("toon_tex"); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
for n in list(N): N.remove(n)
o = N.new("ShaderNodeOutputMaterial"); d = N.new("ShaderNodeBsdfDiffuse"); s2 = N.new("ShaderNodeShaderToRGB"); r = N.new("ShaderNodeValToRGB")
r.color_ramp.interpolation = "CONSTANT"; e = r.color_ramp.elements; e[0].color = (0.6, 0.6, 0.64, 1); e[1].position = 0.18; hi = e.new(0.8); hi.color = (1.1, 1.08, 1.04, 1)
tx = N.new("ShaderNodeTexImage"); tx.image = img
hsv = N.new("ShaderNodeHueSaturation"); hsv.inputs["Saturation"].default_value = 1.15; hsv.inputs["Value"].default_value = 1.05
mx = N.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = "MULTIPLY"; mx.inputs[0].default_value = 1
em = N.new("ShaderNodeEmission")
L.new(tx.outputs[0], hsv.inputs["Color"]); L.new(hsv.outputs[0], mx.inputs[6])
L.new(d.outputs[0], s2.inputs[0]); L.new(s2.outputs[0], r.inputs[0]); L.new(r.outputs[0], mx.inputs[7]); L.new(mx.outputs[2], em.inputs[0]); L.new(em.outputs[0], o.inputs[0])
ob.data.materials.clear(); ob.data.materials.append(m)
# outline: inverted hull
om = bpy.data.materials.new("outline"); om.use_nodes = True; N2 = om.node_tree.nodes
for n in list(N2): N2.remove(n)
oo = N2.new("ShaderNodeOutputMaterial"); oe = N2.new("ShaderNodeEmission"); oe.inputs[0].default_value = (0.02, 0.015, 0.01, 1); om.node_tree.links.new(oe.outputs[0], oo.inputs[0])
om.use_backface_culling = True; ob.data.materials.append(om)
so = ob.modifiers.new("outline", "SOLIDIFY"); so.thickness = float(os.environ.get("OUTLINE", 0.035)); so.offset = 1; so.use_flip_normals = True; so.material_offset = 1; so.use_rim = False

# ---- stage (same desert look as the procedural test)
w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True; w.node_tree.nodes["Background"].inputs[0].default_value = (0.98, 0.72, 0.45, 1)
bpy.ops.mesh.primitive_plane_add(size=200); bpy.context.object.data.materials.append(flat("ground", (214, 170, 96), 0.78))
for (x, y, rr) in ((-18, 40, 9), (6, 55, 14), (30, 45, 10), (-40, 60, 16)):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=rr, location=(x, y, -rr * 0.55)); bpy.ops.object.shade_smooth(); bpy.context.object.data.materials.append(flat("hill", (176, 140, 84), 0.82))
bpy.ops.object.light_add(type="SUN"); Ls = bpy.context.object; Ls.data.energy = 3; Ls.rotation_euler = Euler((math.radians(55), 0, math.radians(-40)))
bpy.ops.object.camera_add(); cam = bpy.context.object; cam.data.lens = 35; sc.camera = cam
os.makedirs(OUT, exist_ok=True)
for name, loc, rot in (("side", (0, -16, 2.6), (84, 0, 0)), ("threequarter", (9.5, -12.5, 3.0), (82, 0, 37)), ("front", (13, -5, 2.6), (84, 0, 68))):
    cam.location = loc; cam.rotation_euler = Euler([math.radians(a) for a in rot])
    sc.render.filepath = os.path.join(OUT, name + ".png"); bpy.ops.render.render(write_still=True)
print("DONE", img.name if img else None)
