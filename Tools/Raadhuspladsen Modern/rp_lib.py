# Blender helpers for the Raadhuspladsen Modern scene.
# All inputs are UNITY scene coordinates (x right, y up, z forward); B() maps them to Blender
# so an FBX exported with axis_forward='-Z', axis_up='Y', bake_space_transform=True lands 1:1 in Unity.
import bpy, bmesh, json, math, os
from mathutils import Vector

SCRATCH = os.path.join(PROJECT, "Tools", "Raadhuspladsen Modern")  # holds osm/scene_features.json
ASSETS = os.path.join(PROJECT, "Assets", "3D Assets", "Raadhuspladsen Modern")

def B(x, y, z): return Vector((-x, -z, y))

def features():
    return {f['id']: f for f in json.load(open(SCRATCH + "/osm/scene_features.json"))}

def mat(name):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    return m

def new_obj(name, bm, material, coll=None):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    me.materials.append(mat(material))
    ob = bpy.data.objects.new(name, me)
    (coll or bpy.context.scene.collection).objects.link(ob)
    return ob

def world_uv(bm, tile=1.0):
    """Planar UVs from Unity x/z (or the dominant axis for walls), in metres / tile."""
    uv = bm.loops.layers.uv.verify()
    for f in bm.faces:
        n = f.normal  # Blender space
        for l in f.loops:
            p = l.vert.co; ux, uy, uz = -p.x, p.z, -p.y
            if abs(n.z) > 0.7: l[uv].uv = (ux / tile, uz / tile)
            elif abs(n.x) > abs(n.y): l[uv].uv = (uz / tile, uy / tile)
            else: l[uv].uv = (ux / tile, uy / tile)

def _offsets(pts, w):
    """Left/right offset points (Unity xz) for a polyline with mitred joints."""
    P = [Vector((x, z)) for x, z in pts]; L, R = [], []
    for i, p in enumerate(P):
        d0 = (p - P[i-1]).normalized() if i > 0 else None
        d1 = (P[i+1] - p).normalized() if i < len(P) - 1 else None
        d = (d0 + d1).normalized() if d0 and d1 and (d0 + d1).length > 1e-4 else (d0 or d1)
        n = Vector((-d.y, d.x))
        k = 1.0
        if d0 and d1: k = 1.0 / max(0.4, n.dot(Vector((-d0.y, d0.x))))
        L.append(p + n * (w / 2) * k); R.append(p - n * (w / 2) * k)
    return L, R

def ribbon(bm, pts, w, y):
    L, R = _offsets(pts, w)
    vl = [bm.verts.new(B(p.x, y, p.y)) for p in L]; vr = [bm.verts.new(B(p.x, y, p.y)) for p in R]
    for i in range(len(pts) - 1):
        f = bm.faces.new((vl[i], vr[i], vr[i+1], vl[i+1]))
        if f.normal.z < 0: f.normal_flip()

def polygon(bm, pts, y, height=0.0):
    """Filled polygon (closed ring, Unity xz). With height>0 it becomes a raised slab with sides."""
    if pts[0] == pts[-1]: pts = pts[:-1]
    top = [bm.verts.new(B(x, y + height, z)) for x, z in pts]
    f = bm.faces.new(top)
    if f.normal.z < 0: f.normal_flip()
    res = bmesh.ops.triangulate(bm, faces=[f])
    if height > 0:
        bot = [bm.verts.new(B(x, y, z)) for x, z in pts]
        n = len(pts)
        for i in range(n):
            s = bm.faces.new((bot[i], bot[(i+1) % n], top[(i+1) % n], top[i]))
        bmesh.ops.recalc_face_normals(bm, faces=[f for f in bm.faces if f.is_valid])
    bm.normal_update()

def box(bm, cx, cy, cz, sx, sy, sz, yaw=0.0):
    """Axis box in Unity coords centred at (cx,cy,cz), size sx,sy,sz, rotated yaw degrees about up."""
    r = bmesh.ops.create_cube(bm, size=1.0)
    vs = r['verts']; c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    for v in vs:
        ux, uz, uy = -v.co.x * sx, -v.co.y * sz, v.co.z * sy
        rx, rz = ux * c + uz * s, -ux * s + uz * c
        v.co = B(cx + rx, cy + uy, cz + rz)
    return vs

def export(objs, name):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        for c in o.users_collection: c.hide_viewport = False
        o.hide_set(False); o.select_set(True)
    assert all(o.select_get() for o in objs), "export: some objects could not be selected" 
    os.makedirs(ASSETS, exist_ok=True)
    bpy.ops.export_scene.fbx(filepath=f"{ASSETS}/{name}.fbx", use_selection=True, apply_scale_options='FBX_SCALE_UNITS',
        axis_forward='-Z', axis_up='Y', bake_space_transform=True, mesh_smooth_type='FACE', add_leaf_bones=False,
        use_mesh_modifiers=True, object_types={'MESH', 'EMPTY'})

def collection(name):
    c = bpy.data.collections.get(name)
    if c:
        for o in list(c.objects): bpy.data.objects.remove(o, do_unlink=True)
    else:
        c = bpy.data.collections.new(name); bpy.context.scene.collection.children.link(c)
    c.hide_viewport = False
    return c

def arch_cutter(bm, x, y0, w, h, depth, z0=-0.5):
    """Box + half-cylinder cutter for an arched opening, bottom at y0, total height h (needs use_self booleans)."""
    r = w / 2; hb = h - r
    box(bm, x, y0 + hb / 2, z0 + depth / 2, w, hb, depth)
    res = bmesh.ops.create_cone(bm, cap_ends=True, segments=16, radius1=r, radius2=r, depth=depth)
    for v in res['verts']:
        lx, ly, lz = v.co.x, v.co.y, v.co.z            # cone axis (Blender Z) -> Unity z
        v.co = B(x + lx, y0 + hb + ly, z0 + depth / 2 + lz)

def gable_roof(bm, x0, x1, z0, z1, y_eave, y_ridge, along_x=True):
    """Pitched roof over rect x0..x1, z0..z1 with the ridge along x (or along z)."""
    if along_x:
        zm = (z0 + z1) / 2
        v = [B(x0, y_eave, z0), B(x1, y_eave, z0), B(x1, y_ridge, zm), B(x0, y_ridge, zm), B(x0, y_eave, z1), B(x1, y_eave, z1)]
    else:
        xm = (x0 + x1) / 2
        v = [B(x0, y_eave, z1), B(x0, y_eave, z0), B(xm, y_ridge, z0), B(xm, y_ridge, z1), B(x1, y_eave, z1), B(x1, y_eave, z0)]
    V = [bm.verts.new(p) for p in v]
    bm.faces.new((V[0], V[1], V[2], V[3])); bm.faces.new((V[5], V[4], V[3], V[2]))
    bm.faces.new((V[0], V[3], V[4])); bm.faces.new((V[1], V[5], V[2]))

def boolean_cut(target, cutter_bm, coll):
    cut = new_obj("cutter", cutter_bm, "RP_Brick", coll)
    m = target.modifiers.new("cut", 'BOOLEAN'); m.object = cut; m.operation = 'DIFFERENCE'
    m.solver = 'EXACT'; m.use_self = True; m.use_hole_tolerant = True
    bpy.context.view_layer.objects.active = target; bpy.ops.object.modifier_apply(modifier="cut")
    bpy.data.objects.remove(cut, do_unlink=True)

def segment_matrix(p0, p1):
    """Blender matrix placing a local frame (x along p0->p1, z inward = right-hand side) at p0 (Unity xz)."""
    from mathutils import Matrix
    dx, dz = p1[0] - p0[0], p1[1] - p0[1]
    th = math.atan2(-dz, dx)                               # Unity yaw so local +x follows the segment
    return Matrix.Translation(B(p0[0], 0, p0[1])) @ Matrix.Rotation(-th, 4, 'Z'), math.hypot(dx, dz)

def facade_segment(name, p0, p1, coll, height, depth, rows, win_w=1.3, spacing=3.2, wall="RP_Brick",
                   roof="RP_RoofSlate", ridge=None, frame="RP_Frame"):
    """Brick block whose front follows p0->p1, windows cut per row (sill_y, win_h), simple pitched roof."""
    M, L = segment_matrix(p0, p1)
    n = max(1, int((L - 1.5) // spacing)); x0 = (L - (n - 1) * spacing) / 2
    objs = []
    bm = bmesh.new(); box(bm, L / 2, height / 2, 0.5, L, height, 1.0); box(bm, L / 2, height / 2, (1 + depth) / 2, L, height, depth - 1)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0005); world_uv(bm, 2.0)
    w = new_obj(name + "_Wall", bm, wall, coll)
    cut = bmesh.new(); glass = bmesh.new(); fr = bmesh.new(); bands = bmesh.new()
    for (sy, h) in rows:
        for i in range(n):
            x = x0 + i * spacing
            box(cut, x, sy + h / 2, 0.0, win_w, h, 1.2)
            box(glass, x, sy + h / 2, 0.3, win_w, h, 0.04)
            box(fr, x, sy + h / 2, 0.27, 0.07, h, 0.05); box(fr, x, sy + h * 0.7, 0.27, win_w, 0.07, 0.05)
        box(bands, L / 2, sy - 0.25, -0.06, L, 0.25, 0.12)
    box(bands, L / 2, height - 0.3, -0.15, L + 0.2, 0.6, 0.3)
    boolean_cut(w, cut, coll)
    for b in (glass, fr, bands): world_uv(b, 2.0)
    objs += [w, new_obj(name + "_Glass", glass, "RP_Glass", coll), new_obj(name + "_Frames", fr, frame, coll),
             new_obj(name + "_Bands", bands, "RP_Limestone", coll)]
    rb = bmesh.new(); gable_roof(rb, 0, L, 0.3, depth, height, ridge or height + depth * 0.6); world_uv(rb, 3.0)
    objs.append(new_obj(name + "_Roof", rb, roof, coll))
    for o in objs: o.data.transform(M)
    return objs
