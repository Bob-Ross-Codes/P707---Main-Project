import os
# Run from Blender (Scripting tab or the Blender MCP). Set PROJECT to your checkout if __file__ is unknown.
PROJECT = globals().get("PROJECT") or os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
exec(open(os.path.join(PROJECT, "Tools", "Raadhuspladsen Modern", "rp_lib.py")).read())
# The 2013 city model as distant backdrop: baked to scene space (same transform as the old block-out
# instance) with every footprint that now has its own model removed.
from mathutils import Matrix
F = features()
CUT = ['r52142',        # City Hall
       'r11318365',     # the square itself (2013 pavilions etc.)
       'w25658852',     # Industriens Hus (under construction in 2013)
       'w638965060',    # Palace Hotel
       'w1013392339']   # corner block south of the Palace
cuts = [[tuple(p) for p in F[i]['pts']] for i in CUT]
def inside(x, z, poly):
    c = False; n = len(poly)
    for i in range(n):
        x1, z1 = poly[i]; x2, z2 = poly[(i + 1) % n]
        if (z1 > z) != (z2 > z) and x < x1 + (z - z1) * (x2 - x1) / (z2 - z1): c = not c
    if c: return True
    # walls sit exactly on the footprint edge, so also take faces within 1.5 m of the outline
    for i in range(n):
        x1, z1 = poly[i]; x2, z2 = poly[(i + 1) % n]
        dx, dz = x2 - x1, z2 - z1; L2 = dx * dx + dz * dz or 1e-9
        t = max(0.0, min(1.0, ((x - x1) * dx + (z - z1) * dz) / L2))
        if math.hypot(x - x1 - t * dx, z - z1 - t * dz) < 1.5: return True
    return False
C = collection("Backdrop")
for m in list(bpy.data.materials):            # keep the FBX material names exact (Unity remaps by name)
    if m.name.split('.')[0] in ("Facades", "Roofs"): bpy.data.materials.remove(m)
before = set(bpy.data.objects)
bpy.ops.import_scene.fbx(filepath=os.path.join(PROJECT, "Assets", "3D Assets", "Raadhuspladsen 2013", "Raadhuspladsen_2013.fbx"))
new = [o for o in bpy.data.objects if o not in before]
M = Matrix.Translation(B(-1.6344, -7.2390, 58.4215)) @ Matrix.Rotation(-math.radians(50.2677), 4, 'Z')
out = []
for o in new:
    for col in o.users_collection: col.objects.unlink(o)
    C.objects.link(o)
    if o.type != 'MESH': continue
    o.data.transform(M @ o.matrix_world); o.matrix_world = Matrix.Identity(4)
    bm = bmesh.new(); bm.from_mesh(o.data)
    kill = [f for f in bm.faces if any(inside(-f.calc_center_median().x, -f.calc_center_median().y, p) for p in cuts)]
    bmesh.ops.delete(bm, geom=kill, context='FACES')
    # UVs: walls get one window bay per 3.0 m x 3.2 m storey, roofs a 3 m planar tile
    uv = bm.loops.layers.uv.verify(); bm.normal_update()
    for f in bm.faces:
        n = f.normal
        if abs(n.z) < 0.5:
            t = Vector((-n.y, n.x)).normalized() if Vector((n.x, n.y)).length > 1e-6 else Vector((1, 0))
            for l in f.loops: l[uv].uv = ((l.vert.co.x * t.x + l.vert.co.y * t.y) / 3.0, l.vert.co.z / 3.2)
        else:
            for l in f.loops: l[uv].uv = (l.vert.co.x / 3.0, l.vert.co.y / 3.0)
    if o.name.startswith("Facades"):
        # four Copenhagen facade colours, one per building (connected piece of the mesh)
        names = ["RP_FacadeOchre", "RP_FacadeRed", "RP_FacadeWhite", "RP_FacadeGrey"]
        o.data.materials.clear()
        for nm in names: o.data.materials.append(mat(nm))
        import random; rnd = random.Random(9); seen = set(); bm.faces.index_update()
        for f in bm.faces:
            if f.index in seen: continue
            idx = rnd.randrange(4); stack = [f]
            while stack:
                g = stack.pop()
                if g.index in seen: continue
                seen.add(g.index); g.material_index = idx
                stack += [h for e in g.edges for h in e.link_faces if h.index not in seen]
    bm.to_mesh(o.data); bm.free()
    o.name = "Backdrop_" + o.name.split('.')[0]; out.append(o)
    print(o.name, "removed", len(kill), "faces")
export(out, "Raadhuspladsen Backdrop")
