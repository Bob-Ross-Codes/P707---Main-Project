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
    for o in objs: o.select_set(True)
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
    return c
